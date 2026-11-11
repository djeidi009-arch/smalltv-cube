import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cube.sources.claude_waiting import ClaudeWaitingSource

ROOT = Path(__file__).resolve().parent.parent


def hook(tmp_path, state, session):
    env = {**os.environ, "CUBE_DATA_DIR": str(tmp_path)}
    stdin = json.dumps({"session_id": session, "cwd": "/Users/x/smalltv-cube", "hook_event_name": "Stop"})
    p = subprocess.run([sys.executable, "-m", "cube.hook", state], input=stdin, text=True,
                       cwd=ROOT, env=env, capture_output=True)
    assert p.returncode == 0, p.stderr


def test_hook_states_drive_indicator_and_card(tmp_path):
    src = ClaudeWaitingSource(tmp_path / "claude_sessions.json")
    assert src.poll().waiting == 0
    hook(tmp_path, "waiting", "s1")
    hook(tmp_path, "waiting", "s2")
    hook(tmp_path, "waiting", "s2")  # Notification после Stop — то же ожидание
    r = src.poll()
    assert r.waiting == 2
    assert [(n.source, n.title, n.body) for n in r.notifications] == [
        ("claude_waiting", "Claude ждёт ответа", "smalltv-cube: нужен ответ, чтобы продолжить")] * 2
    assert src.poll().notifications == []  # карточка один раз
    hook(tmp_path, "answered", "s1")
    assert src.poll().waiting == 1
    hook(tmp_path, "answered", "s2")
    assert src.poll().waiting == 0


def test_stale_sessions_ignored_and_bad_input_never_fails(tmp_path):
    old = (datetime.now(timezone.utc) - timedelta(hours=13)).isoformat()
    (tmp_path / "claude_sessions.json").write_text(json.dumps({"s9": {"waiting": True, "at": old}}))
    assert ClaudeWaitingSource(tmp_path / "claude_sessions.json").poll().waiting == 0
    p = subprocess.run([sys.executable, "-m", "cube.hook", "waiting"], input="not json", text=True, cwd=ROOT,
                       env={**os.environ, "CUBE_DATA_DIR": str(tmp_path)}, capture_output=True)
    assert p.returncode == 0  # хук никогда не мешает Claude Code
