import json
import plistlib
from pathlib import Path

from cube.config import Config
from cube.install import install, uninstall

USER_HOOKS = {
    "SessionStart": [{"hooks": [{"type": "command", "command": "echo start"}]}],
    "PostToolUse": [{"matcher": "Edit", "hooks": [{"type": "command", "command": "lint"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "impeccable hook", "timeout": 30}]}],
}


def test_install_keeps_user_hooks_and_uninstall_leaves_no_trace(tmp_path):
    cfg = Config("cube", None, "1", None, None, 12.2, 109.2, "UTC", tmp_path / "data")
    settings = tmp_path / "settings.json"
    original = {"model": "opus", "hooks": USER_HOOKS}
    settings.write_text(json.dumps(original, indent=2))
    agents = tmp_path / "LaunchAgents"

    for _ in range(2):  # повторная установка не дублирует
        install(cfg, settings=settings, agents=agents, launchctl=False)
    hooks = json.loads(settings.read_text())["hooks"]
    for event in USER_HOOKS:
        assert USER_HOOKS[event][0] in hooks[event]
    cmds = {e: [h["command"] for g in groups for h in g["hooks"] if "cube.hook" in h["command"]]
            for e, groups in hooks.items()}
    assert len(cmds["Stop"]) == 1 and cmds["Stop"][0].endswith("waiting")
    assert len(cmds["Notification"]) == 1 and cmds["Notification"][0].endswith("waiting")
    assert len(cmds["UserPromptSubmit"]) == 1 and cmds["UserPromptSubmit"][0].endswith("answered")

    plist = plistlib.loads((agents / "ru.designbynikita.smalltv-cube.plist").read_bytes())
    assert plist["RunAtLoad"] is True and plist["KeepAlive"] is True
    assert plist["ProgramArguments"][:2] == ["/usr/bin/caffeinate", "-i"]
    assert plist["ProgramArguments"][-3:] == ["-m", "cube", "run"]

    uninstall(cfg, settings=settings, agents=agents, launchctl=False)
    assert json.loads(settings.read_text()) == original
    assert not (agents / "ru.designbynikita.smalltv-cube.plist").exists()


def test_install_into_missing_settings(tmp_path):
    cfg = Config("cube", None, "1", None, None, 12.2, 109.2, "UTC", tmp_path / "data")
    settings = tmp_path / "s.json"
    install(cfg, settings=settings, agents=tmp_path / "LA", launchctl=False)
    uninstall(cfg, settings=settings, agents=tmp_path / "LA", launchctl=False)
    assert json.loads(settings.read_text()) == {}
