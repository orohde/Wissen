"""Writing: new pages, saving with versions and lock, renaming, moving, trash, attachments."""

from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wissen import docops
from wissen.app import create_app
from wissen.config import Settings
from wissen.pages import read_head, set_head, split
from wissen.versions import Locked, Locks

API = {"Authorization": "Bearer tok"}
PAGE = """---
title: "Waschmaschine: entkalken"
date: 2026-11-01
id: abc123def0
quelle: https://example.org/x
---

Erster Absatz mit Zitronensäure.

![Bild](Waschmaschine-%20entkalken.assets/foto%201.png)
"""


@pytest.fixture
def client(settings: Settings) -> TestClient:
    page = settings.archive / "oliver/Geräte/Waschmaschine- entkalken.md"
    page.parent.mkdir(parents=True)
    page.write_text(PAGE, encoding="utf-8")
    assets = page.with_name("Waschmaschine- entkalken.assets")
    assets.mkdir()
    (assets / "foto 1.png").write_bytes(b"\x89PNG")
    (settings.archive / "oliver/Geräte/Ohne Kopf.md").write_text("# Ohne Kopf\n\nNur Text.\n", encoding="utf-8")
    app = create_app(settings, background=False)
    app.state.index.scan()
    return TestClient(app)


def login(client: TestClient, name: str = "oliver", password: str = "geheim123") -> None:
    assert client.post("/api/login", json={"username": name, "password": password}).status_code == 200


def test_head_block_helpers():
    text = set_head(PAGE, title='Neu "mit" Anführung', id="abc123def0")
    head, body = split(text)
    assert head["title"] == 'Neu "mit" Anführung' and head["quelle"] == "https://example.org/x"
    assert body == split(PAGE)[1]
    fresh = set_head("Nur Text.\n", title="Ohne: Kopf", id="zzzzzz1")
    assert read_head(fresh, "x").title == "Ohne: Kopf" and fresh.endswith("---\n\nNur Text.\n")
    listed = set_head("---\ntags:\n  - a\n  - b\ntitle: X\n---\nText", tags="c")
    assert split(listed)[0] == {"tags": "c", "title": "X"}


def test_content_and_save_with_version(client: TestClient, settings: Settings):
    got = client.get("/api/documents/abc123def0/content", headers=API).json()
    assert got["text"] == PAGE and got["head"] + got["body"] == PAGE and got["lock"] is None
    new = PAGE.replace("Zitronensäure", "Essigessenz")
    res = client.put("/api/documents/abc123def0/content", headers=API,
                     json={"text": new, "base_version": got["version"]})
    assert res.status_code == 200 and res.json()["saved"] is True, res.text
    path = settings.archive / "oliver/Geräte/Waschmaschine- entkalken.md"
    assert path.read_text(encoding="utf-8") == new
    # the browser must ask again instead of showing the text from before
    assert client.get("/api/documents/abc123def0/file", headers=API).headers["cache-control"] == "no-cache"
    assert client.get("/api/documents/abc123def0/thumb", headers=API).status_code in (200, 404)
    assert not [p for p in path.parent.iterdir() if p.name.endswith(".tmp")]
    # the index knows the new text at once, without a scan
    found = client.get("/api/documents", headers=API, params={"q": "Essigessenz"}).json()
    assert [d["id"] for d in found["items"]] == ["abc123def0"]
    assert client.get("/api/documents", headers=API, params={"q": "Zitronensäure"}).json()["total"] == 0
    # the stale base version is refused, the same text is not saved twice
    stale = client.put("/api/documents/abc123def0/content", headers=API,
                       json={"text": new + "x", "base_version": got["version"]})
    assert stale.status_code == 409
    same = client.put("/api/documents/abc123def0/content", headers=API, json={"text": new}).json()
    assert same["saved"] is False
    versions = client.get("/api/documents/abc123def0/versions", headers=API).json()["items"]
    assert len(versions) == 1 and versions[0]["by"] == "Bisheriger Schlüssel"
    one = client.get(f"/api/documents/abc123def0/versions/{versions[0]['v']}", headers=API,
                     params={"compare": True}).json()
    assert one["text"] == PAGE and "-Erster Absatz mit Zitronensäure." in one["diff"]
    assert not any(settings.archive.rglob("versions"))        # versions stay out of the share
    back = client.post(f"/api/documents/abc123def0/versions/{versions[0]['v']}/restore", headers=API)
    assert back.status_code == 200 and path.read_text(encoding="utf-8") == PAGE
    assert len(client.get("/api/documents/abc123def0/versions", headers=API).json()["items"]) == 2


def test_body_only_keeps_head_and_id_survives(client: TestClient, settings: Settings):
    path = settings.archive / "oliver/Geräte/Waschmaschine- entkalken.md"
    res = client.put("/api/documents/abc123def0/content", headers=API,
                     json={"text": "\nNur der neue Text.\n", "body_only": True})
    assert res.status_code == 200
    text = path.read_text(encoding="utf-8")
    assert text.startswith(PAGE[:PAGE.index("\n---\n") + 5]) and text.endswith("Nur der neue Text.\n")
    # a text that lost its id gets it back: the page stays the same page
    client.put("/api/documents/abc123def0/content", headers=API, json={"text": "Ganz ohne Kopf.\n"})
    assert read_head(path.read_text(encoding="utf-8"), "").id == "abc123def0"
    assert client.get("/api/documents/abc123def0", headers=API).status_code == 200


def test_page_without_head_gets_an_id(client: TestClient, settings: Settings):
    doc = client.get("/api/documents/by-path", headers=API, params={"path": "oliver/Geräte/Ohne Kopf.md"}).json()
    res = client.put(f"/api/documents/{doc['id']}/content", headers=API, json={"text": "# Ohne Kopf\n\nMehr Text.\n"})
    assert res.status_code == 200
    new_id = res.json()["id"]
    assert new_id != doc["id"] and read_head(
        (settings.archive / "oliver/Geräte/Ohne Kopf.md").read_text(encoding="utf-8"), "").id == new_id
    assert len(client.get(f"/api/documents/{new_id}/versions", headers=API).json()["items"]) == 1


def test_tags_follow_the_new_content(client: TestClient):
    login(client)
    client.put("/api/documents/abc123def0/tags", json={"tags": ["Haushalt"]})
    client.post("/api/documents/abc123def0/lock")
    client.put("/api/documents/abc123def0/content", json={"text": PAGE + "\nMehr.\n"})
    assert client.get("/api/documents/abc123def0").json()["tags"] == ["Haushalt"]
    assert [t["name"] for t in client.get("/api/tags").json()] == ["Haushalt"]


def test_lock(client: TestClient):
    login(client)
    # the editor must hold the lock; the API key may save while nobody else holds one
    assert client.put("/api/documents/abc123def0/content", json={"text": PAGE + "a"}).status_code == 409
    assert client.post("/api/documents/abc123def0/lock").json()["lock"]["mine"] is True
    assert client.put("/api/documents/abc123def0/content", json={"text": PAGE + "a"}).status_code == 200
    other = TestClient(client.app)
    refused = other.put("/api/documents/abc123def0/content", headers=API, json={"text": PAGE + "b"})
    assert refused.status_code == 423 and refused.json()["detail"] == {"code": "locked", "by": "oliver"}
    assert other.post("/api/documents/abc123def0/lock", headers=API).status_code == 423
    assert other.post("/api/documents/abc123def0/trash", headers=API).status_code == 423
    assert other.get("/api/documents/abc123def0/content", headers=API).json()["lock"]["by"] == "oliver"
    assert client.delete("/api/documents/abc123def0/lock").status_code == 200
    assert other.put("/api/documents/abc123def0/content", headers=API, json={"text": PAGE + "b"}).status_code == 200


def test_lock_runs_out():
    locks = Locks(seconds=0)
    locks.acquire("abc123", "a", "A")
    assert locks.get("abc123") is None                      # no heartbeat, no lock
    locks = Locks()
    locks.acquire("abc123", "a", "A")
    locks.acquire("abc123", "a", "A")
    with pytest.raises(Locked):
        locks.acquire("abc123", "b", "B")
    with pytest.raises(Locked):
        locks.release("abc123", "b")
    assert locks.release("abc123", "b", force=True) is True


def test_new_page(client: TestClient, settings: Settings):
    res = client.post("/api/pages", headers=API, json={
        "area": "oliver", "folder": "Geräte/Küche", "title": "Spülmaschine: Salz nachfüllen", "text": "Einfach rein.\n"})
    assert res.status_code == 201, res.text
    doc = res.json()
    assert doc["path"] == "oliver/Geräte/Küche/Spülmaschine- Salz nachfüllen.md"
    assert doc["title"] == "Spülmaschine: Salz nachfüllen" and doc["date"] == date.today().isoformat()
    text = (settings.archive / doc["path"]).read_text(encoding="utf-8")
    assert read_head(text, "").id == doc["id"] and text.endswith("---\n\nEinfach rein.\n")
    assert client.get("/api/documents", headers=API, params={"q": "Einfach rein"}).json()["total"] == 1
    again = client.post("/api/pages", headers=API, json={
        "area": "oliver", "folder": "Geräte/Küche", "title": "Spülmaschine: Salz nachfüllen"})
    assert again.status_code == 409
    for bad in ({"area": "nirgends", "title": "X"}, {"area": "oliver", "title": " . "},
                {"area": "oliver", "folder": "../raus", "title": "X"}, {"area": "oliver", "folder": ".versteckt", "title": "X"}):
        assert client.post("/api/pages", headers=API, json=bad).status_code in (400, 403), bad


def test_rename_page_takes_assets_and_links_along(client: TestClient, settings: Settings):
    res = client.post("/api/documents/abc123def0/rename", headers=API, json={"title": "Waschmaschine pflegen"})
    assert res.status_code == 200, res.text
    doc = res.json()
    assert doc["id"] == "abc123def0" and doc["path"] == "oliver/Geräte/Waschmaschine pflegen.md"
    folder = settings.archive / "oliver/Geräte"
    assert sorted(p.name for p in folder.iterdir()) == [
        "Ohne Kopf.md", "Waschmaschine pflegen.assets", "Waschmaschine pflegen.md"]
    text = (folder / "Waschmaschine pflegen.md").read_text(encoding="utf-8")
    assert "title: Waschmaschine pflegen\n" in text and "quelle: https://example.org/x" in text
    assert "![Bild](Waschmaschine%20pflegen.assets/foto%201.png)" in text
    assert client.get("/api/documents/abc123def0/asset/Waschmaschine%20pflegen.assets/foto%201.png",
                      headers=API).status_code == 200
    assert client.get("/api/documents", headers=API, params={"recursive": True, "kind": "md"}).json()["total"] == 2
    # the name of another page is taken
    clash = client.post("/api/documents/abc123def0/rename", headers=API, json={"title": "Ohne Kopf"})
    assert clash.status_code == 409
    # only the title changes (the file name stays): fine as well
    res = client.post("/api/documents/abc123def0/rename", headers=API, json={"title": "Waschmaschine: pflegen"})
    assert res.status_code == 200 and res.json()["title"] == "Waschmaschine: pflegen"
    assert len(client.get("/api/documents/abc123def0/versions", headers=API).json()["items"]) == 2


def test_rename_pdf_keeps_its_date(client: TestClient, settings: Settings):
    doc = client.get("/api/documents", headers=API, params={"q": "kontoauszug"}).json()["items"][0]
    res = client.post(f"/api/documents/{doc['id']}/rename", headers=API, json={"title": "Auszug März"})
    assert res.status_code == 200 and res.json()["path"] == "oliver/Banken/DKB/2026-03-01_Auszug März.pdf"
    assert res.json()["id"] == doc["id"]


def test_move(client: TestClient, settings: Settings):
    res = client.post("/api/documents/abc123def0/move", headers=API, json={"folder": "Haushalt/Bad", "area": "gemeinsam"})
    assert res.status_code == 200, res.text
    assert res.json()["path"] == "gemeinsam/Haushalt/Bad/Waschmaschine- entkalken.md"
    assert (settings.archive / "gemeinsam/Haushalt/Bad/Waschmaschine- entkalken.assets/foto 1.png").is_file()
    assert not (settings.archive / "oliver/Geräte/Waschmaschine- entkalken.assets").exists()
    assert client.post("/api/documents/abc123def0/move", headers=API,
                       json={"folder": "Haushalt/Bad"}).status_code == 409        # already there
    assert client.post("/api/documents/abc123def0/move", headers=API,
                       json={"folder": "x", "area": "gibtsnicht"}).status_code == 403
    tree = client.get("/api/tree", headers=API, params={"areas": "gemeinsam"}).json()
    assert "Haushalt" in [c["name"] for c in tree["children"]]


def test_trash_and_restore(client: TestClient, settings: Settings):
    res = client.post("/api/documents/abc123def0/trash", headers=API)
    assert res.status_code == 200
    trash_path = res.json()["trash_path"]
    today = date.today().isoformat()
    assert trash_path == f".papierkorb/{today}/oliver/Geräte/Waschmaschine- entkalken.md"
    assert (settings.archive / f".papierkorb/{today}/oliver/Geräte/Waschmaschine- entkalken.assets/foto 1.png").is_file()
    assert client.get("/api/documents/abc123def0", headers=API).status_code == 404
    assert ".papierkorb" not in [a["name"] for a in client.get("/api/areas", headers=API).json()]
    items = client.get("/api/trash", headers=API).json()["items"]
    assert [(i["title"], i["deleted"], i["area"]) for i in items] == [("Waschmaschine: entkalken", today, "oliver")]
    assert client.get("/api/trash/file", headers=API, params={"path": trash_path}).text == PAGE
    assert client.get("/api/trash/file", headers=API, params={"path": "oliver/Geräte/Ohne Kopf.md"}).status_code == 404
    assert client.post("/api/trash/restore", headers=API, json={"trash_path": "../x"}).status_code == 404
    back = client.post("/api/trash/restore", headers=API, json={"trash_path": trash_path})
    assert back.status_code == 200 and back.json()["id"] == "abc123def0"
    assert (settings.archive / "oliver/Geräte/Waschmaschine- entkalken.assets/foto 1.png").is_file()
    assert client.get("/api/trash", headers=API).json()["items"] == []
    assert not any((settings.archive / ".papierkorb").iterdir())          # emptied folders do not linger


def test_emptied_folders_go(client: TestClient, settings: Settings):
    made = client.post("/api/pages", headers=API, json={"area": "oliver", "folder": "A/B/C", "title": "Allein"}).json()
    client.post(f"/api/documents/{made['id']}/move", headers=API, json={"folder": "Geräte"})
    assert not (settings.archive / "oliver/A").exists()
    made = client.post("/api/pages", headers=API, json={"area": "erika", "folder": "Neu", "title": "Kurz"}).json()
    client.post(f"/api/documents/{made['id']}/trash", headers=API)
    assert not (settings.archive / "erika/Neu").exists() and (settings.archive / "erika").is_dir()
    # a folder that still holds something stays, and so does the area itself
    assert (settings.archive / "oliver/Geräte").is_dir()


def test_purge_trash(settings: Settings):
    old = settings.archive / ".papierkorb" / (date.today() - timedelta(days=40)).isoformat() / "oliver/a.md"
    new = settings.archive / ".papierkorb" / date.today().isoformat() / "oliver/b.md"
    for path in (old, new):
        path.parent.mkdir(parents=True)
        path.write_text("x")
    assert docops.purge_trash(settings.archive, 0) == 0
    assert docops.purge_trash(settings.archive, 30) == 1
    assert not old.exists() and new.exists()


def test_asset_upload(client: TestClient, settings: Settings):
    res = client.post("/api/documents/abc123def0/asset", headers=API, params={"name": "../../Mein Foto?.PNG"},
                      content=b"\x89PNG-daten")
    assert res.status_code == 201, res.text
    link = res.json()["link"]
    assert link == "Waschmaschine-%20entkalken.assets/Mein%20Foto.png"
    assert client.get(f"/api/documents/abc123def0/asset/{link}", headers=API).content == b"\x89PNG-daten"
    second = client.post("/api/documents/abc123def0/asset", headers=API, params={"name": "Mein Foto.png"}, content=b"2")
    assert second.json()["link"].endswith("Mein%20Foto%20%282%29.png")
    assert client.post("/api/documents/abc123def0/asset", headers=API, params={"name": "leer.png"},
                       content=b"").status_code == 400
    pdf = client.get("/api/documents", headers=API, params={"q": "kontoauszug"}).json()["items"][0]
    assert client.post(f"/api/documents/{pdf['id']}/asset", headers=API, params={"name": "a.png"},
                       content=b"x").status_code == 400


def test_rights(client: TestClient):
    login(client)
    made = client.post("/api/users", json={"name": "erika", "password": "geheim1234567", "areas": {"oliver": "read"}})
    assert made.status_code == 201, made.text
    key = client.post("/api/security/api-keys", json={"name": "Leser", "right": "read"}).json()["token"]
    reader = TestClient(client.app)
    for auth in ({"Authorization": f"Bearer {key}"}, None):
        if auth is None:
            login(reader, "erika", "geheim1234567")
        kw = {"headers": auth} if auth else {}
        assert reader.get("/api/documents/abc123def0/content", **kw).json()["can_write"] is False
        assert reader.put("/api/documents/abc123def0/content", json={"text": "x"}, **kw).status_code == 403
        assert reader.post("/api/documents/abc123def0/lock", **kw).status_code == 403
        assert reader.post("/api/documents/abc123def0/rename", json={"title": "x"}, **kw).status_code == 403
        assert reader.post("/api/documents/abc123def0/move", json={"folder": "x"}, **kw).status_code == 403
        assert reader.post("/api/documents/abc123def0/trash", **kw).status_code == 403
        assert reader.post("/api/pages", json={"area": "oliver", "title": "x"}, **kw).status_code == 403
        assert reader.post("/api/documents/abc123def0/asset", params={"name": "a.png"}, content=b"x", **kw).status_code == 403
    # what erika may not read does not show in her trash, and she cannot put it back
    trash_path = client.post("/api/documents/abc123def0/trash").json()["trash_path"]
    assert reader.get("/api/trash").json()["items"][0]["title"] == "Waschmaschine: entkalken"
    assert reader.post("/api/trash/restore", json={"trash_path": trash_path}).status_code == 403
    pdf = client.get("/api/documents", params={"q": "rechtsschutz"}).json()["items"][0]
    other = client.post(f"/api/documents/{pdf['id']}/trash").json()["trash_path"]
    assert len(reader.get("/api/trash").json()["items"]) == 1
    assert reader.get("/api/trash/file", params={"path": other}).status_code == 404


def test_names_written_on_a_mac(client: TestClient, settings: Settings):
    import unicodedata
    folder = settings.archive / "oliver" / unicodedata.normalize("NFD", "Küche")
    folder.mkdir()
    (folder / unicodedata.normalize("NFD", "Kühlschrank.md")).write_text("---\nid: nfd0000001\n---\nKalt.\n", encoding="utf-8")
    client.app.state.index.scan()
    assert client.put("/api/documents/nfd0000001/content", headers=API,
                      json={"text": "Sehr kalt.\n", "body_only": True}).status_code == 200
    assert len(list(folder.iterdir())) == 1                  # written to the file that was there, no twin
    made = client.post("/api/pages", headers=API, json={"area": "oliver", "folder": "Küche", "title": "Herd"}).json()
    assert made["path"] == "oliver/Küche/Herd.md" and len(list((settings.archive / "oliver").glob("K*che"))) == 1
    moved = client.post("/api/documents/nfd0000001/move", headers=API, json={"folder": "Geräte"})
    assert moved.status_code == 200 and client.get("/api/documents/nfd0000001", headers=API).json()["folder"] == "Geräte"


def test_pins_and_last_changed(client: TestClient, settings: Settings):
    login(client)
    assert client.get("/api/me/pins").json() == {"items": []}
    pdf = client.get("/api/documents", params={"q": "kontoauszug"}).json()["items"][0]
    assert client.put(f"/api/documents/{pdf['id']}/pin", json={"pinned": True}).json() == {"pinned": True}
    client.put("/api/documents/abc123def0/pin", json={})
    client.put("/api/documents/abc123def0/pin", json={})                 # twice is once
    assert [d["id"] for d in client.get("/api/me/pins").json()["items"]] == [pdf["id"], "abc123def0"]
    # pins hold on through renaming, moving and saving
    client.post(f"/api/documents/{pdf['id']}/rename", json={"title": "Auszug"})
    client.post(f"/api/documents/{pdf['id']}/move", json={"folder": "Banken/Alt"})
    client.post("/api/documents/abc123def0/rename", json={"title": "Pflege"})
    client.post("/api/documents/abc123def0/lock")
    client.put("/api/documents/abc123def0/content", json={"text": "Neu.\n", "body_only": True})
    pins = client.get("/api/me/pins").json()["items"]
    assert [(d["title"], d["folder"]) for d in pins] == [("Auszug", "Banken/Alt"), ("Pflege", "Geräte")]
    # a new order; in the trash a pin is unseen and comes back with the document
    order = client.put("/api/me/pins", json={"ids": ["abc123def0", pdf["id"]]}).json()["items"]
    assert [d["title"] for d in order] == ["Pflege", "Auszug"]
    client.delete("/api/documents/abc123def0/lock")
    trash_path = client.post("/api/documents/abc123def0/trash").json()["trash_path"]
    assert [d["title"] for d in client.get("/api/me/pins").json()["items"]] == ["Auszug"]
    client.post("/api/trash/restore", json={"trash_path": trash_path})
    assert [d["title"] for d in client.get("/api/me/pins").json()["items"]] == ["Pflege", "Auszug"]
    # a page without head block gets its id with the first save: the pin follows
    doc = client.get("/api/documents/by-path", params={"path": "oliver/Geräte/Ohne Kopf.md"}).json()
    client.put(f"/api/documents/{doc['id']}/pin", json={})
    client.post(f"/api/documents/{doc['id']}/lock")
    new_id = client.put(f"/api/documents/{doc['id']}/content", json={"text": "# Ohne Kopf\n\nMehr.\n"}).json()["id"]
    assert client.get("/api/me/pins").json()["items"][-1]["id"] == new_id
    # everyone has their own pins
    assert client.get("/api/me/pins", headers=API).json() == {"items": []}
    assert client.put(f"/api/documents/{pdf['id']}/pin", json={"pinned": False}).json() == {"pinned": False}
    assert len(client.get("/api/me/pins").json()["items"]) == 2
    # what was written last comes first
    last = client.get("/api/documents", params={"recursive": True, "sort": "changed", "limit": 2}).json()["items"]
    assert last[0]["id"] == new_id and last[0]["changed"][:10] == date.today().isoformat()


def test_editor_choice_follows_the_account(client: TestClient):
    login(client)
    assert client.get("/api/me").json()["editor"] == "source"            # the source is where everybody starts
    assert client.put("/api/me/prefs", json={"editor": "rich"}).json()["editor"] == "rich"
    assert client.get("/api/me").json()["editor"] == "rich"
    assert client.put("/api/me/prefs", json={"editor": "word"}).status_code == 400


def test_text_size_and_reading_width_follow_the_account(client: TestClient):
    login(client)
    me = client.get("/api/me").json()
    assert (me["zoom"], me["width"]) == (100, 85)                         # a little margin to begin with
    assert client.put("/api/me/prefs", json={"zoom": 130}).json()["zoom"] == 130
    got = client.put("/api/me/prefs", json={"width": 70}).json()
    assert (got["zoom"], got["width"]) == (130, 70)                       # the one does not reset the other
    far = client.put("/api/me/prefs", json={"zoom": 900, "width": 5}).json()
    assert (far["zoom"], far["width"]) == (250, 40)                       # kept within what the sliders offer
    assert (client.get("/api/me").json()["zoom"], client.get("/api/me").json()["width"]) == (250, 40)


def test_files_shown_inline_cannot_run_scripts(client: TestClient, settings: Settings):
    """An SVG is a picture that may carry a script: wherever one is shown, it must not run in our origin."""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    (settings.archive / "oliver/Geräte/Waschmaschine- entkalken.assets/bild.svg").write_bytes(svg)
    shown = client.get("/api/documents/abc123def0/asset/Waschmaschine-%20entkalken.assets/bild.svg", headers=API)
    assert "default-src 'none'" in shown.headers["content-security-policy"]
    assert shown.headers["x-content-type-options"] == "nosniff"
    trashed = settings.archive / ".papierkorb/2026-11-18/oliver/Geräte/bild.svg"
    trashed.parent.mkdir(parents=True)
    trashed.write_bytes(svg)
    res = client.get("/api/trash/file", headers=API, params={"path": ".papierkorb/2026-11-18/oliver/Geräte/bild.svg"})
    assert res.status_code == 200 and "default-src 'none'" in res.headers["content-security-policy"]
    assert res.headers["x-content-type-options"] == "nosniff"


def test_a_page_outside_every_area_reaches_into_none(client: TestClient, settings: Settings):
    """A page lying in the archive's root sees its own assets – not the files of the areas."""
    page = settings.archive / "Lose Notiz.md"
    page.write_text("---\nid: 0dd0dd0dd0\n---\n# Lose Notiz\n\n![](Lose%20Notiz.assets/a.png)\n", encoding="utf-8")
    (settings.archive / "Lose Notiz.assets").mkdir()
    (settings.archive / "Lose Notiz.assets/a.png").write_bytes(b"\x89PNG-lose")
    client.app.state.index.scan()
    login(client)
    assert client.post("/api/users", json={"name": "erika", "password": "geheim1234567", "areas": {"": "read"}}).status_code == 201
    erika = TestClient(client.app)
    login(erika, "erika", "geheim1234567")
    assert erika.get("/api/documents/0dd0dd0dd0/asset/Lose%20Notiz.assets/a.png").content == b"\x89PNG-lose"
    for rel in ("oliver/Geräte/Waschmaschine-%20entkalken.assets/foto%201.png",
                "oliver/Banken/DKB/2026-03-01_Kontoauszug.pdf", "oliver/.hidden/secret.pdf"):
        assert erika.get(f"/api/documents/0dd0dd0dd0/asset/{rel}").status_code == 404, rel


def test_a_reading_key_changes_nothing(client: TestClient):
    login(client)
    key = client.post("/api/security/api-keys", json={"name": "Leser", "right": "read"}).json()["token"]
    reader = TestClient(client.app)
    auth = {"Authorization": f"Bearer {key}"}
    assert reader.get("/api/documents/abc123def0", headers=auth).status_code == 200
    for method, path in (("PUT", "/api/documents/abc123def0/pin"), ("PUT", "/api/me/pins"), ("POST", "/api/ask")):
        assert reader.request(method, path, headers=auth, json={}).status_code == 403, path
