"""Questions to the archive: search terms, passages, and the route with a stand-in for the AI."""

import pytest
from fastapi.testclient import TestClient

from wissen import ask
from wissen.ai import AIError, Completion
from wissen.app import create_app
from wissen.config import Settings

API = {"Authorization": "Bearer tok"}
HEIZUNG = """---
title: Heizung entlüften
id: heiz000001
---

Wenn ein Heizkörper gluckert oder oben kalt bleibt, ist Luft im System.

## Werkzeug

Entlüftungsschlüssel (Vierkant 5 mm) und ein Lappen. Der Schlüssel hängt im Keller am Verteiler.

## Ablauf

1. Thermostat ganz aufdrehen und zehn Minuten warten.
2. Ventil mit dem Schlüssel eine Vierteldrehung öffnen, bis Wasser kommt.
3. Ventil schließen und den Druck am Kessel prüfen: Soll 1,5 bar.
"""
WLAN = """---
title: WLAN und Router
id: wlan000001
---

Der Router steht im Flur. Das Gäste-WLAN heißt Lindenweg-Gast.
"""


def doc(title, ext="md", sha="a" * 64, area="haus", folder="Heizung"):
    return {"id": sha[:10], "sha256": sha, "title": title, "ext": ext, "area": area, "folder": folder, "path": f"{area}/{folder}/{title}.{ext}"}


def test_terms_drop_filler_words_and_endings():
    assert ask.terms("Wie entlüfte ich die Heizung im Keller?") == ["entlüft", "heizung", "keller"]
    assert ask.terms("Which filter does the dishwasher need?") == ["filter", "dishwasher", "need"]
    assert ask.terms("und oder der die das") == []
    assert ask.terms("Was bedeutet Fehler E24 bei der GS-45?") == ["bedeut", "fehler", "e24", "gs-45"]
    assert ask.terms("Welche Heizkörpern gluckern?") == ["heizkörper", "glucker"]


def test_passages_keep_page_and_section():
    pdf = "Sicherheit\n\nNur mit trockenen Händen.\fFlusensieb\n\nDas Flusensieb sitzt unten rechts hinter der Klappe.\fGarantie"
    pages = ask.split_document(doc("Waschmaschine", "pdf"), pdf)
    assert [(p.page, p.text.split("\n")[0]) for p in pages] == [(1, "Sicherheit"), (2, "Flusensieb"), (3, "Garantie")]
    assert ask.split_document(doc("Alt", "pdf"), "ohne Seitenwechsel")[0].page is None        # read before pages were kept
    body = HEIZUNG.split("---\n", 2)[2]
    sections = ask.split_document(doc("Heizung entlüften"), body)
    assert sections[0].heading == "Werkzeug"                   # named after the first heading in it
    long = body + "\n\n" + "Noch ein Absatz ohne Überschrift. " * 80
    assert ask.split_document(doc("Heizung entlüften"), long)[-1].heading == "Ablauf"      # … else the last one before


def test_choose_prefers_what_fits_and_spreads_over_documents():
    heizung = (doc("Heizung entlüften", sha="a" * 64), HEIZUNG.split("---\n", 2)[2])
    wlan = (doc("WLAN und Router", sha="b" * 64, folder="Technik"), WLAN.split("---\n", 2)[2])
    long = (doc("Handbuch", "pdf", sha="c" * 64), "\f".join(f"Seite {i}: Entlüften der Heizung, Abschnitt {i}. " + "Text. " * 200 for i in range(1, 9)))
    wanted = ask.terms("Wie entlüfte ich die Heizung?")
    chosen = ask.choose([heizung, wlan, long], wanted)
    assert chosen and chosen[0].doc["title"] in ("Heizung entlüften", "Handbuch")
    assert all(p.doc["title"] != "WLAN und Router" for p in chosen)              # says nothing about it
    assert sum(1 for p in chosen if p.doc["title"] == "Handbuch") == ask.MAX_PER_DOC
    assert ask.choose([wlan], wanted) == []
    small = ask.choose([heizung, wlan, long], wanted, ask.LOCAL)
    assert len(small) <= 4 and sum(len(p.text) for p in small) <= 5000        # a local model gets less to read
    text = ask.prompt("Wie entlüfte ich die Heizung?", chosen)
    assert text.startswith("Question: Wie entlüfte ich die Heizung?") and "[1] " in text and "page " in text
    listed = ask.sources(chosen, "Ventil öffnen [1]. Druck prüfen [1][2].")
    assert [s["cited"] for s in listed[:3]] == [True, True, False] and listed[0]["n"] == 1


@pytest.fixture
def client(settings: Settings) -> TestClient:
    for rel, text in (("oliver/Heizung/Heizung entlüften.md", HEIZUNG), ("erika/Technik/WLAN und Router.md", WLAN)):
        path = settings.archive / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    app = create_app(settings, background=False)
    app.state.index.scan()
    app.state.index.refresh(["oliver/Heizung/Heizung entlüften.md", "erika/Technik/WLAN und Router.md"])
    return TestClient(app)


def stand_in(client: TestClient, answer: str = "Ventil eine Vierteldrehung öffnen [1]."):
    """Replace the AI by a function that notes what it was asked."""
    seen = {}

    def complete(system, prompt, max_tokens=2000, effort="low", force=False):
        seen.update(system=system, prompt=prompt)
        return Completion(text=answer, model="stand-in", input_tokens=10, output_tokens=5, cost=0.0, seconds=0.1)
    client.app.state.ai.complete = complete
    return seen


def test_ask_needs_the_ai_switched_on(client: TestClient):
    assert client.post("/api/ask", json={"question": "Wie entlüfte ich die Heizung?"}).status_code == 401
    res = client.post("/api/ask", headers=API, json={"question": "Wie entlüfte ich die Heizung?"})
    assert res.status_code == 400 and res.json()["detail"] == "AI is disabled"
    assert client.get("/api/status", headers=API).json()["ask"] is False
    assert client.post("/api/ask", headers=API, json={"question": "?"}).status_code == 422


def test_ask_answers_with_sources(client: TestClient):
    client.app.state.ai.update({"enabled": True})
    seen = stand_in(client)
    assert client.get("/api/status", headers=API).json()["ask"] is True
    res = client.post("/api/ask", headers=API, json={"question": "Wie entlüfte ich die Heizung?"})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["found"] is True and data["answer"].endswith("[1].")
    first = data["sources"][0]
    assert first["id"] == "heiz000001" and first["cited"] is True and first["title"] == "Heizung entlüften"
    assert "Vierteldrehung" in seen["prompt"] and "Lindenweg-Gast" not in seen["prompt"]
    assert "do not guess" in seen["system"]
    # nothing that fits: the AI is not asked at all
    seen.clear()
    nothing = client.post("/api/ask", headers=API, json={"question": "Wann fährt der Bus nach Mainz?"}).json()
    assert nothing == {"found": False, "answer": "", "sources": []} and not seen


def test_ask_respects_rights_and_excluded_areas(client: TestClient):
    client.app.state.ai.update({"enabled": True})
    seen = stand_in(client, "Lindenweg-Gast [1].")
    client.post("/api/login", json={"username": "oliver", "password": "geheim123"})
    client.post("/api/users", json={"name": "erika", "password": "geheim1234567", "areas": {"erika": "read"}})
    reader = TestClient(client.app)
    reader.post("/api/login", json={"username": "erika", "password": "geheim1234567"})
    # erika may not read the area "oliver": its page never reaches the AI
    assert reader.post("/api/ask", json={"question": "Wie entlüfte ich die Heizung?"}).json()["found"] is False
    assert reader.post("/api/ask", json={"question": "Wie heißt das Gäste-WLAN?"}).json()["sources"][0]["id"] == "wlan000001"
    # an area excluded under Settings → AI is left out for everybody
    client.app.state.ai.update({"excluded_areas": ["erika"]})
    seen.clear()
    assert client.post("/api/ask", json={"question": "Wie heißt das Gäste-WLAN?"}).json()["found"] is False and not seen


def test_ask_passes_on_what_goes_wrong(client: TestClient):
    client.app.state.ai.update({"enabled": True})

    def broken(*args, **kwargs):
        raise AIError("monthly limit reached")
    client.app.state.ai.complete = broken
    res = client.post("/api/ask", headers=API, json={"question": "Wie entlüfte ich die Heizung?"})
    assert res.status_code == 400 and res.json()["detail"] == "monthly limit reached"
