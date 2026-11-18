"""Where the archive lives.

Stored as ``storage.json`` in the data folder. Inside Docker the app only
sees mounted folders, so the folder picker offers the bind mounts of the
container (``/proc/self/mountinfo``) as starting points.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path

SYSTEM_MOUNTS = {"/", "/proc", "/sys", "/dev", "/dev/shm", "/dev/pts", "/dev/mqueue",
                 "/etc/hosts", "/etc/hostname", "/etc/resolv.conf", "/sys/fs/cgroup"}


class StorageError(ValueError):
    pass


@dataclass
class StorageConfig:
    archive_path: str = ""
    area_labels: dict[str, str] = field(default_factory=dict)  # folder name -> display name
    trash_days: int = 30         # delete from the trash after this many days, 0 = never


def path_status(path: str) -> dict:
    p = Path(path)
    exists = p.is_dir()
    return {
        "exists": exists,
        "readable": exists and os.access(p, os.R_OK | os.X_OK),
        "writable": exists and os.access(p, os.W_OK),
    }


def mount_roots() -> list[str]:
    """Bind mounts of this container that hold user data."""
    roots: list[str] = []
    try:
        lines = Path("/proc/self/mountinfo").read_text().splitlines()
    except OSError:
        return roots
    for line in lines:
        parts = line.split(" ")
        if len(parts) < 5:
            continue
        mount_point = parts[4].replace("\\040", " ")
        fstype = line.split(" - ", 1)[1].split(" ")[0] if " - " in line else ""
        if mount_point in SYSTEM_MOUNTS or mount_point.startswith(("/proc", "/sys", "/dev", "/etc")):
            continue
        if fstype in {"proc", "sysfs", "tmpfs", "devpts", "mqueue", "cgroup", "cgroup2", "overlay"}:
            continue
        if Path(mount_point).is_dir():
            roots.append(mount_point)
    return sorted(set(roots))


class StorageService:
    def __init__(self, path: Path, default_archive: Path, extra_roots: list[str] | None = None):
        self.path = path
        self.hidden = {str(path.parent)}  # the app's own data folder is not offered
        self.default_archive = default_archive
        self.extra_roots = extra_roots or []
        self._lock = threading.Lock()

    # ------------------------------------------------------------- config

    def load(self) -> StorageConfig:
        if not self.path.exists():
            return StorageConfig(archive_path=str(self.default_archive))
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return StorageConfig(
            archive_path=raw.get("archive_path") or str(self.default_archive),
            area_labels=dict(raw.get("area_labels", {})),
            trash_days=int(raw.get("trash_days", 30)),
        )

    def _save(self, config: StorageConfig) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    def archive(self) -> Path:
        return Path(self.load().archive_path)

    def update(self, archive_path: str | None = None, area_labels: dict[str, str] | None = None,
               trash_days: int | None = None) -> StorageConfig:
        with self._lock:
            config = self.load()
            if trash_days is not None:
                if not 0 <= trash_days <= 3650:
                    raise StorageError("trash days must be between 0 and 3650")
                config.trash_days = int(trash_days)
            if area_labels is not None:
                config.area_labels = {k: v.strip()[:40] for k, v in area_labels.items() if v and v.strip()}
            if archive_path is not None:
                archive_path = _clean_path(archive_path)
                if not path_status(archive_path)["readable"]:
                    raise StorageError("archive folder not readable")
                config.archive_path = archive_path
            self._save(config)
            return config

    def public(self) -> dict:
        config = self.load()
        return {
            "archive_path": config.archive_path,
            "archive": path_status(config.archive_path),
            "area_labels": config.area_labels,
            "trash_days": config.trash_days,
        }

    # -------------------------------------------------------- folder picker

    def roots(self) -> list[str]:
        return sorted(set(mount_roots() + self.extra_roots) - self.hidden)

    def list_dir(self, path: str) -> dict:
        path = _clean_path(path)
        roots = self.roots()
        if not any(_inside(path, r) or path == r for r in roots):
            raise StorageError("outside the mounted folders")
        p = Path(path)
        if not p.is_dir():
            raise StorageError("not a folder")
        dirs = []
        try:
            for entry in sorted(p.iterdir(), key=lambda e: e.name.casefold()):
                if entry.is_dir() and not entry.name.startswith(".") and entry.name not in {"@eaDir", "#recycle"}:
                    dirs.append(entry.name)
        except PermissionError as exc:
            raise StorageError("no permission") from exc
        parent = str(p.parent) if any(_inside(str(p.parent), r) or str(p.parent) == r for r in roots) else None
        return {"path": path, "parent": parent, "dirs": dirs, "status": path_status(path)}


def _clean_path(path: str) -> str:
    path = (path or "").strip()
    if not path.startswith("/"):
        raise StorageError("absolute path required")
    return os.path.normpath(path)


def _inside(path: str, root: str) -> bool:
    path, root = os.path.normpath(path), os.path.normpath(root)
    return path != root and path.startswith(root.rstrip("/") + "/")
