"""Configuration from environment variables."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path


def _flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    archive: Path
    data: Path
    readonly: bool
    admin_user: str
    admin_password: str
    api_token: str
    rescan_minutes: int
    secret: str
    ocr: bool = True
    ocr_lang: str = "deu+eng"
    ocr_max_pages: int = 30
    text_workers: int = 1
    internal_networks: str = ""   # comma-separated CIDR ranges that count as "at home"; empty = private ranges
    trusted_proxies: str = ""     # who may tell the client address (X-Forwarded-For); empty = private ranges
    max_upload_mb: int = 100       # largest request body in MB (WISSEN_MAX_UPLOAD_MB)

    @property
    def db_path(self) -> Path:
        return self.data / "wissen.db"

    @property
    def users_path(self) -> Path:
        return self.data / "users.json"


def _load_secret(data: Path) -> str:
    """Session signing key: from env, else persisted in the data dir."""
    env = os.environ.get("WISSEN_SECRET")
    if env:
        return env
    path = data / "secret.key"
    if path.exists():
        return path.read_text().strip()
    data.mkdir(parents=True, exist_ok=True)
    key = secrets.token_urlsafe(48)
    path.write_text(key)
    path.chmod(0o600)
    return key


def load_settings() -> Settings:
    data = Path(os.environ.get("WISSEN_DATA", "./data")).resolve()
    data.mkdir(parents=True, exist_ok=True)
    return Settings(
        archive=Path(os.environ.get("WISSEN_ARCHIVE", "./archiv")).resolve(),
        data=data,
        readonly=_flag("WISSEN_READONLY", True),
        admin_user=os.environ.get("WISSEN_ADMIN_USER", "admin"),
        admin_password=os.environ.get("WISSEN_ADMIN_PASSWORD", ""),
        api_token=os.environ.get("WISSEN_API_TOKEN", ""),
        rescan_minutes=int(os.environ.get("WISSEN_RESCAN_MINUTES", "10")),
        secret=_load_secret(data),
        ocr=_flag("WISSEN_OCR", True),
        ocr_lang=os.environ.get("WISSEN_OCR_LANG", "deu+eng"),
        ocr_max_pages=int(os.environ.get("WISSEN_OCR_MAX_PAGES", "30")),
        internal_networks=os.environ.get("WISSEN_INTERNAL_NETWORKS", ""),
        trusted_proxies=os.environ.get("WISSEN_TRUSTED_PROXIES", ""),
        max_upload_mb=int(os.environ.get("WISSEN_MAX_UPLOAD_MB", "100")),
        text_workers=int(os.environ.get("WISSEN_TEXT_WORKERS", str(max(1, min(4, (os.cpu_count() or 2) // 3))))),
    )
