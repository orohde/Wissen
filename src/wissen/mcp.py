"""MCP endpoint: the archive as tools for an AI assistant.

A thin layer over the REST API, spoken as JSON-RPC over HTTP (the "streamable HTTP"
transport of the Model Context Protocol, answered with plain JSON). The API key from
*Settings → Connections* goes along as ``Authorization: Bearer <key>``, exactly as for the
REST API; what a key may not do there it may not do here either. The endpoint is
off until an administrator switches it on (Settings → Connections).

Every tool calls the same functions the REST routes use, so rights, the editing lock,
versions and the trash behave the same.
"""

from __future__ import annotations

import base64
import binascii
import json
from types import SimpleNamespace
from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from . import __version__
from .auth import User, current_user
from .index import HL_END, HL_START

PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")
MAX_ATTACHMENT = 10 * 1024 * 1024       # through this tool; larger files go over the REST route

INSTRUCTIONS = (
    "Wissen! is a folder-based archive of Markdown pages and PDFs. Documents live in areas "
    "(top folders) and folders below them. A page has a fixed id that survives renaming and "
    "moving; use it for every later call. Read a page before changing it. Prefer edit_page "
    "(exact text replacement) or append_to_page over update_page for small changes. Every "
    "change keeps the earlier text as a version, and trash_document only moves to the trash."
)


class ToolError(Exception):
    pass


def _text(value: Any) -> dict:
    return {"type": "text", "text": value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=1)}


def _brief(doc: dict) -> dict:
    out = {"id": doc["id"], "title": doc["title"], "path": doc["path"], "kind": "page" if doc["ext"] == "md" else doc["ext"],
           "date": doc.get("date"), "changed": doc.get("changed")}
    snippet = doc.get("snippet")
    if snippet:
        out["snippet"] = snippet.replace(HL_START, "**").replace(HL_END, "**")
    tags = [*doc.get("page_tags", []), *doc.get("tags", [])]
    if tags:
        out["tags"] = sorted(set(tags))
    return out


def _schema(properties: dict, required: tuple[str, ...] = ()) -> dict:
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


_ID = {"type": "string", "description": "The document's id, as returned by search_documents or create_page."}
_AREA = {"type": "string", "description": "Area name (see list_areas)."}
_FOLDER = {"type": "string", "description": "Folder path inside the area, e.g. \"Haushalt/Küche\"; empty for the area's main folder."}


def build_tools(ops: SimpleNamespace) -> dict[str, dict]:
    """The tools by name: description, input schema, whether it writes, and the function behind it."""
    from .app import ContentIn, MoveIn, PageIn, RenameIn, TrashRestoreIn

    def list_areas(user: User):
        return ops.areas(user=user)

    def list_folders(user: User, area: str = ""):
        def walk(node, depth=0):
            rows = [{"folder": node["path"], "documents": node["own"], "with_subfolders": node["count"]}] if node["path"] else []
            for child in node["children"]:
                rows += walk(child, depth + 1)
            return rows
        return walk(ops.tree(areas=area or None, user=user))

    def search_documents(user: User, query: str = "", area: str = "", folder: str = "", recursive: bool = True,
                         kind: str = "", sort: str = "", limit: int = 30):
        if kind not in ("", "page", "pdf"):
            raise ToolError("kind must be \"page\" or \"pdf\"")
        if sort not in ("", "date", "title", "changed", "relevance"):
            raise ToolError("sort must be date, title, changed or relevance")
        result = ops.documents(folder=folder, recursive=recursive or bool(query), q=query, areas=area or None, tags=None,
                               kind={"page": "md"}.get(kind, kind), limit=max(1, min(int(limit), 200)), offset=0,
                               sort=sort, desc=sort != "title", user=user)
        return {"total": result["total"], "documents": [_brief(d) for d in result["items"]]}

    def _doc(user: User, id: str = "", path: str = "") -> dict:
        if id:
            return ops.document(id, user=user)
        if path:
            return ops.document_by_path(path=path, user=user)
        raise ToolError("give the id or the path of the document")

    def read_document(user: User, id: str = "", path: str = ""):
        doc = _doc(user, id, path)
        meta = _brief(doc)
        if doc["ext"] != "md":
            return [_text({**meta, "note": "PDF: the text below is what was read from it (text layer or OCR)."}),
                    _text(ops.document_text(doc["id"], user=user))]
        content = ops.page_content(doc["id"], user=user)
        meta.update(version=content["version"], can_write=content["can_write"])
        if content["lock"] and not content["lock"]["mine"]:
            meta["locked_by"] = content["lock"]["by"]
        return [_text(meta), _text(content["body"])]

    def _saved(result: dict) -> dict:
        return {**_brief(result), "version": result.get("version"), "saved": result.get("saved", True)}

    def create_page(user: User, area: str, title: str, text: str = "", folder: str = ""):
        return _brief(ops.page_create(PageIn(area=area, folder=folder, title=title, text=text), user=user))

    def update_page(user: User, id: str, text: str, base_version: str = ""):
        return _saved(ops.page_save(id, ContentIn(text=text, base_version=base_version or None, body_only=True), user=user))

    def edit_page(user: User, id: str, old_text: str, new_text: str, replace_all: bool = False):
        if not old_text:
            raise ToolError("old_text must not be empty")
        content = ops.page_content(id, user=user)
        count = content["body"].count(old_text)
        if not count:
            raise ToolError("old_text was not found in the page; read the page and copy the passage exactly")
        if count > 1 and not replace_all:
            raise ToolError(f"old_text occurs {count} times; add surrounding text to make it unique, or set replace_all")
        body = content["body"].replace(old_text, new_text) if replace_all else content["body"].replace(old_text, new_text, 1)
        saved = ops.page_save(id, ContentIn(text=body, base_version=content["version"], body_only=True), user=user)
        return {**_saved(saved), "replaced": count if replace_all else 1}

    def append_to_page(user: User, id: str, text: str):
        content = ops.page_content(id, user=user)
        body = content["body"].rstrip("\n")
        body = (body + "\n\n" if body else "") + text.strip("\n") + "\n"
        return _saved(ops.page_save(id, ContentIn(text=body, base_version=content["version"], body_only=True), user=user))

    def add_attachment(user: User, id: str, name: str, data_base64: str):
        try:
            data = base64.b64decode(data_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ToolError("data_base64 is not valid base64") from exc
        if len(data) > MAX_ATTACHMENT:
            raise ToolError(f"attachment too large for this tool (at most {MAX_ATTACHMENT // 1024 // 1024} MB)")
        saved = ops.asset_save(id, name, data, user)
        picture = name.lower().rsplit(".", 1)[-1] in ("png", "jpg", "jpeg", "gif", "webp", "svg")
        label = name.rsplit(".", 1)[0]
        return {**saved, "markdown": f"{'!' if picture else ''}[{label}]({saved['link']})"}

    def rename_document(user: User, id: str, title: str):
        return _brief(ops.doc_rename(id, RenameIn(title=title), user=user))

    def move_document(user: User, id: str, folder: str = "", area: str = ""):
        return _brief(ops.doc_move(id, MoveIn(folder=folder, area=area or None), user=user))

    def trash_document(user: User, id: str):
        return ops.doc_trash(id, user=user)

    def list_trash(user: User):
        return ops.trash_items(user=user)

    def restore_document(user: User, trash_path: str):
        return _brief(ops.trash_restore(TrashRestoreIn(trash_path=trash_path), user=user))

    def list_versions(user: User, id: str):
        return ops.version_list(id, user=user)["items"]

    def read_version(user: User, id: str, version: str, compare: bool = False):
        got = ops.version_get(id, version, compare=compare, user=user)
        blocks = [_text({"version": got["v"], "at": got["at"], "by": got["by"]}), _text(got["text"])]
        if compare:
            blocks.append(_text(got.get("diff") or "(no difference to the page as it is now)"))
        return blocks

    def restore_version(user: User, id: str, version: str):
        return _saved(ops.version_restore(id, version, user=user))

    def tool(fn: Callable, title: str, description: str, schema: dict, write: bool = False, destructive: bool = False) -> dict:
        return {"fn": fn, "title": title, "description": description, "schema": schema, "write": write,
                "destructive": destructive}

    return {
        "list_areas": tool(list_areas, "List areas", "The areas (top folders) of the archive with their number of documents.", _schema({})),
        "list_folders": tool(list_folders, "List folders", "All folders that hold documents, with counts. Optionally only one area.",
                             _schema({"area": _AREA})),
        "search_documents": tool(
            search_documents, "Search documents",
            "Full-text search over pages and PDFs (title, folder, text). Without a query it lists a folder. "
            "Returns id, title, path, dates and a snippet around the hit.",
            _schema({"query": {"type": "string", "description": "Words that must all occur; \"#tag\" filters by tag."},
                     "area": _AREA, "folder": _FOLDER,
                     "recursive": {"type": "boolean", "description": "Include subfolders (default true)."},
                     "kind": {"type": "string", "enum": ["page", "pdf"], "description": "Only pages or only PDFs."},
                     "sort": {"type": "string", "enum": ["relevance", "date", "changed", "title"]},
                     "limit": {"type": "integer", "minimum": 1, "maximum": 200, "description": "Default 30."}})),
        "read_document": tool(
            read_document, "Read a document",
            "A page as Markdown (without its head block) together with its version, or the text read from a PDF. "
            "Give the id, or the path inside the archive.",
            _schema({"id": _ID, "path": {"type": "string", "description": "e.g. \"oliver/Haushalt/Waschmaschine.md\""}})),
        "create_page": tool(
            create_page, "Create a page", "A new Markdown page. The title becomes the file name; the page gets a fixed id.",
            _schema({"area": _AREA, "title": {"type": "string"}, "folder": _FOLDER,
                     "text": {"type": "string", "description": "Markdown body; no head block and no title heading needed."}},
                    ("area", "title")), write=True),
        "update_page": tool(
            update_page, "Replace a page's text",
            "Replace the whole Markdown body of a page. The head block (title, date, id) stays. Pass the version from "
            "read_document as base_version so a change made meanwhile is not overwritten.",
            _schema({"id": _ID, "text": {"type": "string", "description": "The complete new Markdown body."},
                     "base_version": {"type": "string"}}, ("id", "text")), write=True),
        "edit_page": tool(
            edit_page, "Edit part of a page",
            "Replace an exact passage of a page with new text. old_text must match the page exactly (including line "
            "breaks) and be unique unless replace_all is set.",
            _schema({"id": _ID, "old_text": {"type": "string"}, "new_text": {"type": "string"},
                     "replace_all": {"type": "boolean"}}, ("id", "old_text", "new_text")), write=True),
        "append_to_page": tool(
            append_to_page, "Append to a page", "Add Markdown at the end of a page, after a blank line.",
            _schema({"id": _ID, "text": {"type": "string"}}, ("id", "text")), write=True),
        "add_attachment": tool(
            add_attachment, "Add a picture or attachment",
            "Store a file in the page's own folder and get the Markdown that shows or links it. The page text is not "
            "changed: put the returned markdown where it belongs with edit_page or append_to_page.",
            _schema({"id": _ID, "name": {"type": "string", "description": "File name with extension, e.g. \"ventil.jpg\"."},
                     "data_base64": {"type": "string", "description": "The file's bytes, base64-encoded."}},
                    ("id", "name", "data_base64")), write=True),
        "rename_document": tool(
            rename_document, "Rename a document",
            "Give a page or PDF a new title. A page's file name and picture folder follow, links to it are corrected; the id stays.",
            _schema({"id": _ID, "title": {"type": "string"}}, ("id", "title")), write=True),
        "move_document": tool(
            move_document, "Move a document", "Move a page or PDF into another folder and/or area. Links to it and its own links are corrected.",
            _schema({"id": _ID, "folder": _FOLDER, "area": _AREA}, ("id",)), write=True),
        "trash_document": tool(
            trash_document, "Move a document to the trash",
            "Moves a page or PDF to the trash, from where restore_document brings it back until the trash is emptied.",
            _schema({"id": _ID}, ("id",)), write=True, destructive=True),
        "list_trash": tool(list_trash, "List the trash", "What lies in the trash, newest first, and after how many days it is emptied.", _schema({})),
        "restore_document": tool(
            restore_document, "Restore from the trash", "Put a document from the trash back to where it was.",
            _schema({"trash_path": {"type": "string", "description": "trash_path from list_trash or trash_document."}},
                    ("trash_path",)), write=True),
        "list_versions": tool(list_versions, "List versions of a page", "Earlier versions of a page, newest first; each is the text before a save.",
                              _schema({"id": _ID}, ("id",))),
        "read_version": tool(
            read_version, "Read a version", "The text of an earlier version; with compare also a diff to the page as it is now.",
            _schema({"id": _ID, "version": {"type": "string", "description": "\"v\" from list_versions."},
                     "compare": {"type": "boolean"}}, ("id", "version"))),
        "restore_version": tool(
            restore_version, "Restore a version", "Make an earlier version the page again; the current text becomes a version itself.",
            _schema({"id": _ID, "version": {"type": "string"}}, ("id", "version")), write=True),
    }


def mount_mcp(app: FastAPI, ops: SimpleNamespace) -> None:
    tools = build_tools(ops)

    def can_write_anything(user: User) -> bool:
        return any(user.can_write(a["name"]) for a in app.state.index.areas())

    def listing(user: User) -> list[dict]:
        writer = can_write_anything(user)
        return [
            {"name": name, "title": t["title"], "description": t["description"], "inputSchema": t["schema"],
             "annotations": {"title": t["title"], "readOnlyHint": not t["write"], "destructiveHint": t["destructive"],
                             "idempotentHint": False, "openWorldHint": False}}
            for name, t in tools.items() if writer or not t["write"]      # a reading key is not offered what it may not do
        ]

    def call(user: User, name: str, arguments: dict) -> dict:
        spec = tools.get(name)
        if not spec:
            raise ValueError(f"unknown tool: {name}")
        if spec["write"] and not can_write_anything(user):      # not offered, and not done either
            return {"content": [_text("no write access with this key")], "isError": True}
        allowed = spec["schema"]["properties"]
        try:
            unknown = sorted(set(arguments) - set(allowed))
            if unknown:
                raise ToolError(f"unknown argument: {', '.join(unknown)}")
            missing = [key for key in spec["schema"]["required"] if arguments.get(key) in (None, "")]
            if missing:
                raise ToolError(f"missing argument: {', '.join(missing)}")
            result = spec["fn"](user, **arguments)
        except ToolError as exc:
            return {"content": [_text(str(exc))], "isError": True}
        except HTTPException as exc:
            detail = exc.detail
            if isinstance(detail, dict) and detail.get("code") == "locked":
                detail = f"the page is being edited by {detail.get('by')} right now; try again later"
            return {"content": [_text(f"{detail} (status {exc.status_code})")], "isError": True}
        except (TypeError, ValueError) as exc:        # wrong kind of argument
            return {"content": [_text(f"invalid arguments: {exc}")], "isError": True}
        content = result if isinstance(result, list) and result and isinstance(result[0], dict) and "type" in result[0] \
            else [_text(result)]
        return {"content": content, "isError": False}

    def answer(user: User, message: Any) -> dict | None:
        """One JSON-RPC message in, its answer out (None for a notification)."""
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "invalid request"}}
        method, params, msg_id = message["method"], message.get("params") or {}, message.get("id")
        if "id" not in message:
            return None
        try:
            if method == "initialize":
                wanted = params.get("protocolVersion")
                result = {"protocolVersion": wanted if wanted in PROTOCOLS else PROTOCOLS[0],
                          "capabilities": {"tools": {"listChanged": False}},
                          "serverInfo": {"name": "wissen", "title": "Wissen!", "version": __version__},
                          "instructions": INSTRUCTIONS}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": listing(user)}
            elif method == "tools/call":
                arguments = params.get("arguments") or {}
                if not isinstance(params.get("name"), str) or not isinstance(arguments, dict):
                    raise ValueError("tools/call needs a name and an arguments object")
                result = call(user, params["name"], arguments)
            else:
                return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"method not found: {method}"}}
        except ValueError as exc:
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32602, "message": str(exc)}}
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    @app.post("/api/mcp", tags=["mcp"])
    async def mcp(request: Request, user: User = Depends(current_user)):
        """Model Context Protocol over HTTP: JSON-RPC in, JSON out. Connect an assistant to this address.

        Off in a fresh installation; an administrator turns it on under Settings → Connections.
        """
        if not app.state.system.load().mcp:
            return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {
                "code": -32000, "message": "MCP is switched off in this installation (Settings → Connections)"}}, status_code=403)
        try:
            body = json.loads(await request.body())
        except ValueError:
            return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}, status_code=400)
        if isinstance(body, list):
            answers = [a for a in (answer(user, m) for m in body) if a is not None]
            return JSONResponse(answers) if answers else Response(status_code=202)
        reply = answer(user, body)
        return JSONResponse(reply) if reply is not None else Response(status_code=202)

    @app.get("/api/mcp", tags=["mcp"], include_in_schema=False)
    @app.delete("/api/mcp", tags=["mcp"], include_in_schema=False)
    def mcp_no_stream(user: User = Depends(current_user)):
        # no server-initiated messages and no sessions: there is nothing to listen to or to end
        return Response(status_code=405, headers={"Allow": "POST"})
