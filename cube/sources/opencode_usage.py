"""Лимиты OpenCode Go из эндпоинта подписки."""
from __future__ import annotations

import os
from pathlib import Path

import httpx

from cube.model import Usage
from cube.sources.base import Background, SourceResult, used_percent

URL = "https://opencode.ai/zen/go/v1/usage"


def go_key() -> str:
    key = os.environ.get("OPENCODE_GO_API_KEY", "").strip()
    if key:
        return key
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return (config / "opencode" / "go.key").read_text().strip()


class OpenCodeUsageSource(Background):
    name = "opencode_usage"
    every_s = 5 * 60

    def __init__(self, token=go_key, transport=None):
        self._token = token
        self._http = httpx.Client(timeout=10, transport=transport)

    def fetch(self) -> SourceResult:
        try:
            key = self._token()
            if not key:
                return SourceResult(error=f"{self.name}: missing API key")
            response = self._http.get(URL, headers={"Authorization": f"Bearer {key}"})
            response.raise_for_status()
            data = response.json()["usage"]
            rolling = data.get("rolling") or data.get("five_hour") or {}
            weekly = data.get("weekly") or data.get("seven_day") or {}
            usage = Usage(used_percent(rolling.get("percent")), used_percent(weekly.get("percent")))
            if usage.five_hour is None and usage.weekly is None:
                return SourceResult(error=f"{self.name}: no usage windows")
            return SourceResult(usage={"opencode": usage})
        except httpx.HTTPStatusError as error:
            return SourceResult(error=f"{self.name}: HTTP {error.response.status_code}")
        except Exception as error:
            return SourceResult(error=f"{self.name}: {type(error).__name__}")


def create(cfg) -> OpenCodeUsageSource:
    source = OpenCodeUsageSource()
    source.start()
    return source
