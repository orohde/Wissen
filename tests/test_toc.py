"""Inhaltsverzeichnis: the AI lists the articles of a magazine with their PDF page."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from wissen import toc
from wissen.app import create_app
from wissen.config import Settings

API = {"Authorization": "Bearer tok"}


@pytest.fixture
def client(settings: Settings) -> TestClient:
    import functools
    from wissen.textextract import extract
    app = create_app(settings, background=False)
    app.state.index.scan()
    app.state.index.extract_pending(functools.partial(extract, ocr=False))
    app.state.ai.update({"enabled": True})
    app.state.prompts = []

    def complete(system, prompt, max_tokens=2000, effort="low", force=False):
        app.state.prompts.append(prompt)
        return SimpleNamespace(model="fake", text='[{"page": 1, "title": "Rechtsschutz im Test", "summary": "x", "kind": "Test"},'
                                                  ' {"page": 40, "title": "gibt es nicht"}, {"title": "ohne Seite"}]')
    app.state.ai.complete = complete
    return TestClient(app)


def test_build_text_keeps_page_marks_and_the_top_only():
    text, pages = toc.build_text("A" * 2000 + "\f\fDritte Seite")
    assert text.startswith("[Seite 1] " + "A" * toc.PER_PAGE) and "A" * (toc.PER_PAGE + 1) not in text
    assert "[Seite 3] Dritte Seite" in text and "[Seite 2]" not in text and pages == 3


def test_parse_drops_bad_entries():
    got = toc.parse('[{"page": 5, "title": "B", "kind": "Quatsch"}, {"page": "2", "title": "A"}, {"page": 99, "title": "C"}]', 10)
    assert [(e["page"], e["title"], e["kind"]) for e in got] == [(2, "A", "Artikel"), (5, "B", "Artikel")]


def test_make_get_and_list(client: TestClient):
    pdf = client.get("/api/documents?areas=gemeinsam&recursive=true&q=Rechtsschutz", headers=API).json()["items"][0]
    assert client.get(f"/api/documents/{pdf['id']}/toc", headers=API).json()["entries"] == []
    made = client.post(f"/api/documents/{pdf['id']}/toc", headers=API).json()
    assert [e["title"] for e in made["entries"]] == ["Rechtsschutz im Test"]
    assert "[Seite 1]" in client.app.state.prompts[0]
    assert client.get(f"/api/documents/{pdf['id']}/toc", headers=API).json()["entries"][0]["page"] == 1
    assert client.get("/api/tocs", headers=API).json() == [pdf["sha256"]]
