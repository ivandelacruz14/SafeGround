import requests

from app.blueprints import geocode


def test_modes_seeded(client, app):
    items = client.get("/api/v1/transport/modes").get_json()["items"]
    assert {"jeepney", "bus", "mrt", "lrt", "uv_express", "tricycle", "modern_jeepney"} <= {m["code"] for m in items}


def test_stops_empty_is_not_an_error(client, app):
    r = client.get("/api/v1/transport/stops").get_json()
    assert r["items"] == [] and r["total"] == 0


def test_stops_bbox_filter_and_labels(client, demo_stops):
    r = client.get("/api/v1/transport/stops?bbox=120.9,14.5,121.1,14.7").get_json()
    assert [s["name"] for s in r["items"]] == ["Inside"]
    assert r["items"][0]["verification_status"] == "demo" and r["items"][0]["source"] == "demo"


def test_bbox_validation(client, app):
    assert client.get("/api/v1/transport/stops?bbox=1,2,3").status_code == 400
    assert client.get("/api/v1/transport/stops?bbox=110,5,130,20").get_json()["error"]["code"] == "bbox_too_large"


def test_layers_report_unavailable_data_honestly(client, app):
    layers = {l["id"]: l for l in client.get("/api/v1/map/layers").get_json()["items"]}
    assert layers["transport_stops"]["status"] == "no_data"
    for fid in ("flood_official", "flood_verified", "flood_unverified", "flood_historical", "road_reports"):
        assert layers[fid]["status"] == "planned"


def test_layers_available_once_stops_exist(client, demo_stops):
    layers = {l["id"]: l for l in client.get("/api/v1/map/layers").get_json()["items"]}
    assert layers["transport_stops"]["status"] == "available" and layers["transport_stops"]["count"] == 2


def test_geocoder_unavailable_returns_503(client, monkeypatch):
    geocode._cache.clear()

    def boom(*a, **k):
        raise requests.ConnectionError("down")
    monkeypatch.setattr(geocode.requests, "get", boom)
    r = client.get("/api/v1/geocode/search?q=quezon city")
    assert r.status_code == 503 and r.get_json()["error"]["code"] == "geocoder_unavailable"


def test_geocoder_success_and_cache(client, monkeypatch):
    geocode._cache.clear()
    calls = []

    class Resp:
        def raise_for_status(self): pass
        def json(self): return [{"display_name": "Rizal Park, Manila", "lat": "14.58", "lon": "120.98"}]

    monkeypatch.setattr(geocode.requests, "get", lambda *a, **k: calls.append(1) or Resp())
    for _ in range(2):
        r = client.get("/api/v1/geocode/search?q=rizal park").get_json()
    assert r["items"][0]["lat"] == 14.58 and "OpenStreetMap" in r["source"]["attribution"] and len(calls) == 1
    assert client.get("/api/v1/geocode/search?q=ab").status_code == 422


def test_health_and_docs(client, app):
    assert client.get("/api/v1/health").get_json()["database"] == "ok"
    assert b"openapi" in client.get("/api/v1/openapi.yaml").data
