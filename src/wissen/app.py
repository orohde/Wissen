"""FastAPI application: REST API and web UI."""

from __future__ import annotations

import functools
import hashlib
import logging
import os
import io
from datetime import date
import re
import shutil
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from . import __version__, outbound
from .ai import AIError, AIService
from .apikeys import ApiKeyStore, KeyError_
from .auth import (User, client_ip, cookie_name, current_user, is_external, is_https,
                   require_admin, session_token)
from .config import Settings, load_settings
from . import ask, docops, links
from .docops import DocOpError
from .index import Index, on_disk, sha256_file
from .pages import head_block, new_id, read_head, set_head
from .prefs import PrefsStore
from .security import (
    BodyLimit, DEFAULT_INTERNAL, LoginGuard, Networks, Notifier, SecurityStore, SessionStore, describe_agent,
                       normalise_networks, otpauth_uri, qr_data_uri)
from .storage import StorageError, StorageService, path_status
from .system import SystemConfig, SystemStore
from .versionspruefung import UpdateCheck
from .tags import TagError, TagStore
from .inbox import INBOX_NAME, InboxError, InboxService
from .toc import TocStore
from .vikunja import SYSTEM as MAINTENANCE_SYSTEM, TEXT_CHARS as MAINTENANCE_CHARS, VikunjaError, VikunjaService, parse_tasks
from .textextract import extract, render_thumb, tesseract_available
from .users import UserError, UserStore
from .versions import Locked, Locks, VersionError, Versions, diff

THUMB_WIDTH = 360   # covers on the shelf stay sharp on high-resolution screens

log = logging.getLogger("wissen")
STATIC = Path(__file__).parent / "static"

MEDIA_TYPES = {
    "pdf": "application/pdf",
    "md": "text/markdown; charset=utf-8",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "svg": "image/svg+xml",
    "txt": "text/plain; charset=utf-8",
}
WAKE_SECONDS = 60


def file_headers(ext: str, **more: str) -> dict[str, str]:
    """Headers for a file from the archive shown in the browser: never guessed to be something
    else, and a picture (SVG) never runs a script in our origin."""
    headers = {"X-Content-Type-Options": "nosniff", **more}
    if ext == "svg":
        headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'"
    return headers


class AreaIn(BaseModel):
    name: str = Field(max_length=40)
    label: str = Field(default="", max_length=40)


class SetupIn(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(max_length=1000)
    display_name: str = Field("", max_length=100)


class Login(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(max_length=1000)
    code: str | None = Field(None, max_length=20, description="second factor: app code or recovery code")


class PasswordConfirm(BaseModel):
    password: str = Field(max_length=1000)


class CodeIn(BaseModel):
    code: str = Field(max_length=20)


class TotpOff(BaseModel):
    password: str = Field(max_length=1000)
    code: str = Field(max_length=20)


class SystemChange(BaseModel):
    ocr: bool | None = None
    ocr_lang: str | None = Field(None, max_length=200)
    ocr_max_pages: int | None = None
    rescan_minutes: int | None = None
    text_workers: int | None = None
    mcp: bool | None = None


class SecurityChange(BaseModel):
    internal_networks: str | None = Field(None, max_length=2000)
    require_2fa_external: bool | None = None
    require_2fa_internal: bool | None = None
    ntfy_url: str | None = Field(None, max_length=500)
    ntfy_token: str | None = Field(None, max_length=200)
    clear_ntfy_token: bool = False
    notify_external_login: bool | None = None
    notify_lockout: bool | None = None
    notify_2fa_changes: bool | None = None


class TreePrefs(BaseModel):
    tree_open: list[str] | None = Field(None, max_length=5000)
    language: str | None = Field(None, max_length=5)
    editor: str | None = Field(None, max_length=10)
    zoom: int | None = Field(None, description="text size of pages in percent")
    width: int | None = Field(None, description="reading width in percent of the window")


class ShelfChange(BaseModel):
    folder: str = Field("", max_length=1000, description='folder as in the list ("area/sub"), "" for everything')
    shelf: bool = Field(..., description="true: covers on a shelf, false: the list")


class NewUser(BaseModel):
    name: str
    password: str
    display_name: str = ""
    is_admin: bool = False
    areas: dict[str, str] = Field(default_factory=dict)


class UserChange(BaseModel):
    display_name: str | None = None
    password: str | None = None
    is_admin: bool | None = None
    areas: dict[str, str] | None = None
    reset_totp: bool = False
    sign_out: bool = False


class AIChange(BaseModel):
    enabled: bool | None = None
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    clear_key: bool = False
    monthly_limit_usd: float | None = Field(None, ge=0)
    excluded_areas: list[str] | None = None
    inbox_auto: bool | None = None


class StorageChange(BaseModel):
    archive_path: str | None = None
    area_labels: dict[str, str] | None = None
    trash_days: int | None = None


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=600)
    areas: str | None = Field(None, max_length=2000, description="comma-separated areas; default: all the user may read")
    voice: bool = Field(False, description="a short answer to be read out (Home Assistant, Siri): no marks, no Markdown")


class PinIn(BaseModel):
    pinned: bool = True


class PinOrder(BaseModel):
    ids: list[str] = Field(max_length=500)


class TagsIn(BaseModel):
    tags: list[str]


class TagChangeIn(BaseModel):
    ids: list[str] = Field(max_length=5000)
    add: list[str] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)


class ApiKeyIn(BaseModel):
    name: str = Field(max_length=60)
    right: str = Field("write", pattern="^(read|write)$")


class ApiKeyChange(BaseModel):
    name: str | None = Field(None, max_length=60)
    right: str | None = Field(None, pattern="^(read|write)$")


class ContentIn(BaseModel):
    text: str = Field(max_length=5_000_000)
    base_version: str | None = Field(None, max_length=64, description="``version`` from GET …/content; "
                                     "the save is refused if the page changed since")
    body_only: bool = Field(False, description="``text`` is the page without its head block; the head stays")


class PageIn(BaseModel):
    area: str = Field(max_length=40)
    folder: str = Field("", max_length=1000)
    title: str = Field(max_length=200)
    text: str = Field("", max_length=5_000_000)


class RenameIn(BaseModel):
    title: str = Field(max_length=200)


class MoveIn(BaseModel):
    folder: str = Field("", max_length=1000)
    area: str | None = Field(None, max_length=40)


class ReadingIn(BaseModel):
    id: str = Field(max_length=64, description="the PDF's id")
    page: int | None = Field(None, ge=1, le=100000)
    total: int | None = Field(None, ge=0, le=100000)
    done: bool | None = None


class VikunjaChange(BaseModel):
    url: str | None = Field(None, max_length=300)
    token: str | None = Field(None, max_length=500)
    clear_token: bool = False
    project_id: int | None = Field(None, ge=0)
    project_title: str | None = Field(None, max_length=200)


class MaintenanceTask(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    every_days: int | None = Field(None, ge=1, le=3660)
    due: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    note: str = Field("", max_length=1000)
    page: int | None = Field(None, ge=1)


class MaintenanceIn(BaseModel):
    tasks: list[MaintenanceTask] = Field(max_length=30)
    link: str = Field("", max_length=600, description="where the task points back to (the document in Wissen!)")


class InboxFileIn(BaseModel):
    area: str = Field(max_length=40)
    folder: str = Field("", max_length=1000)
    title: str = Field(max_length=200)
    force: bool = Field(False, description="file even if the same content is already in the archive")


class TrashRestoreIn(BaseModel):
    trash_path: str = Field(max_length=2000)


class PasswordChange(BaseModel):
    old: str
    new: str


def _worker(app: FastAPI, stop: threading.Event) -> None:
    """Keep the index in step with the folders and read the text of new documents."""
    try:
        os.nice(5)  # text recognition must not slow down the UI
    except OSError:
        pass
    last_full = 0.0
    while not stop.is_set():
        config = app.state.system.load()       # changeable under Settings → System while running
        full = app.state.full_scan.is_set() or time.time() - last_full >= max(1, config.rescan_minutes) * 60
        try:
            if full:
                app.state.full_scan.clear()
                last_full = time.time()
                index: Index = app.state.index
                log.info("scan: %s", index.scan())
                purged = docops.purge_trash(index.archive, app.state.storage.load().trash_days)
                if purged:
                    log.info("trash: %s files older than the limit removed for good", purged)
                done = index.extract_pending(app.state.make_extractor(), stop=stop, workers=config.text_workers)
                if done:
                    log.info("texts extracted: %s, status %s", done, index.text_status())
        except Exception:  # noqa: BLE001 - keep the loop alive
            log.exception("background work failed")
        try:            # "Eingang automatisch vorsortieren": every round, not only with a full scan
            areas = [a["name"] for a in app.state.index.areas()]
            asked = app.state.inbox.auto_ai(app.state.ai, lambda: app.state.inbox_ai_args(areas))
            if asked:
                log.info("inbox: AI asked for %s file(s)", asked)
        except Exception:  # noqa: BLE001
            log.exception("inbox: automatic AI failed")
        if config.rescan_minutes <= 0:
            return
        app.state.wake.wait(WAKE_SECONDS)
        app.state.wake.clear()


class UpdateSwitch(BaseModel):
    on: bool


def create_app(settings: Settings | None = None, background: bool = True) -> FastAPI:
    settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        stop = threading.Event()
        if background:
            threading.Thread(target=_worker, args=(app, stop), daemon=True).start()
            threading.Thread(target=app.state.update_check.run, args=(stop,), daemon=True).start()
        yield
        stop.set()
        app.state.wake.set()

    app = FastAPI(
        title="Wissen!",
        version=__version__,
        description=("Folder-based archive for your own documentation and manuals: Markdown pages and PDFs "
                     "side by side. Sign in with the browser, or send the API key from *Settings → Connections* as "
                     "`Authorization: Bearer <key>`."),
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.settings = settings
    extra_roots = [r for r in os.environ.get("WISSEN_BROWSE_ROOTS", "").split(",") if r]
    app.state.storage = StorageService(settings.data / "storage.json", settings.archive, extra_roots)
    app.state.index = Index(settings.db_path, app.state.storage.archive())
    app.state.users = UserStore(settings.users_path)
    app.state.sessions = SessionStore(settings.data / "sessions.json")
    app.state.security = SecurityStore(settings.data / "security.json")
    app.state.notify = Notifier(app.state.security)
    # which addresses count as home: Settings → Security, else WISSEN_INTERNAL_NETWORKS, else private ranges
    app.state.networks = Networks(app.state.security.load().internal_networks or settings.internal_networks)
    app.state.apikeys = ApiKeyStore(settings.data / "apikeys.json")
    if app.state.security.import_api_token(settings.api_token):
        log.info("API key taken over from WISSEN_API_TOKEN; manage it under Settings → Connections from now on")
    # the single key from before becomes a named one; the settings file forgets it
    old = app.state.security.load().api_token
    if old:
        app.state.apikeys.take_over(old, "Bisheriger Schlüssel")
        app.state.security.set_api_token("")
    app.state.guard = LoginGuard()
    app.state.system = SystemStore(settings.data / "system.json", SystemConfig(
        ocr=settings.ocr, ocr_lang=settings.ocr_lang, ocr_max_pages=settings.ocr_max_pages,
        rescan_minutes=settings.rescan_minutes, text_workers=settings.text_workers))
    app.state.wake = threading.Event()
    app.state.update_check = UpdateCheck("wissen", __version__, settings.data)
    app.state.ai = AIService(settings.data / "ai.json")
    app.state.tags = TagStore(settings.data / "tags.json")
    app.state.prefs = PrefsStore(settings.data / "prefs.json")
    app.state.versions = Versions(settings.data / "versions")
    app.state.locks = Locks()
    app.state.full_scan = threading.Event()
    app.state.full_scan.set()

    def make_extractor():
        """The text extractor with the current settings – a partial of a module function, so the
        process pool can pickle it (a closure cannot be sent to the worker processes)."""
        config = app.state.system.load()
        return functools.partial(extract, ocr=config.ocr, lang=config.ocr_lang, max_ocr_pages=config.ocr_max_pages)
    app.state.make_extractor = make_extractor
    inbox_env = os.environ.get("WISSEN_INBOX", "").strip()
    app.state.vikunja = VikunjaService(settings.data / "vikunja.json")
    app.state.toc = TocStore(settings.data / "toc")
    app.state.inbox = InboxService(app.state.index, Path(inbox_env).resolve() if inbox_env else None,
                                   settings.data / "inbox-ai.json")

    def inbox_ai_args(areas: list[str]):
        """What the AI gets to choose from: the areas with their names and the folders that exist."""
        folders = sorted({f"{d['area']}/{d['folder']}"
                          for d in app.state.index.documents(areas, recursive=True, limit=5000)["items"] if d["folder"]},
                         key=str.casefold)
        labels = [{"name": a, "label": area_label(a)} for a in areas]
        extractor = app.state.make_extractor()
        return (lambda p: extractor(p, "pdf").text), labels, folders
    app.state.inbox_ai_args = inbox_ai_args

    def kick(full: bool = True) -> None:
        if full:
            app.state.full_scan.set()
        app.state.wake.set()

    if app.state.users.bootstrap(settings.admin_user, settings.admin_password):
        log.info("created first administrator %r from the environment", settings.admin_user)

    def area_label(name: str) -> str:
        """Display name of an area: own label, else the matching account, else capitalised."""
        if not name:
            return ""
        custom = app.state.storage.load().area_labels.get(name)
        if custom:
            return custom
        account = app.state.users.get(name)
        if account and account.display_name and account.display_name != account.name:
            return account.display_name
        return name[:1].upper() + name[1:]

    def allowed_areas(user: User) -> list[str]:
        return [a["name"] for a in app.state.index.areas() if user.can_read(a["name"])]

    def pick_areas(user: User, wanted: str | None) -> list[str]:
        allowed = allowed_areas(user)
        if not wanted:
            return allowed
        chosen = set(wanted.split(","))
        return [a for a in allowed if a in chosen]

    # ----------------------------------------------------------- public

    @app.get("/api/version", tags=["system"])
    def version():
        return {"name": "Wissen!", "version": __version__}

    @app.post("/api/login", tags=["auth"])
    def login(body: Login, request: Request, response: Response):
        name = body.username.strip().lower()
        external = is_external(request)
        ip = client_ip(request)
        guard: LoginGuard = app.state.guard

        def refuse(status: int, detail: str, count: bool = True):
            if count:
                failures, seconds = guard.fail(name, external)
                if seconds and failures % 5 == 0:
                    app.state.notify.send(
                        "notify_lockout", "lock.title", "lock.body", priority=4, tags="warning",
                        user=name, count=failures, ip=ip, minutes=max(1, seconds // 60),
                        where=app.state.notify.text("where.ext" if external else "where.int"))
            raise HTTPException(status_code=status, detail=detail)

        wait = guard.begin(name, external)
        if wait:
            raise HTTPException(status_code=429, detail="locked", headers={"Retry-After": str(wait)})
        try:
            account = app.state.users.authenticate(name, body.password)
            if not account:
                refuse(401, "invalid credentials")
            policy = app.state.security.load()
            if external and policy.require_2fa_external and not account.has_totp:
                refuse(403, "second factor required outside", count=False)
            mfa = False
            if account.has_totp and (external or policy.require_2fa_internal or body.code):
                if not body.code:
                    raise HTTPException(status_code=401, detail="code required")
                kind = app.state.users.second_factor(name, body.code)
                if not kind:
                    refuse(401, "invalid code")
                mfa = True
                if kind == "recovery":
                    left = app.state.users.get(name).public()["recovery_left"]
                    app.state.notify.send("notify_2fa_changes", "recovery.title", "recovery.body",
                                          priority=4, tags="key", user=name, left=left, ip=ip)
            guard.success(name, external)
            agent = request.headers.get("user-agent", "")
            token = app.state.sessions.create(name, ip=ip, agent=agent, external=external, mfa=mfa)
            response.set_cookie(
                cookie_name(request), token, max_age=SessionStore.max_age(external),
                httponly=True, samesite="lax", secure=is_https(request), path="/",
            )
            if external:
                app.state.notify.send("notify_external_login", "external.title", "external.body",
                                      user=name, ip=ip, agent=describe_agent(agent))
            return account.public()
        finally:
            guard.end(name, external)

    @app.get("/api/setup", tags=["auth"])
    def setup_state(request: Request):
        """Is this a fresh installation without any account? Then the first administrator is created here."""
        return {"needed": not app.state.users.all(), "home": not is_external(request)}

    @app.post("/api/setup", tags=["auth"], status_code=201)
    def setup(body: SetupIn, request: Request, response: Response):
        """Create the first administrator – only while there is no account, and only from the home network."""
        if app.state.users.all():
            raise HTTPException(status_code=409, detail="already set up")
        if is_external(request):
            raise HTTPException(status_code=403, detail="first setup only from the home network")
        try:
            account = app.state.users.create(body.username, body.password, body.display_name,
                                             is_admin=True, only_if_empty=True)
        except UserError as exc:
            status = 409 if "already" in str(exc) else 400
            raise HTTPException(status_code=status, detail=str(exc)) from exc
        log.info("first administrator %r created on the setup page", account.name)
        ip = client_ip(request)
        token = app.state.sessions.create(account.name, ip=ip, agent=request.headers.get("user-agent", ""),
                                          external=False, mfa=False)
        response.set_cookie(
            cookie_name(request), token, max_age=SessionStore.max_age(False),
            httponly=True, samesite="lax", secure=is_https(request), path="/",
        )
        return account.public()

    @app.post("/api/logout", tags=["auth"])
    def logout(request: Request, response: Response):
        token = session_token(request)
        if token:
            app.state.sessions.revoke_token(token)
        response.delete_cookie(cookie_name(request), path="/", secure=is_https(request), httponly=True)
        return {"ok": True}

    # ------------------------------------------------------ authenticated

    @app.get("/api/me", tags=["auth"])
    def me(request: Request, user: User = Depends(current_user)):
        account = app.state.users.get(user.name)
        return {"name": user.name, "display_name": user.display_name,
                "totp": bool(account and account.has_totp),
                "recovery_left": account.public()["recovery_left"] if account else 0,
                "external": is_external(request),
                "is_admin": user.is_admin, "areas": allowed_areas(user),
                "write_areas": [a for a in allowed_areas(user) if user.can_write(a)],
                "language": app.state.prefs.get(user.name)["language"],
                "editor": app.state.prefs.get(user.name)["editor"],
                "zoom": app.state.prefs.get(user.name)["zoom"], "width": app.state.prefs.get(user.name)["width"],
                "shelves": app.state.prefs.get(user.name)["shelves"]}

    @app.get("/api/me/prefs", tags=["auth"])
    def my_prefs(user: User = Depends(current_user)):
        return app.state.prefs.get(user.name)

    @app.put("/api/me/prefs", tags=["auth"])
    def put_my_prefs(body: TreePrefs, user: User = Depends(current_user)):
        if body.language is not None:
            try:
                app.state.prefs.set_language(user.name, body.language)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        if body.editor is not None:
            try:
                app.state.prefs.set_editor(user.name, body.editor)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        if body.zoom is not None or body.width is not None:
            app.state.prefs.set_view(user.name, body.zoom, body.width)
        if body.tree_open is not None:
            app.state.prefs.set_tree_open(user.name, body.tree_open)
        return app.state.prefs.get(user.name)

    @app.post("/api/documents/{doc_id}/cheatsheet", tags=["ai"])
    def make_cheatsheet(doc_id: str, user: User = Depends(current_user)):
        """Let the AI write a "Spickzettel" for a PDF: a page next to it with the essentials and page links.

        An existing one is rewritten (its earlier text stays in the versions)."""
        from . import cheatsheet
        doc = _writable_doc(doc_id, user)
        if doc["ext"] != "pdf":
            raise HTTPException(status_code=400, detail="only for PDFs")
        config = app.state.ai.load()
        if not config.enabled:
            raise HTTPException(status_code=400, detail="AI is disabled")
        if not app.state.ai.allowed_for(doc["area"]):
            raise HTTPException(status_code=403, detail="this area is never sent to the AI")
        body = app.state.index.document_text(doc["sha256"])
        if not body.strip():
            raise HTTPException(status_code=409, detail="the text of this PDF is not read yet")
        limit = cheatsheet.HOSTED_CHARS if config.provider == "anthropic" else cheatsheet.LOCAL_CHARS
        text, pages, cut = cheatsheet.pages_text(body, limit)
        try:
            answer = app.state.ai.complete(cheatsheet.SYSTEM, cheatsheet.prompt(doc["title"], text, cut),
                                           max_tokens=6000, effort="medium")
        except AIError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        pdf_name = doc["path"].rsplit("/", 1)[-1]
        title = doc["title"] + cheatsheet.SUFFIX
        content = cheatsheet.page_text(doc["title"], pdf_name, answer.text, pages, answer.model, cut)
        rel = "/".join(filter(None, [doc["area"], doc.get("folder") or "", docops.file_stem(title) + ".md"]))
        existing = app.state.index.by_path(rel, allowed_areas(user))
        if existing:
            old = docops.read_page(app.state.index.archive, existing)
            text = set_head(head_block(old).rstrip("\n") + "\n\n" + content, date=time.strftime("%Y-%m-%d"))   # same id, new text
            return _save(existing, user, text, old)
        try:
            rel = docops.new_page(app.state.index.archive, doc["area"], doc.get("folder") or "", title, content)
        except DocOpError as exc:
            raise _op(exc) from exc
        return _changed(user, rel)

    # ------------------------------------------------------------- table of contents

    @app.get("/api/documents/{doc_id}/toc", tags=["archive"])
    def get_toc(doc_id: str, user: User = Depends(current_user)):
        """The articles of a magazine with the PDF page they start on (empty until made)."""
        doc = _doc_or_404(doc_id, user)
        found = app.state.toc.get(doc["sha256"]) if doc["ext"] == "pdf" else None
        return found or {"entries": [], "model": "", "at": ""}

    @app.post("/api/documents/{doc_id}/toc", tags=["ai"])
    def make_toc(doc_id: str, user: User = Depends(current_user)):
        """Let the AI list the articles (a few cents for a magazine); an earlier list is replaced."""
        from . import toc
        doc = _writable_doc(doc_id, user)
        if doc["ext"] != "pdf":
            raise HTTPException(status_code=400, detail="only for PDFs")
        if not app.state.ai.load().enabled:
            raise HTTPException(status_code=400, detail="AI is disabled")
        if not app.state.ai.allowed_for(doc["area"]):
            raise HTTPException(status_code=403, detail="this area is never sent to the AI")
        text, pages = toc.build_text(app.state.index.document_text(doc["sha256"]))
        if not text.strip():
            raise HTTPException(status_code=409, detail="the text of this PDF is not read yet")
        try:
            answer = app.state.ai.complete(toc.SYSTEM, f"Dokument: {doc['title']}\n\n{text}", max_tokens=4000)
        except AIError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return app.state.toc.put(doc["sha256"], toc.parse(answer.text, pages), answer.model)

    @app.get("/api/tocs", tags=["archive"])
    def tocs_known(user: User = Depends(current_user)):
        """Content hashes of the PDFs that have a table of contents (for the shelf)."""
        return sorted(app.state.toc.known() & set(app.state.index.shas(allowed_areas(user))))

    # ------------------------------------------------------------- vikunja

    @app.get("/api/vikunja", tags=["vikunja"])
    def get_vikunja(user: User = Depends(require_admin)):
        return app.state.vikunja.load().public()

    @app.put("/api/vikunja", tags=["vikunja"])
    def put_vikunja(body: VikunjaChange, user: User = Depends(require_admin)):
        try:
            return app.state.vikunja.update(body.url, body.token, body.project_id, body.project_title,
                                            body.clear_token).public()
        except VikunjaError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/vikunja/projects", tags=["vikunja"])
    def vikunja_projects(user: User = Depends(require_admin)):
        """The projects the token can see – also the connection test."""
        try:
            return app.state.vikunja.projects()
        except VikunjaError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/documents/{doc_id}/maintenance", tags=["vikunja"])
    def maintenance_suggest(doc_id: str, user: User = Depends(current_user)):
        """The AI reads the recurring maintenance of a manual or cheat sheet; nothing is created yet."""
        doc = _doc_or_404(doc_id, user)
        if not app.state.ai.load().enabled:
            raise HTTPException(status_code=400, detail="AI is disabled")
        if not app.state.ai.allowed_for(doc["area"]):
            raise HTTPException(status_code=403, detail="this area is never sent to the AI")
        if doc["ext"] == "md":
            from .pages import body_text
            text = body_text(docops.read_page(app.state.index.archive, doc))
        else:
            from . import cheatsheet
            text = cheatsheet.pages_text(app.state.index.document_text(doc["sha256"]), MAINTENANCE_CHARS)[0]
        if not text.strip():
            raise HTTPException(status_code=409, detail="the text of this document is not read yet")
        try:
            answer = app.state.ai.complete(MAINTENANCE_SYSTEM, f"Dokument: {doc['title']}\n\n{text[:MAINTENANCE_CHARS]}",
                                           max_tokens=2000)
        except AIError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"tasks": parse_tasks(answer.text)}

    @app.post("/api/documents/{doc_id}/maintenance/create", tags=["vikunja"])
    def maintenance_create(doc_id: str, body: MaintenanceIn, user: User = Depends(current_user)):
        """Create the confirmed tasks in the chosen Vikunja project, each pointing back to the document."""
        doc = _doc_or_404(doc_id, user)
        if not [a for a in allowed_areas(user) if user.can_write(a)]:
            raise HTTPException(status_code=403, detail="no write access")
        link = body.link if re.match(r"^https?://", body.link or "") else ""
        made, failed = [], []
        for task in body.tasks:
            lines = [task.note] if task.note else []
            if link:
                lines.append(f"Aus Wissen!: [{doc['title']}{f', S. {task.page}' if task.page else ''}]({link})")
            due = date.fromisoformat(task.due) if task.due else None
            try:
                made.append(app.state.vikunja.create_task(task.title, "\n\n".join(lines), due, task.every_days))
            except VikunjaError as exc:
                failed.append({"title": task.title, "error": str(exc)})
                if any(w in str(exc) for w in ("token", "reached", "set up", "project")):   # the rest would fail alike
                    break
        return {"created": made, "failed": failed}

    @app.get("/api/qr", tags=["archive"])
    def qr_code(text: str = Query(..., max_length=600, description="what the code holds, an http(s) link"),
                user: User = Depends(current_user)):
        """A QR code as SVG, e.g. for a sticker that opens a manual on the phone."""
        if not re.match(r"^https?://", text):
            raise HTTPException(status_code=400, detail="only links")
        import segno
        buf = io.BytesIO()
        segno.make(text, error="m").save(buf, kind="svg", scale=10, border=2, dark="#000", light="#fff",
                                         xmldecl=False, svgns=True)
        return Response(buf.getvalue(), media_type="image/svg+xml",
                        headers={"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
                                 "X-Content-Type-Options": "nosniff"})

    @app.get("/api/me/reading", tags=["archive"])
    def my_reading(user: User = Depends(current_user)):
        """How far this account got in its PDFs: {id: {page, total, done, at}} for the documents it may read."""
        mine = app.state.prefs.reading(_holder(user))
        if not mine:
            return {}
        areas = allowed_areas(user)
        found = {}
        for doc in app.state.index.documents(areas, recursive=True, kind="pdf", limit=100000)["items"]:
            if doc["sha256"] in mine:
                found[doc["id"]] = mine[doc["sha256"]]
        return found

    @app.put("/api/me/reading", tags=["archive"])
    def put_my_reading(body: ReadingIn, user: User = Depends(current_user)):
        """Remember the page of a PDF (the reader does this while scrolling), or mark it as read."""
        doc = _doc_or_404(body.id, user)
        if doc["ext"] != "pdf":
            raise HTTPException(status_code=400, detail="only PDFs have a reading position")
        return app.state.prefs.set_reading(_holder(user), doc["sha256"], body.page, body.total, body.done,
                                           time.strftime("%Y-%m-%dT%H:%M:%S"))

    @app.put("/api/me/shelf", tags=["auth"])
    def put_my_shelf(body: ShelfChange, user: User = Depends(current_user)):
        """Show a folder as a shelf of covers (first pages) or as the list."""
        try:
            return {"shelves": app.state.prefs.set_shelf(user.name, body.folder, body.shelf)}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def confirm(name: str, request: Request, check) -> bool:
        """Password or code asked again while signed in: the same brake as at the sign-in, so a
        stolen session cannot be used to try passwords or codes without end."""
        guard: LoginGuard = app.state.guard
        external = is_external(request)
        wait = guard.begin(name, external)
        if wait:
            raise HTTPException(status_code=429, detail="locked", headers={"Retry-After": str(wait)})
        try:
            if check():
                return True
            guard.fail(name, external)
            return False
        finally:
            guard.end(name, external)

    @app.post("/api/me/password", tags=["auth"])
    def change_own_password(body: PasswordChange, request: Request, user: User = Depends(current_user)):
        if not confirm(user.name, request, lambda: app.state.users.authenticate(user.name, body.old)):
            raise HTTPException(status_code=403, detail="wrong password")
        try:
            app.state.users.update(user.name, password=body.new)
        except UserError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        # whoever knew the old password is signed out everywhere else
        return {"ok": True, "signed_out": app.state.sessions.revoke(user.name, keep_token=session_token(request))}

    def _account_user(user: User):
        account = app.state.users.get(user.name)
        if not account:
            raise HTTPException(status_code=400, detail="only for personal accounts")
        return account

    @app.get("/api/me/sessions", tags=["auth"])
    def my_sessions(request: Request, user: User = Depends(current_user)):
        mine = app.state.sessions.get(session_token(request))
        return [{"id": s.id, "device": describe_agent(s.agent), "agent": s.agent, "ip": s.ip,
                 "created": s.created, "last_seen": s.last_seen, "expires": s.expires,
                 "external": s.external, "mfa": s.mfa, "current": bool(mine and mine.id == s.id)}
                for s in app.state.sessions.for_user(user.name)]

    @app.delete("/api/me/sessions/{session_id}", tags=["auth"])
    def end_session(session_id: str, user: User = Depends(current_user)):
        if not app.state.sessions.revoke(user.name, session_id=session_id):
            raise HTTPException(status_code=404, detail="unknown session")
        return {"ok": True}

    @app.post("/api/me/sessions/others", tags=["auth"])
    def end_other_sessions(request: Request, user: User = Depends(current_user)):
        return {"signed_out": app.state.sessions.revoke(user.name, keep_token=session_token(request))}

    @app.post("/api/me/totp/setup", tags=["auth"])
    def totp_setup(body: PasswordConfirm, request: Request, user: User = Depends(current_user)):
        account = _account_user(user)
        if not confirm(user.name, request, lambda: app.state.users.authenticate(user.name, body.password)):
            raise HTTPException(status_code=403, detail="wrong password")
        if account.has_totp:
            raise HTTPException(status_code=400, detail="second factor already on")
        secret = app.state.users.totp_begin(user.name)
        uri = otpauth_uri(secret, user.name)
        return {"secret": " ".join(secret[i:i + 4] for i in range(0, len(secret), 4)),
                "uri": uri, "qr": qr_data_uri(uri)}

    @app.post("/api/me/totp/enable", tags=["auth"])
    def totp_enable(body: CodeIn, request: Request, user: User = Depends(current_user)):
        _account_user(user)
        try:
            codes = app.state.users.totp_confirm(user.name, body.code)
        except UserError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        token = session_token(request)
        app.state.sessions.mark_mfa(token)
        # sessions from before the second factor existed must not stay valid
        app.state.sessions.revoke(user.name, keep_token=token)
        app.state.notify.send("notify_2fa_changes", "2fa.on.title", "2fa.on.body", tags="key", user=user.name)
        return {"recovery_codes": codes}

    @app.post("/api/me/totp/disable", tags=["auth"])
    def totp_disable(body: TotpOff, request: Request, user: User = Depends(current_user)):
        _account_user(user)
        if not confirm(user.name, request, lambda: app.state.users.authenticate(user.name, body.password)):
            raise HTTPException(status_code=403, detail="wrong password")
        if not confirm(user.name, request, lambda: app.state.users.second_factor(user.name, body.code)):
            raise HTTPException(status_code=400, detail="invalid code")
        app.state.users.totp_off(user.name)
        app.state.notify.send("notify_2fa_changes", "2fa.off.title", "2fa.off.body", priority=4,
                              tags="warning", user=user.name, by=user.name)
        return {"ok": True}

    @app.post("/api/me/totp/recovery", tags=["auth"])
    def totp_recovery(body: CodeIn, request: Request, user: User = Depends(current_user)):
        _account_user(user)
        if not confirm(user.name, request, lambda: app.state.users.second_factor(user.name, body.code) == "totp"):
            raise HTTPException(status_code=400, detail="invalid code")
        return {"recovery_codes": app.state.users.new_recovery(user.name)}

    @app.get("/api/security", tags=["security"])
    def get_security(request: Request, user: User = Depends(require_admin)):
        accounts = app.state.users.all()
        return {**app.state.security.load().public(), "api_keys": len(app.state.apikeys.all()),
                "without_2fa": [a.name for a in accounts if not a.has_totp],
                "networks_default": settings.internal_networks or ", ".join(DEFAULT_INTERNAL),
                "client_ip": client_ip(request)}

    @app.put("/api/security", tags=["security"])
    def put_security(body: SecurityChange, request: Request, user: User = Depends(require_admin)):
        changes = body.model_dump(exclude_unset=True)
        prefs = app.state.prefs.get(user.name) if user.name != "api" else {}
        if prefs.get("language") in ("de", "en"):
            changes["language"] = prefs["language"]
        if changes.get("require_2fa_external"):
            account = app.state.users.get(user.name)
            if account and not account.has_totp:
                raise HTTPException(status_code=400, detail="set up your own second factor first")
        if "internal_networks" in changes and changes["internal_networks"] is not None:
            try:
                spec = normalise_networks(changes["internal_networks"])
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            here = client_ip(request)
            # whoever saves from home must stay at home, or the next sign-in suddenly asks for a code
            if app.state.networks.is_internal(here) and not Networks(spec or settings.internal_networks).is_internal(here):
                raise HTTPException(status_code=400, detail=f"your own address {here} would no longer count as home")
        try:
            config = app.state.security.update(changes)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        app.state.networks = Networks(config.internal_networks or settings.internal_networks)
        return get_security(request, user)

    def _key_error(exc: KeyError_):
        return HTTPException(status_code=404 if "unknown" in str(exc) else 409 if "exists" in str(exc) else 400,
                             detail=str(exc))

    @app.get("/api/security/api-keys", tags=["security"])
    def list_api_keys(user: User = Depends(require_admin)):
        """All API keys with name, right and when they were made and last used – never the key itself."""
        return [k.public() for k in app.state.apikeys.all()]

    @app.post("/api/security/api-keys", tags=["security"], status_code=201)
    def new_api_key(body: ApiKeyIn, user: User = Depends(require_admin)):
        """A new key. ``token`` is in this answer only – it is stored as a hash and cannot be shown again."""
        try:
            key, token = app.state.apikeys.create(body.name, body.right)
        except KeyError_ as exc:
            raise _key_error(exc) from exc
        return {**key.public(), "token": token}

    @app.patch("/api/security/api-keys/{key_id}", tags=["security"])
    def change_api_key(key_id: str, body: ApiKeyChange, user: User = Depends(require_admin)):
        try:
            return app.state.apikeys.change(key_id, body.name, body.right).public()
        except KeyError_ as exc:
            raise _key_error(exc) from exc

    @app.post("/api/security/api-keys/{key_id}/renew", tags=["security"])
    def renew_api_key(key_id: str, user: User = Depends(require_admin)):
        """Same name and right, new secret; the old secret stops working at once."""
        try:
            key, token = app.state.apikeys.renew(key_id)
        except KeyError_ as exc:
            raise _key_error(exc) from exc
        return {**key.public(), "token": token}

    @app.delete("/api/security/api-keys/{key_id}", tags=["security"])
    def delete_api_key(key_id: str, user: User = Depends(require_admin)):
        try:
            app.state.apikeys.delete(key_id)
        except KeyError_ as exc:
            raise _key_error(exc) from exc
        return {"ok": True}

    @app.post("/api/security/test", tags=["security"])
    def test_security(user: User = Depends(require_admin)):
        error = app.state.notify.send("", "test.title", "test.body", wait=True, tags="white_check_mark")
        if error:
            raise HTTPException(status_code=400, detail=error)
        return {"ok": True}

    @app.get("/api/status", tags=["system"])
    def status(user: User = Depends(current_user)):
        writable = path_status(str(app.state.index.archive))["writable"]
        return {**app.state.index.meta(), "readonly": not writable, "version": __version__,
                "ocr": app.state.system.load().ocr and tesseract_available(),
                "ask": app.state.ai.load().enabled,
                "inbox": _inbox_count(user),
                "vikunja": app.state.vikunja.load().public()["ready"]}

    def _inbox_count(user: User) -> int | None:
        """Waiting files for anyone who may file somewhere; None for read-only accounts."""
        if not [a for a in allowed_areas(user) if user.can_write(a)]:
            return None
        try:
            return app.state.inbox.count()
        except OSError:
            return 0

    @app.get("/api/text-errors", tags=["system"])
    def text_errors(user: User = Depends(current_user)):
        """Documents whose text could not be read (password, damaged file …)."""
        return {"items": app.state.index.text_errors(allowed_areas(user))}

    @app.post("/api/text-errors/retry", tags=["system"])
    def text_errors_retry(user: User = Depends(require_admin)):
        n = app.state.index.retry_text_errors()
        kick()
        return {"retried": n}

    @app.get("/api/system/settings", tags=["system"])
    def get_system_settings(user: User = Depends(require_admin)):
        """Text recognition, rescan interval and worker count (defaults from the environment)."""
        return app.state.system.public()

    @app.put("/api/system/settings", tags=["system"])
    def put_system_settings(body: SystemChange, user: User = Depends(require_admin)):
        try:
            app.state.system.update(body.model_dump(exclude_unset=True))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        kick(full=False)
        return app.state.system.public()

    @app.get("/api/update", tags=["system"])
    def get_update(user: User = Depends(current_user)):
        """Update check (version.worldgate.de): installed and newest version. Only admins see the details."""
        info = app.state.update_check.public()
        return info if user.is_admin else {"installed": info["installed"]}

    @app.put("/api/update", tags=["system"])
    def put_update(body: UpdateSwitch, user: User = Depends(require_admin)):
        if app.state.update_check.public()["locked"]:
            raise HTTPException(status_code=409, detail="switched off by VERSIONSPRUEFUNG=0")
        return app.state.update_check.set_enabled(body.on)

    @app.post("/api/update/check", tags=["system"])
    def check_update(user: User = Depends(require_admin)):
        if not app.state.update_check.enabled():
            raise HTTPException(status_code=409, detail="update check is switched off")
        return app.state.update_check.check()

    @app.post("/api/rescan", tags=["system"])
    def rescan(user: User = Depends(require_admin)):
        kick()
        return {"started": True}

    @app.get("/api/areas", tags=["archive"])
    def areas(user: User = Depends(current_user)):
        return [{**a, "label": area_label(a["name"])}
                for a in app.state.index.areas() if user.can_read(a["name"])]

    @app.post("/api/areas", tags=["archive"], status_code=201)
    def area_create(body: AreaIn, user: User = Depends(require_admin)):
        """A new area: a top folder in the archive that belongs to no account; members get rights per area."""
        name = body.name.strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,39}", name):
            raise HTTPException(status_code=400, detail="invalid area name")
        archive = app.state.index.archive
        if not path_status(str(archive))["writable"]:
            raise HTTPException(status_code=400, detail="archive is read-only")
        if any(a["name"].lower() == name for a in app.state.index.areas()):
            raise HTTPException(status_code=409, detail="area exists")
        (archive / name).mkdir()
        os.chmod(archive / name, 0o775)
        if body.label.strip():
            labels = {**app.state.storage.load().area_labels, name: body.label.strip()}
            app.state.storage.update(area_labels=labels)
        return {"name": name, "label": area_label(name)}

    @app.delete("/api/areas/{name}", tags=["archive"])
    def area_delete(name: str, user: User = Depends(require_admin)):
        """Remove an area – only while it holds no documents (empty subfolders are fine)."""
        archive = app.state.index.archive
        if not any(a["name"] == name for a in app.state.index.areas()) or name.startswith((".", "_")) or "/" in name:
            raise HTTPException(status_code=404, detail="unknown area")
        if next((a for a in app.state.index.areas() if a["name"] == name), {}).get("count"):
            raise HTTPException(status_code=409, detail="area contains documents")
        target = archive / name
        if any(p.is_file() for p in target.rglob("*")):
            raise HTTPException(status_code=409, detail="area contains documents")
        shutil.rmtree(target)
        return {"ok": True}

    @app.get("/api/tree", tags=["archive"])
    def tree(areas: str | None = Query(None, description="comma-separated areas"),
             user: User = Depends(current_user)):
        return app.state.index.tree(pick_areas(user, areas))

    @app.get("/api/documents", tags=["archive"])
    def documents(
        folder: str = "",
        recursive: bool = False,
        q: str = "",
        areas: str | None = Query(None, description="comma-separated areas"),
        tags: str | None = Query(None, description="comma-separated tags, all must be present"),
        kind: str = Query("", pattern="^(|md|pdf)$", description="only pages (md) or only PDFs"),
        limit: int = Query(500, ge=1, le=5000),
        offset: int = Query(0, ge=0),
        sort: str = Query("", pattern="^(|date|title|area|changed|relevance)$",
                          description="relevance: best hits first for a search; changed: last written first; "
                                      "else (and by default) date"),
        desc: bool = Query(True),
        user: User = Depends(current_user),
    ):
        store = app.state.tags
        # "#steuer2026" in the search, or tags=… from the tag list: documents carrying all of them
        wanted = [t for t in (tags or "").split(",") if t.strip()]
        words = []
        for word in q.split():
            if word.startswith("#") and len(word) > 1:
                key = word[1:].casefold()
                match = next((x["name"] for x in store.counts() if x["name"].casefold().replace(" ", "") == key), None)
                wanted.append(match or word[1:])
            else:
                words.append(word)
        shas = store.shas_with_all(wanted) if wanted else None
        result = app.state.index.documents(
            pick_areas(user, areas), folder="" if wanted and not folder else folder,
            recursive=recursive or bool(wanted) or bool(words and not folder), query=" ".join(words), limit=limit, offset=offset, shas=shas,
            kind=kind, sort=sort, desc=desc,
        )
        tagmap = store.mapping()
        for item in result["items"]:
            item["tags"] = list(tagmap.get(item["sha256"], []))
        return result

    def _doc_or_404(doc_id: str, user: User) -> dict:
        doc = app.state.index.document(doc_id, allowed_areas(user))
        if not doc:
            raise HTTPException(status_code=404, detail="document not found")
        doc["tags"] = app.state.tags.of(doc["sha256"])
        return doc

    # ------------------------------------------------------------- pins

    def _pin_key(doc: dict) -> str:
        """What a pin holds on to: the fixed id of a page, else the content (a PDF keeps it when moved or renamed)."""
        return doc["sha256"] if doc["sha256"].startswith(doc["id"]) else doc["id"]

    def _pinned(user: User) -> list[dict]:
        allowed, out = allowed_areas(user), []
        for key in app.state.prefs.pins(_holder(user)):
            doc = app.state.index.document(key, allowed)
            if doc:                     # in the trash or no longer readable: the pin waits, unseen
                out.append({**doc, "pin": key})
        return out

    @app.get("/api/me/pins", tags=["archive"])
    def my_pins(user: User = Depends(current_user)):
        """The documents pinned to the start page, in their order."""
        return {"items": _pinned(user)}

    @app.put("/api/me/pins", tags=["archive"])
    def order_pins(body: PinOrder, user: User = Depends(current_user)):
        """Put the pins into a new order (ids as they come from GET /api/me/pins)."""
        keys = []
        for doc_id in body.ids:
            doc = app.state.index.document(doc_id, allowed_areas(user))
            if doc:
                keys.append(_pin_key(doc))
        app.state.prefs.set_pins(_holder(user), keys)
        return {"items": _pinned(user)}

    @app.put("/api/documents/{doc_id}/pin", tags=["archive"])
    def pin_document(doc_id: str, body: PinIn, user: User = Depends(current_user)):
        """Pin a page or PDF to the own start page, or take it off again."""
        doc = _doc_or_404(doc_id, user)
        try:
            app.state.prefs.pin(_holder(user), _pin_key(doc), body.pinned)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"pinned": body.pinned}

    # ------------------------------------------------------------- tags

    @app.get("/api/tags", tags=["tags"])
    def tag_list(areas: str | None = Query(None), user: User = Depends(current_user)):
        """Tags with the number of visible documents carrying them."""
        return app.state.tags.counts(app.state.index.shas(pick_areas(user, areas)))

    @app.put("/api/documents/{doc_id}/tags", tags=["tags"])
    def document_tags(doc_id: str, body: TagsIn, user: User = Depends(current_user)):
        doc = _doc_or_404(doc_id, user)
        if not user.can_write(doc["area"]):
            raise HTTPException(status_code=403, detail="no write access")
        try:
            return {"tags": app.state.tags.set(doc["sha256"], body.tags)}
        except TagError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/tags/change", tags=["tags"])
    def tags_change(body: TagChangeIn, user: User = Depends(current_user)):
        """Add and/or remove tags on many documents at once."""
        writable = [a for a in allowed_areas(user) if user.can_write(a)]
        shas = []
        for doc_id in body.ids:
            doc = app.state.index.document(doc_id, writable)
            if not doc:
                raise HTTPException(status_code=404, detail="document not found")
            shas.append(doc["sha256"])
        try:
            return {"changed": app.state.tags.change(shas, body.add, body.remove)}
        except TagError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/documents/by-path", tags=["archive"])
    def document_by_path(path: str = Query(..., max_length=2000, description="path inside the archive, e.g. oliver/Geräte/Waschmaschine.md"),
                         user: User = Depends(current_user)):
        """Find a page or PDF by where it lies – what links between pages need."""
        doc = app.state.index.by_path(path.strip("/"), allowed_areas(user))
        if not doc:
            raise HTTPException(status_code=404, detail="document not found")
        return _doc_or_404(doc["id"], user)

    @app.get("/api/documents/{doc_id}", tags=["archive"])
    def document(doc_id: str, user: User = Depends(current_user)):
        return _doc_or_404(doc_id, user)

    @app.get("/api/documents/{doc_id}/text", tags=["archive"], response_class=PlainTextResponse)
    def document_text(doc_id: str, user: User = Depends(current_user)):
        doc = _doc_or_404(doc_id, user)
        return app.state.index.document_text(doc["sha256"])

    @app.get("/api/documents/{doc_id}/file", tags=["archive"])
    def document_file(doc_id: str, download: bool = False, user: User = Depends(current_user)):
        doc = _doc_or_404(doc_id, user)
        root = app.state.index.archive.resolve()
        path = on_disk(root, doc["path"]).resolve()
        if root not in path.parents or not path.is_file():
            raise HTTPException(status_code=404, detail="file not found")
        return FileResponse(
            path,
            media_type=MEDIA_TYPES.get(doc["ext"], "application/octet-stream"),
            filename=doc["name"],
            content_disposition_type="attachment" if download else "inline",
            headers=file_headers(doc["ext"]),
        )

    @app.get("/api/documents/{doc_id}/asset/{rel:path}", tags=["archive"])
    def document_asset(doc_id: str, rel: str, user: User = Depends(current_user)):
        """A file a page points to (picture, attachment), relative to the page's own folder.

        It may lie anywhere inside the page's area – usually in ``<Seite>.assets/`` next to it –
        but never outside, so a page cannot reach into an area the reader may not see.
        """
        doc = _doc_or_404(doc_id, user)
        root = app.state.index.archive.resolve()
        area_root = (root / doc["area"]).resolve() if doc["area"] else root
        path = on_disk(root, doc["path"].rsplit("/", 1)[0] + "/" + rel if "/" in doc["path"] else rel).resolve()
        if area_root not in path.parents or not path.is_file():
            raise HTTPException(status_code=404, detail="file not found")
        inside = path.relative_to(area_root).parts
        if any(part.startswith(".") for part in inside):          # hidden folders, the trash
            raise HTTPException(status_code=404, detail="file not found")
        # a page in the archive's root belongs to no area: it reaches its own files next to it and
        # its <Seite>.assets folder, never into the areas below
        if not doc["area"] and len(inside) > 1 and not inside[0].endswith(".assets"):
            raise HTTPException(status_code=404, detail="file not found")
        ext = path.suffix.lstrip(".").lower()
        return FileResponse(path, media_type=MEDIA_TYPES.get(ext, "application/octet-stream"),
                            filename=path.name, content_disposition_type="inline",
                            headers=file_headers(ext, **{"Cache-Control": "max-age=3600"}))

    # ---------------------------------------------------------- writing

    def _op(exc: Exception) -> HTTPException:
        text = str(exc)
        status = (404 if "not found" in text or "unknown" in text or "not in the trash" in text
                  else 403 if "no write access" in text
                  else 409 if "exists" in text or "already" in text or "nothing changed" in text
                  else 400)
        return HTTPException(status_code=status, detail=text)

    def _holder(user: User) -> str:
        # every API key is the user "api": the key's name tells them apart
        return f"api:{user.display_name}" if user.name == "api" else user.name

    def _writable_doc(doc_id: str, user: User, page: bool = False) -> dict:
        doc = _doc_or_404(doc_id, user)
        if not user.can_write(doc["area"]):
            raise HTTPException(status_code=403, detail="no write access")
        if page and doc["ext"] != "md":
            raise HTTPException(status_code=400, detail="only pages can be edited")
        return doc

    def _free(doc: dict, user: User, need_own: bool = False) -> None:
        """Nobody else is editing this page (and, for the editor, the lock is the user's own)."""
        lock = app.state.locks.get(doc["id"])
        if lock and lock["holder"] != _holder(user):
            raise HTTPException(status_code=423, detail={"code": "locked", "by": lock["name"]})
        if need_own and not lock and user.name != "api":
            raise HTTPException(status_code=409, detail="lock required")

    def _sha(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _lock_view(doc: dict, user: User) -> dict | None:
        lock = app.state.locks.get(doc["id"])
        return lock and {"by": lock["name"], "mine": lock["holder"] == _holder(user),
                         "since": int(lock["since"]), "until": int(lock["until"])}

    def _changed(user: User, new_rel: str, old: dict | None = None) -> dict:
        """After a write: index at once, carry the tags along, return the document as it is now."""
        gone = [old["path"]] if old and old["path"] != new_rel else []
        app.state.index.refresh([new_rel], gone)
        doc = app.state.index.by_path(new_rel, allowed_areas(user))
        if not doc:
            raise HTTPException(status_code=500, detail="written, but not found in the index")
        if old and old["sha256"] != doc["sha256"]:
            store = app.state.tags
            tags = store.of(old["sha256"])
            if tags:      # tags hang on the content; new content takes them along
                try:
                    store.set(doc["sha256"], [*store.of(doc["sha256"]), *tags])
                    if old["sha256"] not in app.state.index.shas(allowed_areas(user)):
                        store.set(old["sha256"], [])
                except TagError:
                    log.exception("tags could not follow %s", new_rel)
        if old and old["id"] != doc["id"]:
            app.state.locks.move(old["id"], doc["id"])
        if old and _pin_key(old) != _pin_key(doc):
            app.state.prefs.repin(_pin_key(old), _pin_key(doc))
        app.state.wake.set()
        return _doc_or_404(doc["id"], user)

    def _relink(user: User, old: dict, new_rel: str) -> int:
        """After a rename or move: correct the links that would now lead nowhere. Returns pages changed.

        The document's own links are counted from its new folder, and every page that pointed at
        it gets the new path. A page somebody else is editing right now is left alone.
        """
        archive, index = app.state.index.archive, app.state.index
        writable = [a for a in allowed_areas(user) if user.can_write(a)]
        who = user.display_name or user.name
        changed = 0

        def rewrite(rel: str, fn) -> None:
            nonlocal changed
            page = index.by_path(rel, writable)
            if not page:
                return
            lock = app.state.locks.get(page["id"])
            if lock and lock["holder"] != _holder(user):
                return
            try:
                text = docops.read_page(archive, page)
                new = fn(text)
                if new == text:
                    return
                page_id = read_head(text, "").id
                if page_id:
                    app.state.versions.save(page_id, text, who)
                docops.write_page(archive, page, new)
            except (DocOpError, VersionError):
                log.exception("links in %s could not be corrected", rel)
                return
            _changed(user, rel, page)
            changed += 1

        if old["ext"] == "md":
            rewrite(new_rel, lambda text: links.rebase(text, old["path"], new_rel))
        for rel in index.pages(writable):
            if rel != new_rel:
                rewrite(rel, lambda text, rel=rel: links.retarget(text, rel, old["path"], new_rel))
        return changed

    def _save(doc: dict, user: User, text: str, old: str) -> dict:
        """Write ``text`` as the page; the text before goes to the versions. The id never changes."""
        keep, now = read_head(old, "").id, read_head(text, "").id
        if keep and now != keep:
            text = set_head(text, id=keep)
        elif not now:
            text = set_head(text, id=new_id())
        if text == old:
            return {**doc, "version": _sha(old), "saved": False}
        page_id = read_head(text, "").id
        try:
            app.state.versions.save(page_id, old, user.display_name or user.name)
            docops.write_page(app.state.index.archive, doc, text)
        except (DocOpError, VersionError) as exc:
            raise _op(exc) from exc
        return {**_changed(user, doc["path"], doc), "version": _sha(text), "saved": True}

    @app.get("/api/documents/{doc_id}/content", tags=["write"])
    def page_content(doc_id: str, user: User = Depends(current_user)):
        """A page as it stands in its file: the whole text, split into head block and body.

        ``version`` goes back as ``base_version`` when saving, so a change made meanwhile is noticed.
        """
        doc = _doc_or_404(doc_id, user)
        if doc["ext"] != "md":
            raise HTTPException(status_code=400, detail="only pages can be edited")
        try:
            text = docops.read_page(app.state.index.archive, doc)
        except DocOpError as exc:
            raise _op(exc) from exc
        head = head_block(text)
        return {"id": doc["id"], "path": doc["path"], "title": doc["title"], "text": text, "head": head,
                "body": text[len(head):], "version": _sha(text), "lock": _lock_view(doc, user),
                "can_write": user.can_write(doc["area"])}

    @app.put("/api/documents/{doc_id}/content", tags=["write"])
    def page_save(doc_id: str, body: ContentIn, user: User = Depends(current_user)):
        """Save a page. The editor needs the lock; an API key may save while nobody else holds it."""
        doc = _writable_doc(doc_id, user, page=True)
        _free(doc, user, need_own=True)
        try:
            old = docops.read_page(app.state.index.archive, doc)
        except DocOpError as exc:
            raise _op(exc) from exc
        if body.base_version and body.base_version.lower() != _sha(old):
            raise HTTPException(status_code=409, detail="page changed meanwhile")
        text = body.text.replace("\r\n", "\n")
        if body.body_only:
            text = head_block(old) + text
        return _save(doc, user, text, old)

    @app.post("/api/pages", tags=["write"], status_code=201)
    def page_create(body: PageIn, user: User = Depends(current_user)):
        """A new page ``<title>.md`` in a folder of an area; it gets a head block with a fixed id."""
        if body.area not in allowed_areas(user) or not user.can_write(body.area):
            raise HTTPException(status_code=403, detail="no write access")
        page_id = new_id()
        while app.state.index.document(page_id, [a["name"] for a in app.state.index.areas()]):
            page_id = new_id()
        try:
            rel = docops.new_page(app.state.index.archive, body.area, body.folder, body.title,
                                  body.text.replace("\r\n", "\n"), page_id)
        except DocOpError as exc:
            raise _op(exc) from exc
        return _changed(user, rel)

    @app.post("/api/documents/{doc_id}/rename", tags=["write"])
    def doc_rename(doc_id: str, body: RenameIn, user: User = Depends(current_user)):
        """A new title: head block and file name of a page (its assets folder follows), file name of a PDF."""
        doc = _writable_doc(doc_id, user)
        _free(doc, user)
        archive = app.state.index.archive
        try:
            before = docops.read_page(archive, doc) if doc["ext"] == "md" else ""
            rel = docops.rename(archive, doc, body.title)
            if read_head(before, "").id:
                app.state.versions.save(read_head(before, "").id, before, user.display_name or user.name)
        except (DocOpError, VersionError) as exc:
            raise _op(exc) from exc
        result = _changed(user, rel, doc)
        updated = _relink(user, doc, rel) if rel != doc["path"] else 0
        return {**_doc_or_404(result["id"], user), "links_updated": updated}

    @app.post("/api/documents/{doc_id}/move", tags=["write"])
    def doc_move(doc_id: str, body: MoveIn, user: User = Depends(current_user)):
        """Into another folder, or another area. Links to it, and its own links, are corrected."""
        doc = _writable_doc(doc_id, user)
        _free(doc, user)
        area = body.area or doc["area"]
        if area not in allowed_areas(user) or not user.can_write(area):
            raise HTTPException(status_code=403, detail="no write access")
        try:
            rel = docops.move(app.state.index.archive, doc, body.folder, area)
        except DocOpError as exc:
            raise _op(exc) from exc
        result = _changed(user, rel, doc)
        updated = _relink(user, doc, rel)
        return {**_doc_or_404(result["id"], user), "links_updated": updated}

    @app.post("/api/documents/{doc_id}/trash", tags=["write"])
    def doc_trash(doc_id: str, user: User = Depends(current_user)):
        """Into the trash – nothing is deleted for good before the days set under Settings → Storage are over."""
        doc = _writable_doc(doc_id, user)
        _free(doc, user)
        try:
            trash_path = docops.trash(app.state.index.archive, doc)
        except DocOpError as exc:
            raise _op(exc) from exc
        app.state.index.refresh([], [doc["path"]])
        app.state.locks.release(doc["id"], _holder(user), force=True)
        return {"trash_path": trash_path}

    @app.get("/api/trash", tags=["write"])
    def trash_items(user: User = Depends(current_user)):
        return {"items": docops.trash_list(app.state.index.archive, user.can_read),
                "days": app.state.storage.load().trash_days}

    @app.get("/api/trash/file", tags=["write"])
    def trash_get(path: str = Query(..., max_length=2000), user: User = Depends(current_user)):
        try:
            full = docops.trash_file(app.state.index.archive, path, user.can_read)
        except DocOpError as exc:
            raise _op(exc) from exc
        ext = full.suffix.lstrip(".").lower()
        return FileResponse(full, media_type=MEDIA_TYPES.get(ext, "application/octet-stream"),
                            filename=full.name, content_disposition_type="inline", headers=file_headers(ext))

    @app.post("/api/trash/restore", tags=["write"])
    def trash_restore(body: TrashRestoreIn, user: User = Depends(current_user)):
        try:
            rel = docops.restore(app.state.index.archive, body.trash_path, user.can_write)
        except DocOpError as exc:
            raise _op(exc) from exc
        return _changed(user, rel)

    @app.post("/api/trash/purge", tags=["write"])
    def trash_purge(body: TrashRestoreIn, user: User = Depends(current_user)):
        """Delete one document in the trash for good – this cannot be undone."""
        try:
            docops.purge_one(app.state.index.archive, body.trash_path, user.can_write)
        except DocOpError as exc:
            raise _op(exc) from exc
        return {"ok": True}

    def asset_save(doc_id: str, name: str, data: bytes, user: User) -> dict:
        doc = _writable_doc(doc_id, user, page=True)
        try:
            link = docops.save_asset(app.state.index.archive, doc, name, data)
        except DocOpError as exc:
            raise HTTPException(status_code=413 if "too large" in str(exc) else 400, detail=str(exc)) from exc
        return {"link": link, "size": len(data)}

    @app.post("/api/documents/{doc_id}/asset", tags=["write"], status_code=201)
    async def page_asset_upload(doc_id: str, request: Request,
                                name: str = Query(..., max_length=200, description="file name, e.g. foto.jpg"),
                                user: User = Depends(current_user)):
        """Upload a picture or attachment of a page: the file itself is the request body.

        It lands in ``<Seite>.assets/``; ``link`` is what goes into the page, e.g. ``![Foto](<link>)``.
        """
        _writable_doc(doc_id, user, page=True)
        if int(request.headers.get("content-length") or 0) > docops.MAX_ASSET:
            raise HTTPException(status_code=413, detail="file too large")
        return asset_save(doc_id, name, await request.body(), user)

    # ------------------------------------------------------------- inbox

    def _filer(user: User) -> list[str]:
        areas = [a for a in allowed_areas(user) if user.can_write(a)]
        if not areas:
            raise HTTPException(status_code=403, detail="no write access")
        return areas

    def _inbox_err(exc: Exception) -> HTTPException:
        return _op(exc) if "unknown item" not in str(exc) else HTTPException(status_code=404, detail=str(exc))

    @app.get("/api/inbox", tags=["inbox"])
    def inbox_list(user: User = Depends(current_user)):
        """Files waiting in the inbox (``_Eingang``), each with a suggestion where it belongs."""
        areas = _filer(user)
        ai = app.state.ai.load()
        return {"items": app.state.inbox.items(set(areas)), "folder": INBOX_NAME
                if app.state.inbox.root.parent == app.state.index.archive else str(app.state.inbox.root),
                "areas": areas, "auto": ai.enabled and ai.inbox_auto}

    @app.post("/api/inbox/upload", tags=["inbox"], status_code=201)
    async def inbox_upload(request: Request, name: str = Query(..., max_length=200, description="file name, e.g. Heft.pdf"),
                           user: User = Depends(current_user)):
        """One file into the inbox, the file itself is the request body. Photos become PDFs."""
        _filer(user)
        data = await request.body()
        if not data:
            raise HTTPException(status_code=400, detail="empty file")
        try:
            added = app.state.inbox.add(name, data)
        except (InboxError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        kick(full=False)            # the automatic AI (if on) need not wait for the next round
        return {"name": added}

    @app.get("/api/inbox/{key}/file", tags=["inbox"])
    def inbox_pdf(key: str, user: User = Depends(current_user)):
        _filer(user)
        try:
            path = app.state.inbox.path_of(key)
        except InboxError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return FileResponse(path, media_type="application/pdf", filename=path.name,
                            content_disposition_type="inline", headers=file_headers("pdf"))

    @app.get("/api/inbox/{key}/thumb", tags=["inbox"])
    def inbox_thumb(key: str, user: User = Depends(current_user)):
        _filer(user)
        try:
            path = app.state.inbox.path_of(key)
            sha = sha256_file(path)
        except (InboxError, OSError) as exc:
            raise HTTPException(status_code=404, detail="no preview") from exc
        cache = settings.data / "thumbs" / f"{sha}.w{THUMB_WIDTH}.png"
        if not cache.exists():
            try:
                render_thumb(path, "pdf", cache, width=THUMB_WIDTH)
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=404, detail="no preview") from exc
        return FileResponse(cache, media_type="image/png", headers={"Cache-Control": "max-age=86400"})

    @app.post("/api/inbox/{key}/file", tags=["inbox"])
    def inbox_do_file(key: str, body: InboxFileIn, user: User = Depends(current_user)):
        """File one item: it moves into the archive as ``area/folder/title.pdf``."""
        if body.area not in _filer(user):
            raise HTTPException(status_code=403, detail="no write access")
        try:
            rel = app.state.inbox.file(key, body.area, body.folder, body.title, body.force)
        except (InboxError, OSError) as exc:
            raise _inbox_err(exc) from exc
        kick(full=False)              # read the text in the background
        return _changed(user, rel)

    @app.post("/api/inbox/{key}/ai", tags=["inbox"])
    def inbox_ai(key: str, user: User = Depends(current_user)):
        """Ask the AI where the file belongs (area, folder, title)."""
        areas = _filer(user)
        try:
            return app.state.inbox.ask_ai(key, app.state.ai, *inbox_ai_args(areas))
        except InboxError as exc:
            raise _inbox_err(exc) from exc
        except AIError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/api/inbox/{key}", tags=["inbox"])
    def inbox_delete(key: str, user: User = Depends(current_user)):
        """Delete a file from the inbox for good (it was never in the archive)."""
        _filer(user)
        try:
            app.state.inbox.delete(key)
        except InboxError as exc:
            raise _inbox_err(exc) from exc
        return {"ok": True}

    @app.get("/api/documents/{doc_id}/lock", tags=["write"])
    def lock_state(doc_id: str, user: User = Depends(current_user)):
        return {"lock": _lock_view(_doc_or_404(doc_id, user), user)}

    @app.post("/api/documents/{doc_id}/lock", tags=["write"])
    def lock_take(doc_id: str, user: User = Depends(current_user)):
        """Take the editing lock or keep it alive (send it again every few minutes while editing)."""
        doc = _writable_doc(doc_id, user, page=True)
        try:
            app.state.locks.acquire(doc["id"], _holder(user), user.display_name or user.name)
        except Locked as exc:
            raise HTTPException(status_code=423, detail={"code": "locked", "by": exc.by}) from exc
        return {"lock": _lock_view(doc, user)}

    @app.delete("/api/documents/{doc_id}/lock", tags=["write"])
    def lock_drop(doc_id: str, force: bool = False, user: User = Depends(current_user)):
        """Give the lock back; an administrator may break a foreign one with ``force``."""
        doc = _writable_doc(doc_id, user, page=True)
        try:
            app.state.locks.release(doc["id"], _holder(user), force=force and user.is_admin)
        except Locked as exc:
            raise HTTPException(status_code=423, detail={"code": "locked", "by": exc.by}) from exc
        return {"ok": True}

    @app.get("/api/documents/{doc_id}/versions", tags=["write"])
    def version_list(doc_id: str, user: User = Depends(current_user)):
        """Earlier versions of a page, newest first – each is the text as it stood before a save."""
        doc = _doc_or_404(doc_id, user)
        try:
            return {"items": app.state.versions.list(doc["id"])}
        except VersionError:
            return {"items": []}

    @app.get("/api/documents/{doc_id}/versions/{v}", tags=["write"])
    def version_get(doc_id: str, v: str, compare: bool = Query(False, description="add a diff to the page as it is now"),
                    user: User = Depends(current_user)):
        doc = _doc_or_404(doc_id, user)
        try:
            version = app.state.versions.read(doc["id"], v)
            if compare:
                version["diff"] = diff(version["text"], docops.read_page(app.state.index.archive, doc))
        except (VersionError, DocOpError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return version

    @app.post("/api/documents/{doc_id}/versions/{v}/restore", tags=["write"])
    def version_restore(doc_id: str, v: str, user: User = Depends(current_user)):
        """Make an earlier version the page again; what stands there now becomes a version itself."""
        doc = _writable_doc(doc_id, user, page=True)
        _free(doc, user)
        try:
            version = app.state.versions.read(doc["id"], v)
            old = docops.read_page(app.state.index.archive, doc)
        except (VersionError, DocOpError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _save(doc, user, version["text"], old)

    # ------------------------------------------------------------ admin

    @app.get("/api/users", tags=["users"])
    def list_users(user: User = Depends(require_admin)):
        return [u.public() for u in app.state.users.all()]

    @app.post("/api/users", tags=["users"], status_code=201)
    def create_user(body: NewUser, user: User = Depends(require_admin)):
        try:
            return app.state.users.create(**body.model_dump()).public()
        except UserError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.patch("/api/users/{name}", tags=["users"])
    def update_user(name: str, body: UserChange, user: User = Depends(require_admin)):
        if name == user.name and body.is_admin is False:
            raise HTTPException(status_code=400, detail="cannot remove your own admin role")
        changes = body.model_dump(exclude_unset=True)
        reset_totp = changes.pop("reset_totp", False)
        sign_out = changes.pop("sign_out", False)
        try:
            account = app.state.users.update(name, **changes)
            if reset_totp and account.has_totp:
                app.state.users.totp_off(name)
                app.state.notify.send("notify_2fa_changes", "2fa.off.title", "2fa.off.body", priority=4,
                                      tags="warning", user=name, by=user.name)
        except UserError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if (sign_out or changes.get("password") or reset_totp) and name != user.name:
            app.state.sessions.revoke(name)
        return app.state.users.get(name).public()

    @app.delete("/api/users/{name}", tags=["users"])
    def delete_user(name: str, user: User = Depends(require_admin)):
        if name == user.name:
            raise HTTPException(status_code=400, detail="cannot delete yourself")
        try:
            app.state.users.delete(name)
        except UserError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        app.state.prefs.forget(name)
        app.state.sessions.revoke(name)
        return {"ok": True}

    @app.get("/api/storage", tags=["storage"])
    def get_storage(user: User = Depends(require_admin)):
        return app.state.storage.public()

    @app.put("/api/storage", tags=["storage"])
    def put_storage(body: StorageChange, user: User = Depends(require_admin)):
        try:
            config = app.state.storage.update(body.archive_path, body.area_labels, body.trash_days)
        except StorageError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        new_archive = Path(config.archive_path)
        if new_archive != app.state.index.archive:
            log.info("archive folder changed to %s, rescanning", new_archive)
            app.state.index.archive = new_archive
        kick()
        return app.state.storage.public()
    @app.get("/api/fs/roots", tags=["storage"])
    def fs_roots(user: User = Depends(require_admin)):
        return [{"path": r, "status": path_status(r)} for r in app.state.storage.roots()]

    @app.get("/api/fs/list", tags=["storage"])
    def fs_list(path: str, user: User = Depends(require_admin)):
        try:
            return app.state.storage.list_dir(path)
        except StorageError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/documents/{doc_id}/thumb", tags=["archive"])
    def document_thumb(doc_id: str, user: User = Depends(current_user)):
        """First page as a small picture (cached in the data folder)."""
        doc = _doc_or_404(doc_id, user)
        cache = settings.data / "thumbs" / f"{doc['sha256']}.w{THUMB_WIDTH}.png"
        if not cache.exists():
            root = app.state.index.archive.resolve()
            path = on_disk(root, doc["path"]).resolve()
            if root not in path.parents or not path.is_file():
                raise HTTPException(status_code=404, detail="file not found")
            try:
                render_thumb(path, doc["ext"], cache, width=THUMB_WIDTH)
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=404, detail="no preview") from exc
        return FileResponse(cache, media_type="image/png", headers={"Cache-Control": "max-age=86400"})

    def ai_view(config) -> dict:
        return config.public()

    @app.get("/api/ai", tags=["ai"])
    def get_ai(user: User = Depends(require_admin)):
        return ai_view(app.state.ai.load())

    @app.put("/api/ai", tags=["ai"])
    def put_ai(body: AIChange, user: User = Depends(require_admin)):
        try:
            config = app.state.ai.update(body.model_dump(exclude_unset=True))
        except AIError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if config.enabled and config.inbox_auto:
            kick(full=False)        # switched on: the inbox gets sorted now, not with the next round
        return ai_view(config)

    @app.get("/api/ai/models", tags=["ai"])
    def ai_models(user: User = Depends(require_admin)):
        return app.state.ai.list_models()

    @app.post("/api/ai/test", tags=["ai"])
    def test_ai(user: User = Depends(require_admin)):
        try:
            result = app.state.ai.complete(
                "You are a connection test. Reply with exactly one word.",
                "Antworte nur mit: OK", max_tokens=1000, force=True,
            )
        except AIError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"text": result.text[:200], "model": result.model, "seconds": result.seconds,
                "input_tokens": result.input_tokens, "output_tokens": result.output_tokens,
                "cost": round(result.cost, 6)}

    # the same functions again as tools for an AI assistant (Model Context Protocol)
    from types import SimpleNamespace

    from .mcp import mount_mcp
    mount_mcp(app, SimpleNamespace(
        areas=areas, tree=tree, documents=documents, document=document, document_by_path=document_by_path,
        document_text=document_text, page_content=page_content, page_save=page_save, page_create=page_create,
        doc_rename=doc_rename, doc_move=doc_move, doc_trash=doc_trash, trash_items=trash_items,
        trash_restore=trash_restore, version_list=version_list, version_get=version_get, asset_save=asset_save,
        version_restore=version_restore, inbox_list=inbox_list, inbox_do_file=inbox_do_file,
        InboxFileIn=InboxFileIn))

    @app.post("/api/ask", tags=["ai"])
    def ask_archive(body: AskIn, user: User = Depends(current_user)):
        """Answer a question from the archive, with the passages it rests on.

        Only the best-fitting passages of documents the user may read go to the AI, never areas
        that are excluded under Settings → AI. Without a fitting passage nothing is sent at all.
        """
        config = app.state.ai.load()
        if not config.enabled:
            raise HTTPException(status_code=400, detail="AI is disabled")
        allowed = [a for a in pick_areas(user, body.areas) if app.state.ai.allowed_for(a)]
        wanted = ask.terms(body.question)
        limits = ask.HOSTED if config.provider == "anthropic" else ask.LOCAL
        passages = ask.choose(app.state.index.candidates(allowed, wanted), wanted, limits) if allowed else []
        if not passages:
            return {"found": False, "answer": "", "sources": []}
        try:
            if body.voice:
                result = app.state.ai.complete(ask.VOICE_SYSTEM, ask.prompt(body.question, passages),
                                               max_tokens=400, effort="low")
            else:
                result = app.state.ai.complete(ask.SYSTEM, ask.prompt(body.question, passages),
                                               max_tokens=1500 if limits is ask.HOSTED else 600, effort="medium")
        except AIError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if body.voice:
            return {"found": True, "answer": ask.spoken(result.text),
                    "sources": [{"title": p.doc["title"], "page": p.page} for p in passages[:3]],
                    "model": result.model, "seconds": result.seconds, "cost": round(result.cost, 6)}
        return {"found": True, "answer": result.text, "sources": ask.sources(passages, result.text),
                "model": result.model, "seconds": result.seconds, "cost": round(result.cost, 6)}

    @app.middleware("http")
    async def same_origin_only(request: Request, call_next):
        """Changes only from pages of this very host (protection against cross-site requests).

        Browsers say where a request comes from in Sec-Fetch-Site; older ones only send
        Origin. Requests without either (scripts, the API token) carry no cookies of a
        victim and pass.
        """
        if request.method not in ("GET", "HEAD", "OPTIONS") and request.url.path.startswith("/api/"):
            site = request.headers.get("sec-fetch-site")
            origin = request.headers.get("origin")
            refused = False
            if site:
                refused = site not in ("same-origin", "none")
            elif origin and origin != "null":
                host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
                refused = origin.split("://", 1)[-1].rstrip("/") != host.split(",")[0].strip()
            elif origin == "null":
                refused = True
            if refused:
                return JSONResponse({"detail": "cross-site request refused"}, status_code=403)
        return await call_next(request)

    @app.middleware("http")
    async def no_stale_ui(request: Request, call_next):
        """The UI must always be revalidated, otherwise a deploy shows the old version."""
        response = await call_next(request)
        # the API as well: a page just saved must not come back from the browser's cache
        # (answers that set their own lifetime, like thumbnails, keep it)
        if not request.url.path.startswith("/api/") or "cache-control" not in response.headers:
            response.headers["Cache-Control"] = "no-cache"
        return response

    outbound.install()          # keys and tokens never follow a redirect to another address

    @app.middleware("http")
    async def docs_for_members(request: Request, call_next):
        """The API description is for those who may use the API: signed in, or with a key."""
        if request.url.path.startswith(("/api/docs", "/api/openapi.json", "/api/redoc")):
            try:
                current_user(request)
            except HTTPException as exc:
                return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        return await call_next(request)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        """Every answer says: do not guess the content type, do not show me in a frame of another
        site (clickjacking), and do not tell other sites which page the link was on."""
        response = await call_next(request)
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        headers.setdefault("Referrer-Policy", "same-origin")
        if "content-security-policy" not in headers:
            headers["Content-Security-Policy"] = "frame-ancestors 'self'"
        return response

    # Outermost layer: the client address and scheme come from X-Forwarded-For/-Proto only when the
    # connection itself comes from a trusted proxy, and then from the rightmost entry that is not one
    # of them. Trusting everybody would let anyone on the internet claim a home address.
    app.add_middleware(BodyLimit, limit=max(1, settings.max_upload_mb) * 1024 * 1024)
    app.add_middleware(ProxyHeadersMiddleware,
                       trusted_hosts=settings.trusted_proxies or ", ".join(DEFAULT_INTERNAL))
    app.mount("/", StaticFiles(directory=STATIC, html=True), name="ui")
    return app