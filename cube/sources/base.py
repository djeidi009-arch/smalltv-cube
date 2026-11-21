from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol

from cube.model import Notification, Usage, Weather


@dataclass
class SourceResult:
    notifications: List[Notification] = field(default_factory=list)
    badge: Optional[int] = None
    weather: Optional[Weather] = None
    usage: Dict[str, Usage] = field(default_factory=dict)
    waiting: Optional[int] = None
    error: Optional[str] = None


class Source(Protocol):
    name: str
    interval_s: int

    def poll(self) -> SourceResult: ...


class Background:
    """Медленный fetch() крутится в своём потоке раз в every_s; poll() мгновенно отдаёт накопленное."""
    interval_s = 5
    every_s = 60

    def start(self) -> None:
        self._acc, self._lock = SourceResult(), threading.Lock()
        threading.Thread(target=self._loop, daemon=True, name=getattr(self, "name", "source")).start()

    def fetch(self) -> SourceResult:
        raise NotImplementedError

    def _loop(self) -> None:
        while True:
            try:
                r = self.fetch()
            except Exception as e:  # fetch обязан не бросать, но поток не должен умереть
                r = SourceResult(error=f"{type(e).__name__}")
            with self._lock:
                a = self._acc
                a.notifications += r.notifications
                a.usage.update(r.usage)
                for f in ("badge", "weather", "waiting", "error"):
                    if getattr(r, f) is not None:
                        setattr(a, f, getattr(r, f))
            time.sleep(self.every_s)

    def poll(self) -> SourceResult:
        with self._lock:
            r, self._acc = self._acc, SourceResult()
        return r


def used_percent(value) -> Optional[float]:
    try:
        pct = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return min(100.0, max(0.0, pct)) if math.isfinite(pct) else None
