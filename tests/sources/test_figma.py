import httpx

from cube.sources.figma import FigmaSource
from cube.store import Store


class FakeFigma:
    def __init__(self):
        self.files = [{"key": "k1", "name": "Лендинг v3"}]
        self.comments = {"k1": [self.c("old", "u1", "Анна", "Старый")]}

    @staticmethod
    def c(cid, uid, handle, msg, at="2026-11-11T09:00:00Z"):
        return {"id": cid, "message": msg, "user": {"id": uid, "handle": handle}, "created_at": at}

    def __call__(self, req: httpx.Request):
        assert req.headers["X-Figma-Token"] == "tkn"
        p = req.url.path
        if p == "/v1/me":
            return httpx.Response(200, json={"id": "me", "handle": "Никита"})
        if p == "/v1/projects/450204584/files":
            return httpx.Response(200, json={"files": self.files})
        key = p.split("/")[3]
        return httpx.Response(200, json={"comments": self.comments.get(key, [])})


def make(tmp_path, api):
    return FigmaSource("tkn", "450204584", Store(tmp_path / "figma.json"), transport=httpx.MockTransport(api))


def test_only_new_foreign_comments_notify_and_new_files_are_picked_up(tmp_path):
    api = FakeFigma()
    src = make(tmp_path, api)
    assert src.fetch().notifications == []  # первый запуск: старое не показываем

    api.comments["k1"].append(api.c("c2", "u1", "Анна", "Давай кнопку заметнее\nи ещё", at="2099-01-01T00:00:00Z"))
    api.comments["k1"].append(api.c("c3", "me", "Никита", "Мой", at="2099-01-01T00:00:00Z"))
    api.files.append({"key": "k2", "name": "Онбординг"})
    api.comments["k2"] = [api.c("c4", "u2", "Олег", "Новый файл", at="2099-01-01T00:00:00Z")]
    got = src.fetch().notifications
    assert [(n.source, n.title, n.body) for n in got] == [
        ("figma", "Анна · Лендинг v3", "Давай кнопку заметнее"),
        ("figma", "Олег · Онбординг", "Новый файл"),
    ]
    assert src.fetch().notifications == []

    # после перезапуска уже показанное не повторяется
    assert make(tmp_path, api).fetch().notifications == []


def test_error_is_reported_without_token(tmp_path):
    res = make(tmp_path, lambda r: httpx.Response(403, json={"err": "no"})).fetch()
    assert res.error and "tkn" not in res.error and res.notifications == []
