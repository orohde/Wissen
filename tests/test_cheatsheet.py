"""Spickzettel: the AI's summary of a manual as a page next to the PDF."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from wissen import cheatsheet
from wissen.app import create_app
from wissen.config import Settings

API = {"Authorization": "Bearer tok"}
ANSWER = """# Titel, den die KI nicht schreiben soll

## Kurz gesagt
Rechtsschutzpolice der ARAG (S. 1).

## Wartung und Pflege
| Was | Wie oft | Seite |
|---|---|---|
| Beitrag prüfen | jährlich | (S. 1, 99) |
"""


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings, background=False)
    app.state.index.scan()
    from wissen.textextract import extract
    import functools
    app.state.index.extract_pending(functools.partial(extract, ocr=False))
    calls = []

    def complete(system, prompt, max_tokens=2000, effort="low", force=False):
        calls.append(prompt)
        return SimpleNamespace(text=globals()["ANSWER"], model="fake-1")
    app.state.ai.complete = complete
    app.state.ai.update({"enabled": True})
    app.state.calls = calls
    return TestClient(app)


def _pdf(client):
    return client.get("/api/documents?areas=gemeinsam&recursive=true&q=Rechtsschutz", headers=API).json()["items"][0]


def test_pages_text_marks_and_cuts():
    text, pages, cut = cheatsheet.pages_text("eins\fzwei\f\fvier", 1000)
    assert "[Seite 1]\neins" in text and "[Seite 4]\nvier" in text and "[Seite 3]" not in text
    assert pages == 4 and not cut
    assert cheatsheet.pages_text("a" * 50 + "\f" + "b" * 50, 70)[2] is True


def test_page_links():
    md = cheatsheet.page_links("Filter (S. 3, 12) und (S. 99)", "Anleitung K4.pdf", 20)
    assert md == "Filter (S. [3](Anleitung%20K4.pdf#page=3), [12](Anleitung%20K4.pdf#page=12)) und (S. 99)"
    assert cheatsheet.page_links("| Entkalken | S. 6, 7 |", "a.pdf", 9) == "| Entkalken | S. [6](a.pdf#page=6), [7](a.pdf#page=7) |"
    once = cheatsheet.page_links("S. 4", "a.pdf", 9)
    assert cheatsheet.page_links(once, "a.pdf", 9) == once                  # linked numbers stay as they are


def test_create_and_rewrite(client: TestClient):
    pdf = _pdf(client)
    res = client.post(f"/api/documents/{pdf['id']}/cheatsheet", headers=API)
    assert res.status_code == 200, res.text
    page = res.json()
    assert page["title"] == pdf["title"] + " – Spickzettel"
    assert page["path"] == f"gemeinsam/Versicherungen/ARAG/{pdf['title']} – Spickzettel.md"
    assert "[Seite 1]" in client.app.state.calls[0] and "ARAG Rechtsschutz" in client.app.state.calls[0]
    text = client.get(f"/api/documents/{page['id']}/file", headers=API).text
    assert "Titel, den die KI" not in text
    assert "> [!NOTE]" in text and "fake-1" in text
    assert "[1](2025-05-05_Rechtsschutz.pdf#page=1)" in text and "(S. [1](" in text
    assert "99](" not in text                                     # a page the PDF does not have stays plain
    global ANSWER
    ANSWER = ANSWER.replace("jährlich", "alle zwei Jahre")
    again = client.post(f"/api/documents/{pdf['id']}/cheatsheet", headers=API).json()
    assert again["id"] == page["id"]                              # rewritten in place, same id
    assert "alle zwei Jahre" in client.get(f"/api/documents/{page['id']}/file", headers=API).text
    versions = client.get(f"/api/documents/{page['id']}/versions", headers=API).json()["items"]
    assert len(versions) == 1                                     # the first text is kept as a version


def test_refusals(client: TestClient, settings: Settings):
    pdf = _pdf(client)
    client.app.state.ai.update({"excluded_areas": ["gemeinsam"]})
    assert client.post(f"/api/documents/{pdf['id']}/cheatsheet", headers=API).status_code == 403
    client.app.state.ai.update({"excluded_areas": [], "enabled": False})
    assert client.post(f"/api/documents/{pdf['id']}/cheatsheet", headers=API).status_code == 400
    client.app.state.ai.update({"enabled": True})
    page = settings.archive / "gemeinsam/Notiz.md"
    page.write_text("---\ntitle: Notiz\nid: notiz12345\n---\n\nText\n", encoding="utf-8")
    client.app.state.index.scan()
    assert client.post("/api/documents/notiz12345/cheatsheet", headers=API).status_code == 400
