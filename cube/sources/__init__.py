"""Сборка источников. Погода есть всегда; остальные — модули таска 02, если они есть."""
from __future__ import annotations

import importlib
from typing import List

from cube.config import Config
from cube.sources.base import Source
from cube.sources.weather import WeatherSource

OPTIONAL = ("figma", "telegram", "claude_usage", "claude_waiting")


def build_sources(cfg: Config) -> List[Source]:
    sources: List[Source] = [WeatherSource(cfg.lat, cfg.lon)]
    for name in OPTIONAL:
        try:
            mod = importlib.import_module(f"cube.sources.{name}")
        except ModuleNotFoundError as e:
            if e.name != f"cube.sources.{name}":
                raise
            continue
        src = mod.create(cfg)  # контракт модуля: create(cfg) -> Source | None (None — нет ключей в .env)
        if src is not None:
            sources.append(src)
    return sources
