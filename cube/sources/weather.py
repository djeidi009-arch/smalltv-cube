"""Погода из Open-Meteo (без ключа)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import httpx

from cube.model import Weather
from cube.sources.base import SourceResult

URL = "https://api.open-meteo.com/v1/forecast"

# коды WMO → подпись; иконку по тому же коду рисует render.weather_kind
LABELS = {0: "Ясно", 1: "Малооблачно", 2: "Облачно", 3: "Пасмурно", 45: "Туман", 48: "Туман"}
LABELS.update({c: "Морось" for c in (51, 53, 55, 56, 57)})
LABELS.update({c: "Дождь" for c in (61, 63, 65, 66, 67, 80, 81, 82)})
LABELS.update({c: "Ливень" for c in (65, 82)})
LABELS.update({c: "Снег" for c in (71, 73, 75, 77, 85, 86)})
LABELS.update({c: "Гроза" for c in (95, 96, 99)})


class WeatherSource:
    name = "weather"
    interval_s = 15 * 60

    def __init__(self, lat: float, lon: float, transport: Optional[httpx.BaseTransport] = None):
        self._params = {"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code"}
        self._http = httpx.Client(timeout=10, transport=transport)

    def poll(self) -> SourceResult:
        try:
            r = self._http.get(URL, params=self._params)
            r.raise_for_status()
            cur = r.json()["current"]
            code = int(cur["weather_code"])
            return SourceResult(weather=Weather(
                temp_c=float(cur["temperature_2m"]), code=code,
                label_ru=LABELS.get(code, "—"), fetched_at=datetime.now(timezone.utc),
            ))
        except httpx.HTTPStatusError as e:  # текст ошибки содержит URL с координатами — в лог не берём
            return SourceResult(error=f"weather: HTTP {e.response.status_code}")
        except Exception as e:  # источник никогда не роняет главный цикл
            return SourceResult(error=f"weather: {type(e).__name__}")
