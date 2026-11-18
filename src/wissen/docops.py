"""Writing to the archive: new pages, saving, renaming, moving and the trash.

Every change is a plain file operation, so the folders stay the source of truth.
Texts are written atomically (temporary file, then ``os.replace``). Nothing is
deleted for good: "delete" moves the file to ``.papierkorb/<date>/<original path>``
inside the archive. The index skips dot folders, so it disappears from the app
but stays reachable via SMB and can be put back.

A page takes its pictures along: ``<Seite>.assets/`` is renamed, moved and
binned together with ``<Seite>.md``.
"""

from __future__ import annotations

import os
import re
import shutil
import threading
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import quote

from .index import EXTS, nfc, on_disk, parse_name
from .pages import ASSET_SUFFIX, new_id, read_head, set_head
from .storage import path_status

TRASH = ".papierkorb"
INVALID = set('<>:"\\|?*')
MAX_ASSET = 50 * 1024 * 1024


class DocOpError(ValueError):
    pass


_lock = threading.Lock()


def clean_folder(path: str) -> str:
    """A folder path inside an area, checked part by part (empty = the area itself)."""
    parts = [p.strip() for p in nfc(path or "").replace("\\", "/").split("/") if p.strip()]
    for part in parts:
        if part in (".", "..") or part.startswith(".") or INVALID & set(part) or len(part) > 80 \
                or part.endswith(ASSET_SUFFIX):
            raise DocOpError(f"invalid folder name: {part}")
    return "/".join(parts)


def file_stem(title: str, limit: int = 120) -> str:
    """A file name for a title that works everywhere (Finder, SMB, sync clients)."""
    name = re.sub(r'[/\\:*?"<>|\x00-\x1f]', "-", nfc(title or ""))
    name = re.sub(r"\s+", " ", name).strip(" .-")
    return name[:limit].rstrip(" .-")


def _makedirs(path: Path, root: Path) -> None:
    """Create missing folders below ``root`` with group write access (SMB users)."""
    missing = []
    p = path
    while not p.exists() and p != root and p != p.parent:
        missing.append(p)
        p = p.parent
    for d in reversed(missing):
        try:
            d.mkdir()
            os.chmod(d, 0o775)
        except FileExistsError:
            pass


def _prune(folder: Path, stop: Path) -> None:
    """Remove folders the last document just left, up to (not including) ``stop``.

    The app only shows folders that hold documents; an emptied one would linger unseen on the share.
    """
    stop = stop.resolve()
    while folder != stop and stop in folder.parents:
        try:
            folder.rmdir()          # fails as soon as anything is left in it
        except OSError:
            return
        folder = folder.parent


def _writable(archive: Path) -> None:
    if not path_status(str(archive))["writable"]:
        raise DocOpError("archive is read-only")


def _source(archive: Path, doc: dict) -> Path:
    root = archive.resolve()
    src = on_disk(root, doc["path"]).resolve()
    if root not in src.parents or not src.is_file():
        raise DocOpError("file not found")
    return src


def _area_dir(archive: Path, area: str) -> Path:
    if not area or area.startswith((".", "_")) or "/" in area or "\\" in area:
        raise DocOpError("unknown area")
    path = on_disk(archive.resolve(), area)
    if not path.is_dir():
        raise DocOpError("unknown area")
    return path


def _assets(page: Path) -> Path:
    return page.with_name(page.stem + ASSET_SUFFIX)


def _rel(archive: Path, path: Path) -> str:
    return nfc(path.relative_to(archive.resolve()).as_posix())


def _same(a: Path, b: Path) -> bool:
    try:
        return a.samefile(b)
    except OSError:
        return False


def write_atomic(path: Path, data: bytes) -> None:
    """Replace ``path`` in one step, so no reader (or sync client) ever sees half a file."""
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o664
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def read_page(archive: Path, doc: dict) -> str:
    return _source(archive, doc).read_text(encoding="utf-8", errors="replace")


def write_page(archive: Path, doc: dict, text: str) -> None:
    _writable(archive)
    src = _source(archive, doc)
    with _lock:
        write_atomic(src, text.encode("utf-8"))


def new_page(archive: Path, area: str, folder: str, title: str, body: str = "", page_id: str = "") -> str:
    """Create ``<title>.md`` with a head block; returns its path relative to the archive."""
    _writable(archive)
    title = " ".join(nfc(title or "").split())
    stem = file_stem(title)
    if not stem:
        raise DocOpError("title missing")
    folder = clean_folder(folder)
    target_dir = _area_dir(archive, area)
    if folder:
        target_dir = on_disk(target_dir, folder)
    dest = target_dir / f"{stem}.md"
    text = set_head(body.lstrip("\n"), title=title, date=date.today().isoformat(), id=page_id or new_id())
    with _lock:
        if dest.exists() or on_disk(target_dir, dest.name).exists():
            raise DocOpError("target exists")
        _makedirs(target_dir, archive.resolve())
        write_atomic(dest, text.encode("utf-8"))
    return _rel(archive, dest)


def _relink(text: str, old: str, new: str) -> str:
    """Point the links of a page at its renamed assets folder."""
    for form in ("NFC", "NFD"):
        was = unicodedata.normalize(form, old) + ASSET_SUFFIX + "/"
        for a, b in ((quote(was), quote(new + ASSET_SUFFIX + "/")), (was, new + ASSET_SUFFIX + "/")):
            text = text.replace("(" + a, "(" + b).replace("(<" + a, "(<" + b).replace('"' + a, '"' + b)
    return text


def rename(archive: Path, doc: dict, title: str) -> str:
    """Give a document a new title; returns the new relative path.

    A page gets the title in its head block and as its file name, and its assets
    folder follows. A PDF only changes its file name (a leading date stays).
    """
    _writable(archive)
    title = " ".join(nfc(title or "").split())
    stem = file_stem(title)
    if not stem:
        raise DocOpError("title missing")
    src = _source(archive, doc)
    is_page = src.suffix.lower() == ".md"
    if not is_page:
        parsed = parse_name(src.stem)
        if parsed.doc_date:
            stem = f"{parsed.doc_date}_{stem}"
    dest = src.with_name(stem + src.suffix)
    moved = nfc(dest.name) != nfc(src.name)
    with _lock:
        if moved and dest.exists() and not _same(src, dest):
            raise DocOpError("target exists")
        old_assets, new_assets = _assets(src), _assets(dest)
        with_assets = is_page and moved and old_assets.is_dir()
        if with_assets and new_assets.exists() and not _same(old_assets, new_assets):
            raise DocOpError("target exists")
        if is_page:
            text = src.read_text(encoding="utf-8", errors="replace")
            changed = set_head(text, title=title)
            if with_assets:
                changed = _relink(changed, src.stem, stem)
            if not moved and changed == text:
                raise DocOpError("nothing changed")
            if moved:
                os.rename(src, dest)
            write_atomic(dest, changed.encode("utf-8"))
            if with_assets:
                os.rename(old_assets, new_assets)
        else:
            if not moved:
                raise DocOpError("nothing changed")
            os.rename(src, dest)
    return _rel(archive, dest)


def move(archive: Path, doc: dict, folder: str, area: str | None = None) -> str:
    """Move ``doc`` into ``folder`` of ``area`` (default: its own); returns the new relative path."""
    _writable(archive)
    folder = clean_folder(folder)
    area = area or doc["area"]
    target_dir = _area_dir(archive, area)
    if area == doc["area"] and folder == (doc.get("folder") or ""):
        raise DocOpError("already in this folder")
    src = _source(archive, doc)
    if folder:
        target_dir = on_disk(target_dir, folder)
    dest = target_dir / src.name
    assets = _assets(src) if src.suffix.lower() == ".md" else None
    with _lock:
        if dest.exists():
            raise DocOpError("target exists")
        if assets and assets.is_dir() and _assets(dest).exists():
            raise DocOpError("target exists")
        _makedirs(target_dir, archive.resolve())
        os.replace(src, dest)
        if assets and assets.is_dir():
            os.rename(assets, _assets(dest))
        _prune(src.parent, on_disk(archive.resolve(), doc["area"]))
    return _rel(archive, dest)


def trash(archive: Path, doc: dict) -> str:
    """Move ``doc`` to the trash; returns the trash path (relative to the archive)."""
    _writable(archive)
    root = archive.resolve()
    src = _source(archive, doc)
    rel = src.relative_to(root)
    dest = root / TRASH / date.today().isoformat() / rel
    assets = _assets(src) if src.suffix.lower() == ".md" else None
    with _lock:
        n = 1
        while dest.exists() or _assets(dest).exists():
            n += 1
            dest = dest.with_name(f"{src.stem} ({n}){src.suffix}")
        _makedirs(dest.parent, root)
        os.replace(src, dest)
        if assets and assets.is_dir():
            os.rename(assets, _assets(dest))
        _prune(src.parent, root / rel.parts[0])
    return nfc(dest.relative_to(root).as_posix())


def _trash_source(archive: Path, trash_path: str) -> tuple[Path, Path]:
    """``(file, original relative path)`` for a path below the trash."""
    parts = Path(trash_path).parts
    if len(parts) < 4 or parts[0] != TRASH or ".." in parts:
        raise DocOpError("not in the trash")
    root = archive.resolve()
    src = on_disk(root, trash_path).resolve()
    if (root / TRASH).resolve() not in src.parents or not src.is_file():
        raise DocOpError("not in the trash")
    return src, Path(*parts[2:])


def restore(archive: Path, trash_path: str, allowed) -> str:
    """Put a file from the trash back to its original place; ``allowed(area)`` checks rights."""
    _writable(archive)
    src, rel = _trash_source(archive, trash_path)
    if not allowed(nfc(rel.parts[0])):
        raise DocOpError("no write access")
    root = archive.resolve()
    dest = on_disk(root, rel.parent.as_posix()) / src.name
    assets = _assets(src) if src.suffix.lower() == ".md" else None
    with _lock:
        if dest.exists() or (assets and assets.is_dir() and _assets(dest).exists()):
            raise DocOpError("target exists")
        _makedirs(dest.parent, root)
        os.replace(src, dest)
        if assets and assets.is_dir():
            os.rename(assets, _assets(dest))
        _prune(src.parent, root / TRASH)
    return _rel(archive, dest)


def trash_list(archive: Path, can_read) -> list[dict]:
    """Everything in the trash the user may see, newest first."""
    root = archive.resolve() / TRASH
    items = []
    if not root.is_dir():
        return items
    for day in sorted((d for d in root.iterdir() if d.is_dir()), reverse=True):
        for dirpath, dirnames, files in os.walk(day):
            dirnames[:] = sorted(d for d in dirnames if not d.endswith(ASSET_SUFFIX))
            for name in sorted(files):
                full = Path(dirpath) / name
                rel = full.relative_to(day)
                stem, _, ext = name.rpartition(".")
                if name.startswith(".") or ext.lower() not in EXTS:
                    continue
                if len(rel.parts) < 2 or not can_read(nfc(rel.parts[0])):
                    continue
                parsed = parse_name(stem)
                title, doc_date = parsed.title, parsed.doc_date
                if ext.lower() == "md":
                    head = read_head(full.read_text(encoding="utf-8", errors="replace"), nfc(stem))
                    title, doc_date = head.title, head.date
                items.append({
                    "trash_path": nfc(full.relative_to(archive.resolve()).as_posix()),
                    "path": nfc(rel.as_posix()),
                    "area": nfc(rel.parts[0]),
                    "folder": nfc("/".join(rel.parts[1:-1])),
                    "title": title,
                    "date": doc_date,
                    "ext": ext.lower(),
                    "deleted": day.name,
                    "size": full.stat().st_size,
                })
    return items


def trash_file(archive: Path, trash_path: str, can_read) -> Path:
    src, rel = _trash_source(archive, trash_path)
    if not can_read(nfc(rel.parts[0])):
        raise DocOpError("not in the trash")
    return src


def purge_trash(archive: Path, days: int, today: date | None = None) -> int:
    """Delete trash day folders older than ``days`` for good; returns the number of files removed."""
    if days <= 0:
        return 0
    root = archive / TRASH
    if not root.is_dir():
        return 0
    today = today or date.today()
    removed = 0
    for day in root.iterdir():
        try:
            when = date.fromisoformat(day.name)
        except ValueError:
            continue
        if day.is_dir() and (today - when).days >= days:
            removed += sum(len(files) for _, _, files in os.walk(day))
            shutil.rmtree(day)
    return removed


def save_asset(archive: Path, doc: dict, name: str, data: bytes) -> str:
    """Store a picture or attachment in ``<Seite>.assets/``; returns the link to put into the page."""
    _writable(archive)
    if not data:
        raise DocOpError("empty file")
    if len(data) > MAX_ASSET:
        raise DocOpError("file too large")
    src = _source(archive, doc)
    if src.suffix.lower() != ".md":
        raise DocOpError("only pages have attachments")
    base = Path(nfc(name or "").replace("\\", "/")).name
    stem, dot, ext = base.rpartition(".")
    if not dot:
        stem, ext = base, ""
    stem, ext = file_stem(stem, 80), re.sub(r"[^0-9A-Za-z]", "", ext)[:10].lower()
    if not stem:
        raise DocOpError("file name missing")
    folder = _assets(src)
    with _lock:
        _makedirs(folder, archive.resolve())
        dest, n = folder / (f"{stem}.{ext}" if ext else stem), 1
        while dest.exists():
            n += 1
            dest = folder / (f"{stem} ({n}).{ext}" if ext else f"{stem} ({n})")
        write_atomic(dest, data)
    return quote(f"{nfc(folder.name)}/{dest.name}")
