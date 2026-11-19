"""Reading position of PDFs: per account, per content, survives renaming."""

import pytest
from fastapi.testclient import TestClient

from wissen.app import create_app
from wissen.config import Settings

API = {"Authorization": "Bearer tok"}


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings, background=False)
    app.state.index.scan()
    return TestClient(app)


def _pdf(client: TestClient) -> dict:
    found = client.get("/api/documents?areas=gemeinsam&recursive=true&q=Rechtsschutz", headers=API).json()
    return found["items"][0]


def test_position_is_kept_and_follows_a_rename(client: TestClient):
    doc = _pdf(client)
    assert client.get("/api/me/reading", headers=API).json() == {}
    r = client.put("/api/me/reading", headers=API, json={"id": doc["id"], "page": 7, "total": 12})
    assert r.status_code == 200 and r.json()["page"] == 7 and r.json()["done"] is False
    assert client.put("/api/me/reading", headers=API, json={"id": doc["id"], "page": 99}).json()["page"] == 12
    renamed = client.post(f"/api/documents/{doc['id']}/rename", headers=API, json={"title": "Rechtsschutz neu"}).json()
    mine = client.get("/api/me/reading", headers=API).json()
    assert mine[renamed["id"]]["page"] == 12
    assert client.put("/api/me/reading", headers=API, json={"id": doc["id"], "done": True}).json()["done"] is True


def test_only_pdfs_and_only_own(client: TestClient, settings: Settings):
    page = settings.archive / "gemeinsam/Notiz.md"
    page.write_text("---\ntitle: Notiz\nid: notiz12345\n---\n\nText\n", encoding="utf-8")
    client.app.state.index.scan()
    assert client.put("/api/me/reading", headers=API, json={"id": "notiz12345", "page": 2}).status_code == 400
    assert client.put("/api/me/reading", headers=API, json={"id": "zzzzzz9999", "page": 2}).status_code == 404
    assert client.put("/api/me/reading", headers=API, json={"id": _pdf(client)["id"], "page": 0}).status_code == 422


def test_pdfjs_is_served_as_module(client: TestClient):
    res = client.get("/vendor/pdfjs/pdf.min.mjs")
    assert res.status_code == 200 and "javascript" in res.headers["content-type"]


def test_qr_code(client: TestClient):
    res = client.get("/api/qr", params={"text": "https://wissen.example/#/dokument/abc123/4"}, headers=API)
    assert res.status_code == 200 and res.headers["content-type"].startswith("image/svg+xml")
    assert res.content.lstrip().startswith(b"<svg") and b"<script" not in res.content
    assert client.get("/api/qr", params={"text": "javascript:alert(1)"}, headers=API).status_code == 400
    assert client.get("/api/qr", params={"text": "https://x"}).status_code == 401
