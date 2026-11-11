from datetime import datetime, timedelta, timezone
from pathlib import Path

from cube.app import App
from cube.config import Config
from cube.device import CubeOffline
from cube.model import ClaudeUsage, Notification
from cube.sources.base import SourceResult

T0 = datetime(2026, 11, 11, 16, 42, 5, tzinfo=timezone(timedelta(hours=7)))
CFG = Config("cube", None, "1", None, None, 12.2, 109.2, "Asia/Ho_Chi_Minh", Path("/tmp"))


class FakeDevice:
    def __init__(self):
        self.shown = []  # расширения показанных кадров по порядку
        self.offline = False
        self.prepared = 0

    def prepare(self):
        if self.offline:
            raise CubeOffline("down")
        self.prepared += 1

    def show(self, data, ext):
        if self.offline:
            raise CubeOffline("down")
        self.shown.append(ext)


class FakeSource:
    name = "fake"
    interval_s = 60

    def __init__(self, *results):
        self.results = list(results)

    def poll(self):
        return self.results.pop(0) if self.results else SourceResult()


class Clock:
    def __init__(self):
        self.t = T0

    def __call__(self):
        return self.t

    def run(self, app, seconds):
        for _ in range(seconds):
            app.tick()
            self.t += timedelta(seconds=1)


def note(i, source="telegram"):
    return Notification(source, f"Анна {i}", "Привет", T0, f"k{i}")


def make(*sources, dev=None):
    clock, dev = Clock(), dev or FakeDevice()
    return App(CFG, dev, list(sources), clock=clock), dev, clock


def test_unchanged_frame_is_not_resent():
    app, dev, clock = make(FakeSource())
    clock.run(app, 30)  # те же ЧЧ:ММ
    assert dev.shown == ["jpg"]
    clock.run(app, 60)
    assert dev.shown == ["jpg", "jpg"]  # сменилась минута


def test_card_gif_then_holds_15s_then_clock_with_badge():
    app, dev, clock = make(FakeSource(SourceResult(notifications=[note(1)])))
    clock.run(app, 14)
    assert dev.shown == ["gif", "jpg"]  # выезд, затем статичная карточка
    clock.run(app, 2)
    assert dev.shown == ["gif", "jpg", "jpg"]  # через 15 с снова часы
    assert app.snapshot.badges == {"telegram": 1}


def test_burst_from_one_source_collapses_into_summary():
    app, dev, clock = make(FakeSource(SourceResult(notifications=[note(i) for i in range(5)])))
    titles = []
    for _ in range(80):
        app.tick()
        if app.current and app.current.title not in titles:
            titles.append(app.current.title)
        clock.t += timedelta(seconds=1)
    assert titles == ["Анна 0", "Анна 1", "Анна 2", "Ещё 2"]
    assert dev.shown.count("gif") == 4
    assert app.snapshot.badges == {"telegram": 5}


def test_badge_fades_after_an_hour_without_new():
    app, dev, clock = make(FakeSource(SourceResult(notifications=[note(1)])))
    app.tick()
    clock.t += timedelta(minutes=59)
    app.tick()
    assert app.snapshot.badges == {"telegram": 1}
    clock.t += timedelta(minutes=2)
    app.tick()
    assert app.snapshot.badges == {}


def test_offline_cube_retries_every_30s_and_resends():
    dev = FakeDevice()
    dev.offline = True
    app, dev, clock = make(FakeSource(), dev=dev)
    clock.run(app, 10)  # не падает
    dev.offline = False
    clock.run(app, 15)
    assert dev.shown == []  # ещё не прошло 30 с
    clock.run(app, 10)
    assert dev.shown == ["jpg"] and dev.prepared == 1


def test_weather_kept_on_error_and_usage_hidden_when_stale():
    from cube.model import Weather
    w = Weather(28, 0, "Ясно", T0)
    u = ClaudeUsage(40, None)
    src = FakeSource(SourceResult(weather=w, usage=u), SourceResult(error="offline"))
    src.interval_s = 600
    app, dev, clock = make(src)
    app.tick()
    clock.t += timedelta(minutes=10)
    app.tick()
    assert app.snapshot.weather == w and app.snapshot.usage == u
    clock.t += timedelta(minutes=6)
    app.tick()
    assert app.snapshot.usage is None and app.snapshot.weather == w


def test_same_badge_count_does_not_relight_after_an_hour():
    src = FakeSource(*[SourceResult(badge=5) for _ in range(200)])
    app, dev, clock = make(src)
    for _ in range(62):  # опрос раз в минуту, всё время «5 непрочитанных», новых нет
        app.tick()
        clock.t += timedelta(minutes=1)
    assert app.snapshot.badges == {}
    src.results.insert(0, SourceResult(badge=6))  # появилось новое — снова горит
    clock.t += timedelta(minutes=1)
    app.tick()
    assert app.snapshot.badges == {"fake": 6}


def test_notification_after_expiry_relights_badge():
    src = FakeSource(SourceResult(notifications=[note(1)]))
    app, dev, clock = make(src)
    app.tick()
    clock.t += timedelta(minutes=61)
    app.tick()
    assert app.snapshot.badges == {}
    src.results.append(SourceResult(notifications=[note(2)]))
    clock.t += timedelta(minutes=1)
    app.tick()
    assert app.snapshot.badges == {"telegram": 1}


def test_intro_gif_sent_once_even_if_clock_or_waiting_change():
    src = FakeSource(SourceResult(notifications=[note(1)]), SourceResult(waiting=1, badge=3), SourceResult(waiting=2))
    src.interval_s = 1
    app, dev, clock = make(src)
    clock.t = T0.replace(second=59)  # на втором тике меняется минута
    clock.run(app, 5)
    assert dev.shown.count("gif") == 1
