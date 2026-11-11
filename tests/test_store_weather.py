import httpx

from cube.sources.weather import WeatherSource
from cube.store import Store


def test_store_survives_restart(tmp_path):
    Store(tmp_path / "state.json").set("figma_seen", ["c1"])
    assert Store(tmp_path / "state.json").get("figma_seen") == ["c1"]
    assert Store(tmp_path / "missing.json").get("x", 7) == 7


def test_weather_parses_open_meteo():
    body = {"current": {"temperature_2m": 28.4, "weather_code": 61}}
    src = WeatherSource(12.2, 109.2, transport=httpx.MockTransport(lambda r: httpx.Response(200, json=body)))
    res = src.poll()
    assert res.error is None
    assert res.weather.temp_c == 28.4 and res.weather.code == 61
    assert res.weather.label_ru == "Дождь"


def test_weather_error_does_not_raise():
    def down(req):
        raise httpx.ConnectError("offline")

    res = WeatherSource(12.2, 109.2, transport=httpx.MockTransport(down)).poll()
    assert res.weather is None and res.error


def test_weather_error_hides_url_and_coordinates():
    res = WeatherSource(12.2388, 109.1967, transport=httpx.MockTransport(lambda r: httpx.Response(503))).poll()
    assert res.error == "weather: HTTP 503"
    assert "latitude" not in res.error and "open-meteo" not in res.error
