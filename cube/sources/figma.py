"""Новые комментарии во всех файлах проекта Figma. Сеть — в своём потоке, poll() мгновенный."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from cube.model import Notification
from cube.sources.base import Background, SourceResult
from cube.store import Store

API = "https://api.figma.com/v1"
log = logging.getLogger("cube")


def _when(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class FigmaSource(Background):
    name = "figma"
    every_s = 120

    def __init__(self, token: str, project_id: str, store: Store,
                 transport: Optional[httpx.BaseTransport] = None):
        self._project = project_id
        self._store = store
        self._http = httpx.Client(base_url=API, timeout=15, headers={"X-Figma-Token": token}, transport=transport)
        self._me: Optional[str] = None

    def _get(self, path: str) -> dict:
        r = self._http.get(path)
        r.raise_for_status()
        return r.json()

    def fetch(self) -> SourceResult:
        try:
            if self._me is None:
                self._me = self._get("/me")["id"]
            since = self._store.get("since")
            if since is None:  # первый запуск: всё, что было до него, — не новое
                since = datetime.now(timezone.utc).isoformat()
            seen = set(self._store.get("seen", []))
            alive, out = set(), []
            for f in self._get(f"/projects/{self._project}/files")["files"]:
                for c in self._get(f"/files/{f['key']}/comments")["comments"]:
                    alive.add(c["id"])
                    if c["id"] in seen or c["user"]["id"] == self._me or _when(c["created_at"]) <= _when(since):
                        continue
                    seen.add(c["id"])
                    lines = (c.get("message") or "").strip().splitlines() or [""]
                    out.append(Notification("figma", f"{c['user']['handle']} · {f['name']}", lines[0][:120],
                                            _when(c["created_at"]), f"figma-{c['id']}"))
            self._store.set("since", since)
            self._store.set("seen", sorted(seen & alive))  # удалённые комментарии забываем, файл не растёт
            return SourceResult(notifications=out)
        except Exception as e:  # httpx-ошибки содержат URL, но не заголовок с токеном
            return SourceResult(error=f"figma: {type(e).__name__}: {e}")


def create(cfg) -> Optional[FigmaSource]:
    if not cfg.figma_token:
        return None
    try:
        src = FigmaSource(cfg.figma_token, cfg.figma_project_id, Store(cfg.data_dir / "figma.json"))
        src.start()
        return src
    except Exception as e:
        log.warning("figma: не запустился: %s", type(e).__name__)
        return None
