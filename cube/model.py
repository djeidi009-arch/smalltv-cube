"""Общие типы: только данные."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Literal, Optional

SourceName = Literal["figma", "telegram", "claude_limit", "claude_waiting"]


@dataclass
class Notification:
    source: SourceName
    title: str
    body: str
    created_at: datetime
    key: str


@dataclass
class Weather:
    temp_c: float
    code: int
    label_ru: str
    fetched_at: datetime


@dataclass
class ClaudeUsage:
    used_pct: float
    resets_at: Optional[datetime]


@dataclass
class Snapshot:
    now: datetime
    weather: Optional[Weather] = None
    usage: Optional[ClaudeUsage] = None
    badges: Dict[str, int] = field(default_factory=dict)
    claude_waiting: int = 0
