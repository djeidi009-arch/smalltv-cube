import asyncio
from types import SimpleNamespace as NS

from cube.sources.telegram import TelegramSource


def event(text="", private=True, chat_id=7, msg_id=1, **media):
    sender = NS(first_name="Мама", last_name=None, username="mom")
    msg = NS(id=msg_id, **{"photo": None, "voice": None, "sticker": None, **media})

    async def get_sender():
        return sender

    return NS(is_private=private, raw_text=text, chat_id=chat_id, message=msg, get_sender=get_sender)


def feed(src, *events):
    for e in events:
        asyncio.run(src.on_message(e))


def test_private_messages_become_cards_groups_ignored():
    src = TelegramSource()
    feed(src, event("Позвони\nкогда сможешь"), event("в группе", private=False, chat_id=-100, msg_id=2),
         event(photo=object(), msg_id=3), event(voice=object(), msg_id=4), event(sticker=object(), msg_id=5))
    res = src.poll()
    assert [(n.source, n.title, n.body) for n in res.notifications] == [
        ("telegram", "Мама", "Позвони"),
        ("telegram", "Мама", "Фото"),
        ("telegram", "Мама", "Голосовое"),
        ("telegram", "Мама", "Стикер"),
    ]
    assert res.badge == 4
    assert src.poll().notifications == []


def test_reading_chat_clears_badge():
    src = TelegramSource()
    feed(src, event("привет"))
    src.poll()
    asyncio.run(src.on_read(NS(chat_id=7)))
    assert src.poll().badge == 0
