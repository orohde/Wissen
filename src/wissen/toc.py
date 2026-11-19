"""Inhaltsverzeichnis for magazines (and other long PDFs): articles with the page they start on.

The AI gets the top of every page (headline and lead sit there) with [Seite N] marks and lists the
articles. N is the page in the PDF – printed page numbers in a magazine differ from it, and the
reader jumps by PDF page. Kept per content in ``toc/<sha256>.json`` in the data folder.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

PAGE_BREAK = "\f"
PER_PAGE = 900
MAX_ENTRIES = 80
KINDS = ("Bauanleitung", "Werkstattpraxis", "Test", "Technik", "Tipps", "Porträt", "Rubrik", "Artikel")

SYSTEM = (
    "Du machst das Inhaltsverzeichnis einer Zeitschrift (oder eines langen Dokuments). Du bekommst den Anfang "
    "jeder Seite mit der Marke [Seite N].\n"
    "Antworte nur mit einer JSON-Liste: [{\"page\": 12, \"title\": \"…\", \"summary\": \"…\", \"kind\": \"…\"}].\n"
    "- page: die Seite N aus der Marke [Seite N], auf der der Beitrag BEGINNT. Nicht die im Heft gedruckte "
    "Seitenzahl (die steht im gedruckten Inhaltsverzeichnis und weicht ab).\n"
    "- title: die Überschrift des Beitrags, sinnvoll gekürzt.\n"
    "- summary: ein kurzer Satz, worum es geht (Werkstück, Technik, Werkzeug).\n"
    "- kind: eins von " + ", ".join(KINDS) + ".\n"
    "- Nur echte Beiträge. Keine Werbung, kein Impressum, keine Leserbriefe, keine Vorschau aufs nächste Heft, "
    "nicht das gedruckte Inhaltsverzeichnis selbst. Reihenfolge nach Seite."
)


def build_text(body: str) -> tuple[str, int]:
    pages = (body or "").split(PAGE_BREAK)
    parts = []
    for n, page in enumerate(pages, 1):
        page = re.sub(r"\s+", " ", page).strip()
        if page:
            parts.append(f"[Seite {n}] {page[:PER_PAGE]}")
    return "\n".join(parts), len(pages)


def parse(text: str, pages: int) -> list[dict]:
    match = re.search(r"\[.*\]", text or "", re.S)
    if not match:
        return []
    try:
        raw = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    entries = []
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict):
            continue
        try:
            page = int(item.get("page"))
        except (TypeError, ValueError):
            continue
        title = str(item.get("title") or "").strip()
        if not title or not 1 <= page <= max(pages, 1):
            continue
        kind = str(item.get("kind") or "").strip()
        entries.append({"page": page, "title": title[:200], "summary": str(item.get("summary") or "").strip()[:300],
                        "kind": kind if kind in KINDS else "Artikel"})
    entries.sort(key=lambda e: e["page"])
    return entries[:MAX_ENTRIES]


class TocStore:
    def __init__(self, folder: Path):
        self.folder = folder

    def _path(self, sha: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{64}", sha or ""):
            raise ValueError("bad hash")
        return self.folder / f"{sha}.json"

    def get(self, sha: str) -> dict | None:
        try:
            return json.loads(self._path(sha).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def put(self, sha: str, entries: list[dict], model: str) -> dict:
        self.folder.mkdir(parents=True, exist_ok=True)
        data = {"entries": entries, "model": model, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        path = self._path(sha)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, path)
        return data

    def known(self) -> set[str]:
        try:
            return {p.stem for p in self.folder.glob("*.json")}
        except OSError:
            return set()
