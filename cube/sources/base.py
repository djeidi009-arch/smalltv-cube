from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Protocol

from cube.model import ClaudeUsage, Notification, Weather


@dataclass
class SourceResult:
    notifications: List[Notification] = field(default_factory=list)
    badge: Optional[int] = None
    weather: Optional[Weather] = None
    usage: Optional[ClaudeUsage] = None
    waiting: Optional[int] = None
    error: Optional[str] = None


class Source(Protocol):
    name: str
    interval_s: int

    def poll(self) -> SourceResult: ...
