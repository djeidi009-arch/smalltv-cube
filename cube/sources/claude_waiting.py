"""«Claude ждёт ответа»: читает файл, который пишут хуки (cube/hook.py). Только локальный файл — быстро."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Set

from cube.hook import FILE, fresh
from cube.model import Notification
from cube.sources.base import SourceResult


class ClaudeWaitingSource:
    name = "claude_waiting"
    interval_s = 3

    def __init__(self, path: Path):
        self._path = path
        self._shown: Optional[Set[str]] = None

    def poll(self) -> SourceResult:
        try:
            data = json.loads(self._path.read_text()) if self._path.exists() else {}
            now = datetime.now(timezone.utc)
            waiting = {f"{sid}@{v['at']}": v for sid, v in data.items() if v["waiting"] and fresh(v["at"], now)}
        except Exception as e:
            return SourceResult(error=f"claude_waiting: {type(e).__name__}: {e}")
        cards = []
        if self._shown is not None:  # при старте программы уже ждущие — только индикатор, без карточек
            for key, v in waiting.items():
                if key not in self._shown:
                    where = f"{v['project']}: " if v.get("project") else ""
                    cards.append(Notification("claude_waiting", "Claude ждёт ответа",
                                              f"{where}нужен ответ, чтобы продолжить", now, f"claude-wait-{key}"))
        self._shown = set(waiting)
        return SourceResult(notifications=cards, waiting=len(waiting))


def create(cfg) -> ClaudeWaitingSource:
    return ClaudeWaitingSource(cfg.data_dir / FILE)
