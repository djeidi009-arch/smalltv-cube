import httpx

from cube.model import Usage
from cube.sources import codex_usage
from cube.sources.opencode_usage import OpenCodeUsageSource


def test_codex_uses_shared_bucket_and_maps_by_window_duration(monkeypatch):
    monkeypatch.setattr(codex_usage, "read_limits", lambda: {
        "rateLimits": {"primary": {"windowDurationMins": 300, "usedPercent": 99}},
        "rateLimitsByLimitId": {"codex": {
            "primary": {"windowDurationMins": 10080, "usedPercent": 36},
            "secondary": None,
        }},
    })

    result = codex_usage.CodexUsageSource().fetch()
    assert result.usage == {"codex": Usage(weekly=36)}


def test_opencode_preserves_zero_and_missing_window():
    def api(request):
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(200, json={"usage": {"rolling": {"percent": 0}, "weekly": None}})

    source = OpenCodeUsageSource(token=lambda: "test-key", transport=httpx.MockTransport(api))
    assert source.fetch().usage == {"opencode": Usage(five_hour=0)}


def test_opencode_errors_omit_credentials_and_response():
    source = OpenCodeUsageSource(
        token=lambda: "test-key",
        transport=httpx.MockTransport(lambda _: httpx.Response(401, text="test-key")),
    )
    result = source.fetch()
    assert result.usage == {}
    assert result.error == "opencode_usage: HTTP 401"
