"""Per-person view settings that follow the account, not the browser.

Kept in ``prefs.json`` in the data folder, one entry per user name: which folders
are expanded in the sidebar tree, the language, and the documents pinned to the
start page.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

LANGUAGES = ("de", "en", "fr", "it")
EDITORS = ("source", "rich")      # how a page opens for editing: markdown source or formatted
ZOOM = (80, 250, 100)             # text size of pages in percent: lowest, highest, where everybody starts
WIDTH = (40, 100, 85)             # reading width in percent of the window: a little margin to begin with
MAX_PATHS = 5000
MAX_PATH_LEN = 1000
MAX_PINS = 200


def _within(value, limits: tuple[int, int, int]) -> int:
    low, high, default = limits
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default


class PrefsStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def _load(self) -> dict[str, dict]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        return {name: dict(p) for name, p in raw.get("users", {}).items()}

    def _save(self, users: dict[str, dict]) -> None:
        data = {"version": 1, "users": dict(sorted(users.items()))}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    def get(self, user: str) -> dict:
        with self._lock:
            p = self._load().get(user, {})
        return {"tree_open": list(p.get("tree_open", [])), "language": p.get("language", ""),
                "editor": p.get("editor") if p.get("editor") in EDITORS else "source",
                "zoom": _within(p.get("zoom"), ZOOM), "width": _within(p.get("width"), WIDTH)}

    def set_language(self, user: str, language: str) -> str:
        if language not in LANGUAGES:
            raise ValueError("unknown language")
        with self._lock:
            users = self._load()
            users.setdefault(user, {})["language"] = language
            self._save(users)
        return language

    def set_view(self, user: str, zoom: int | None = None, width: int | None = None) -> None:
        """How large and how wide pages read – follows the account to every browser."""
        with self._lock:
            users = self._load()
            p = users.setdefault(user, {})
            if zoom is not None:
                p["zoom"] = _within(zoom, ZOOM)
            if width is not None:
                p["width"] = _within(width, WIDTH)
            self._save(users)

    def set_editor(self, user: str, editor: str) -> str:
        if editor not in EDITORS:
            raise ValueError("unknown editor")
        with self._lock:
            users = self._load()
            users.setdefault(user, {})["editor"] = editor
            self._save(users)
        return editor

    def set_tree_open(self, user: str, paths: list[str]) -> list[str]:
        clean = sorted({str(p) for p in paths if p and len(str(p)) <= MAX_PATH_LEN})[:MAX_PATHS]
        with self._lock:
            users = self._load()
            users.setdefault(user, {})["tree_open"] = clean
            self._save(users)
        return clean

    def pins(self, user: str) -> list[str]:
        """Keys of the pinned documents in their order: page id, or content hash for a PDF."""
        with self._lock:
            return [str(k) for k in self._load().get(user, {}).get("pins", [])]

    def pin(self, user: str, key: str, on: bool) -> list[str]:
        with self._lock:
            users = self._load()
            pins = [k for k in users.get(user, {}).get("pins", []) if k != key]
            if on:
                if len(pins) >= MAX_PINS:
                    raise ValueError("too many pins")
                pins.append(key)
            users.setdefault(user, {})["pins"] = pins
            self._save(users)
        return pins

    def set_pins(self, user: str, keys: list[str]) -> list[str]:
        """A new order: only keys that are pinned already count, the rest keeps its place at the end."""
        with self._lock:
            users = self._load()
            have = list(users.get(user, {}).get("pins", []))
            first = [k for k in dict.fromkeys(keys) if k in have]
            pins = first + [k for k in have if k not in first]
            users.setdefault(user, {})["pins"] = pins
            self._save(users)
        return pins

    def repin(self, old: str, new: str) -> None:
        """A document got a new key (a page without id was given one): every pin follows."""
        with self._lock:
            users = self._load()
            hit = False
            for p in users.values():
                if old in p.get("pins", []):
                    p["pins"] = list(dict.fromkeys(new if k == old else k for k in p["pins"]))
                    hit = True
            if hit:
                self._save(users)

    def forget(self, user: str) -> None:
        with self._lock:
            users = self._load()
            if users.pop(user, None) is not None:
                self._save(users)
