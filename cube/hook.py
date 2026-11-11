"""Хук Claude Code: python -m cube.hook waiting|answered, JSON хука на stdin.

Пишет data_dir/claude_sessions.json: {session_id: {"waiting": bool, "at": iso, "project": str}}.
Никогда не завершается ошибкой, чтобы не мешать Claude Code.
"""
from __future__ import annotations

import fcntl
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

TTL = timedelta(hours=12)
FILE = "claude_sessions.json"


def fresh(at: str, now: datetime) -> bool:
    return now - datetime.fromisoformat(at) < TTL


def record(path: Path, session_id: str, waiting: bool, project: str = "", event: str = "") -> None:
    now = datetime.now(timezone.utc)
    with open(path.with_suffix(".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)  # несколько сессий могут сработать одновременно
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            data = {}
        data = {k: v for k, v in data.items() if fresh(v["at"], now)}
        # Notification после Stop — то же ожидание, одна карточка; Stop после разрешения — новое ожидание
        if not (waiting and event == "Notification" and data.get(session_id, {}).get("waiting")):
            data[session_id] = {"waiting": waiting, "at": now.isoformat(), "project": project}
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False))
        os.replace(tmp, path)


def main(argv=None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    try:
        from cube.config import load_config

        event = json.loads(sys.stdin.read())
        record(load_config().data_dir / FILE, event["session_id"], argv[0] == "waiting",
               Path(event.get("cwd") or "").name, event.get("hook_event_name", ""))
    except Exception as e:
        print(f"cube.hook: {type(e).__name__}", file=sys.stderr)


if __name__ == "__main__":
    main()
