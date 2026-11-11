import http.server
import socket
import threading

import httpx
import pytest

from cube.device import CubeClient, CubeOffline


class FakeCube:
    """Кубик в памяти: принимает загрузки, помнит показанное и файлы."""

    def __init__(self, files=("ezgif-1.jpg",)):
        self.files = set(files)
        self.shown = None
        self.calls = []

    def __call__(self, req: httpx.Request) -> httpx.Response:
        self.calls.append((req.method, req.url.path, dict(req.url.params)))
        p, q = req.url.path, req.url.params
        if p == "/doUpload":
            name = req.content.split(b'filename="')[1].split(b'"')[0].decode()
            self.files.add(name)
        elif p == "/set" and "img" in q:
            self.shown = q["img"]
        elif p == "/delete":
            self.files.discard(q["file"].rsplit("/", 1)[1])
        elif p == "/filelist":
            rows = "".join(f"<tr><td>{f}</td></tr>" for f in sorted(self.files))
            return httpx.Response(200, text=f"<table>{rows}</table>")
        return httpx.Response(200, text="OK")


def test_show_replaces_own_file_and_keeps_foreign():
    cube = FakeCube(files=("ezgif-1.jpg", "cube-1731300000000.jpg"))
    c = CubeClient("cube.local", transport=httpx.MockTransport(cube))
    c.prepare()
    assert "cube-1731300000000.jpg" not in cube.files  # остатки прошлого запуска убраны
    c.show(b"one", "jpg")
    first = cube.shown
    c.show(b"two", "gif")
    own = [f for f in cube.files if f.startswith("cube-")]
    assert len(own) == 1 and own[0].endswith(".gif")
    assert cube.shown == "/image/" + own[0] != first
    assert "ezgif-1.jpg" in cube.files


def test_offline_raises_cube_offline():
    def down(req):
        raise httpx.ConnectError("no route")

    c = CubeClient("cube.local", transport=httpx.MockTransport(down))
    assert c.is_online() is False
    with pytest.raises(CubeOffline):
        c.show(b"x", "jpg")


def test_prepare_deletes_only_own_numbered_frames():
    foreign = {"cube-photo.jpg", "mycube-1.jpg", "my-cube-2.gif", "cube-3.jpg.bak", "ezgif-1.jpg"}
    cube = FakeCube(files=foreign | {"cube-17.gif"})
    CubeClient("cube.local", transport=httpx.MockTransport(cube)).prepare()
    assert cube.files == foreign
    assert [q["file"] for _, path, q in cube.calls if path == "/delete"] == ["/image/cube-17.gif"]


class _DoubleLengthHandler(http.server.BaseHTTPRequestHandler):
    """Как прошивка Ultra-V9.0.51 на /filelist и /doUpload: Content-Length дважды."""

    extra = 0  # насколько врёт: + — второй больше, - — первый больше

    def _reply(self):
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        body = b"<table><tr><td>cube-5.jpg</td></tr></table>" if self.path.startswith("/filelist") else b"OK"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body) + max(-self.extra, 0)))
        self.send_header("Content-Length", str(len(body) + max(self.extra, 0)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = _reply

    def log_message(self, *args):
        pass


@pytest.mark.parametrize("extra", [0, 7, -7])
def test_duplicate_content_length_is_not_offline(extra):
    handler = type("H", (_DoubleLengthHandler,), {"extra": extra})
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        c = CubeClient(f"127.0.0.1:{srv.server_port}")
        assert c.is_online()
        c.prepare()
        c.show(b"one", "jpg")
        c.show(b"two", "gif")
    finally:
        srv.shutdown()


def test_refused_and_silent_cube_is_offline():
    with socket.socket() as s:  # порт, который никто не слушает
        s.bind(("127.0.0.1", 0))
        refused = s.getsockname()[1]
    with pytest.raises(CubeOffline):
        CubeClient(f"127.0.0.1:{refused}").show(b"x", "jpg")
    with socket.socket() as silent:  # принимает соединение, но не отвечает
        silent.bind(("127.0.0.1", 0))
        silent.listen()
        with pytest.raises(CubeOffline):
            CubeClient(f"127.0.0.1:{silent.getsockname()[1]}", timeout=0.3).show(b"x", "jpg")
