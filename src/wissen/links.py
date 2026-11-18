"""Links between documents: keep them pointing at the right file when one is renamed or moved.

A page links to another page or to a PDF with a path relative to its own folder,
``[Anleitung](../Geräte/Waschmaschine.pdf#page=3)``. Two things can break that:

* the target gets a new name or place – every page that points at it is corrected
  (:func:`retarget`);
* the page itself moves to another folder – its own links are counted from the new
  folder (:func:`rebase`).

Only relative links outside code blocks are touched; addresses on the web, anchors
within the page and the page's own pictures (they travel with it) stay as they are.
"""

from __future__ import annotations

import posixpath
import re
from typing import Callable
from urllib.parse import quote, unquote

from .index import nfc
from .pages import ASSET_SUFFIX

_LINK_RE = re.compile(r"(!?\[[^\]\n]*\]\()(<[^>\n]+>|[^)\s]+)")
_EXTERNAL_RE = re.compile(r"^([a-z][a-z0-9+.-]*:|//|#)", re.I)
_FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")


def _folder(rel: str) -> str:
    return posixpath.dirname(rel)


def resolve(page_rel: str, target: str) -> str:
    """Where a link in ``page_rel`` leads, as a path inside the archive."""
    return nfc(posixpath.normpath(posixpath.join(_folder(page_rel), target)))


def relative(page_rel: str, target_rel: str) -> str:
    return posixpath.relpath(target_rel, _folder(page_rel) or ".")


def _each_link(text: str, change: Callable[[str], str | None]) -> str:
    """Run ``change`` over the path of every relative link outside code blocks; None keeps the link."""
    def swap(match: re.Match) -> str:
        raw = match.group(2)
        bracketed = raw.startswith("<")
        inner = raw[1:-1] if bracketed else raw
        path, hash_, fragment = inner.partition("#")
        if not path or _EXTERNAL_RE.match(inner):
            return match.group(0)
        new = change(unquote(path))
        if new is None:
            return match.group(0)
        new = (new if bracketed else quote(new, safe="/")) + hash_ + fragment
        return match.group(1) + (f"<{new}>" if bracketed else new)

    out, fence = [], None
    for line in text.split("\n"):
        mark = _FENCE_RE.match(line)
        if mark:
            if fence is None:
                fence = mark.group(1)[0]
            elif mark.group(1)[0] == fence:
                fence = None
            out.append(line)
            continue
        out.append(line if fence else _LINK_RE.sub(swap, line))
    return "\n".join(out)


def retarget(text: str, page_rel: str, old_rel: str, new_rel: str) -> str:
    """``text`` of the page ``page_rel`` with every link to ``old_rel`` pointing at ``new_rel``."""
    old_rel = nfc(old_rel)

    def change(target: str) -> str | None:
        return relative(page_rel, new_rel) if resolve(page_rel, target) == old_rel else None
    return _each_link(text, change)


def rebase(text: str, old_page_rel: str, new_page_rel: str) -> str:
    """``text`` of a page that moved from ``old_page_rel`` to ``new_page_rel``: its links, counted anew."""
    if _folder(old_page_rel) == _folder(new_page_rel):
        return text
    own_assets = nfc(posixpath.splitext(old_page_rel)[0] + ASSET_SUFFIX) + "/"

    def change(target: str) -> str | None:
        where = resolve(old_page_rel, target)
        if where.startswith(own_assets) or where.startswith("../"):
            return None                              # its pictures travel along; outside the archive: hands off
        new = relative(new_page_rel, where)
        return new if new != target else None
    return _each_link(text, change)
