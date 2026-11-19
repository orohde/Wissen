"""Eingang: PDFs waiting to be filed into the archive.

The inbox is one folder, by default ``_Eingang`` in the archive folder (``WISSEN_INBOX``
sets another). Files get there in three ways: dropped onto the page in the browser,
copied over the network share, or through a sync client (kDrive and the like). The
leading underscore keeps the folder out of the areas and the index.

Nothing is filed without confirmation. Each file comes with a suggestion: the title
from the file name, area and folder from the subfolder it sits in inside the inbox
(``_Eingang/zeitschriften/Holzwerken/Heft.pdf`` → area ``zeitschriften``, folder
``Holzwerken``). The AI can be asked for a better one. Filing moves the file into
the archive as ``{area}/{folder}/{title}.pdf``; nothing stays behind in the inbox.

The AI's answers are kept per content in ``inbox-ai.json`` (data folder), so a suggestion
survives reloading the page. With "Eingang automatisch vorsortieren" switched on, the
background worker asks for every new file whose place is not given by its subfolder.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import shutil
import threading
import time
import uuid
from pathlib import Path

from .docops import DocOpError, _area_dir, _makedirs, _prune, clean_folder, file_stem
from .index import SKIP_FILES, SKIP_NAMES, Index, nfc, on_disk, sha256_file

INBOX_NAME = "_Eingang"
EXTENSIONS = {"pdf"}
IMAGE_EXT = {"jpg", "jpeg", "png", "heic", "heif", "tif", "tiff", "webp"}
SETTLE_SECONDS = 10            # a copy over the network may still be running for younger files
MAX_SIDE = 3000                # px – plenty for A4 at ~250 dpi, keeps phone photos small
AI_TEXT_CHARS = 4000
AI_FOLDERS = 400
AI_RETRY_SECONDS = 24 * 3600   # a failed automatic question is tried again a day later

_lock = threading.Lock()


class InboxError(ValueError):
    pass


def item_key(rel: str) -> str:
    return base64.urlsafe_b64encode(rel.encode("utf-8")).decode("ascii").rstrip("=")


def key_rel(key: str) -> str:
    try:
        return base64.urlsafe_b64decode(key + "=" * (-len(key) % 4)).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise InboxError("unknown item") from exc


def title_from_name(name: str) -> str:
    """"Holzwerken_131-2026.pdf" → "Holzwerken 131-2026": underscores become spaces."""
    stem = name.rsplit(".", 1)[0] if "." in name else name
    stem = re.sub(r"[_\s]+", " ", nfc(stem)).strip(" .-")
    return stem or "Dokument"


def safe_name(name: str) -> str:
    """A harmless file name for an upload (no folders, nothing the share or Finder chokes on)."""
    name = nfc(name).replace("\\", "/").rsplit("/", 1)[-1]
    stem, _, ext = name.rpartition(".") if "." in name else (name, "", "")
    stem = file_stem(stem, 100) or "Upload"
    return f"{stem}.{ext.lower()}" if ext else stem


def image_to_pdf(data: bytes) -> bytes:
    """A photo (also HEIC from the iPhone, multi-page TIFF) as a PDF, upright and reasonably small."""
    from PIL import Image, ImageOps

    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:          # optional: without it HEIC is refused with a clear error
        pass
    try:
        img = Image.open(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001
        raise InboxError("not a picture (or HEIC support missing)") from exc
    pages = []
    try:
        while True:
            frame = ImageOps.exif_transpose(img.copy()).convert("RGB")
            frame.thumbnail((MAX_SIDE, MAX_SIDE))
            pages.append(frame)
            img.seek(img.tell() + 1)
    except EOFError:
        pass
    dpi = max(72.0, max(pages[0].size) / 11.69)    # the long side becomes A4 height
    buf = io.BytesIO()
    pages[0].save(buf, "PDF", save_all=True, append_images=pages[1:], resolution=dpi, quality=85)
    return buf.getvalue()


class InboxService:
    def __init__(self, index: Index, path: Path | None = None, ai_cache: Path | None = None):
        self.index = index
        self._path = path
        self._shas: dict[str, tuple[int, float, str]] = {}     # rel -> (size, mtime, sha256)
        self._cache_path = ai_cache
        self._cache_lock = threading.Lock()
        self._ai: dict[str, dict] = {}                          # sha256 -> answer (or error) of the AI
        if ai_cache is not None and ai_cache.is_file():
            try:
                self._ai = {k: v for k, v in json.loads(ai_cache.read_text(encoding="utf-8")).items()
                            if isinstance(v, dict)}
            except (OSError, ValueError):
                self._ai = {}

    def _remember(self, sha: str, answer: dict) -> None:
        with self._cache_lock:
            self._ai[sha] = answer
            self._save_cache()

    def _save_cache(self) -> None:
        if self._cache_path is None:
            return
        tmp = self._cache_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._ai, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, self._cache_path)

    def ai_answer(self, sha: str) -> dict | None:
        answer = self._ai.get(sha)
        return answer if answer and not answer.get("error") else None

    @property
    def root(self) -> Path:
        return self._path or (self.index.archive / INBOX_NAME)

    def _ensure(self) -> Path:
        root = self.root
        if not root.is_dir():
            try:
                root.mkdir(parents=True)
                os.chmod(root, 0o775)
            except OSError as exc:
                raise InboxError("inbox folder cannot be created") from exc
        return root

    # ------------------------------------------------------------- listing

    def _walk(self):
        root = self.root
        if not root.is_dir():
            return
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith((".", "@", "#")) and d not in SKIP_NAMES)
            for name in sorted(filenames):
                if name.startswith(".") or name in SKIP_FILES:
                    continue
                if name.rpartition(".")[2].lower() not in EXTENSIONS:
                    continue
                full = Path(dirpath) / name
                if full.is_file():
                    yield full, nfc(full.relative_to(root).as_posix())

    def _sha(self, full: Path, rel: str, stat: os.stat_result) -> str:
        known = self._shas.get(rel)
        if known and known[0] == stat.st_size and known[1] == stat.st_mtime:
            return known[2]
        sha = sha256_file(full)
        self._shas[rel] = (stat.st_size, stat.st_mtime, sha)
        return sha

    def suggest(self, rel: str, areas: set[str]) -> dict:
        parts = rel.split("/")
        folders = parts[:-1]
        area = ""
        if folders and folders[0] in areas:
            area, folders = folders[0], folders[1:]
        return {"title": title_from_name(parts[-1]), "area": area, "folder": "/".join(folders)}

    def items(self, areas: set[str], now: float | None = None) -> list[dict]:
        """Files waiting in the inbox, oldest first, each with a suggestion and a duplicate check.

        A suggestion of the AI wins over the one from the file name and subfolder."""
        now = now or time.time()
        found = []
        seen = set()
        shas = set()
        walked = self.root.is_dir()
        for full, rel in self._walk():
            stat = full.stat()
            if now - stat.st_mtime < SETTLE_SECONDS:
                continue                       # still being written
            seen.add(rel)
            sha = self._sha(full, rel, stat)
            shas.add(sha)
            with self.index.connect() as con:
                dup = con.execute("SELECT path FROM files WHERE sha256=? LIMIT 1", (sha,)).fetchone()
            suggestion = self.suggest(rel, areas)
            answer = self.ai_answer(sha)
            if answer:
                suggestion = {"title": answer.get("title") or suggestion["title"],
                              "area": answer.get("area") if answer.get("area") in areas else suggestion["area"],
                              "folder": answer.get("folder", "") if answer.get("area") in areas else suggestion["folder"],
                              "ai": True}
            found.append({"key": item_key(rel), "rel": rel, "name": rel.rsplit("/", 1)[-1],
                          "size": stat.st_size, "added": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)),
                          "sha256": sha, "duplicate": dup[0] if dup else None, "suggestion": suggestion,
                          "ai_failed": bool(self._ai.get(sha, {}).get("error"))})
        for rel in [r for r in self._shas if r not in seen]:
            self._shas.pop(rel, None)
        if walked:              # answers for files that left the inbox are of no use any more
            with self._cache_lock:
                gone = [sha for sha in self._ai if sha not in shas]
                if gone:
                    for sha in gone:
                        del self._ai[sha]
                    self._save_cache()
        found.sort(key=lambda i: (i["added"], i["rel"]))
        return found

    def count(self) -> int:
        now = time.time()
        return sum(1 for full, _ in self._walk() if now - full.stat().st_mtime >= SETTLE_SECONDS)

    def path_of(self, key: str) -> Path:
        rel = key_rel(key)
        root = self.root.resolve()
        path = on_disk(root, rel).resolve() if root.is_dir() else None
        if path is None or root not in path.parents or not path.is_file() \
                or path.suffix.lower().lstrip(".") not in EXTENSIONS:
            raise InboxError("unknown item")
        return path

    # ------------------------------------------------------------- adding

    def add(self, name: str, data: bytes) -> str:
        """One upload from the browser: PDFs as they are, photos become PDFs. Returns the file name."""
        name = safe_name(name)
        ext = name.rpartition(".")[2].lower() if "." in name else ""
        if ext in IMAGE_EXT:
            data, name = image_to_pdf(data), name.rpartition(".")[0] + ".pdf"
        elif ext != "pdf":
            raise InboxError(f"unsupported file type: {name}")
        elif not data.startswith(b"%PDF-"):
            raise InboxError(f"not a PDF: {name}")
        root = self._ensure()
        with _lock:
            dest = root / name
            n = 1
            while dest.exists():
                n += 1
                dest = root / f"{Path(name).stem} ({n}){Path(name).suffix}"
            tmp = root / f".{uuid.uuid4().hex}.part"
            try:
                tmp.write_bytes(data)
                os.chmod(tmp, 0o664)
                past = time.time() - SETTLE_SECONDS - 1     # written in one step: no need to wait
                os.utime(tmp, (past, past))
                os.replace(tmp, dest)
            finally:
                tmp.unlink(missing_ok=True)
        return dest.name

    # ------------------------------------------------------------- filing

    def file(self, key: str, area: str, folder: str, title: str, force: bool = False) -> str:
        """Move one file into the archive as ``area/folder/title.pdf``; returns the archive path."""
        src = self.path_of(key)
        archive = self.index.archive.resolve()
        try:
            target_dir = _area_dir(archive, area)
            folder = clean_folder(folder)
        except DocOpError as exc:
            raise InboxError(str(exc)) from exc
        stem = file_stem(title)
        if not stem:
            raise InboxError("title missing")
        sha = sha256_file(src)
        if not force:
            with self.index.connect() as con:
                dup = con.execute("SELECT path FROM files WHERE sha256=? LIMIT 1", (sha,)).fetchone()
            if dup:
                raise InboxError(f"already in the archive: {dup[0]}")
        if folder:
            target_dir = on_disk(target_dir, folder)
        dest = target_dir / f"{stem}.pdf"
        with _lock:
            if dest.exists():
                raise InboxError("target exists")
            _makedirs(target_dir, archive)
            try:
                os.replace(src, dest)
            except OSError:                   # another file system: copy, check, then let go
                tmp = target_dir / f".{uuid.uuid4().hex}.part"
                try:
                    shutil.copyfile(src, tmp)
                    if sha256_file(tmp) != sha:
                        raise InboxError("copy differs from the original – nothing filed")
                    os.replace(tmp, dest)
                finally:
                    tmp.unlink(missing_ok=True)
                src.unlink()
            os.chmod(dest, 0o664)
            _prune(src.parent, self.root.resolve())
        self._shas.pop(key_rel(key), None)
        return nfc(dest.relative_to(archive).as_posix())

    def delete(self, key: str) -> None:
        """Junk goes for good: the file in the inbox (empty subfolders with it)."""
        src = self.path_of(key)
        try:
            src.unlink()
        except OSError as exc:
            raise InboxError("cannot delete") from exc
        _prune(src.parent, self.root.resolve())
        self._shas.pop(key_rel(key), None)

    # ------------------------------------------------------------- AI

    def text(self, key: str, extractor) -> str:
        return extractor(self.path_of(key))[:AI_TEXT_CHARS]

    def ask_ai(self, key: str, ai, extractor, areas: list[dict], folders: list[str]) -> dict:
        """Ask the AI for area, folder and title, picked from what the archive already has.

        The answer is kept for this content until the file leaves the inbox."""
        path = self.path_of(key)
        stat = path.stat()
        sha = self._sha(path, key_rel(key), stat)
        text = self.text(key, extractor)
        area_lines = "\n".join(f"- {a['name']} ({a.get('label') or a['name']})" for a in areas)
        folder_lines = "\n".join(f"- {f}" for f in folders[:AI_FOLDERS]) or "- (noch keine)"
        system = ("Du sortierst PDFs in ein Archiv mit Anleitungen, Handbüchern, Zeitschriften und Ratgebern. "
                  "Antworte nur mit einem JSON-Objekt: {\"area\": \"…\", \"folder\": \"…\", \"title\": \"…\"}. "
                  "area ist genau einer der genannten Bereichsnamen. folder ist ein vorhandener Ordner dieses "
                  "Bereichs (ohne Bereichsnamen), nur wenn keiner passt ein neuer, kurzer. title ist ein klarer "
                  "deutscher Titel: Hersteller und Gerät bzw. Zeitschrift mit Heftnummer und Jahr, ohne Dateiendung.")
        prompt = (f"Bereiche:\n{area_lines}\n\nVorhandene Ordner (Bereich/Ordner):\n{folder_lines}\n\n"
                  f"Dateiname: {path.name}\n\nText vom Anfang des PDFs:\n{text or '(kein Text lesbar)'}")
        answer = ai.complete(system, prompt, max_tokens=300)
        data = _parse_json(answer.text)
        names = {a["name"] for a in areas}
        area = str(data.get("area") or "").strip()
        folder = str(data.get("folder") or "").strip().strip("/")
        if area not in names:
            area = ""
        if area and folder.startswith(area + "/"):
            folder = folder[len(area) + 1:]
        try:
            folder = clean_folder(folder)
        except DocOpError:
            folder = ""
        title = file_stem(str(data.get("title") or "")) or title_from_name(path.name)
        result = {"area": area, "folder": folder, "title": title, "model": answer.model}
        self._remember(sha, {**result, "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        return result

    def auto_ai(self, ai, args, limit: int = 10, now: float | None = None) -> int:
        """Ask for files nobody placed yet: no AI answer so far and no area from the subfolder.

        ``args()`` gives (extractor, areas, folders) – only built when there is something to do.
        A failure (limit reached, provider down …) is remembered, the file is tried again a day later."""
        now = now or time.time()
        config = ai.load()
        if not (config.enabled and config.inbox_auto):
            return 0
        names = set()
        try:
            names = {a["name"] for a in self.index.areas()}
        except Exception:  # noqa: BLE001
            pass
        todo = []
        for item in self.items(names, now):
            known = self._ai.get(item["sha256"])
            if item["suggestion"].get("ai") or item["suggestion"]["area"]:
                continue
            if known and known.get("error") and now - known.get("tried", 0) < AI_RETRY_SECONDS:
                continue
            todo.append(item)
        done = 0
        built = None
        for item in todo[:limit]:
            built = built or args()
            try:
                self.ask_ai(item["key"], ai, *built)
            except InboxError:
                continue                     # gone meanwhile
            except Exception as exc:  # noqa: BLE001
                self._remember(item["sha256"], {"error": str(exc)[:200], "tried": now})
            done += 1
        return done


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text or "", re.S)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
