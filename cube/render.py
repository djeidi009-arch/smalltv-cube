"""Внешний вид кубика: чистые функции Snapshot → картинка 240×240. Решения — docs/design.md."""
from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from cube.model import Notification, Snapshot, Usage

SIZE = 240
S = 3  # рисуем в 3× и уменьшаем: Pillow не сглаживает фигуры сам
FONT = "/System/Library/Fonts/SFNSRounded.ttf"

BG = (13, 14, 17)
PANEL = (29, 31, 37)
TEXT = (242, 240, 236)
MUTED = (152, 152, 160)
BODY = (206, 204, 199)
TRACK = (44, 46, 53)
AMBER = (255, 184, 77)
RED = (240, 96, 84)
INK = (24, 18, 8)  # тёмный текст на янтарной плашке

SOURCES = {
    "figma": ("Figma", (167, 108, 255)),
    "telegram": ("Telegram", (52, 172, 238)),
    "claude_limit": ("Лимит Claude", AMBER),
    "claude_waiting": ("Claude Code", (222, 128, 96)),
}
BADGE_ORDER = ("figma", "telegram")

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


def _blank() -> Tuple[Image.Image, Canvas]:
    img = Image.new("RGB", (SIZE * S, SIZE * S), BG)
    return img, Canvas(img)


def _done(img: Image.Image) -> Image.Image:
    return img.resize((SIZE, SIZE), Image.LANCZOS)


def _badges(c: Canvas, s: Snapshot, y: float) -> float:
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
    return x


def _top_row(c: Canvas, s: Snapshot, left: str) -> None:
    y = 26
    badge_edge = _badges(c, s, y)
    if s.claude_waiting > 0:
        count = str(s.claude_waiting) if s.claude_waiting < 100 else "99+"
        suffix = f" · {count}" if s.claude_waiting > 1 else ""
        label = "Claude ждёт" + suffix
        size = 16
        if 12 + c.width(label, size, "Semibold") + 22 > badge_edge:
            label = "Ждёт" + suffix
            size = 15
        w = c.width(label, size, "Semibold")
        c.rect((12, y - 14, 12 + w + 22, y + 14), 14, AMBER)
        c.text((12 + 11, y), label, size, "Semibold", fill=INK, anchor="lm")
    elif left:
        c.text((16, y), left, 22, "Bold", anchor="lm")


PROVIDERS = (("claude", "Claude"), ("codex", "Codex"), ("opencode", "OpenCode Go"))


def _meter(c: Canvas, right: int, y: int, used_pct: Optional[float]) -> None:
    if used_pct is None:
        c.text((right, y), "—", 20, "Semibold", fill=MUTED, anchor="rm")
        return
    pct = round(used_pct)
    color = RED if pct >= 95 else AMBER if pct >= 80 else TEXT
    c.text((right, y), f"{pct}%", 19, "Semibold", fill=color, anchor="rm")
    left = right - 46
    c.rect((left, y + 15, right, y + 19), 2, TRACK)
    if used_pct > 0:
        c.rect((left, y + 15, left + max(4, 46 * used_pct / 100), y + 19), 2, color)


def render_limits(s: Snapshot) -> Image.Image:
    img, c = _blank()
    _top_row(c, s, "Лимиты")
    c.text((16, 61), "Использовано", 15, "Medium", fill=MUTED, anchor="lm")
    for right, label in ((170, "5 ч"), (224, "7 дн")):
        c.text((right, 61), label, 15, "Medium", fill=MUTED, anchor="rm")
    for row, (provider, label) in enumerate(PROVIDERS):
        y = 94 + row * 55
        c.rect((16, y - 20, 224, y - 19), 0, TRACK)
        c.text((16, y), label, 16, "Semibold", anchor="lm")
        usage = s.usage.get(provider) or Usage()
        _meter(c, 170, y, usage.five_hour)
        _meter(c, 224, y, usage.weekly)
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
    """Фон и панель карточки отдельно — для анимации выезда."""
    bg, c = _blank()
    _top_row(c, s, "")

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
VICTIM_FRACTION = 0.45  # главный экран уходит к 45% хода карточки (hyperframes: reactive-displacement)


def _ease_out_expo(t: float) -> float:
    # ≈ cubic-bezier(0.16, 1, 0.3, 1) — уверенное торможение без отскока
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def render_card_intro(n: Notification, s: Snapshot) -> List[Tuple[Image.Image, int]]:
    bg, panel = _card_layers(n, s)
    limits = render_limits(s)
    frames = [(limits, FRAME_MS)]
    background = limits.resize(bg.size, Image.LANCZOS)
    for i in range(1, FRAMES):
        p = _ease_out_expo(i / (FRAMES - 1))
        vp = min(1.0, p / VICTIM_FRACTION)
        victim = Image.new("RGB", bg.size, BG)
        victim.paste(background, (0, -round(28 * vp * S)))  # главный экран приподнимается, их «толкает» карточка
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
