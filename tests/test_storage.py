from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wissen.app import create_app
from wissen.config import Settings


@pytest.fixture
def client(settings: Settings, tmp_path: Path, monkeypatch) -> TestClient:
    (tmp_path / "scanner").mkdir()
    (tmp_path / "scanner" / "scan1.pdf").write_bytes(b"%PDF")
    (tmp_path / "neu-archiv" / "oliver" / "Banken").mkdir(parents=True)
    monkeypatch.setenv("WISSEN_BROWSE_ROOTS", str(tmp_path))
    app = create_app(settings, background=False)
    app.state.index.scan()
    c = TestClient(app)
    assert c.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    return c


def test_defaults_to_environment_archive(client: TestClient, settings: Settings):
    data = client.get("/api/storage").json()
    assert data["archive_path"] == str(settings.archive)
    assert data["archive"]["readable"] is True
    assert data["trash_days"] == 30




def test_change_archive_rescans(client: TestClient, tmp_path: Path):
    new = tmp_path / "neu-archiv"
    (new / "oliver" / "Banken" / "2026-01-01_Auszug.pdf").write_bytes(b"%PDF-1 x")
    assert client.put("/api/storage", json={"archive_path": str(new)}).status_code == 200
    client.app.state.index.scan()
    docs = client.get("/api/documents", params={"recursive": True}).json()
    assert docs["total"] == 1 and docs["items"][0]["title"] == "Auszug"


def test_folder_picker_stays_inside_roots(client: TestClient, tmp_path: Path):
    roots = [r["path"] for r in client.get("/api/fs/roots").json()]
    assert str(tmp_path) in roots
    listing = client.get("/api/fs/list", params={"path": str(tmp_path)}).json()
    assert "scanner" in listing["dirs"] and "neu-archiv" in listing["dirs"]
    assert client.get("/api/fs/list", params={"path": "/etc"}).status_code == 400


def test_area_labels(client: TestClient):
    client.patch("/api/users/oliver", json={"display_name": "Oliver Muster"})
    labels = {a["name"]: a["label"] for a in client.get("/api/areas").json()}
    assert labels["oliver"] == "Oliver Muster"      # from the account
    assert labels["gemeinsam"] == "Gemeinsam"        # capitalised
    assert labels[""] == ""                          # files without area
    client.put("/api/storage", json={"area_labels": {"gemeinsam": "Familie", "erika": "  "}})
    labels = {a["name"]: a["label"] for a in client.get("/api/areas").json()}
    assert labels["gemeinsam"] == "Familie" and labels["erika"] == "Erika"
