"""Новые личные сообщения в Telegram. Клиент Telethon живёт в своём потоке, poll() отдаёт накопленное."""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from cube.model import Notification
from cube.sources.base import SourceResult

log = logging.getLogger("cube")


def session_path(cfg) -> Path:
    return cfg.data_dir / "telegram"  # Telethon допишет .session; лежит вне репозитория


def _name(u) -> str:
    full = " ".join(p for p in (getattr(u, "first_name", None), getattr(u, "last_name", None)) if p)
    return full or getattr(u, "username", None) or getattr(u, "title", None) or "Telegram"


def _text(event) -> str:
    lines = (event.raw_text or "").strip().splitlines()
    if lines:
        return lines[0][:120]
    m = event.message
    for attr, label in (("photo", "Фото"), ("voice", "Голосовое"), ("sticker", "Стикер")):
        if getattr(m, attr, None):
            return label
    return "Вложение"


class TelegramSource:
    name = "telegram"
    interval_s = 3

    def __init__(self):
        self._lock = threading.Lock()
        self._new: List[Notification] = []
        self._unread: Dict[int, int] = {}
        self._changed = False
        self._error: Optional[str] = None

    async def on_message(self, event) -> None:
        if not event.is_private:  # группы и каналы не показываем
            return
        n = Notification("telegram", _name(await event.get_sender()), _text(event),
                         datetime.now(timezone.utc), f"tg-{event.chat_id}-{event.message.id}")
        with self._lock:
            self._new.append(n)
            self._unread[event.chat_id] = self._unread.get(event.chat_id, 0) + 1
            self._changed = True

    async def on_read(self, event) -> None:  # прочитал чат в Telegram — счётчик этого чата сбрасывается
        with self._lock:
            if self._unread.pop(event.chat_id, None) is not None:
                self._changed = True

    def poll(self) -> SourceResult:
        with self._lock:
            new, self._new = self._new, []
            badge = sum(self._unread.values()) if self._changed else None
            self._changed = False
            err, self._error = self._error, None
        return SourceResult(notifications=new, badge=badge, error=err)

    def start(self, cfg) -> None:
        threading.Thread(target=self._run, args=(cfg,), daemon=True, name="telegram").start()

    def _run(self, cfg) -> None:
        from telethon import TelegramClient, events

        while True:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                client = TelegramClient(str(session_path(cfg)), cfg.telegram_api_id, cfg.telegram_api_hash)
                client.add_event_handler(self.on_message, events.NewMessage(incoming=True))
                client.add_event_handler(self.on_read, events.MessageRead(inbox=True))
                loop.run_until_complete(self._serve(client))
            except Exception as e:
                self._error = f"telegram: {type(e).__name__}: {e}"
            finally:
                loop.close()
            time.sleep(30)  # связь пропала — переподключаемся

    async def _serve(self, client) -> None:
        await client.connect()
        try:
            if not await client.is_user_authorized():
                self._error = "telegram: нет входа — запусти `uv run python -m cube telegram-login`"
                return
            await client.run_until_disconnected()
        finally:
            await client.disconnect()


def create(cfg) -> Optional[TelegramSource]:
    if not (cfg.telegram_api_id and cfg.telegram_api_hash):
        return None
    if not Path(f"{session_path(cfg)}.session").exists():
        log.warning("telegram: нет входа — запусти `uv run python -m cube telegram-login`")
        return None
    try:
        src = TelegramSource()
        src.start(cfg)
        return src
    except Exception as e:
        log.warning("telegram: не запустился: %s", type(e).__name__)
        return None


def login(cfg) -> None:
    """Интерактивный вход: телефон, код из Telegram и, если есть, облачный пароль вводит сам пользователь."""
    if not (cfg.telegram_api_id and cfg.telegram_api_hash):
        sys.exit("Сначала впиши TELEGRAM_API_ID и TELEGRAM_API_HASH в файл .env (см. README.md).")
    from telethon.sync import TelegramClient

    with TelegramClient(str(session_path(cfg)), cfg.telegram_api_id, cfg.telegram_api_hash) as client:
        me = client.get_me()
    os.chmod(f"{session_path(cfg)}.session", 0o600)  # сессия = доступ к аккаунту, только для владельца
    print(f"Готово: вход выполнен как {_name(me)}. Сессия сохранена в {cfg.data_dir}.")
