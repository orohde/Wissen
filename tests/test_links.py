"""Links between documents follow when one of them is renamed or moved."""

import base64

import pytest
from fastapi.testclient import TestClient

from wissen import links
from wissen.app import create_app
from wissen.config import Settings

API = {"Authorization": "Bearer tok"}


def test_retarget_only_touches_links_to_the_document():
    text = ("Siehe [Anleitung](../Ger%C3%A4te/Waschmaschine.pdf#page=3) und [Notiz](Notiz.md), "
            "nicht [Web](https://example.org/Notiz.md) oder [Anker](#oben).\n\n"
            "```\n[Notiz](Notiz.md)\n```\n![Bild](Seite.assets/foto%201.png) <[x](<Mit Leer.md>)>")
    out = links.retarget(text, "haus/Küche/Seite.md", "haus/Küche/Notiz.md", "haus/Keller/Merkzettel.md")
    assert "[Notiz](../Keller/Merkzettel.md)," in out
    assert "```\n[Notiz](Notiz.md)\n```" in out                     # code stays code
    assert "https://example.org/Notiz.md" in out and "(#oben)" in out
    pdf = links.retarget(text, "haus/Küche/Seite.md", "haus/Geräte/Waschmaschine.pdf", "anleitungen/Bad/WM 900.pdf")
    assert "[Anleitung](../../anleitungen/Bad/WM%20900.pdf#page=3)" in pdf          # the page number stays
    spaced = links.retarget(text, "haus/Küche/Seite.md", "haus/Küche/Mit Leer.md", "haus/Küche/Ohne.md")
    assert "[x](<Ohne.md>)" in spaced
    assert links.retarget(text, "haus/Küche/Seite.md", "haus/Küche/Gibtsnicht.md", "x.md") == text


def test_rebase_counts_a_moved_page_s_links_anew():
    text = "[Notiz](Notiz.md) ![Bild](Seite.assets/foto.png) [PDF](../Geräte/WM.pdf#page=2) [Web](https://a.b)"
    out = links.rebase(text, "haus/Küche/Seite.md", "haus/Seite.md")
    assert out == ("[Notiz](K%C3%BCche/Notiz.md) ![Bild](Seite.assets/foto.png) "
                   "[PDF](Ger%C3%A4te/WM.pdf#page=2) [Web](https://a.b)")
    assert links.rebase(text, "haus/Küche/Seite.md", "haus/Küche/Anders.md") == text      # same folder: nothing to do


@pytest.fixture
def client(settings: Settings) -> TestClient:
    files = {
        "oliver/Haus/Heizung.md": "---\ntitle: Heizung\nid: heiz000001\n---\n\nSiehe [Kessel](Kessel.md) und [Plan](../Pläne/Rohrplan.md).\n",
        "oliver/Haus/Kessel.md": "---\ntitle: Kessel\nid: kess000001\n---\n\nZurück zur [Heizung](Heizung.md).\n",
        "oliver/Pläne/Rohrplan.md": "---\ntitle: Rohrplan\nid: rohr000001\n---\n\nGehört zur [Heizung](../Haus/Heizung.md), Kontoauszug: [PDF](../Banken/DKB/2026-03-01_Kontoauszug.pdf#page=1).\n",
    }
    for rel, text in files.items():
        path = settings.archive / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    app = create_app(settings, background=False)
    app.state.index.scan()
    app.state.system.update({"mcp": True})
    return TestClient(app)


def read(settings: Settings, rel: str) -> str:
    return (settings.archive / rel).read_text(encoding="utf-8")


def test_rename_corrects_links_to_the_page(client: TestClient, settings: Settings):
    res = client.post("/api/documents/heiz000001/rename", headers=API, json={"title": "Heizung im Keller"})
    assert res.status_code == 200 and res.json()["links_updated"] == 2, res.text
    assert "[Heizung](Heizung%20im%20Keller.md)" in read(settings, "oliver/Haus/Kessel.md")
    assert "[Heizung](../Haus/Heizung%20im%20Keller.md)" in read(settings, "oliver/Pläne/Rohrplan.md")
    # the corrected pages kept their earlier text as a version, and the links still lead somewhere
    assert len(client.get("/api/documents/kess000001/versions", headers=API).json()["items"]) == 1
    hit = client.get("/api/documents/by-path", headers=API, params={"path": "oliver/Haus/Heizung im Keller.md"})
    assert hit.json()["id"] == "heiz000001"
    # only the title changes, the file keeps its name: no link to correct
    again = client.post("/api/documents/heiz000001/rename", headers=API, json={"title": "Heizung im Keller."})
    assert again.json()["links_updated"] == 0


def test_move_corrects_links_both_ways(client: TestClient, settings: Settings):
    res = client.post("/api/documents/heiz000001/move", headers=API, json={"folder": "Technik/Wärme"})
    assert res.status_code == 200 and res.json()["links_updated"] == 3, res.text
    moved = read(settings, "oliver/Technik/Wärme/Heizung.md")
    assert "[Kessel](../../Haus/Kessel.md)" in moved and "[Plan](../../Pl%C3%A4ne/Rohrplan.md)" in moved
    assert "[Heizung](../Technik/W%C3%A4rme/Heizung.md)" in read(settings, "oliver/Haus/Kessel.md")
    assert "[Heizung](../Technik/W%C3%A4rme/Heizung.md)" in read(settings, "oliver/Pläne/Rohrplan.md")
    # a PDF that moves takes the links to it along, page number included
    pdf = client.get("/api/documents", headers=API, params={"q": "kontoauszug"}).json()["items"][0]
    moved_pdf = client.post(f"/api/documents/{pdf['id']}/move", headers=API, json={"folder": "Auszüge"})
    assert moved_pdf.json()["links_updated"] == 1
    assert "[PDF](../Ausz%C3%BCge/2026-03-01_Kontoauszug.pdf#page=1)" in read(settings, "oliver/Pläne/Rohrplan.md")


def test_a_page_somebody_edits_is_left_alone(client: TestClient, settings: Settings):
    client.post("/api/login", json={"username": "oliver", "password": "geheim123"})
    client.post("/api/documents/kess000001/lock")
    other = TestClient(client.app)
    res = other.post("/api/documents/heiz000001/rename", headers=API, json={"title": "Wärme"})
    assert res.json()["links_updated"] == 1                          # the plan, not the page being edited
    assert "[Heizung](Heizung.md)" in read(settings, "oliver/Haus/Kessel.md")


def test_purge_one_from_the_trash(client: TestClient, settings: Settings):
    client.post("/api/documents/kess000001/asset", headers=API, params={"name": "typenschild.jpg"}, content=b"jpg")
    trash_path = client.post("/api/documents/kess000001/trash", headers=API).json()["trash_path"]
    other = client.post("/api/documents/rohr000001/trash", headers=API).json()["trash_path"]
    assert client.post("/api/trash/purge", headers=API, json={"trash_path": "oliver/Haus/Heizung.md"}).status_code == 404
    assert client.post("/api/trash/purge", headers=API, json={"trash_path": trash_path}).json() == {"ok": True}
    assert [i["title"] for i in client.get("/api/trash", headers=API).json()["items"]] == ["Rohrplan"]
    left = [p.relative_to(settings.archive).as_posix() for p in (settings.archive / ".papierkorb").rglob("*") if p.is_file()]
    assert left == [other]                                           # the page, its pictures and the empty folder are gone
    assert (settings.archive / "oliver/Haus/Heizung.md").is_file()
    # reading alone is not enough to delete for good
    client.post("/api/login", json={"username": "oliver", "password": "geheim123"})
    key = client.post("/api/security/api-keys", json={"name": "Leser", "right": "read"}).json()["token"]
    assert TestClient(client.app).post("/api/trash/purge", headers={"Authorization": f"Bearer {key}"},
                                       json={"trash_path": other}).status_code == 403


def test_attachment_through_mcp(client: TestClient, settings: Settings):
    def call(tool, **arguments):
        res = client.post("/api/mcp", headers=API, json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                           "params": {"name": tool, "arguments": arguments}})
        return res.json()["result"]
    data = base64.b64encode(b"\x89PNG-ventil").decode()
    result = call("add_attachment", id="heiz000001", name="Ventil oben.png", data_base64=data)
    assert result["isError"] is False and "![Ventil oben](Heizung.assets/Ventil%20oben.png)" in result["content"][0]["text"]
    assert (settings.archive / "oliver/Haus/Heizung.assets/Ventil oben.png").read_bytes() == b"\x89PNG-ventil"
    assert "Heizung.assets" not in read(settings, "oliver/Haus/Heizung.md")         # the text is the caller's business
    assert call("add_attachment", id="heiz000001", name="x.png", data_base64="kein base64!")["isError"] is True
    pdf = call("add_attachment", id="heiz000001", name="Datenblatt.pdf", data_base64=data)
    assert "[Datenblatt](Heizung.assets/Datenblatt.pdf)" in pdf["content"][0]["text"]
