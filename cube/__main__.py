"""python -m cube run | preview <папка> | status | telegram-login | install | uninstall"""
from __future__ import annotations

import importlib
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from cube import render
from cube.model import ClaudeUsage, Notification, Snapshot, Weather

LATER = {  # команда: модуль, функция
    "telegram-login": ("cube.sources.telegram", "login"),
    "install": ("cube.install", "install"),
    "uninstall": ("cube.install", "uninstall"),
}


def run(cfg) -> None:
    from cube.app import App
    from cube.device import CubeClient
    from cube.sources import build_sources

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(cfg.data_dir / "cube.log")])
    logging.getLogger("httpx").setLevel(logging.WARNING)  # иначе каждый запрос — строка в логе
    App(cfg, CubeClient(cfg.cube_host), build_sources(cfg)).run_forever()


def preview(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    now = datetime(2026, 11, 11, 16, 42, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    w = Weather(28.4, 2, "Облачно", now)
    u = ClaudeUsage(42, now + timedelta(hours=2))
    full = Snapshot(now, w, u, {"figma": 2, "telegram": 5}, 0)
    clocks = {
        "empty": Snapshot(now),
        "weather": Snapshot(now, w),
        "badges": Snapshot(now, w, None, {"figma": 2, "telegram": 5}),
        "usage": Snapshot(now, w, u),
        "usage-high": Snapshot(now, Weather(26, 61, "Дождь", now), ClaudeUsage(87, u.resets_at)),
        "waiting": Snapshot(now, w, u, {"telegram": 1}, 2),
    }
    for name, s in clocks.items():
        render.render_clock(s).save(out / f"clock-{name}.png")
    cards = {
        "figma": Notification("figma", "Анна · Лендинг v3", "Давай сделаем кнопку заметнее и поднимем блок с ценами выше", now, "f"),
        "telegram": Notification("telegram", "Мама", "Позвони, когда освободишься", now, "t"),
        "claude_limit": Notification("claude_limit", "Использовано 80%", "Лимит сбросится в 18:40", now, "l"),
        "claude_waiting": Notification("claude_waiting", "Claude ждёт ответа", "smalltv-cube: нужен ответ, чтобы продолжить", now, "w"),
        "summary": Notification("telegram", "Ещё 4", "Последнее: Олег", now, "s"),
    }
    for name, n in cards.items():
        render.render_card(n, full).save(out / f"card-{name}.png")
    (out / "card-telegram-intro.gif").write_bytes(render.encode_gif(render.render_card_intro(cards["telegram"], full)))
    print(f"превью: {out}")


def status(cfg) -> None:
    from cube.device import CubeClient
    from cube.sources import build_sources

    print(f"кубик {cfg.cube_host}: {'на связи' if CubeClient(cfg.cube_host).is_online() else 'недоступен'}")
    print("источники:", ", ".join(s.name for s in build_sources(cfg)))
    print(f"данные: {cfg.data_dir}")


def main(argv=None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else ""
    if cmd == "preview":
        return preview(Path(argv[1] if len(argv) > 1 else "out"))
    from cube.config import load_config

    if cmd == "run":
        return run(load_config())
    if cmd == "status":
        return status(load_config())
    if cmd in LATER:
        mod, fn = LATER[cmd]
        return getattr(importlib.import_module(mod), fn)(load_config())
    sys.exit(__doc__)


if __name__ == "__main__":
    main()
