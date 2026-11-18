"""Earlier versions of pages and the lock that keeps two editors apart.

Versions live in the data folder, ``versions/<page id>/<time>--<who>.md``, not
next to the pages: the archive share stays free of clutter for SMB and sync
clients. A version is the text as it stood *before* a save.

The lock is held in memory only. It ends by itself when the editor stops
sending its heartbeat – a closed laptop must not block a page for good.
"""

from __future__ import annotations

import difflib
import re
import threading
import time
from datetime import datetime
from pathlib import Path

from .pages import ID_RE

LOCK_SECONDS = 600
_V_RE = re.compile(r"\d{8}T\d{12}")


class VersionError(ValueError):
    pass


class Versions:
    def __init__(self, root: Path):
        self.root = root

    def _dir(self, page_id: str) -> Path:
        if not ID_RE.fullmatch(page_id or ""):
            raise VersionError("unknown page")
        return self.root / page_id

    def save(self, page_id: str, text: str, by: str) -> str:
        folder = self._dir(page_id)
        folder.mkdir(parents=True, exist_ok=True)
        who = re.sub(r"[^\w .-]", "_", by or "")[:40].strip() or "unbekannt"
        while True:
            v = datetime.now().strftime("%Y%m%dT%H%M%S%f")
            if not any(folder.glob(f"{v}--*.md")):
                break
            time.sleep(0.001)
        (folder / f"{v}--{who}.md").write_text(text, encoding="utf-8")
        return v

    def _file(self, page_id: str, v: str) -> Path:
        if not _V_RE.fullmatch(v or ""):
            raise VersionError("unknown version")
        found = sorted(self._dir(page_id).glob(f"{v}--*.md"))
        if not found:
            raise VersionError("unknown version")
        return found[0]

    def list(self, page_id: str) -> list[dict]:
        """Newest first."""
        folder = self._dir(page_id)
        out = []
        if not folder.is_dir():
            return out
        for path in sorted(folder.glob("*--*.md"), reverse=True):
            v, _, who = path.stem.partition("--")
            if not _V_RE.fullmatch(v):
                continue
            out.append({"v": v, "at": datetime.strptime(v, "%Y%m%dT%H%M%S%f").isoformat(timespec="seconds"),
                        "by": who, "size": path.stat().st_size})
        return out

    def read(self, page_id: str, v: str) -> dict:
        path = self._file(page_id, v)
        _, _, who = path.stem.partition("--")
        return {"v": v, "at": datetime.strptime(v, "%Y%m%dT%H%M%S%f").isoformat(timespec="seconds"),
                "by": who, "text": path.read_text(encoding="utf-8")}


def diff(old: str, new: str, old_name: str = "version", new_name: str = "current") -> str:
    return "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                        old_name, new_name))


class Locked(Exception):
    def __init__(self, by: str):
        super().__init__(by)
        self.by = by


class Locks:
    def __init__(self, seconds: int = LOCK_SECONDS):
        self.seconds = seconds
        self._held: dict[str, dict] = {}
        self._lock = threading.Lock()

    def _live(self, page_id: str) -> dict | None:
        entry = self._held.get(page_id)
        if entry and entry["until"] <= time.time():
            del self._held[page_id]
            return None
        return entry

    def get(self, page_id: str) -> dict | None:
        with self._lock:
            entry = self._live(page_id)
            return dict(entry) if entry else None

    def acquire(self, page_id: str, holder: str, name: str) -> dict:
        """Take the lock or keep it alive; raises :class:`Locked` while someone else holds it."""
        with self._lock:
            entry = self._live(page_id)
            if entry and entry["holder"] != holder:
                raise Locked(entry["name"])
            now = time.time()
            entry = {"holder": holder, "name": name, "since": entry["since"] if entry else now,
                     "until": now + self.seconds}
            self._held[page_id] = entry
            return dict(entry)

    def release(self, page_id: str, holder: str, force: bool = False) -> bool:
        with self._lock:
            entry = self._live(page_id)
            if not entry:
                return False
            if entry["holder"] != holder and not force:
                raise Locked(entry["name"])
            del self._held[page_id]
            return True

    def move(self, old_id: str, new_id: str) -> None:
        with self._lock:
            if old_id != new_id and old_id in self._held:
                self._held[new_id] = self._held.pop(old_id)
