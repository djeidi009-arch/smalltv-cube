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
    cube = FakeCube(files=("ezgif-1.jpg", "cube-old.jpg"))
    c = CubeClient("cube.local", transport=httpx.MockTransport(cube))
    c.prepare()
    assert "cube-old.jpg" not in cube.files  # остатки прошлого запуска убраны
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
