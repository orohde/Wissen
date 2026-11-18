"""SQLite index of the archive folders.

The folders are the source of truth. This index can be deleted at any time
and is rebuilt from the file system by :func:`Index.scan` and the text queue.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .pages import ASSET_SUFFIX, read_head

MIN_ID_LEN = 6
SCHEMA_VERSION = "w2"      # w2: the text of a PDF keeps its page breaks
EXTS = {"pdf", "md"}          # what the archive shows: PDFs and Markdown pages
SKIP_NAMES = {"@eaDir", "#recycle", "lost+found"}
SKIP_FILES = {"RCLONE_TEST", "Thumbs.db", "desktop.ini"}  # sync markers and system files
HL_START, HL_END = "\x02", "\x03"

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id        INTEGER PRIMARY KEY,
    path      TEXT NOT NULL UNIQUE,
    area      TEXT NOT NULL,
    folder    TEXT NOT NULL,
    name      TEXT NOT NULL,
    ext       TEXT NOT NULL,
    title     TEXT NOT NULL,
    doc_date  TEXT,
    size      INTEGER NOT NULL,
    mtime     REAL NOT NULL,
    sha256    TEXT NOT NULL,
    short_id  TEXT NOT NULL DEFAULT '',
    page_id   TEXT NOT NULL DEFAULT '',
    page_tags TEXT NOT NULL DEFAULT '[]',
    haystack  TEXT NOT NULL,
    seen      INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS files_area   ON files(area);
CREATE INDEX IF NOT EXISTS files_folder ON files(area, folder);
CREATE INDEX IF NOT EXISTS files_sha    ON files(sha256);
CREATE INDEX IF NOT EXISTS files_short  ON files(short_id);
CREATE INDEX IF NOT EXISTS files_page   ON files(page_id);
CREATE TABLE IF NOT EXISTS texts (
    sha256       TEXT PRIMARY KEY,
    body         TEXT NOT NULL,
    pages        INTEGER NOT NULL DEFAULT 0,
    ocr_pages    INTEGER NOT NULL DEFAULT 0,
    method       TEXT NOT NULL,
    error        TEXT NOT NULL DEFAULT '',
    extracted_at TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(
    place, title, body, tokenize = 'trigram remove_diacritics 1'
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

_NAME_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})[_ ](?P<title>.+?)(?:_(?P<sid>[0-9a-f]{6,64}))?$"
)


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def fold(text: str) -> str:
    """Normalise text for case-insensitive matching."""
    return nfc(text).casefold()


@dataclass(frozen=True)
class ParsedName:
    title: str
    doc_date: str | None


def parse_name(stem: str) -> ParsedName:
    """Split ``2026-10-01_Rezept_a3f9c1`` into date and title."""
    stem = nfc(stem)
    match = _NAME_RE.match(stem)
    if not match:
        return ParsedName(title=stem, doc_date=None)
    return ParsedName(title=match["title"].strip(), doc_date=match["date"])


def on_disk(root: Path, rel: str) -> Path:
    """The real file for an index path.

    The index keeps paths in NFC; a name written on a Mac may sit on disk in NFD
    ("ü" as u + diaeresis). Where the plain path does not exist, each part is
    matched against the folder's entries by its NFC form.
    """
    direct = root / rel
    if direct.exists():
        return direct
    current = root
    for part in rel.split("/"):
        candidate = current / part
        if part in ("", ".", "..") or candidate.exists():
            current = candidate
            continue
        wanted = nfc(part)
        try:
            match = next((e for e in os.listdir(current) if nfc(e) == wanted), None)
        except OSError:
            return direct
        if match is None:
            return direct
        current = current / match
    return current


def split_path(rel: str) -> tuple[str, str]:
    """Return (area, folder) for a path relative to the archive root."""
    parts = rel.split("/")
    if len(parts) == 1:
        return "", ""
    return parts[0], "/".join(parts[1:-1])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def shortest_unique_ids(hashes: list[str], min_len: int = MIN_ID_LEN) -> dict[str, str]:
    """Shortest prefix (at least ``min_len``) that is unique among ``hashes``."""
    ordered = sorted(set(hashes))
    result: dict[str, str] = {}
    for i, value in enumerate(ordered):
        need = min_len
        for other in (ordered[i - 1] if i else None, ordered[i + 1] if i + 1 < len(ordered) else None):
            if other is None:
                continue
            common = 0
            while common < len(value) and value[common] == other[common]:
                common += 1
            need = max(need, common + 1)
        result[value] = value[:need]
    return result


def _place(area: str, folder: str, doc_date: str | None) -> str:
    return " ".join(filter(None, [area, folder.replace("/", " "), doc_date or ""]))


class Index:
    def __init__(self, db_path: Path, archive: Path):
        self.db_path = db_path
        self.archive = archive
        self._scan_lock = threading.Lock()
        self._text_lock = threading.Lock()
        self._migrate()

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
        return con

    def _migrate(self) -> None:
        """The index is disposable: on a schema change it is simply rebuilt."""
        with self.connect() as con:
            con.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            row = con.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
            if not row or row[0] != SCHEMA_VERSION:
                for (name,) in con.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table') AND name NOT LIKE 'sqlite_%' "
                    "AND name NOT LIKE 'fts_%'"
                ).fetchall():
                    con.execute(f'DROP TABLE IF EXISTS "{name}"')
            con.executescript(SCHEMA)
            con.execute(
                "INSERT INTO meta(key, value) VALUES('schema', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (SCHEMA_VERSION,),
            )

    # ------------------------------------------------------------------ scan

    @property
    def scanning(self) -> bool:
        return self._scan_lock.locked()

    def scan(self) -> dict:
        """Synchronise the index with the archive folders."""
        if not self._scan_lock.acquire(blocking=False):
            return {"started": False, "reason": "scan already running"}
        try:
            return self._scan()
        finally:
            self._scan_lock.release()

    def _iter_files(self):
        root = self.archive
        for dirpath, dirnames, filenames in os.walk(root):
            # "<Seite>.assets" holds the pictures of a page, not documents of their own
            dirnames[:] = sorted(
                d for d in dirnames
                if not d.startswith(".") and d not in SKIP_NAMES and not d.endswith(ASSET_SUFFIX)
            )
            for name in filenames:
                if name.startswith(".") or name in SKIP_FILES:
                    continue
                if name.rpartition(".")[2].lower() not in EXTS:
                    continue
                full = Path(dirpath) / name
                if not full.is_file():
                    continue
                yield full, nfc(full.relative_to(root).as_posix())

    def _upsert(self, con: sqlite3.Connection, full: Path, rel: str, stat: os.stat_result, generation: int) -> str:
        """Read one file into the index (new or changed); returns the hash of its content."""
        sha = sha256_file(full)
        area, folder = split_path(rel)
        name = rel.rsplit("/", 1)[-1]
        stem, dot, ext = name.rpartition(".")
        if not dot:
            stem, ext = name, ""
        parsed = parse_name(stem)
        title, doc_date, page_id, page_tags = parsed.title, parsed.doc_date, "", []
        if ext.lower() == "md":
            # a page names itself in its head block or first heading, not in its file name
            head = read_head(full.read_text(encoding="utf-8", errors="replace"), nfc(stem))
            title, doc_date, page_id, page_tags = head.title, head.date, head.id, head.tags
        haystack = fold(" ".join(filter(None, [
            area, folder.replace("/", " "), title, doc_date or "", *page_tags])))
        file_id = con.execute(
            """INSERT INTO files(path, area, folder, name, ext, title, doc_date, size, mtime,
                                 sha256, page_id, page_tags, haystack, seen)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(path) DO UPDATE SET
                 area=excluded.area, folder=excluded.folder, name=excluded.name,
                 ext=excluded.ext, title=excluded.title, doc_date=excluded.doc_date,
                 size=excluded.size, mtime=excluded.mtime, sha256=excluded.sha256,
                 page_id=excluded.page_id, page_tags=excluded.page_tags,
                 haystack=excluded.haystack, seen=excluded.seen
               RETURNING id""",
            (rel, area, folder, name, ext.lower(), title, doc_date,
             stat.st_size, stat.st_mtime, sha, page_id, json.dumps(page_tags, ensure_ascii=False),
             haystack, generation),
        ).fetchone()[0]
        con.execute("DELETE FROM fts WHERE rowid=?", (file_id,))
        con.execute(
            "INSERT INTO fts(rowid, place, title, body) VALUES(?, ?, ?, "
            "COALESCE((SELECT body FROM texts WHERE sha256=?), ''))",
            (file_id, _place(area, folder, doc_date), " ".join([title, *page_tags]), sha),
        )
        return sha

    def _short_ids(self, con: sqlite3.Connection) -> None:
        hashes = [row[0] for row in con.execute("SELECT sha256 FROM files")]
        con.executemany(
            "UPDATE files SET short_id=? WHERE sha256=? AND short_id != ?",
            [(sid, sha, sid) for sha, sid in shortest_unique_ids(hashes).items()],
        )

    def refresh(self, changed: list[str] = (), gone: list[str] = ()) -> None:
        """Bring single files up to date right after the app wrote them – no waiting for the next scan.

        ``changed`` are paths that are new or have new content, ``gone`` paths that no longer exist
        (moved away, renamed, binned). The text of a page is stored at once, so the search finds it.
        """
        from .textextract import extract

        pages = []
        with self._scan_lock:       # a running scan would take the new rows for leftovers
            with self.connect() as con:
                generation = int(_meta(con, "generation", "0"))
                for rel in gone:
                    rel = nfc(rel)
                    con.execute("DELETE FROM fts WHERE rowid IN (SELECT id FROM files WHERE path=?)", (rel,))
                    con.execute("DELETE FROM files WHERE path=?", (rel,))
                for rel in changed:
                    rel = nfc(rel)
                    full = on_disk(self.archive, rel)
                    if not full.is_file():
                        continue
                    sha = self._upsert(con, full, rel, full.stat(), generation)
                    if rel.lower().endswith(".md"):
                        pages.append((sha, full))
                self._short_ids(con)
                con.commit()
        for sha, full in pages:
            self.store_text(sha, extract(full, "md"))

    def _scan(self) -> dict:
        started = time.time()
        added = updated = hashed = 0
        if not self.archive.is_dir():
            raise FileNotFoundError(f"archive folder missing: {self.archive}")
        with self.connect() as con:
            generation = int(_meta(con, "generation", "0")) + 1
            known = {
                row["path"]: (row["size"], row["mtime"], row["sha256"])
                for row in con.execute("SELECT path, size, mtime, sha256 FROM files")
            }
            batch = 0
            for full, rel in self._iter_files():
                stat = full.stat()
                old = known.get(rel)
                if old and old[0] == stat.st_size and abs(old[1] - stat.st_mtime) < 1e-6:
                    con.execute("UPDATE files SET seen=? WHERE path=?", (generation, rel))
                    continue
                self._upsert(con, full, rel, stat, generation)
                hashed += 1
                if old:
                    updated += 1
                else:
                    added += 1
                batch += 1
                if batch >= 200:
                    con.commit()
                    batch = 0
            con.execute("DELETE FROM fts WHERE rowid IN (SELECT id FROM files WHERE seen != ?)", (generation,))
            removed = con.execute("DELETE FROM files WHERE seen != ?", (generation,)).rowcount
            # texts stored while this scan ran (a document just filed) are kept
            con.execute("DELETE FROM texts WHERE sha256 NOT IN (SELECT sha256 FROM files) AND extracted_at < ?",
                        (time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(started)),))
            # a read error "file not found" is stale once the file is there again (archive switch, move)
            con.execute("DELETE FROM texts WHERE method = 'error' AND error LIKE 'FileNotFoundError%' "
                        "AND sha256 IN (SELECT sha256 FROM files)")
            self._short_ids(con)
            total = con.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            result = {
                "started": True,
                "total": total,
                "added": added,
                "updated": updated,
                "removed": removed,
                "hashed": hashed,
                "seconds": round(time.time() - started, 2),
                "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            for key, value in (
                ("generation", str(generation)),
                ("last_scan", result["finished_at"]),
                ("last_scan_seconds", str(result["seconds"])),
            ):
                _set_meta(con, key, value)
            con.commit()
        return result

    # ------------------------------------------------------------ text queue

    @property
    def extracting(self) -> bool:
        return self._text_lock.locked()

    def pending_texts(self, limit: int = 20) -> list[sqlite3.Row]:
        with self.connect() as con:
            return con.execute(
                """SELECT f.sha256, MIN(f.path) AS path, f.ext, MAX(f.doc_date) AS d
                   FROM files f LEFT JOIN texts t ON t.sha256 = f.sha256
                   WHERE t.sha256 IS NULL
                   GROUP BY f.sha256 ORDER BY d IS NULL, d DESC LIMIT ?""",
                (limit,),
            ).fetchall()

    def extract_pending(self, extractor: Callable, batch: int = 10, stop: threading.Event | None = None,
                        workers: int = 1) -> int:
        """Extract text for documents without text. Returns the number processed."""
        if not self._text_lock.acquire(blocking=False):
            return 0
        done = 0
        try:
            # separate processes: pdfium is not thread-safe
            with ProcessPoolExecutor(max_workers=max(1, workers), initializer=_lower_priority) as pool:
                while not (stop and stop.is_set()):
                    rows = self.pending_texts(max(batch, workers * 2))
                    if not rows:
                        break
                    futures = {
                        pool.submit(extractor, on_disk(self.archive, row["path"]), row["ext"]): row["sha256"]
                        for row in rows
                    }
                    for future in as_completed(futures):
                        self.store_text(futures[future], future.result())
                        done += 1
        finally:
            self._text_lock.release()
        return done

    def store_text(self, sha: str, result) -> None:
        with self.connect() as con:
            con.execute(
                """INSERT INTO texts(sha256, body, pages, ocr_pages, method, error, extracted_at)
                   VALUES(?,?,?,?,?,?,?)
                   ON CONFLICT(sha256) DO UPDATE SET body=excluded.body, pages=excluded.pages,
                     ocr_pages=excluded.ocr_pages, method=excluded.method, error=excluded.error,
                     extracted_at=excluded.extracted_at""",
                (sha, result.text, result.pages, result.ocr_pages, result.method, result.error,
                 time.strftime("%Y-%m-%dT%H:%M:%S")),
            )
            con.execute(
                "UPDATE fts SET body=? WHERE rowid IN (SELECT id FROM files WHERE sha256=?)",
                (result.text, sha),
            )

    def text_status(self) -> dict:
        with self.connect() as con:
            total = con.execute("SELECT COUNT(DISTINCT sha256) FROM files").fetchone()[0]
            row = con.execute(
                """SELECT COUNT(*) AS done, COALESCE(SUM(ocr_pages), 0) AS ocr_pages,
                          COALESCE(SUM(method = 'error'), 0) AS errors,
                          COALESCE(SUM(length(body) = 0 AND method != 'error'), 0) AS empty
                   FROM texts"""
            ).fetchone()
        return {"total": total, "done": row["done"], "ocr_pages": row["ocr_pages"],
                "errors": row["errors"], "empty": row["empty"], "running": self.extracting}

    def text_errors(self, areas: list[str]) -> list[dict]:
        """Documents whose text could not be read, with a plain reason."""
        if not areas:
            return []
        marks = ",".join("?" * len(areas))
        with self.connect() as con:
            rows = con.execute(
                f"""SELECT f.*, NULL AS snip, t.error FROM texts t JOIN files f ON f.sha256 = t.sha256
                    WHERE t.method = 'error' AND f.area IN ({marks}) GROUP BY f.sha256 ORDER BY f.path""",
                areas,
            ).fetchall()
        out = []
        for r in rows:
            err = r["error"] or ""
            reason = ("password" if "password" in err.lower()
                      else "missing" if err.startswith("FileNotFoundError")
                      else "damaged" if "Failed to load" in err or "PdfiumError" in err
                      else "other")
            out.append({**_public(r), "reason": reason, "error": err[:300]})
        return out

    def retry_text_errors(self, shas: list[str] | None = None) -> int:
        """Forget failed text extractions so the background worker tries them again."""
        with self.connect() as con:
            if shas is None:
                return con.execute("DELETE FROM texts WHERE method = 'error'").rowcount
            marks = ",".join("?" * len(shas))
            return con.execute(f"DELETE FROM texts WHERE method = 'error' AND sha256 IN ({marks})", shas).rowcount

    # --------------------------------------------------------------- queries

    def meta(self) -> dict:
        with self.connect() as con:
            rows = dict(con.execute("SELECT key, value FROM meta").fetchall())
            total = con.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        return {
            "total": total,
            "last_scan": rows.get("last_scan"),
            "last_scan_seconds": float(rows["last_scan_seconds"]) if "last_scan_seconds" in rows else None,
            "scanning": self.scanning,
            "texts": self.text_status(),
        }

    def areas(self) -> list[dict]:
        """Areas with their document count – empty area folders included, so they can get members."""
        with self.connect() as con:
            counts = {r["area"]: r["n"] for r in con.execute(
                "SELECT area, COUNT(*) AS n FROM files GROUP BY area")}
        try:
            for entry in os.scandir(self.archive):
                if (entry.is_dir() and not entry.name.startswith((".", "_", "@", "#"))
                        and entry.name not in SKIP_NAMES):
                    counts.setdefault(nfc(entry.name), 0)
        except OSError:
            pass
        return [{"name": name, "count": counts[name]} for name in sorted(counts)]

    def tree(self, areas: list[str], template: set[str] | None = None) -> dict:
        """One merged folder tree across all given areas, plus empty template folders."""
        root = {"name": "", "path": "", "count": 0, "own": 0, "areas": set(), "children": {}}
        for folder in sorted(template or ()):
            node, path = root, []
            for part in folder.split("/"):
                path.append(part)
                node = node["children"].setdefault(
                    part, {"name": part, "path": "/".join(path), "count": 0, "own": 0,
                           "areas": set(), "children": {}})
        if not areas:
            return _finish(root)
        marks = ",".join("?" * len(areas))
        with self.connect() as con:
            rows = con.execute(
                f"SELECT area, folder, COUNT(*) AS n FROM files WHERE area IN ({marks}) "
                "GROUP BY area, folder",
                areas,
            ).fetchall()
        for row in rows:
            node = root
            node["count"] += row["n"]
            node["areas"].add(row["area"])
            if row["folder"]:
                path = []
                for part in row["folder"].split("/"):
                    path.append(part)
                    node = node["children"].setdefault(
                        part,
                        {"name": part, "path": "/".join(path), "count": 0, "own": 0,
                         "areas": set(), "children": {}},
                    )
                    node["count"] += row["n"]
                    node["areas"].add(row["area"])
            node["own"] += row["n"]
        return _finish(root)

    def documents(
        self,
        areas: list[str],
        folder: str = "",
        recursive: bool = False,
        query: str = "",
        limit: int = 500,
        offset: int = 0,
        shas: set[str] | None = None,
        kind: str = "",
        before: str | None = None,
        sort: str = "",
        desc: bool = True,
    ) -> dict:
        """``sort`` is ``date``, ``title``, ``area``, ``changed`` or ``relevance`` (best hits first, searches only; empty: relevance for a search, else date).

        ``shas`` limits the result to these contents (tag filter); empty set = nothing.

        ``kind`` keeps only pages (``md``) or only PDFs (``pdf``).
        ``before`` keeps only documents dated before this ISO date (undated ones never match).
        """
        if not areas or shas is not None and not shas:
            return {"total": 0, "items": []}
        marks = ",".join("?" * len(areas))
        where = [f"f.area IN ({marks})"]
        args: list = list(areas)
        if shas is not None:
            where.append("f.sha256 IN (SELECT value FROM json_each(?))")
            args.append(json.dumps(sorted(shas)))
        folder = folder.strip("/")
        if folder:
            if recursive:
                where.append("(f.folder = ? OR f.folder LIKE ? ESCAPE '\\')")
                args += [folder, _like_escape(folder) + "/%"]
            else:
                where.append("f.folder = ?")
                args.append(folder)
        elif not recursive:
            where.append("f.folder = ''")
        if kind:
            where.append("f.ext = ?")
            args.append(kind)
        if before:
            where.append("f.doc_date IS NOT NULL AND f.doc_date < ?")
            args.append(before)

        tokens = fold(query).split()
        long_tokens = [t for t in tokens if len(t) >= 3]
        for token in (t for t in tokens if len(t) < 3):
            where.append("f.haystack LIKE ? ESCAPE '\\'")
            args.append("%" + _like_escape(token) + "%")

        order = _order(sort, desc) if sort in _SORTS else ""
        with self.connect() as con:
            if long_tokens:
                match = " AND ".join('"' + t.replace('"', '""') + '"' for t in long_tokens)
                sql_where = "fts MATCH ? AND " + " AND ".join(where)
                margs = [match, *args]
                base = "FROM fts JOIN files f ON f.id = fts.rowid WHERE " + sql_where
                total = con.execute(f"SELECT COUNT(*) {base}", margs).fetchone()[0]
                rows = con.execute(
                    f"""SELECT f.*, snippet(fts, 2, '{HL_START}', '{HL_END}', '…', 16) AS snip
                        {base} ORDER BY {order or "bm25(fts, 4.0, 8.0, 1.0), f.doc_date DESC"}
                        LIMIT ? OFFSET ?""",
                    margs + [limit, offset],
                ).fetchall()
            else:
                sql_where = " AND ".join(where)
                total = con.execute(f"SELECT COUNT(*) FROM files f WHERE {sql_where}", args).fetchone()[0]
                rows = con.execute(
                    f"""SELECT f.*, NULL AS snip FROM files f WHERE {sql_where}
                        ORDER BY {order or _order("date", True)}
                        LIMIT ? OFFSET ?""",
                    args + [limit, offset],
                ).fetchall()
        return {"total": total, "items": [_public(r) for r in rows]}

    def candidates(self, areas: list[str], terms: list[str], limit: int = 12) -> list[tuple[dict, str]]:
        """Documents that contain any of ``terms`` (parts of words count), best first, with their text.

        For questions: unlike the search, not every word has to occur.
        """
        terms = [t for t in terms if len(t) >= 3]
        if not areas or not terms:
            return []
        marks = ",".join("?" * len(areas))
        match = " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)
        with self.connect() as con:
            rows = con.execute(
                f"""SELECT f.*, NULL AS snip, t.body AS body
                    FROM fts JOIN files f ON f.id = fts.rowid JOIN texts t ON t.sha256 = f.sha256
                    WHERE fts MATCH ? AND f.area IN ({marks}) AND length(t.body) > 0
                    ORDER BY bm25(fts, 4.0, 8.0, 1.0) LIMIT ?""",
                [match, *areas, limit * 2],
            ).fetchall()
        seen, out = set(), []
        for row in rows:                    # the same content in two places counts once
            if row["sha256"] not in seen:
                seen.add(row["sha256"])
                out.append((_public(row), row["body"]))
        return out[:limit]

    def shas(self, areas: list[str]) -> set[str]:
        """Contents present in these areas."""
        if not areas:
            return set()
        marks = ",".join("?" * len(areas))
        with self.connect() as con:
            return {r[0] for r in con.execute(
                f"SELECT DISTINCT sha256 FROM files WHERE area IN ({marks})", list(areas))}

    def document(self, doc_id: str, areas: list[str]) -> dict | None:
        """Look up a document by its id, limited to ``areas``.

        The id of a page is the fixed ``id`` from its head block; a PDF (or a page without one)
        is found by (a prefix of) the hash of its content.
        """
        doc_id = doc_id.lower()
        if not re.fullmatch(r"[0-9a-z]{6,64}", doc_id) or not areas:
            return None
        marks = ",".join("?" * len(areas))
        with self.connect() as con:
            rows = con.execute(
                f"SELECT f.*, NULL AS snip FROM files f WHERE f.page_id = ? AND f.area IN ({marks}) "
                "ORDER BY f.path",
                [doc_id, *areas],
            ).fetchall()
            if not rows and re.fullmatch(r"[0-9a-f]{6,64}", doc_id):
                rows = con.execute(
                    f"SELECT f.*, NULL AS snip FROM files f WHERE f.sha256 LIKE ? AND f.area IN ({marks}) "
                    "ORDER BY f.path",
                    [doc_id + "%", *areas],
                ).fetchall()
            if not rows or len({r["sha256"] for r in rows}) != 1:
                return None
            text = con.execute(
                "SELECT pages, ocr_pages, method, error, length(body) AS chars FROM texts WHERE sha256=?",
                (rows[0]["sha256"],),
            ).fetchone()
        doc = _public(rows[0])
        doc["copies"] = [r["path"] for r in rows]
        doc["text"] = dict(text) if text else None
        return doc

    def by_path(self, path: str, areas: list[str]) -> dict | None:
        if not areas:
            return None
        marks = ",".join("?" * len(areas))
        with self.connect() as con:
            row = con.execute(f"SELECT f.*, NULL AS snip FROM files f WHERE f.path = ? AND f.area IN ({marks})",
                              [nfc(path), *areas]).fetchone()
        return _public(row) if row else None

    def document_text(self, sha: str) -> str:
        with self.connect() as con:
            row = con.execute("SELECT body FROM texts WHERE sha256=?", (sha,)).fetchone()
        return row["body"] if row else ""


def _lower_priority() -> None:
    try:
        os.nice(10)
    except OSError:
        pass


def _meta(con: sqlite3.Connection, key: str, default: str) -> str:
    row = con.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row[0] if row else default


def _set_meta(con: sqlite3.Connection, key: str, value: str) -> None:
    con.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


_SORTS = ("date", "title", "area", "changed")


def _order(sort: str, desc: bool) -> str:
    """ORDER BY for the list; undated documents always go last, ties fall back to date and title."""
    way = "DESC" if desc else "ASC"
    date = f"f.doc_date IS NULL, f.doc_date {way}"
    if sort == "title":
        return f"f.title COLLATE NOCASE {way}, f.doc_date DESC"
    if sort == "changed":       # when the file was last written, not the date the document carries
        return f"f.mtime {way}, f.title COLLATE NOCASE"
    if sort == "area":
        return f"f.area COLLATE NOCASE {way}, f.doc_date IS NULL, f.doc_date DESC, f.title COLLATE NOCASE"
    return f"{date}, f.title COLLATE NOCASE"


def _public(row: sqlite3.Row) -> dict:
    snippet = row["snip"]
    return {
        "id": row["page_id"] or row["short_id"] or row["sha256"][:MIN_ID_LEN],
        "sha256": row["sha256"],
        "path": row["path"],
        "area": row["area"],
        "folder": row["folder"],
        "name": row["name"],
        "ext": row["ext"],
        "title": row["title"],
        "date": row["doc_date"],
        "size": row["size"],
        "changed": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(row["mtime"])),
        "page_tags": json.loads(row["page_tags"] or "[]"),
        "snippet": snippet if snippet and HL_START in snippet else None,
    }


def _finish(node: dict) -> dict:
    return {
        "name": node["name"],
        "path": node["path"],
        "count": node["count"],
        "own": node["own"],
        "areas": sorted(node["areas"]),
        "children": [
            _finish(child)
            for child in sorted(node["children"].values(), key=lambda c: fold(c["name"]))
        ],
    }


def _like_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
