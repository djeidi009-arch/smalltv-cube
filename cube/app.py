"""Главный цикл: опрос источников, очередь карточек, выбор и отправка кадра."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
from zoneinfo import ZoneInfo

from cube import render
from cube.config import Config
from cube.device import CubeClient, CubeOffline
from cube.model import Notification, Snapshot
from cube.sources.base import Source

log = logging.getLogger("cube")

CARD_S = 15
INTRO_S = 2          # сколько держим GIF-выезд, прежде чем заменить его статичной карточкой
RETRY_S = 30
BURST_WINDOW = timedelta(minutes=1)
BURST_MAX = 3
BADGE_TTL = timedelta(hours=1)
USAGE_TTL = timedelta(minutes=15)  # лимит не обновлялся 3 опроса подряд — полоску прячем


class App:
    def __init__(self, cfg: Config, device: CubeClient, sources: List[Source],
                 clock: Optional[Callable[[], datetime]] = None):
        self.device = device
        self.sources = sources
        self.clock = clock or (lambda: datetime.now(ZoneInfo(cfg.tz)))
        now = self.clock()
        self.snapshot = Snapshot(now=now)
        self.queue: List[Notification] = []
        self.current: Optional[Notification] = None
        self._card_at = now
        self._due = {id(s): now for s in sources}
        self._recent: Dict[str, List[datetime]] = {}
        self._summary: Dict[str, Notification] = {}
        self._summary_n: Dict[str, int] = {}
        self._badge_at: Dict[str, datetime] = {}
        self._badge_last: Dict[str, int] = {}
        self._usage_at = now
        self._sent: Optional[bytes] = None
        self._prepared = False
        self._retry_at = now
        self._intro: tuple = (None, b"")  # (карточка, её GIF): выезд рисуем и шлём один раз

    def tick(self) -> None:
        now = self.clock()
        self.snapshot.now = now
        self._poll(now)
        self._expire(now)
        data, ext = self._frame(now)
        self._send(now, data, ext)

    def run_forever(self) -> None:
        while True:
            try:
                self.tick()
            except Exception:  # кадр не нарисовался — пробуем на следующем тике, но не падаем
                log.exception("tick failed")
            time.sleep(1)

    def _poll(self, now: datetime) -> None:
        for src in self.sources:
            if now < self._due[id(src)]:
                continue
            self._due[id(src)] = now + timedelta(seconds=src.interval_s)
            try:
                r = src.poll()
            except Exception as e:  # источник обязан не бросать, но цикл важнее
                log.warning("%s: %s", src.name, e)
                continue
            if r.error:
                log.warning("%s", r.error)
            if r.weather is not None:
                self.snapshot.weather = r.weather
            if r.usage is not None:
                self.snapshot.usage, self._usage_at = r.usage, now
            if r.waiting is not None:
                self.snapshot.claude_waiting = r.waiting
            for n in r.notifications:
                self._enqueue(n, now)
            if r.badge is not None:  # источник знает точное число (прочитано в приложении)
                self._set_badge(src.name, r.badge, now)

    def _enqueue(self, n: Notification, now: datetime) -> None:
        recent = [t for t in self._recent.get(n.source, []) if now - t < BURST_WINDOW]
        recent.append(now)
        self._recent[n.source] = recent
        self._set_badge(n.source, self.snapshot.badges.get(n.source, 0) + 1, now, new=True)
        if len(recent) <= BURST_MAX:
            self.queue.append(n)
            return
        summary = self._summary.get(n.source)
        if summary is None:
            summary = Notification(n.source, "", "", now, f"summary-{n.source}")
            self._summary[n.source] = summary
            self._summary_n[n.source] = 0
            self.queue.append(summary)
        self._summary_n[n.source] += 1
        summary.title = f"Ещё {self._summary_n[n.source]}"
        summary.body = f"Последнее: {n.title}"

    def _set_badge(self, source: str, value: int, now: datetime, new: bool = False) -> None:
        # сравниваем с последним присланным, а не с показанным: погасший через час
        # счётчик иначе считался бы нулём и то же число зажигало бы его снова
        last = self._badge_last.get(source, 0)
        self._badge_last[source] = value
        if value <= 0:
            self.snapshot.badges.pop(source, None)
            self._badge_at.pop(source, None)
        elif new or value > last:
            self.snapshot.badges[source] = value
            self._badge_at[source] = now
        elif source in self.snapshot.badges:  # часть прочитана — число меньше, час не продлеваем
            self.snapshot.badges[source] = value

    def _expire(self, now: datetime) -> None:
        for src, at in list(self._badge_at.items()):
            if now - at >= BADGE_TTL:
                self.snapshot.badges.pop(src, None)
                del self._badge_at[src]
        if self.snapshot.usage is not None and now - self._usage_at > USAGE_TTL:
            self.snapshot.usage = None
        if self.current and (now - self._card_at).total_seconds() >= CARD_S:
            self.current = None
        if self.current is None and self.queue:
            self.current = self.queue.pop(0)
            self._card_at = now
            if self._summary.get(self.current.source) is self.current:
                del self._summary[self.current.source]  # следующие лишние соберутся в новую сводную

    def _frame(self, now: datetime):
        s = self.snapshot
        if self.current is None:
            return render.encode_jpeg(render.render_clock(s)), "jpg"
        if (now - self._card_at).total_seconds() < INTRO_S:
            if self._intro[0] is not self.current:
                self._intro = (self.current, render.encode_gif(render.render_card_intro(self.current, s)))
            return self._intro[1], "gif"
        return render.encode_jpeg(render.render_card(self.current, s)), "jpg"

    def _send(self, now: datetime, data: bytes, ext: str) -> None:
        if data == self._sent or now < self._retry_at:
            return
        try:
            if not self._prepared:
                self.device.prepare()
                self._prepared = True
            self.device.show(data, ext)
            self._sent = data
        except CubeOffline as e:
            log.warning("кубик недоступен, повтор через %s с: %s", RETRY_S, e)
            self._prepared, self._sent = False, None
            self._retry_at = now + timedelta(seconds=RETRY_S)
