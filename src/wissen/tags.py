"""Tags: labels across folders ("Heizung", "Garantie", "Haus Musterweg").

Tags belong to a document's content, not to its place: they are kept per SHA-256
in ``tags.json`` in the data folder, so they survive renaming and moving and the
archive files stay untouched. This file is configuration – it cannot be rebuilt
from the archive. (Tags a page names in its own head block are read from the file.)
"""

from __future__ import annotations

import json
import os
import re
import threading
from collections import Counter
from pathlib import Path

MAX_LEN = 40
MAX_PER_DOC = 30
_BAD = re.compile(r"[,#\x00-\x1f]")


class TagError(ValueError):
    pass


def clean(tag: str) -> str:
    tag = _BAD.sub(" ", str(tag or ""))
    tag = re.sub(r"\s+", " ", tag).strip()
    if len(tag) > MAX_LEN:
        raise TagError("tag too long")
    return tag


class TagStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._cache: tuple[int, dict[str, list[str]]] | None = None

    # ---------------------------------------------------------- persistence

    def _load(self) -> dict[str, list[str]]:
        try:
            mtime = self.path.stat().st_mtime_ns
        except FileNotFoundError:
            return {}
        if self._cache and self._cache[0] == mtime:
            return self._cache[1]
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        docs = {sha: list(tags) for sha, tags in raw.get("docs", {}).items() if tags}
        self._cache = (mtime, docs)
        return docs

    def _save(self, docs: dict[str, list[str]]) -> None:
        data = {"version": 1, "docs": {sha: tags for sha, tags in sorted(docs.items()) if tags}}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)
        self._cache = None

    # ---------------------------------------------------------------- read

    def of(self, sha: str) -> list[str]:
        return list(self._load().get(sha, []))

    def mapping(self) -> dict[str, list[str]]:
        return self._load()

    def shas_with_all(self, tags: list[str]) -> set[str]:
        wanted = {t.casefold() for t in tags}
        return {sha for sha, have in self._load().items() if wanted <= {t.casefold() for t in have}}

    def counts(self, shas: set[str] | None = None) -> list[dict]:
        """All tags with their number of documents (only those in ``shas`` if given)."""
        counter: Counter = Counter()
        spelling: dict[str, str] = {}
        for sha, tags in self._load().items():
            if shas is not None and sha not in shas:
                continue
            for t in tags:
                spelling.setdefault(t.casefold(), t)
                counter[t.casefold()] += 1
        return sorted(({"name": spelling[k], "count": n} for k, n in counter.items()),
                      key=lambda x: x["name"].casefold())

    # --------------------------------------------------------------- write

    def _canonical(self, docs: dict[str, list[str]], tag: str) -> str:
        """Use the spelling a tag already has elsewhere ("steuer 2026" → "Steuer 2026")."""
        key = tag.casefold()
        for tags in docs.values():
            for t in tags:
                if t.casefold() == key:
                    return t
        return tag

    @staticmethod
    def _merge(current: list[str], add: list[str], remove: list[str]) -> list[str]:
        drop = {t.casefold() for t in remove}
        result = [t for t in current if t.casefold() not in drop]
        have = {t.casefold() for t in result}
        for t in add:
            if t.casefold() not in have:
                result.append(t)
                have.add(t.casefold())
        if len(result) > MAX_PER_DOC:
            raise TagError("too many tags")
        return sorted(result, key=str.casefold)

    def set(self, sha: str, tags: list[str]) -> list[str]:
        cleaned = [c for c in (clean(t) for t in tags) if c]
        with self._lock:
            docs = dict(self._load())
            cleaned = [self._canonical(docs, t) for t in cleaned]
            docs[sha] = self._merge([], cleaned, [])
            self._save(docs)
            return docs[sha]

    def change(self, shas: list[str], add: list[str], remove: list[str]) -> int:
        add = [c for c in (clean(t) for t in add) if c]
        remove = [c for c in (clean(t) for t in remove) if c]
        with self._lock:
            docs = dict(self._load())
            add = [self._canonical(docs, t) for t in add]
            changed = 0
            for sha in set(shas):
                before = docs.get(sha, [])
                after = self._merge(before, add, remove)
                if after != before:
                    docs[sha] = after
                    changed += 1
            if changed:
                self._save(docs)
            return changed
