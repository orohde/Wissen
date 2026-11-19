"""Spickzettel: the essentials of a long manual as a Markdown page next to the PDF.

The AI gets the PDF's text with page marks and writes a short page: what the device is,
maintenance with intervals, error codes, spare parts and consumables, important values. Every
fact carries its page as "(S. 12)"; those become links that open the reader at that page.
"""

from __future__ import annotations

import re
from urllib.parse import quote

PAGE_BREAK = "\f"
HOSTED_CHARS = 120_000           # about 30 000 tokens: a long manual fits, a few cents per sheet
LOCAL_CHARS = 20_000             # small local models do not get more
SUFFIX = " – Spickzettel"

SYSTEM = (
    "Du machst aus einer Bedienungsanleitung, einem Handbuch oder Datenblatt einen kurzen Spickzettel auf "
    "Deutsch, als Markdown. Er ist für jemanden, der das Gerät schon hat und schnell etwas nachschlagen will.\n"
    "Regeln:\n"
    "- Nur was im Text steht. Nichts erfinden, nichts aus eigenem Wissen ergänzen.\n"
    "- Nach jeder Angabe die Seite in der Form (S. 12), mehrere als (S. 12, 14). Die Seiten stehen als "
    "[Seite N] im Text.\n"
    "- Abschnitte als ## Überschrift, nur die, zu denen der Text etwas hergibt, in dieser Reihenfolge:\n"
    "  ## Kurz gesagt (2–4 Sätze: was es ist, Modell/Typ, wofür)\n"
    "  ## Wartung und Pflege (Tabelle: | Was | Wie oft | Seite |, Intervalle so genau wie im Text)\n"
    "  ## Fehler und Störungen (Tabelle: | Anzeige/Code | Bedeutung | Abhilfe | Seite |)\n"
    "  ## Ersatzteile und Verbrauchsmaterial (Liste mit Bestellnummern, falls genannt)\n"
    "  ## Wichtige Werte und Einstellungen (Liste: Maße, Drücke, Drehmomente, Füllmengen, Werkseinstellungen …)\n"
    "  ## Sicherheit (nur das Wichtigste, höchstens 5 Punkte)\n"
    "- Kein Titel (# …), keine Einleitung, kein Schlusswort. Knapp, Stichworte statt Prosa. Garzeit-, Rezept- "
    "und ähnliche lange Tabellen nicht abschreiben, nur sagen, auf welchen Seiten sie stehen.\n"
    "- Ist der Text gar keine Anleitung oder fast leer, schreibe nur einen Satz, der das sagt."
)


def pages_text(body: str, limit: int) -> tuple[str, int, bool]:
    """The stored text with [Seite N] marks; returns (text, pages, cut short)."""
    pages = (body or "").split(PAGE_BREAK)
    parts, used = [], 0
    for n, page in enumerate(pages, 1):
        page = re.sub(r"[ \t]+", " ", page).strip()
        if not page:
            continue
        chunk = f"[Seite {n}]\n{page}\n"
        if used + len(chunk) > limit:
            return "".join(parts), len(pages), True
        parts.append(chunk)
        used += len(chunk)
    return "".join(parts), len(pages), False


def prompt(title: str, text: str, cut: bool) -> str:
    note = "\n(Der Text ist gekürzt – spätere Seiten fehlen.)" if cut else ""
    return f"Dokument: {title}{note}\n\n{text}"


def page_links(markdown: str, pdf_name: str, pages: int) -> str:
    """"(S. 12, 14)" → links into the PDF ("Anleitung.pdf#page=12"), which the reader opens."""
    target = quote(pdf_name)

    def one(m: re.Match) -> str:
        n = int(m.group(0))
        return f"[{n}]({target}#page={n})" if 1 <= n <= max(pages, 1) else m.group(0)

    def group(m: re.Match) -> str:
        return m.group(1) + re.sub(r"\d+", one, m.group(2))

    # "S. 12", "(S. 12, 14)", "S. 3–5" – in text and in table cells; "S. [3](…)" is linked already
    return re.sub(r"(\bS\. ?)(\d+(?:\s*[,–-]\s*\d+)*)", group, markdown)


def page_text(title: str, pdf_name: str, markdown: str, pages: int, model: str, cut: bool) -> str:
    """The body of the cheat sheet page (the head block is added by the caller)."""
    body = markdown.strip()
    body = re.sub(r"^\s*#\s+.*\n+", "", body)            # a title of its own would repeat the page title
    lines = [f"> [!NOTE]\n> Von der KI ({model}) aus [{title}]({quote(pdf_name)}) zusammengefasst. "
             "Im Zweifel gilt die Anleitung."]
    if cut:
        lines.append("> Die Anleitung war zu lang, die hinteren Seiten sind nicht berücksichtigt.")
    return "\n".join(lines) + "\n\n" + page_links(body, pdf_name, pages) + "\n"
