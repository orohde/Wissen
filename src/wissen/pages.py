"""Markdown pages: the head block (front matter) and what the index needs from a page.

A page is an ordinary Markdown file. What belongs to the page beyond its text –
title, date, tags and a fixed id – stands in a short head block at the top::

    ---
    title: Waschmaschine entkalken
    date: 2026-11-17
    tags: [Haushalt, Geräte]
    id: 3f9a1c2b7d
    ---

Only this small subset of YAML is read (``key: value``, lists in brackets or as
``- item`` lines); anything else in the block is kept but ignored. Without a head
block the title is the first ``# heading``, else the file name.

Pictures and attachments of a page live in a folder next to it,
``<Seite>.assets/`` – the index skips such folders.
"""

from __future__ import annotations

import json
import re
import secrets
from dataclasses import dataclass, field

ASSET_SUFFIX = ".assets"
ID_RE = re.compile(r"[0-9a-z]{6,32}")
_HEAD_RE = re.compile(r"\A﻿?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
_KEY_RE = re.compile(r"^([A-Za-z_][\w-]*)[ \t]*:[ \t]*(.*)$")
_H1_RE = re.compile(r"^#[ \t]+(.+?)[ \t#]*$", re.M)
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass
class Head:
    title: str = ""
    date: str | None = None
    tags: list[str] = field(default_factory=list)
    id: str = ""
    raw: dict = field(default_factory=dict)


def _scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:                      # written by yaml_str: escapes like \" inside
            parsed = json.loads(value)
            if isinstance(parsed, str):
                return parsed.strip()
        except ValueError:
            pass
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value.strip()


def yaml_str(value: str) -> str:
    """A value for the head block; quoted where plain YAML would misread it."""
    value = " ".join(str(value).split())
    if re.search(r'[:#\[\]{},"\'&*!|>%@`]', value) or not value:
        return json.dumps(value, ensure_ascii=False)
    return value


def new_id() -> str:
    return secrets.token_hex(5)


def set_head(text: str, **fields: str) -> str:
    """``text`` with these head block entries set; everything else in the block stays as it is."""
    match = _HEAD_RE.match(text)
    if not match:
        lines = [f"{key}: {yaml_str(value)}" for key, value in fields.items()]
        return "---\n" + "\n".join(lines) + "\n---\n\n" + text.lstrip("﻿").lstrip("\n")
    lines = match.group(1).splitlines()
    for key, value in fields.items():
        entry = f"{key}: {yaml_str(value)}"
        at = next((i for i, line in enumerate(lines)
                   if (kv := _KEY_RE.match(line)) and kv.group(1).lower() == key), None)
        if at is None:
            lines.append(entry)
            continue
        end = at + 1
        while end < len(lines) and re.match(r"^[ \t]*-[ \t]+", lines[end]):
            end += 1                # a list that stood under this key goes with it
        lines[at:end] = [entry]
    return "---\n" + "\n".join(lines) + "\n---\n" + text[match.end():]


def head_block(text: str) -> str:
    """The head block exactly as it stands in ``text`` (empty without one)."""
    match = _HEAD_RE.match(text)
    return text[:match.end()] if match else ""


def _list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [_scalar(v) for v in value.split(",") if _scalar(v)]


def split(text: str) -> tuple[dict, str]:
    """``(head, body)``: the parsed head block (empty without one) and the text after it."""
    match = _HEAD_RE.match(text)
    if not match:
        return {}, text
    head: dict = {}
    key = None
    for line in match.group(1).splitlines():
        item = re.match(r"^[ \t]+-[ \t]+(.*)$", line) or re.match(r"^-[ \t]+(.*)$", line)
        if item and key:
            if not isinstance(head.get(key), list):
                head[key] = []
            head[key].append(_scalar(item.group(1)))
            continue
        kv = _KEY_RE.match(line)
        if not kv:
            continue
        key, value = kv.group(1).lower(), kv.group(2)
        head[key] = _list(value) if value.strip().startswith("[") else _scalar(value)
    return head, text[match.end():]


def read_head(text: str, fallback_title: str) -> Head:
    raw, body = split(text)
    title = raw.get("title") if isinstance(raw.get("title"), str) else ""
    if not title:
        h1 = _H1_RE.search(body)
        title = h1.group(1).strip() if h1 else fallback_title
    date = raw.get("date") if isinstance(raw.get("date"), str) else ""
    date = date[:10] if _DATE_RE.fullmatch(date[:10] or "") else None
    tags = raw.get("tags", [])
    if isinstance(tags, str):
        tags = _list(tags)
    page_id = raw.get("id") if isinstance(raw.get("id"), str) else ""
    page_id = page_id.lower() if ID_RE.fullmatch(page_id.lower()) else ""
    return Head(title=title, date=date, tags=[t for t in tags if t], id=page_id, raw=raw)


def body_text(text: str) -> str:
    """The text of a page for the search: without the head block."""
    return split(text)[1]
