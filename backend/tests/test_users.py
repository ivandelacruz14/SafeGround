from tests.conftest import login, make_user


def test_preferences_roundtrip_and_validation(client, user_headers):
    r = client.put("/api/v1/users/me/preferences", headers=user_headers,
                   json={"max_walk_meters": 1200, "default_mode_codes": ["bus", "lrt"], "avoid_flood_risk": False})
    assert r.status_code == 200
    got = client.get("/api/v1/users/me/preferences", headers=user_headers).get_json()
    assert got["max_walk_meters"] == 1200 and got["default_mode_codes"] == ["bus", "lrt"]
    assert client.put("/api/v1/users/me/preferences", headers=user_headers,
                      json={"max_walk_meters": 5}).status_code == 422
    assert client.put("/api/v1/users/me/preferences", headers=user_headers,
                      json={"default_mode_codes": ["hoverboard"]}).status_code == 422


def test_saved_places_crud_and_isolation(client, user_headers, app):
    r = client.post("/api/v1/users/me/saved-places", headers=user_headers,
                    json={"label": "Home", "category": "home", "lat": 14.6, "lng": 121.0})
    assert r.status_code == 201
    place = r.get_json()
    assert place["lat"] == 14.6 and place["lng"] == 121.0
    make_user("other@example.com")
    other = login(client, "other@example.com")
    assert client.get("/api/v1/users/me/saved-places", headers=other).get_json()["items"] == []
    assert client.delete(f"/api/v1/users/me/saved-places/{place['id']}", headers=other).status_code == 404
    assert client.delete(f"/api/v1/users/me/saved-places/{place['id']}", headers=user_headers).status_code == 204


def test_saved_place_rejects_bad_coordinates(client, user_headers):
    r = client.post("/api/v1/users/me/saved-places", headers=user_headers,
                    json={"label": "X", "lat": 123, "lng": 121})
    assert r.status_code == 422 and "lat" in r.get_json()["error"]["details"]


def test_change_password(client, user_headers, app):
    assert client.post("/api/v1/users/me/password", headers=user_headers,
                       json={"current_password": "wrong-password-x", "new_password": "another-long-pass"}).status_code == 403
    assert client.post("/api/v1/users/me/password", headers=user_headers,
                       json={"current_password": "correct-horse-battery",
                             "new_password": "another-long-pass"}).status_code == 200
    r = client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "another-long-pass"})
    assert r.status_code == 200
