from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wissen.app import create_app
from wissen.config import Settings
from wissen.pages import read_head, split
from wissen.textextract import extract

PAGE = """---
title: Waschmaschine entkalken
date: 2026-11-17
tags: [Haushalt, Geräte]
id: 3f9a1c2b7d
---

# Etwas anderes

Alle drei Monate mit Zitronensäure, siehe ![Bild](Waschmaschine.assets/trommel.png).
"""


def test_head_block():
    head = read_head(PAGE, "datei")
    assert head.title == "Waschmaschine entkalken"
    assert head.date == "2026-11-17"
    assert head.tags == ["Haushalt", "Geräte"]
    assert head.id == "3f9a1c2b7d"


def test_head_block_with_dash_list_and_quotes():
    head = read_head('---\ntitle: "Mit: Doppelpunkt"\ntags:\n  - eins\n  - zwei\n---\nText', "x")
    assert head.title == "Mit: Doppelpunkt"
    assert head.tags == ["eins", "zwei"]
    assert head.id == "" and head.date is None


def test_title_without_head_block():
    assert read_head("Vorwort\n\n# Heizung warten\n\nText", "datei").title == "Heizung warten"
    assert read_head("nur Text", "Dateiname").title == "Dateiname"
    assert split("kein Kopf")[0] == {}


def test_search_text_leaves_the_head_block_out(tmp_path: Path):
    path = tmp_path / "seite.md"
    path.write_text(PAGE, encoding="utf-8")
    text = extract(path, "md", ocr=False).text
    assert "Zitronensäure" in text and "title:" not in text


@pytest.fixture
def client(settings: Settings) -> TestClient:
    archive = settings.archive
    (archive / "oliver/Geräte").mkdir(parents=True)
    (archive / "oliver/Geräte/Waschmaschine.md").write_text(PAGE, encoding="utf-8")
    assets = archive / "oliver/Geräte/Waschmaschine.assets"
    assets.mkdir()
    (assets / "trommel.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
    (assets / "Schaltplan.pdf").write_bytes(b"%PDF-1.4 not a document of its own")
    (archive / "oliver/Geräte/notizen.txt").write_text("wird nicht gezeigt", encoding="utf-8")
    (archive / "erika/geheim.png").write_bytes(b"\x89PNG")
    app = create_app(settings, background=False)
    app.state.index.scan()
    app.state.index.extract_pending(app.state.make_extractor())
    client = TestClient(app)
    res = client.post("/api/login", json={"username": "oliver", "password": "geheim123"})
    assert res.status_code == 200
    return client


def test_page_in_the_archive(client: TestClient):
    pages = client.get("/api/documents", params={"recursive": True, "kind": "md"}).json()
    assert pages["total"] == 1
    page = pages["items"][0]
    assert page["id"] == "3f9a1c2b7d"
    assert page["title"] == "Waschmaschine entkalken"
    assert page["date"] == "2026-11-17"
    assert page["page_tags"] == ["Haushalt", "Geräte"]
    # pages and PDFs side by side, other files and the picture folder stay out
    every = client.get("/api/documents", params={"recursive": True, "limit": 100}).json()["items"]
    assert {d["ext"] for d in every} == {"pdf", "md"}
    assert not any(".assets" in d["path"] for d in every)
    assert client.get("/api/documents", params={"recursive": True, "kind": "pdf"}).json()["total"] == len(every) - 1


def test_search_finds_page_text_and_tags(client: TestClient):
    assert client.get("/api/documents", params={"q": "Zitronensäure"}).json()["total"] == 1
    assert client.get("/api/documents", params={"q": "haushalt"}).json()["total"] == 1


def test_page_by_its_fixed_id(client: TestClient):
    doc = client.get("/api/documents/3f9a1c2b7d").json()
    assert doc["path"] == "oliver/Geräte/Waschmaschine.md"
    res = client.get("/api/documents/3f9a1c2b7d/file")
    assert res.status_code == 200 and res.headers["content-type"].startswith("text/markdown")
    assert "Zitronensäure" in res.text


def test_assets_of_a_page(client: TestClient):
    res = client.get("/api/documents/3f9a1c2b7d/asset/Waschmaschine.assets/trommel.png")
    assert res.status_code == 200 and res.headers["content-type"] == "image/png"
    # nothing outside the page's own area, however the path is written
    assert client.get("/api/documents/3f9a1c2b7d/asset/../../erika/geheim.png").status_code == 404
    assert client.get("/api/documents/3f9a1c2b7d/asset/Waschmaschine.assets/fehlt.png").status_code == 404


def test_page_by_its_path(client: TestClient):
    doc = client.get("/api/documents/by-path", params={"path": "oliver/Geräte/Waschmaschine.md"}).json()
    assert doc["id"] == "3f9a1c2b7d"
    assert client.get("/api/documents/by-path", params={"path": "oliver/fehlt.md"}).status_code == 404


def test_names_written_on_a_mac(settings: Settings):
    """A file name in NFD (as a Mac writes it) is read, served and searched like any other."""
    import unicodedata
    folder = settings.archive / "oliver" / unicodedata.normalize("NFD", "Küche")
    folder.mkdir(parents=True)
    from conftest import make_pdf
    (folder / unicodedata.normalize("NFD", "Kühlschrank Gebrauch.pdf")).write_bytes(make_pdf("Gefrierfach abtauen"))
    app = create_app(settings, background=False)
    app.state.index.scan()
    app.state.index.extract_pending(app.state.make_extractor())
    client = TestClient(app)
    client.post("/api/login", json={"username": "oliver", "password": "geheim123"})
    hits = client.get("/api/documents", params={"q": "Gefrierfach"}).json()
    assert hits["total"] == 1
    assert client.get(f"/api/documents/{hits['items'][0]['id']}/file").status_code == 200
