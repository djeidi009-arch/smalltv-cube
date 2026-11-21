"""Лимиты ChatGPT через локальный Codex App Server."""
from __future__ import annotations

import json
import os
import selectors
import shutil
import signal
import subprocess
import time

from cube.model import Usage
from cube.sources.base import Background, SourceResult, used_percent


def read_limits() -> dict:
    env = os.environ.copy()
    # У launchd сокращённый PATH, а Homebrew-обёртка Codex ищет node через env.
    env["PATH"] = os.pathsep.join((env.get("PATH", os.defpath), "/opt/homebrew/bin", "/usr/local/bin"))
    command = shutil.which("codex", path=env["PATH"])
    if command is None:
        raise FileNotFoundError("codex")

    with subprocess.Popen(
        [command, "app-server", "--listen", "stdio://"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        env=env, start_new_session=True,
    ) as process, selectors.DefaultSelector() as selector:
        try:
            selector.register(process.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + 10
            pending = b""

            def send(message: dict) -> None:
                process.stdin.write(json.dumps(message).encode() + b"\n")
                process.stdin.flush()

            def response(request_id: int) -> dict:
                nonlocal pending
                while True:
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        frame = json.loads(line)
                        if frame.get("id") == request_id and "method" not in frame:
                            return frame["result"]
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise EOFError
                    pending += chunk

            send({"id": 1, "method": "initialize", "params": {"clientInfo": {
                "name": "smalltv-cube", "title": "SmallTV Cube", "version": "0.1.0",
            }}})
            response(1)
            send({"method": "initialized"})
            send({"id": 2, "method": "account/rateLimits/read"})
            return response(2)
        finally:
            # У npm-обёртки есть дочерний процесс, его тоже нужно завершить.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


class CodexUsageSource(Background):
    name = "codex_usage"
    every_s = 5 * 60

    def fetch(self) -> SourceResult:
        try:
            result = read_limits()
            limits = (result.get("rateLimitsByLimitId") or {}).get("codex") or result["rateLimits"]
            windows = {}
            for key in ("primary", "secondary"):
                window = limits.get(key) or {}
                windows[window.get("windowDurationMins")] = used_percent(window.get("usedPercent"))
            usage = Usage(five_hour=windows.get(300), weekly=windows.get(10080))
            if usage.five_hour is None and usage.weekly is None:
                return SourceResult(error=f"{self.name}: no usage windows")
            return SourceResult(usage={"codex": usage})
        except Exception as error:
            return SourceResult(error=f"{self.name}: {type(error).__name__}")


def create(cfg) -> CodexUsageSource:
    source = CodexUsageSource()
    source.start()
    return source
