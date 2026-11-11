"""Внешний вид кубика: чистые функции Snapshot → картинка 240×240. Решения — docs/design.md."""
from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
from io import BytesIO
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from cube.model import Notification, Snapshot

SIZE = 240
S = 3  # рисуем в 3× и уменьшаем: Pillow не сглаживает фигуры сам
FONT = "/System/Library/Fonts/SFNSRounded.ttf"
WEATHER_STALE = timedelta(hours=2)

BG = (13, 14, 17)
PANEL = (29, 31, 37)
TEXT = (242, 240, 236)
MUTED = (152, 152, 160)
BODY = (206, 204, 199)
TRACK = (44, 46, 53)
AMBER = (255, 184, 77)
RED = (240, 96, 84)
SUN = (255, 204, 92)
CLOUD = (200, 204, 214)
DROP = (96, 170, 255)
INK = (24, 18, 8)  # тёмный текст на янтарной плашке

SOURCES = {
    "figma": ("Figma", (167, 108, 255)),
    "telegram": ("Telegram", (52, 172, 238)),
    "claude_limit": ("Лимит Claude", AMBER),
    "claude_waiting": ("Claude Code", (222, 128, 96)),
}
BADGE_ORDER = ("figma", "telegram")

DAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
MONTHS = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля",
          "августа", "сентября", "октября", "ноября", "декабря")


@lru_cache(maxsize=None)
def font(size: int, weight: str = "Regular"):
    try:
        f = ImageFont.truetype(FONT, size * S)
        f.set_variation_by_name(weight)
        return f
    except OSError:  # нет SF Rounded (не Mac) — рисуем запасным, лишь бы не упасть
        return ImageFont.load_default(size * S)


class Canvas:
    """ImageDraw в координатах 240×240 поверх холста 720×720."""

    def __init__(self, img: Image.Image):
        self.img = img
        self.d = ImageDraw.Draw(img)

    def text(self, xy, s, size, weight="Regular", fill=TEXT, anchor="la"):
        self.d.text((xy[0] * S, xy[1] * S), s, font=font(size, weight), fill=fill, anchor=anchor)

    def width(self, s, size, weight="Regular") -> float:
        return self.d.textlength(s, font=font(size, weight)) / S

    def rect(self, box, r, fill):
        self.d.rounded_rectangle([v * S for v in box], radius=r * S, fill=fill)

    def circle(self, cx, cy, r, fill):
        self.d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=fill)

    def line(self, pts, w, fill):
        self.d.line([(x * S, y * S) for x, y in pts], width=round(w * S), fill=fill, joint="curve")
        for x, y in (pts[0], pts[-1]):  # скруглённые концы
            self.circle(x, y, w / 2, fill)


def _blank() -> Tuple[Image.Image, Canvas]:
    img = Image.new("RGB", (SIZE * S, SIZE * S), BG)
    return img, Canvas(img)


def _done(img: Image.Image) -> Image.Image:
    return img.resize((SIZE, SIZE), Image.LANCZOS)


def _date_ru(s: Snapshot) -> str:
    return f"{DAYS[s.now.weekday()]}, {s.now.day} {MONTHS[s.now.month - 1]}"


def _badges(c: Canvas, s: Snapshot, y: float) -> None:
    x = SIZE - 16
    for src in reversed(BADGE_ORDER):
        n = s.badges.get(src, 0)
        if n <= 0:
            continue
        label = str(n) if n < 100 else "99+"
        w = c.width(label, 17, "Semibold")
        c.text((x, y), label, 17, "Semibold", anchor="rm")
        c.circle(x - w - 9, y, 5, SOURCES[src][1])
        x -= w + 9 + 5 + 12


def _top_row(c: Canvas, s: Snapshot, left: str) -> None:
    y = 26
    if s.claude_waiting > 0:
        label = "Claude ждёт" + (f" · {s.claude_waiting}" if s.claude_waiting > 1 else "")
        w = c.width(label, 16, "Semibold")
        c.rect((12, y - 14, 12 + w + 22, y + 14), 14, AMBER)
        c.text((12 + 11, y), label, 16, "Semibold", fill=INK, anchor="lm")
    elif left:
        c.text((16, y), left, 17, "Medium", fill=MUTED, anchor="lm")
    _badges(c, s, y)


def weather_kind(code: int) -> str:
    if code == 0:
        return "sun"
    if code in (1, 2):
        return "partly"
    if code in (45, 48):
        return "fog"
    if 51 <= code <= 67 or 80 <= code <= 82:
        return "rain"
    if 71 <= code <= 77 or code in (85, 86):
        return "snow"
    if code >= 95:
        return "storm"
    return "cloud"


def _cloud(c: Canvas, x, y, k=1.0, fill=CLOUD):
    # x, y — левый нижний угол облака шириной ~30k
    c.rect((x, y - 11 * k, x + 30 * k, y), 5.5 * k, fill)
    c.circle(x + 10 * k, y - 11 * k, 7 * k, fill)
    c.circle(x + 19 * k, y - 14 * k, 9 * k, fill)


def _sun(c: Canvas, cx, cy, r):
    c.circle(cx, cy, r, SUN)
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1), (.7, .7), (-.7, .7), (.7, -.7), (-.7, -.7)):
        c.line([(cx + dx * (r + 3.5), cy + dy * (r + 3.5)), (cx + dx * (r + 7), cy + dy * (r + 7))], 2.4, SUN)


def _weather_icon(c: Canvas, kind: str, x, cy) -> None:
    """Иконка 34×34, левый край x, центр по вертикали cy."""
    if kind == "sun":
        _sun(c, x + 17, cy, 8)
    elif kind == "partly":
        _sun(c, x + 12, cy - 6, 6.5)
        _cloud(c, x + 4, cy + 12)
    elif kind == "fog":
        for i, w in enumerate((28, 22, 28)):
            c.line([(x + 3, cy - 8 + i * 8), (x + 3 + w, cy - 8 + i * 8)], 3, CLOUD)
    else:
        _cloud(c, x + 2, cy + 4)
        if kind == "rain":
            for i in range(3):
                c.line([(x + 9 + i * 8, cy + 9), (x + 6 + i * 8, cy + 15)], 2.6, DROP)
        elif kind == "snow":
            for i in range(3):
                c.circle(x + 8 + i * 8, cy + 12 + (i % 2) * 3, 2, TEXT)
        elif kind == "storm":
            c.d.polygon([(v * S) for v in (x + 18, cy + 4, x + 12, cy + 13, x + 17, cy + 13, x + 14, cy + 20,
                                           x + 22, cy + 10, x + 17, cy + 10, x + 20, cy + 4)], fill=SUN)


def _weather(c: Canvas, s: Snapshot, cy: float) -> None:
    w = s.weather
    if w is None or s.now - w.fetched_at > WEATHER_STALE:
        c.text((SIZE / 2, cy), "—", 28, "Semibold", fill=MUTED, anchor="mm")
        return
    temp = f"{round(w.temp_c)}°"
    tw, lw = c.width(temp, 30, "Semibold"), c.width(w.label_ru, 17, "Medium")
    show_label = 34 + 8 + tw + 10 + lw <= SIZE - 24
    total = 34 + 8 + tw + (10 + lw if show_label else 0)
    x = (SIZE - total) / 2
    _weather_icon(c, weather_kind(w.code), x, cy)
    c.text((x + 42, cy), temp, 30, "Semibold", anchor="lm")
    if show_label:
        c.text((x + 42 + tw + 10, cy + 1), w.label_ru, 17, "Medium", fill=MUTED, anchor="lm")


def _usage(c: Canvas, s: Snapshot) -> None:
    u = s.usage
    if u is None:
        return
    pct = max(0.0, min(100.0, u.used_pct))
    color = RED if pct >= 95 else AMBER if pct >= 80 else TEXT
    c.text((16, 206), f"Claude {round(pct)}%", 15, "Medium", fill=MUTED if pct < 80 else color, anchor="lm")
    if u.resets_at:
        c.text((SIZE - 16, 206), f"до {u.resets_at.astimezone(s.now.tzinfo):%H:%M}", 15, "Medium",
               fill=MUTED, anchor="rm")
    c.rect((16, 220, SIZE - 16, 226), 3, TRACK)
    if pct > 0:
        c.rect((16, 220, 16 + max(6, (SIZE - 32) * pct / 100), 226), 3, color)


def render_clock(s: Snapshot) -> Image.Image:
    img, c = _blank()
    _top_row(c, s, _date_ru(s))
    t = f"{s.now:%H:%M}"
    size = 84
    while c.width(t, size, "Bold") > SIZE - 24:
        size -= 2
    c.text((SIZE / 2, 98), t, size, "Bold", anchor="mm")
    _weather(c, s, 158)
    _usage(c, s)
    return _done(img)


def _wrap(c: Canvas, text: str, size: int, weight: str, width: float, max_lines: int) -> List[str]:
    lines, cur = [], ""
    for word in text.split():
        cand = f"{cur} {word}".strip()
        if c.width(cand, size, weight) <= width or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] += "…"
    for i, ln in enumerate(lines):  # слово длиннее строки — режем по символам
        while c.width(ln, size, weight) > width and len(ln) > 1:
            ln = ln[:-2] + "…"
        lines[i] = ln
    return lines


PANEL_Y = 48


def _card_layers(n: Notification, s: Snapshot) -> Tuple[Image.Image, Image.Image]:
    """Фон (время + счётчики) и панель карточки отдельно — для анимации выезда."""
    bg, c = _blank()
    _top_row(c, s, "")
    if s.claude_waiting <= 0:
        c.text((16, 26), f"{s.now:%H:%M}", 20, "Semibold", anchor="lm")

    h = SIZE - 8 - PANEL_Y
    panel = Image.new("RGBA", (SIZE * S, h * S), (0, 0, 0, 0))
    p = Canvas(panel)
    p.rect((8, 0, SIZE - 8, h), 20, PANEL)
    label, accent = SOURCES.get(n.source, (n.source, TEXT))
    p.circle(28, 24, 5, accent)
    p.text((40, 24), label, 15, "Semibold", fill=accent, anchor="lm")
    y = 44
    for ln in _wrap(p, n.title, 22, "Bold", SIZE - 56, 2):
        p.text((24, y), ln, 22, "Bold")
        y += 28
    y += 6
    for ln in _wrap(p, n.body, 18, "Regular", SIZE - 56, (h - y - 14) // 23):
        p.text((24, y), ln, 18, "Regular", fill=BODY)
        y += 23
    return bg, panel


def _compose(bg: Image.Image, panel: Image.Image, dy: float) -> Image.Image:
    img = bg.copy()
    img.paste(panel, (0, round((PANEL_Y + dy) * S)), panel)
    return _done(img)


def render_card(n: Notification, s: Snapshot) -> Image.Image:
    bg, panel = _card_layers(n, s)
    return _compose(bg, panel, 0)


FRAMES = 10
FRAME_MS = 60      # 10 × 60 мс = 600 мс — «авторский фокусный вход» (impeccable: 500–800 мс)
VICTIM_FRACTION = 0.45  # часы уходят к 45% хода карточки (hyperframes: reactive-displacement)


def _ease_out_expo(t: float) -> float:
    # ≈ cubic-bezier(0.16, 1, 0.3, 1) — уверенное торможение без отскока
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def render_card_intro(n: Notification, s: Snapshot) -> List[Tuple[Image.Image, int]]:
    bg, panel = _card_layers(n, s)
    clock = render_clock(s).resize(bg.size, Image.LANCZOS)
    frames = []
    for i in range(FRAMES):
        p = _ease_out_expo(i / (FRAMES - 1))
        vp = min(1.0, p / VICTIM_FRACTION)
        victim = Image.new("RGB", bg.size, BG)
        victim.paste(clock, (0, -round(28 * vp * S)))  # часы приподнимаются, их «толкает» карточка
        base = Image.blend(victim, bg, vp)
        frames.append((_compose(base, panel, (SIZE - PANEL_Y) * (1 - p)), FRAME_MS))
    frames[-1] = (frames[-1][0], 1000)
    return frames


def encode_jpeg(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=92)
    return buf.getvalue()


def encode_gif(frames: List[Tuple[Image.Image, int]]) -> bytes:
    buf = BytesIO()
    imgs = [f.convert("RGB") for f, _ in frames]
    # без loop: GIF проигрывается один раз и остаётся на последнем кадре
    imgs[0].save(buf, "GIF", save_all=True, append_images=imgs[1:], duration=[d for _, d in frames])
    return buf.getvalue()
