from datetime import datetime, timedelta, timezone
from io import BytesIO

from PIL import Image, ImageChops

from cube import render
from cube.model import ClaudeUsage, Notification, Snapshot, Weather

NOW = datetime(2026, 11, 11, 16, 42, tzinfo=timezone(timedelta(hours=7)))


def weather(age):
    return Weather(temp_c=28.4, code=1, label_ru="Малооблачно", fetched_at=NOW - age)


def same(a, b):
    return ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox() is None


def test_clock_is_240_square_and_changes_with_minute():
    a = render.render_clock(Snapshot(now=NOW))
    b = render.render_clock(Snapshot(now=NOW + timedelta(minutes=1)))
    assert a.size == (240, 240)
    assert not same(a, b)


def test_stale_weather_drawn_as_missing():
    fresh = render.render_clock(Snapshot(now=NOW, weather=weather(timedelta(minutes=30))))
    stale = render.render_clock(Snapshot(now=NOW, weather=weather(timedelta(hours=3))))
    none = render.render_clock(Snapshot(now=NOW))
    assert same(stale, none)
    assert not same(fresh, none)


def test_badges_usage_and_waiting_are_visible():
    base = render.render_clock(Snapshot(now=NOW))
    for s in (
        Snapshot(now=NOW, badges={"telegram": 5}),
        Snapshot(now=NOW, usage=ClaudeUsage(used_pct=42, resets_at=NOW + timedelta(hours=2))),
        Snapshot(now=NOW, claude_waiting=2),
    ):
        assert not same(render.render_clock(s), base)


def test_card_intro_gif_is_short_and_ends_on_card():
    n = Notification("telegram", "Анна", "Привет! Ты посмотрел макет?", NOW, "t1")
    s = Snapshot(now=NOW)
    frames = render.render_card_intro(n, s)
    assert 2 <= len(frames) <= 12
    assert same(frames[-1][0], render.render_card(n, s))
    gif = render.encode_gif(frames)
    assert len(gif) <= 200_000
    assert Image.open(BytesIO(gif)).format == "GIF"
    assert Image.open(BytesIO(render.encode_jpeg(frames[-1][0]))).format == "JPEG"
