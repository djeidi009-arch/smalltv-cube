"""Лимиты Claude Code. Токен Claude Code читается из Связки ключей и нигде не сохраняется."""
from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Callable, Optional
from zoneinfo import ZoneInfo

import httpx

from cube.model import Notification, Usage
from cube.sources.base import Background, SourceResult, used_percent
from cube.store import Store

URL = "https://api.anthropic.com/api/oauth/usage"
THRESHOLDS = (80, 95)
log = logging.getLogger("cube")


def keychain_token() -> str:
    out = subprocess.run(["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
                         capture_output=True, text=True, check=True, timeout=10).stdout
    return json.loads(out)["claudeAiOauth"]["accessToken"]


class ClaudeUsageSource(Background):
    name = "claude_usage"
    every_s = 5 * 60

    def __init__(self, store: Store, tz: str, token: Callable[[], str] = keychain_token,
                 transport: Optional[httpx.BaseTransport] = None):
        self._store, self._tz, self._token = store, ZoneInfo(tz), token
        self._http = httpx.Client(timeout=10, transport=transport)

    def fetch(self) -> SourceResult:
        try:
            r = self._http.get(URL, headers={"Authorization": f"Bearer {self._token()}",
                                             "anthropic-beta": "oauth-2025-04-20"})
            r.raise_for_status()
            data = r.json()
            five = data.get("five_hour") or {}
            week = data.get("seven_day") or {}
            pct = used_percent(five.get("utilization"))
            weekly = used_percent(week.get("utilization"))
            reset_at = five.get("resets_at")
            resets = datetime.fromisoformat(reset_at.replace("Z", "+00:00")) if reset_at else None
        except httpx.HTTPStatusError as e:
            return SourceResult(error=f"claude_usage: HTTP {e.response.status_code}")
        except Exception as e:  # только тип: текст исключения может содержать ответ или токен
            return SourceResult(error=f"claude_usage: {type(e).__name__}")
        if pct is None and weekly is None:
            return SourceResult(error="claude_usage: no usage windows")
        alerts = self._alerts(pct, resets) if pct is not None else []
        return SourceResult(usage={"claude": Usage(pct, weekly)}, notifications=alerts)

    def _alerts(self, pct: float, resets: Optional[datetime]) -> list:
        window = self._store.get("window")
        shown = self._store.get("shown", [])
        if resets and (window is None or abs(datetime.fromisoformat(window) - resets) > timedelta(minutes=30)):
            window, shown = resets.isoformat(), []  # новое окно: пороги снова можно показать
        crossed = [t for t in THRESHOLDS if pct >= t and t not in shown]
        self._store.set("window", window)
        self._store.set("shown", shown + crossed)
        if not crossed:
            return []
        body = f"Лимит сбросится в {resets.astimezone(self._tz):%H:%M}" if resets else "Время сброса неизвестно"
        return [Notification("claude_limit", f"Использовано {round(pct)}%", body, datetime.now(self._tz),
                             f"claude-limit-{max(crossed)}-{window}")]  # перескочили оба порога — одна карточка


def create(cfg) -> Optional[ClaudeUsageSource]:
    try:
        src = ClaudeUsageSource(Store(cfg.data_dir / "claude_usage.json"), cfg.tz)
        src.start()
        return src
    except Exception as e:
        log.warning("claude_usage: не запустился: %s", type(e).__name__)
        return None
