import httpx

from cube.model import Usage
from cube.sources.claude_usage import ClaudeUsageSource
from cube.store import Store

RESET = "2026-11-11T11:40:00+00:00"  # 18:40 в Нячанге


def make(tmp_path, answers, token=lambda: "secret-tok"):
    pcts = iter(answers)

    def api(req):
        assert req.headers["Authorization"] == "Bearer secret-tok"
        assert req.headers["anthropic-beta"] == "oauth-2025-04-20"
        pct, reset = next(pcts)
        return httpx.Response(200, json={
            "five_hour": {"utilization": pct, "resets_at": reset},
            "seven_day": {"utilization": 17},
        })

    return ClaudeUsageSource(Store(tmp_path / "usage.json"), "Asia/Ho_Chi_Minh", token=token,
                             transport=httpx.MockTransport(api))


def test_usage_bar_and_one_card_per_threshold_per_window(tmp_path):
    src = make(tmp_path, [(42.0, RESET), (81.0, RESET), (85.0, RESET), (96.0, RESET),
                          (5.0, "2026-11-11T16:40:00+00:00"), (82.0, "2026-11-11T16:40:00+00:00")])
    r = src.fetch()
    assert r.usage == {"claude": Usage(42, 17)}
    assert r.notifications == []
    cards = [n for _ in range(5) for n in src.fetch().notifications]
    assert [(n.source, n.title, n.body) for n in cards] == [
        ("claude_limit", "Использовано 81%", "Лимит сбросится в 18:40"),
        ("claude_limit", "Использовано 96%", "Лимит сбросится в 18:40"),
        ("claude_limit", "Использовано 82%", "Лимит сбросится в 23:40"),  # новое окно — снова
    ]


def test_read_error_hides_bar_and_never_leaks_token(tmp_path):
    def broken():
        raise RuntimeError("secret-tok")

    for src in (make(tmp_path, [], token=broken),
                ClaudeUsageSource(Store(tmp_path / "u.json"), "UTC", token=lambda: "secret-tok",
                                  transport=httpx.MockTransport(lambda r: httpx.Response(401, text="secret-tok")))):
        r = src.fetch()
        assert not r.usage and r.error and "secret-tok" not in r.error
