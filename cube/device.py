"""Общение с кубиком SmallTV-Ultra (родная прошивка, режим «фотоальбом»)."""
from __future__ import annotations

import http.client
import re
import time
from typing import Literal, Optional

import httpx

OWN_PREFIX = "cube-"  # трогаем только свои файлы, чужие картинки пользователя не удаляем


class CubeOffline(Exception):
    pass


class _StdlibTransport(httpx.BaseTransport):
    """Прошивка шлёт Content-Length дважды (/filelist, /doUpload), иногда с разными числами;
    h11 такой ответ отвергает, а http.client терпит."""

    def __init__(self, timeout: float):
        self._timeout = timeout

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        conn = http.client.HTTPConnection(request.url.host, request.url.port, timeout=self._timeout)
        try:
            # close: тело кончается обрывом, а не по Content-Length, которому нельзя верить
            headers = {**request.headers, "Connection": "close"}
            conn.request(request.method, request.url.raw_path.decode(), request.read(), headers)
            r = conn.getresponse()
            try:
                body = r.read()
            except http.client.IncompleteRead as e:  # первый Content-Length больше настоящего
                body = e.partial
            return httpx.Response(r.status, headers=r.getheaders(), content=body)
        except (OSError, http.client.HTTPException) as e:  # отказ, таймаут, обрыв
            raise httpx.TransportError(str(e)) from e
        finally:
            conn.close()


class CubeClient:
    def __init__(self, host: str, timeout: float = 5.0, transport: Optional[httpx.BaseTransport] = None):
        self._http = httpx.Client(
            base_url=f"http://{host}", timeout=timeout, transport=transport or _StdlibTransport(timeout)
        )
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
        for name in set(re.findall(rf"(?<![\w-]){OWN_PREFIX}\d+\.(?:jpg|gif)(?![\w.-])", listing)):
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
