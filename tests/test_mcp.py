"""The MCP endpoint: the archive as tools, over the same functions as the REST API."""

import json

import pytest
from fastapi.testclient import TestClient

from wissen.app import create_app
from wissen.config import Settings

API = {"Authorization": "Bearer tok"}
PAGE = """---
title: Waschmaschine entkalken
date: 2026-11-01
id: abc123def0
---

Erster Absatz mit Zitronensäure.

Zweiter Absatz.
"""


@pytest.fixture
def client(settings: Settings) -> TestClient:
    page = settings.archive / "oliver/Geräte/Waschmaschine entkalken.md"
    page.parent.mkdir(parents=True)
    page.write_text(PAGE, encoding="utf-8")
    app = create_app(settings, background=False)
    app.state.index.scan()
    app.state.index.refresh(["oliver/Geräte/Waschmaschine entkalken.md"])     # the page's text, without the worker
    app.state.system.update({"mcp": True})
    return TestClient(app)


def rpc(client: TestClient, method: str, params: dict | None = None, headers: dict = API, msg_id: int | None = 1):
    message = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if msg_id is not None:
        message["id"] = msg_id
    return client.post("/api/mcp", json=message, headers=headers)


def call(client: TestClient, name: str, headers: dict = API, **arguments):
    """(is_error, content blocks parsed where they are JSON)"""
    res = rpc(client, "tools/call", {"name": name, "arguments": arguments}, headers)
    assert res.status_code == 200, res.text
    result = res.json()["result"]
    blocks = []
    for block in result["content"]:
        try:
            blocks.append(json.loads(block["text"]))
        except ValueError:
            blocks.append(block["text"])
    return result["isError"], blocks


def test_handshake(client: TestClient):
    assert client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"}).status_code == 401
    res = rpc(client, "initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}})
    info = res.json()["result"]
    assert info["protocolVersion"] == "2025-03-26" and info["serverInfo"]["name"] == "wissen"
    assert info["capabilities"] == {"tools": {"listChanged": False}} and "Wissen!" in info["instructions"]
    assert rpc(client, "initialize", {"protocolVersion": "1999-01-01"}).json()["result"]["protocolVersion"] == "2025-06-18"
    assert rpc(client, "notifications/initialized", msg_id=None).status_code == 202        # a notification gets no answer
    assert rpc(client, "ping").json() == {"jsonrpc": "2.0", "id": 1, "result": {}}
    assert rpc(client, "resources/list").json()["error"]["code"] == -32601
    assert client.get("/api/mcp", headers=API).status_code == 405
    assert client.post("/api/mcp", content=b"{", headers=API).json()["error"]["code"] == -32700
    both = client.post("/api/mcp", headers=API, json=[
        {"jsonrpc": "2.0", "id": 1, "method": "ping"}, {"jsonrpc": "2.0", "method": "notifications/initialized"}]).json()
    assert both == [{"jsonrpc": "2.0", "id": 1, "result": {}}]


def test_tools_are_listed_by_right(client: TestClient):
    tools = rpc(client, "tools/list").json()["result"]["tools"]
    names = [t["name"] for t in tools]
    assert {"search_documents", "read_document", "create_page", "edit_page", "trash_document"} <= set(names)
    for tool in tools:
        assert tool["description"] and tool["inputSchema"]["type"] == "object"
    assert next(t for t in tools if t["name"] == "trash_document")["annotations"]["destructiveHint"] is True
    assert next(t for t in tools if t["name"] == "search_documents")["annotations"]["readOnlyHint"] is True
    # a reading key is offered no tool that writes – and cannot call one either
    client.post("/api/login", json={"username": "oliver", "password": "geheim123"})
    key = client.post("/api/security/api-keys", json={"name": "Leser", "right": "read"}).json()["token"]
    reader = {"Authorization": f"Bearer {key}"}
    fresh = TestClient(client.app)
    readable = [t["name"] for t in rpc(fresh, "tools/list", headers=reader).json()["result"]["tools"]]
    assert "read_document" in readable and "create_page" not in readable and "trash_document" not in readable
    error, blocks = call(fresh, "append_to_page", headers=reader, id="abc123def0", text="x")
    assert error and "no write access" in blocks[0]
    error, blocks = call(fresh, "read_document", headers=reader, id="abc123def0")
    assert not error and blocks[0]["can_write"] is False


def test_search_and_read(client: TestClient):
    error, (found,) = call(client, "search_documents", query="Zitronensäure")
    assert not error and found["total"] == 1
    hit = found["documents"][0]
    assert hit["id"] == "abc123def0" and hit["kind"] == "page" and "**" in hit["snippet"]
    error, (listed,) = call(client, "search_documents", area="oliver", folder="Geräte")
    assert [d["title"] for d in listed["documents"]] == ["Waschmaschine entkalken"]
    error, (meta, body) = call(client, "read_document", id="abc123def0")
    assert meta["title"] == "Waschmaschine entkalken" and len(meta["version"]) == 64
    assert body == "\nErster Absatz mit Zitronensäure.\n\nZweiter Absatz.\n"        # the head block is not the tool's business
    error, (meta2, _) = call(client, "read_document", path="oliver/Geräte/Waschmaschine entkalken.md")
    assert meta2["id"] == "abc123def0"
    error, (areas,) = call(client, "list_areas")
    assert {a["name"] for a in areas} >= {"oliver", "erika", "gemeinsam"}
    error, (folders,) = call(client, "list_folders", area="oliver")
    assert {"folder": "Geräte", "documents": 1, "with_subfolders": 1} in folders
    # a PDF comes as the text read from it
    pdf = call(client, "search_documents", query="kontoauszug")[1][0]["documents"][0]
    error, (meta, text) = call(client, "read_document", id=pdf["id"])
    assert not error and meta["kind"] == "pdf" and isinstance(text, str)
    # what goes wrong comes back as a tool error, not as a broken call
    assert call(client, "read_document")[0] and call(client, "read_document", id="zzzzzzzz")[0]
    assert call(client, "search_documents", kind="word")[0] and call(client, "search_documents", frage="x")[0]
    assert rpc(client, "tools/call", {"name": "gibtsnicht", "arguments": {}}).json()["error"]["code"] == -32602


def test_write_tools(client: TestClient, settings: Settings):
    path = settings.archive / "oliver/Geräte/Waschmaschine entkalken.md"
    error, (saved,) = call(client, "edit_page", id="abc123def0", old_text="Zitronensäure", new_text="Essigessenz")
    assert not error and saved["saved"] is True and saved["replaced"] == 1
    assert path.read_text(encoding="utf-8") == PAGE.replace("Zitronensäure", "Essigessenz")
    assert call(client, "edit_page", id="abc123def0", old_text="gibt es nicht", new_text="x")[0]
    error, blocks = call(client, "edit_page", id="abc123def0", old_text="Absatz", new_text="Abschnitt")
    assert error and "2 times" in blocks[0]
    error, (saved,) = call(client, "edit_page", id="abc123def0", old_text="Absatz", new_text="Abschnitt", replace_all=True)
    assert saved["replaced"] == 2
    call(client, "append_to_page", id="abc123def0", text="Dritter Abschnitt.")
    text = path.read_text(encoding="utf-8")
    assert text.endswith("Zweiter Abschnitt.\n\nDritter Abschnitt.\n") and text.startswith(PAGE[:PAGE.index("\n---\n") + 5])
    # the whole body, guarded by the version that was read
    _, (meta, body) = call(client, "read_document", id="abc123def0")
    error, _ = call(client, "update_page", id="abc123def0", text="Ganz neu.\n", base_version="0" * 64)
    assert error                                                              # somebody else changed it meanwhile
    error, (saved,) = call(client, "update_page", id="abc123def0", text="Ganz neu.\n", base_version=meta["version"])
    assert not error and path.read_text(encoding="utf-8").endswith("---\nGanz neu.\n")
    # versions: every save kept the text before
    _, (versions,) = call(client, "list_versions", id="abc123def0")
    assert len(versions) == 4
    _, (vmeta, vtext, diff) = call(client, "read_version", id="abc123def0", version=versions[-1]["v"], compare=True)
    assert vtext == PAGE and "+Ganz neu." in diff
    call(client, "restore_version", id="abc123def0", version=versions[-1]["v"])
    assert path.read_text(encoding="utf-8") == PAGE
    # new page, rename, move, trash and back
    error, (made,) = call(client, "create_page", area="oliver", folder="Geräte/Küche", title="Herd", text="Heiß.\n")
    assert not error and made["path"] == "oliver/Geräte/Küche/Herd.md"
    _, (renamed,) = call(client, "rename_document", id=made["id"], title="Backofen")
    assert renamed["path"] == "oliver/Geräte/Küche/Backofen.md" and renamed["id"] == made["id"]
    _, (moved,) = call(client, "move_document", id=made["id"], folder="Haushalt", area="gemeinsam")
    assert moved["path"] == "gemeinsam/Haushalt/Backofen.md"
    _, (binned,) = call(client, "trash_document", id=made["id"])
    assert call(client, "read_document", id=made["id"])[0]
    _, (trash,) = call(client, "list_trash")
    assert [i["title"] for i in trash["items"]] == ["Backofen"]
    _, (back,) = call(client, "restore_document", trash_path=binned["trash_path"])
    assert back["id"] == made["id"] and not call(client, "read_document", id=made["id"])[0]
    assert call(client, "create_page", area="oliver", title="")[0] and call(client, "create_page", area="nirgends", title="x")[0]


def test_lock_is_respected(client: TestClient):
    client.post("/api/login", json={"username": "oliver", "password": "geheim123"})
    client.post("/api/documents/abc123def0/lock")
    fresh = TestClient(client.app)
    error, blocks = call(fresh, "append_to_page", id="abc123def0", text="x")
    assert error and "being edited by oliver" in blocks[0]
    _, (meta, _) = call(fresh, "read_document", id="abc123def0")
    assert meta["locked_by"] == "oliver"


def test_off_until_an_admin_turns_it_on(settings: Settings):
    app = create_app(settings, background=False)
    app.state.index.scan()
    fresh = TestClient(app)
    res = rpc(fresh, "initialize")
    assert res.status_code == 403 and "switched off" in res.json()["error"]["message"]
    assert rpc(fresh, "tools/list").status_code == 403
    fresh.post("/api/login", json={"username": "oliver", "password": "geheim123"})
    assert fresh.get("/api/system/settings").json()["mcp"] is False
    assert fresh.put("/api/system/settings", json={"mcp": True}).json()["mcp"] is True
    assert rpc(fresh, "initialize").status_code == 200
    assert fresh.put("/api/system/settings", json={"mcp": False}).json()["mcp"] is False
    assert rpc(fresh, "ping").status_code == 403


def test_inbox_tools(client: TestClient, settings: Settings):
    import os
    import time

    from conftest import make_pdf
    inbox = settings.archive / "_Eingang" / "gemeinsam"
    inbox.mkdir(parents=True)
    pdf = inbox / "Heft_7.pdf"
    pdf.write_bytes(make_pdf("Heft sieben"))
    past = time.time() - 60
    os.utime(pdf, (past, past))
    error, [items] = call(client, "list_inbox")
    assert not error and items[0]["file"] == "gemeinsam/Heft_7.pdf"
    assert items[0]["suggestion"] == {"title": "Heft 7", "area": "gemeinsam", "folder": ""}
    error, [doc] = call(client, "file_inbox_item", key=items[0]["key"], area="gemeinsam", folder="Hefte", title="Heft 7")
    assert not error and doc["path"] == "gemeinsam/Hefte/Heft 7.pdf"
    error, [items] = call(client, "list_inbox")
    assert items == []
