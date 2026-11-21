from datetime import datetime, timedelta, timezone
from io import BytesIO

from PIL import Image, ImageChops

from cube import render
from cube.model import Notification, Snapshot, Usage

NOW = datetime(2026, 11, 11, 16, 42, tzinfo=timezone(timedelta(hours=7)))


def same(a, b):
    return ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox() is None


def test_limits_are_240_square_and_independent_of_time():
    a = render.render_limits(Snapshot(now=NOW))
    b = render.render_limits(Snapshot(now=NOW + timedelta(minutes=1)))
    assert a.size == (240, 240)
    assert same(a, b)


def test_badges_usage_and_waiting_are_visible():
    base = render.render_limits(Snapshot(now=NOW))
    for s in (
        Snapshot(now=NOW, badges={"telegram": 5}),
        Snapshot(now=NOW, usage={"claude": Usage(42, 16)}),
        Snapshot(now=NOW, usage={"codex": Usage(weekly=0)}),
        Snapshot(now=NOW, usage={"opencode": Usage(87, 100)}),
        Snapshot(now=NOW, claude_waiting=2),
    ):
        assert not same(render.render_limits(s), base)


def test_card_intro_gif_is_short_and_ends_on_card():
    n = Notification("telegram", "Анна", "Привет! Ты посмотрел макет?", NOW, "t1")
    s = Snapshot(now=NOW)
    frames = render.render_card_intro(n, s)
    assert 2 <= len(frames) <= 12
    assert same(frames[0][0], render.render_limits(s))
    assert same(frames[-1][0], render.render_card(n, s))
    gif = render.encode_gif(frames)
    assert len(gif) <= 200_000
    assert Image.open(BytesIO(gif)).format == "GIF"
    assert Image.open(BytesIO(render.encode_jpeg(frames[-1][0]))).format == "JPEG"
