"""Vikunja: maintenance from a manual becomes recurring tasks.

Address, API token and target project are kept in ``vikunja.json`` in the data folder (0600).
The token goes only to that address (see outbound.py). The AI reads the maintenance points of
a manual or cheat sheet; the person picks, adjusts and confirms them before anything is created.
"""

from __future__ import annotations

import json
import os
import re
import threading
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import date, datetime, time as dtime
from pathlib import Path

TIMEOUT = 15
MAX_TASKS = 30
TEXT_CHARS = 40_000

SYSTEM = (
    "Du liest eine Anleitung oder einen Spickzettel und schreibst die regelmäßigen Wartungs- und Pflegearbeiten "
    "heraus, als JSON-Liste: [{\"title\": \"…\", \"every_days\": 90, \"note\": \"…\", \"page\": 12}].\n"
    "- title: kurz und eindeutig mit Gerät, z. B. \"Dampfgarer entkalken\".\n"
    "- every_days: Intervall in Tagen, wie im Text (monatlich = 30, vierteljährlich = 91, jährlich = 365). "
    "Ohne festes Intervall im Text: null. Nichts erfinden.\n"
    "- note: ein Satz, wie es geht oder was man braucht (Mittel, Menge), sonst leer.\n"
    "- page: Seite in der Anleitung, falls bekannt, sonst null.\n"
    "- Nur echte wiederkehrende Arbeiten (reinigen, entkalken, Filter wechseln, schmieren, prüfen), keine "
    "einmaligen Schritte wie Aufbau oder Erstinbetriebnahme. Höchstens 12 Einträge. Nur das JSON, sonst nichts."
)


class VikunjaError(ValueError):
    pass


@dataclass
class VikunjaConfig:
    url: str = ""
    token: str = ""
    project_id: int = 0
    project_title: str = ""

    def public(self) -> dict:
        data = asdict(self)
        data.pop("token")
        data["token_set"] = bool(self.token)
        data["ready"] = bool(self.url and self.token and self.project_id)
        return data


class VikunjaService:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def load(self) -> VikunjaConfig:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return VikunjaConfig()
        known = VikunjaConfig.__dataclass_fields__.keys()
        return VikunjaConfig(**{k: v for k, v in raw.items() if k in known})

    def _save(self, config: VikunjaConfig) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(config), indent=1, ensure_ascii=False), encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.path)

    def update(self, url: str | None = None, token: str | None = None, project_id: int | None = None,
               project_title: str | None = None, clear_token: bool = False) -> VikunjaConfig:
        with self._lock:
            config = self.load()
            if url is not None:
                url = url.strip().rstrip("/")
                if url.endswith("/api/v1"):
                    url = url[: -len("/api/v1")]
                if url and not re.match(r"^https?://[^/\s]+", url):
                    raise VikunjaError("address must start with https://")
                if url != config.url:
                    config.token = ""          # a token belongs to the address it was given for
                    config.project_id, config.project_title = 0, ""
                config.url = url
            if clear_token:
                config.token = ""
            elif token:
                config.token = token.strip()
            if project_id is not None:
                config.project_id = max(0, int(project_id))
            if project_title is not None:
                config.project_title = project_title[:200]
            self._save(config)
            return config

    # --------------------------------------------------------------- calls

    def _call(self, method: str, path: str, body: dict | None = None, config: VikunjaConfig | None = None):
        config = config or self.load()
        if not (config.url and config.token):
            raise VikunjaError("Vikunja is not set up")
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(config.url + "/api/v1" + path, data=data, method=method,
                                     headers={"Authorization": "Bearer " + config.token,
                                              "Content-Type": "application/json", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as res:   # noqa: S310 - address set by an admin
                return json.loads(res.read() or b"null")
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise VikunjaError("Vikunja refused the token") from exc
            raise VikunjaError(f"Vikunja answered {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise VikunjaError("Vikunja cannot be reached") from exc

    def projects(self) -> list[dict]:
        found = self._call("GET", "/projects?per_page=200") or []
        return [{"id": p["id"], "title": p["title"], "parent": p.get("parent_project_id") or 0}
                for p in found if not p.get("is_archived") and p.get("id", 0) > 0]

    def create_task(self, title: str, description: str = "", due: date | None = None,
                    every_days: int | None = None) -> dict:
        config = self.load()
        if not (config.url and config.token):
            raise VikunjaError("Vikunja is not set up")
        if not config.project_id:
            raise VikunjaError("no Vikunja project chosen")
        body: dict = {"title": title[:250], "description": description}
        if due:
            body["due_date"] = datetime.combine(due, dtime(9, 0)).astimezone().isoformat()
        if every_days:
            body["repeat_after"] = int(every_days) * 86400
            body["repeat_mode"] = 0            # repeat from the due date
        task = self._call("PUT", f"/projects/{config.project_id}/tasks", body, config)
        return {"id": task.get("id"), "title": task.get("title"), "url": f"{config.url}/tasks/{task.get('id')}"}


def parse_tasks(text: str) -> list[dict]:
    """The AI's JSON list, cleaned: title, every_days (int or None), note, page."""
    match = re.search(r"\[.*\]", text or "", re.S)
    if not match:
        return []
    try:
        raw = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    tasks = []
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict) or not str(item.get("title") or "").strip():
            continue
        every = item.get("every_days")
        try:
            every = int(every) if every not in (None, "", 0) else None
        except (TypeError, ValueError):
            every = None
        page = item.get("page")
        try:
            page = int(page) if page not in (None, "") else None
        except (TypeError, ValueError):
            page = None
        tasks.append({"title": str(item["title"]).strip()[:200], "every_days": every if every and every > 0 else None,
                      "note": str(item.get("note") or "").strip()[:500], "page": page})
    return tasks[:MAX_TASKS]
