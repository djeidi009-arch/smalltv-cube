"""Общение с кубиком SmallTV-Ultra (родная прошивка, режим «фотоальбом»)."""
from __future__ import annotations

import re
import time
from typing import Literal, Optional

import httpx

OWN_PREFIX = "cube-"  # трогаем только свои файлы, чужие картинки пользователя не удаляем


class CubeOffline(Exception):
    pass


class CubeClient:
    def __init__(self, host: str, timeout: float = 5.0, transport: Optional[httpx.BaseTransport] = None):
        self._http = httpx.Client(base_url=f"http://{host}", timeout=timeout, transport=transport)
        self._current: Optional[str] = None

    def _get(self, path: str, **params) -> httpx.Response:
        try:
            r = self._http.get(path, params=params)
            r.raise_for_status()
            return r
        except httpx.HTTPError as e:
            raise CubeOffline(str(e)) from e

    def is_online(self) -> bool:
        try:
            self._get("/v.json")
            return True
        except CubeOffline:
            return False

    def prepare(self) -> None:
        self._get("/set", theme=3)
        self._get("/set", i_i=60, autoplay=0)
        # свои кадры, оставшиеся от прошлого запуска, иначе память кубика забьётся
        listing = self._get("/filelist", dir="/image/").text
        for name in set(re.findall(rf"{OWN_PREFIX}[\w.-]+\.(?:jpg|gif)", listing)):
            self._get("/delete", file=f"/image/{name}")
        self._current = None

    def show(self, data: bytes, ext: Literal["jpg", "gif"]) -> None:
        name = f"{OWN_PREFIX}{time.time_ns() // 1_000_000}.{ext}"
        mime = "image/gif" if ext == "gif" else "image/jpeg"
        try:
            r = self._http.post("/doUpload", params={"dir": "/image/"}, files={"image": (name, data, mime)})
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise CubeOffline(str(e)) from e
        self._get("/set", img=f"/image/{name}")
        previous, self._current = self._current, name
        if previous and previous != name:
            self._get("/delete", file=f"/image/{previous}")
