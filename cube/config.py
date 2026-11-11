"""Настройки из .env. Значения секретов никуда не печатаются."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    cube_host: str
    figma_token: Optional[str]
    figma_project_id: str
    telegram_api_id: Optional[int]
    telegram_api_hash: Optional[str]
    lat: float
    lon: float
    tz: str
    data_dir: Path


def load_config() -> Config:
    load_dotenv(ROOT / ".env")
    env = lambda k, d=None: os.environ.get(k) or d  # noqa: E731 — пустая строка = не задано
    api_id = env("TELEGRAM_API_ID")
    data_dir = Path(env("CUBE_DATA_DIR", "~/Library/Application Support/smalltv-cube")).expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)
    return Config(
        cube_host=env("CUBE_HOST", "192.168.100.54"),
        figma_token=env("FIGMA_TOKEN"),
        figma_project_id=env("FIGMA_PROJECT_ID", "450204584"),
        telegram_api_id=int(api_id) if api_id else None,
        telegram_api_hash=env("TELEGRAM_API_HASH"),
        lat=float(env("CUBE_LAT", "12.2388")),
        lon=float(env("CUBE_LON", "109.1967")),
        tz=env("CUBE_TZ", "Asia/Ho_Chi_Minh"),
        data_dir=data_dir,
    )
