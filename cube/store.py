"""Маленькое постоянное состояние в JSON (что уже показано)."""
from __future__ import annotations

import json
import os
from pathlib import Path


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        try:
            self._data = json.loads(self.path.read_text())
        except (OSError, ValueError):
            self._data = {}

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False))
        os.replace(tmp, self.path)  # атомарно: файл никогда не остаётся наполовину записанным
