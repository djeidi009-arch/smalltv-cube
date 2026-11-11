"""install / uninstall: автозапуск через launchd (под caffeinate -i) и хуки Claude Code рядом с существующими."""
from __future__ import annotations

import json
import os
import plistlib
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from cube.config import ROOT

LABEL = "ru.designbynikita.smalltv-cube"
SETTINGS = Path("~/.claude/settings.json").expanduser()
AGENTS = Path("~/Library/LaunchAgents").expanduser()
MARK = "-m cube.hook"  # по этой подстроке узнаём свои хуки, чужие не трогаем
HOOKS = {"Stop": "waiting", "Notification": "waiting", "UserPromptSubmit": "answered", "SessionEnd": "answered"}


def _command(state: str) -> str:
    # хук запускается в папке чужого проекта, поэтому сначала переходим в свою
    return f"cd {shlex.quote(str(ROOT))} && {shlex.quote(sys.executable)} {MARK} {state}"


def _load(settings: Path) -> dict:
    return json.loads(settings.read_text()) if settings.exists() else {}  # битый JSON — падаем, не перезаписываем


def _save(settings: Path, data: dict) -> None:
    settings.parent.mkdir(parents=True, exist_ok=True)
    tmp = settings.with_suffix(".cube-tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, settings)


def _strip(data: dict) -> dict:
    hooks = data.get("hooks", {})
    for event in list(hooks):
        groups = []
        for g in hooks[event]:
            ours = [h for h in g.get("hooks", []) if MARK in h.get("command", "")]
            if not ours:
                groups.append(g)
            elif len(ours) < len(g["hooks"]):
                groups.append({**g, "hooks": [h for h in g["hooks"] if h not in ours]})
        if groups or not hooks[event]:
            hooks[event] = groups
        else:
            del hooks[event]  # событие было только нашим
    if "hooks" in data and not hooks:
        del data["hooks"]
    return data


def _launchctl(*args: str) -> None:
    subprocess.run(["launchctl", *args], capture_output=True)


def install(cfg, settings: Path = SETTINGS, agents: Path = AGENTS, launchctl: bool = True) -> None:
    if settings.exists():
        shutil.copy2(settings, settings.with_name(settings.name + ".smalltv-cube.bak"))
    data = _strip(_load(settings))
    for event, state in HOOKS.items():
        data.setdefault("hooks", {}).setdefault(event, []).append(
            {"hooks": [{"type": "command", "command": _command(state), "timeout": 5}]})
    _save(settings, data)
    print(f"Хуки Claude Code добавлены в {settings} (копия до правки: {settings.name}.smalltv-cube.bak)")

    agents.mkdir(parents=True, exist_ok=True)
    plist = agents / f"{LABEL}.plist"
    plist.write_bytes(plistlib.dumps({
        "Label": LABEL,
        "ProgramArguments": ["/usr/bin/caffeinate", "-i", sys.executable, "-m", "cube", "run"],
        "WorkingDirectory": str(ROOT),
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(cfg.data_dir / "launchd.log"),
        "StandardErrorPath": str(cfg.data_dir / "launchd.log"),
    }))
    if launchctl:
        _launchctl("bootout", f"gui/{os.getuid()}/{LABEL}")
        _launchctl("bootstrap", f"gui/{os.getuid()}", str(plist))
    print(f"Автозапуск установлен: {plist}")


def uninstall(cfg, settings: Path = SETTINGS, agents: Path = AGENTS, launchctl: bool = True) -> None:
    if settings.exists():
        _save(settings, _strip(_load(settings)))
        print(f"Хуки Claude Code убраны из {settings}")
    if launchctl:
        _launchctl("bootout", f"gui/{os.getuid()}/{LABEL}")
    (agents / f"{LABEL}.plist").unlink(missing_ok=True)
    print("Автозапуск удалён")
