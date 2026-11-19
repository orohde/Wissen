"""Eingang: drop PDFs in, get a suggestion, file them into the archive."""

import io
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import make_pdf
from wissen.app import create_app
from wissen.config import Settings
from wissen.inbox import INBOX_NAME, InboxService, key_rel, title_from_name

API = {"Authorization": "Bearer tok"}


def _aged(path: Path) -> None:
    past = time.time() - 60
    os.utime(path, (past, past))


@pytest.fixture
def client(settings: Settings) -> TestClient:
    inbox = settings.archive / INBOX_NAME / "gemeinsam" / "Ratgeber"
    inbox.mkdir(parents=True)
    (inbox / "Test_Kaffeevollautomaten.pdf").write_bytes(make_pdf("Stiftung Warentest Kaffeevollautomaten"))
    _aged(inbox / "Test_Kaffeevollautomaten.pdf")
    app = create_app(settings, background=False)
    app.state.index.scan()
    return TestClient(app)


def test_title_from_name():
    assert title_from_name("Holzwerken_131-2026.pdf") == "Holzwerken 131-2026"
    assert title_from_name("  .pdf") == "Dokument"


def test_inbox_is_no_area_and_not_indexed(client: TestClient):
    names = [a["name"] for a in client.get("/api/areas", headers=API).json()]
    assert INBOX_NAME not in names
    found = client.get("/api/documents?areas=gemeinsam,oliver,erika&recursive=true&q=Kaffeevollautomaten", headers=API).json()
    assert found["total"] == 0


def test_listing_with_suggestion_from_subfolder(client: TestClient):
    data = client.get("/api/inbox", headers=API).json()
    assert data["folder"] == INBOX_NAME
    [item] = data["items"]
    assert item["rel"] == "gemeinsam/Ratgeber/Test_Kaffeevollautomaten.pdf"
    assert item["suggestion"] == {"title": "Test Kaffeevollautomaten", "area": "gemeinsam", "folder": "Ratgeber"}
    assert item["duplicate"] is None
    assert client.get("/api/status", headers=API).json()["inbox"] == 1


def test_file_moves_into_archive_and_indexes(client: TestClient, settings: Settings):
    [item] = client.get("/api/inbox", headers=API).json()["items"]
    res = client.post(f"/api/inbox/{item['key']}/file", headers=API,
                      json={"area": "gemeinsam", "folder": "Tests & Ratgeber", "title": "Kaffeevollautomaten (test 12-2021)"})
    assert res.status_code == 200, res.text
    doc = res.json()
    assert doc["path"] == "gemeinsam/Tests & Ratgeber/Kaffeevollautomaten (test 12-2021).pdf"
    assert (settings.archive / doc["path"]).is_file()
    assert not (settings.archive / INBOX_NAME / item["rel"]).exists()
    assert not (settings.archive / INBOX_NAME / "gemeinsam").exists()     # emptied subfolders go
    assert (settings.archive / INBOX_NAME).is_dir()                       # the inbox itself stays
    assert client.get("/api/inbox", headers=API).json()["items"] == []
    listed = client.get("/api/documents?areas=gemeinsam&folder=Tests%20%26%20Ratgeber", headers=API).json()
    assert [d["title"] for d in listed["items"]] == ["Kaffeevollautomaten (test 12-2021)"]


def test_duplicate_needs_force(client: TestClient, settings: Settings):
    same = settings.archive / INBOX_NAME / "Rechtsschutz nochmal.pdf"
    same.write_bytes((settings.archive / "gemeinsam/Versicherungen/ARAG/2025-05-05_Rechtsschutz.pdf").read_bytes())
    _aged(same)
    item = next(i for i in client.get("/api/inbox", headers=API).json()["items"] if i["name"] == same.name)
    assert item["duplicate"] == "gemeinsam/Versicherungen/ARAG/2025-05-05_Rechtsschutz.pdf"
    body = {"area": "gemeinsam", "folder": "", "title": "Rechtsschutz nochmal"}
    res = client.post(f"/api/inbox/{item['key']}/file", headers=API, json=body)
    assert res.status_code == 409 and "already in the archive" in res.json()["detail"]
    assert client.post(f"/api/inbox/{item['key']}/file", headers=API, json={**body, "force": True}).status_code == 200


def test_target_exists_and_bad_input(client: TestClient, settings: Settings):
    [item] = client.get("/api/inbox", headers=API).json()["items"]
    url = f"/api/inbox/{item['key']}/file"
    taken = {"area": "gemeinsam", "folder": "Versicherungen/ARAG", "title": "2025-05-05_Rechtsschutz"}
    assert client.post(url, headers=API, json=taken).status_code == 409
    assert client.post(url, headers=API, json={"area": "nirgends", "title": "x"}).status_code in (403, 404)
    assert client.post(url, headers=API, json={"area": "gemeinsam", "folder": "../oliver", "title": "x"}).status_code == 400
    assert client.post(url, headers=API, json={"area": "gemeinsam", "title": "  "}).status_code == 400
    assert client.post("/api/inbox/Li4vLi4vZXRjL3Bhc3N3ZA/file", headers=API,       # "../../etc/passwd"
                       json={"area": "gemeinsam", "title": "x"}).status_code == 404
    assert (settings.archive / INBOX_NAME / item["rel"]).is_file()           # nothing lost on the way


def test_upload_pdf_and_photo(client: TestClient, settings: Settings):
    res = client.post("/api/inbox/upload?name=Neues%20Heft.pdf", headers=API, content=make_pdf("Heft 131"))
    assert res.status_code == 201 and res.json()["name"] == "Neues Heft.pdf"
    again = client.post("/api/inbox/upload?name=Neues%20Heft.pdf", headers=API, content=make_pdf("Heft 132"))
    assert again.json()["name"] == "Neues Heft (2).pdf"
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (60, 80), "white").save(buf, "JPEG")
    photo = client.post("/api/inbox/upload?name=../IMG_0001.JPG", headers=API, content=buf.getvalue())
    assert photo.status_code == 201 and photo.json()["name"] == "IMG_0001.pdf"
    assert (settings.archive / INBOX_NAME / "IMG_0001.pdf").read_bytes().startswith(b"%PDF-")
    assert client.post("/api/inbox/upload?name=x.pdf", headers=API, content=b"kein pdf").status_code == 400
    assert client.post("/api/inbox/upload?name=x.exe", headers=API, content=b"MZ").status_code == 400
    names = {i["name"] for i in client.get("/api/inbox", headers=API).json()["items"]}
    assert {"Neues Heft.pdf", "Neues Heft (2).pdf", "IMG_0001.pdf"} <= names


def test_young_files_wait(client: TestClient, settings: Settings):
    (settings.archive / INBOX_NAME / "kopiert-gerade.pdf").write_bytes(make_pdf("halb"))
    names = {i["name"] for i in client.get("/api/inbox", headers=API).json()["items"]}
    assert "kopiert-gerade.pdf" not in names


def test_delete_and_preview(client: TestClient, settings: Settings):
    [item] = client.get("/api/inbox", headers=API).json()["items"]
    pdf = client.get(f"/api/inbox/{item['key']}/file", headers=API)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF-")
    assert client.delete(f"/api/inbox/{item['key']}", headers=API).status_code == 200
    assert not (settings.archive / INBOX_NAME / item["rel"]).exists()
    assert client.delete(f"/api/inbox/{item['key']}", headers=API).status_code == 404


def test_read_only_account_has_no_inbox(client: TestClient):
    assert client.post("/api/login", json={"username": "oliver", "password": "geheim123"}).status_code == 200
    assert client.post("/api/users", json={"name": "leser", "password": "leser-pass-2026", "areas": {"gemeinsam": "read"}}
                       ).status_code == 201
    reader = TestClient(client.app)
    assert reader.post("/api/login", json={"username": "leser", "password": "leser-pass-2026"}).status_code == 200
    assert reader.get("/api/inbox").status_code == 403
    assert reader.post("/api/inbox/upload?name=a.pdf", content=make_pdf("x")).status_code == 403
    assert reader.get("/api/status").json()["inbox"] is None


def test_key_roundtrip_and_own_folder(settings: Settings, tmp_path: Path):
    from wissen.index import Index
    idx = Index(settings.db_path, settings.archive)
    own = tmp_path / "eingang"
    service = InboxService(idx, own)
    assert service.root == own
    name = service.add("Ä Heft.pdf", make_pdf("x"))
    [item] = service.items({"gemeinsam"})
    assert key_rel(item["key"]) == name == item["rel"]


class FakeAI:
    """Answers like the AI would; counts the questions."""

    def __init__(self, answer='{"area": "gemeinsam", "folder": "Werkzeug", "title": "Bosch GSR 12V"}', auto=True, fail=False):
        self.answer, self.auto, self.fail, self.calls = answer, auto, fail, 0

    def load(self):
        from types import SimpleNamespace
        return SimpleNamespace(enabled=True, inbox_auto=self.auto)

    def complete(self, system, prompt, max_tokens=2000, effort="low", force=False):
        from types import SimpleNamespace
        self.calls += 1
        if self.fail:
            raise RuntimeError("provider down")
        return SimpleNamespace(text=self.answer, model="fake")


def _two_files(settings: Settings) -> None:
    for name in ("Anleitung_eins.pdf", "Anleitung_zwei.pdf"):
        f = settings.archive / INBOX_NAME / name
        f.write_bytes(make_pdf(name))
        _aged(f)


def _args():
    return (lambda p: "Text", [{"name": "gemeinsam", "label": "Gemeinsam"}], ["gemeinsam/Werkzeug"])


def test_ai_answer_survives_filing_another(client: TestClient, settings: Settings):
    _two_files(settings)
    inbox = client.app.state.inbox
    ai = FakeAI()
    for item in [i for i in client.get("/api/inbox", headers=API).json()["items"] if i["name"].startswith("Anleitung")]:
        inbox.ask_ai(item["key"], ai, *_args())
    items = {i["name"]: i for i in client.get("/api/inbox", headers=API).json()["items"]}
    assert items["Anleitung_zwei.pdf"]["suggestion"] == {"title": "Bosch GSR 12V", "area": "gemeinsam", "folder": "Werkzeug", "ai": True}
    first = items["Anleitung_eins.pdf"]
    assert client.post(f"/api/inbox/{first['key']}/file", headers=API,
                       json={"area": "gemeinsam", "folder": "Werkzeug", "title": "Eins"}).status_code == 200
    again = {i["name"]: i for i in client.get("/api/inbox", headers=API).json()["items"]}
    assert again["Anleitung_zwei.pdf"]["suggestion"]["ai"] is True       # still there after filing the other one
    assert "Anleitung_eins.pdf" not in again
    # the answer for the filed file is forgotten, the other one is kept on disk
    import json
    kept = json.loads((settings.data / "inbox-ai.json").read_text())
    assert list(kept) == [again["Anleitung_zwei.pdf"]["sha256"]]


def test_auto_ai_only_for_unplaced_files(client: TestClient, settings: Settings):
    _two_files(settings)
    inbox = client.app.state.inbox
    ai = FakeAI()
    assert inbox.auto_ai(ai, _args) == 2              # the file in gemeinsam/Ratgeber has its place already
    assert inbox.auto_ai(ai, _args) == 0              # asked once is enough
    assert ai.calls == 2
    assert inbox.auto_ai(FakeAI(auto=False), _args) == 0


def test_auto_ai_failure_waits_a_day(client: TestClient, settings: Settings):
    _two_files(settings)
    inbox = client.app.state.inbox
    down = FakeAI(fail=True)
    assert inbox.auto_ai(down, _args) == 2
    items = [i for i in client.get("/api/inbox", headers=API).json()["items"] if i["name"].startswith("Anleitung")]
    assert all(i["ai_failed"] for i in items)
    assert inbox.auto_ai(down, _args) == 0             # not again at once
    assert inbox.auto_ai(FakeAI(), _args, now=time.time() + 25 * 3600) == 2


def test_inbox_auto_switch_is_saved(client: TestClient):
    assert client.put("/api/ai", headers=API, json={"inbox_auto": True}).json()["inbox_auto"] is True
    assert client.get("/api/ai", headers=API).json()["inbox_auto"] is True
    assert client.get("/api/inbox", headers=API).json()["auto"] is False      # the AI itself is still off
