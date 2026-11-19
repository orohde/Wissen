"""Maintenance → Vikunja: settings, the AI's list, creating recurring tasks."""

import io
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from wissen import vikunja
from wissen.app import create_app
from wissen.config import Settings

API = {"Authorization": "Bearer tok"}


class FakeVikunja:
    """Stands in for urlopen: answers like Vikunja and keeps what was sent."""

    def __init__(self):
        self.sent = []

    def __call__(self, req, timeout=None):
        self.sent.append((req.get_method(), req.full_url, dict(req.header_items()), req.data))
        if req.full_url.endswith("/projects?per_page=200"):
            body = [{"id": 1, "title": "Inbox"}, {"id": 12, "title": "Wartung", "parent_project_id": 0},
                    {"id": -1, "title": "Favoriten"}]
        else:
            body = {"id": 500 + len(self.sent), "title": json.loads(req.data)["title"]}
        return io.BytesIO(json.dumps(body).encode())


@pytest.fixture
def client(settings: Settings, monkeypatch) -> TestClient:
    fake = FakeVikunja()
    monkeypatch.setattr(vikunja.urllib.request, "urlopen", fake)
    app = create_app(settings, background=False)
    app.state.index.scan()
    app.state.fake = fake
    app.state.ai.update({"enabled": True})
    app.state.ai.complete = lambda *a, **k: SimpleNamespace(
        text='Hier: [{"title": "Police prüfen", "every_days": 365, "note": "Beitrag vergleichen", "page": 1},'
             ' {"title": "Ohne Intervall", "every_days": null}, {"title": ""}]', model="fake")
    return TestClient(app)


def test_parse_tasks():
    tasks = vikunja.parse_tasks('[{"title": " A ", "every_days": "30", "page": "x"}, {"note": "ohne Titel"}, 3]')
    assert tasks == [{"title": "A", "every_days": 30, "note": "", "page": None}]
    assert vikunja.parse_tasks("kein JSON") == []


def test_settings_hide_the_token_and_forget_it_with_a_new_address(client: TestClient, settings: Settings):
    r = client.put("/api/vikunja", headers=API, json={"url": "https://todo.example/api/v1/", "token": "tk_geheim"})
    assert r.json() == {"url": "https://todo.example", "project_id": 0, "project_title": "", "token_set": True, "ready": False}
    assert "tk_geheim" not in json.dumps(client.get("/api/vikunja", headers=API).json())
    assert oct((settings.data / "vikunja.json").stat().st_mode & 0o777) == "0o600"
    assert [p["title"] for p in client.get("/api/vikunja/projects", headers=API).json()] == ["Inbox", "Wartung"]
    assert client.app.state.fake.sent[-1][2]["Authorization"] == "Bearer tk_geheim"
    r = client.put("/api/vikunja", headers=API, json={"url": "https://anders.example"})
    assert r.json()["token_set"] is False                      # the token never goes to a new address
    assert client.put("/api/vikunja", headers=API, json={"url": "ftp://x"}).status_code == 400


def test_suggest_and_create(client: TestClient):
    client.put("/api/vikunja", headers=API, json={"url": "https://todo.example", "token": "tk", "project_id": 12,
                                                  "project_title": "Wartung"})
    assert client.get("/api/status", headers=API).json()["vikunja"] is True
    pdf = client.get("/api/documents?areas=gemeinsam&recursive=true&q=Rechtsschutz", headers=API).json()["items"][0]
    import functools
    from wissen.textextract import extract
    client.app.state.index.extract_pending(functools.partial(extract, ocr=False))
    tasks = client.post(f"/api/documents/{pdf['id']}/maintenance", headers=API).json()["tasks"]
    assert [t["title"] for t in tasks] == ["Police prüfen", "Ohne Intervall"]
    body = {"link": "https://wissen.example/#/dokument/" + pdf["id"], "tasks": [
        {"title": "Police prüfen", "every_days": 365, "due": "2027-01-15", "note": "Beitrag vergleichen", "page": 1},
        {"title": "Einmalig"}]}
    r = client.post(f"/api/documents/{pdf['id']}/maintenance/create", headers=API, json=body).json()
    assert [c["title"] for c in r["created"]] == ["Police prüfen", "Einmalig"] and r["failed"] == []
    method, url, _, data = client.app.state.fake.sent[-2]
    sent = json.loads(data)
    assert method == "PUT" and url == "https://todo.example/api/v1/projects/12/tasks"
    assert sent["repeat_after"] == 365 * 86400 and sent["due_date"].startswith("2027-01-15T09:00")
    assert "Beitrag vergleichen" in sent["description"] and "#/dokument/" in sent["description"] and "S. 1" in sent["description"]
    single = json.loads(client.app.state.fake.sent[-1][3])
    assert "repeat_after" not in single and "due_date" not in single


def test_not_set_up(client: TestClient):
    pdf = client.get("/api/documents?areas=gemeinsam&recursive=true&q=Rechtsschutz", headers=API).json()["items"][0]
    r = client.post(f"/api/documents/{pdf['id']}/maintenance/create", headers=API, json={"tasks": [{"title": "x"}]}).json()
    assert r["created"] == [] and "not set up" in r["failed"][0]["error"]
