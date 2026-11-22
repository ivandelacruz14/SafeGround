from app import mailer
from app.models import User
from tests.conftest import PASSWORD, login, make_user, verification_token


def reg(client, email="new@example.com", password=PASSWORD):
    return client.post("/api/v1/auth/register",
                       json={"email": email, "password": password, "display_name": "New Person"})


def test_register_sends_verification_and_verifies(client, app):
    assert reg(client).status_code == 201
    assert len(mailer.OUTBOX) == 1
    assert not User.query.filter_by(email="new@example.com").one().email_verified_at
    r = client.post("/api/v1/auth/verify-email", json={"token": verification_token()})
    assert r.status_code == 200
    assert User.query.filter_by(email="new@example.com").one().email_verified_at


def test_register_duplicate_is_indistinguishable(client, app):
    reg(client)
    r = reg(client)
    assert r.status_code == 201
    assert len(mailer.OUTBOX) == 1  # no second email, no account probing


def test_register_validation(client, app):
    assert reg(client, password="short").status_code == 422
    assert reg(client, email="not-an-email").status_code == 422
    assert reg(client, password="1234567890").status_code == 422


def test_verify_rejects_bad_token(client, app):
    r = client.post("/api/v1/auth/verify-email", json={"token": "garbage"})
    assert r.status_code == 400 and r.get_json()["error"]["code"] == "token_invalid"


def test_login_success_sets_refresh_cookie(client, app):
    make_user("a@example.com")
    r = client.post("/api/v1/auth/login", json={"email": "A@example.com", "password": PASSWORD})
    assert r.status_code == 200
    assert r.get_json()["user"]["role"] == "user"
    cookie = next(c for c in r.headers.getlist("Set-Cookie") if c.startswith("refresh_token_cookie"))
    assert "HttpOnly" in cookie


def test_login_failures_are_generic(client, app):
    make_user("a@example.com")
    bad_pw = client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "nope-nope-nope"})
    no_user = client.post("/api/v1/auth/login", json={"email": "x@example.com", "password": "nope-nope-nope"})
    assert bad_pw.status_code == no_user.status_code == 401
    assert bad_pw.get_json() == no_user.get_json()


def test_suspended_user_cannot_login_or_use_existing_token(client, app):
    u = make_user("a@example.com")
    headers = login(client, "a@example.com")
    u.status = "suspended"
    from app.extensions import db
    db.session.commit()
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": PASSWORD}).status_code == 403


def test_refresh_requires_csrf_header(client, app):
    make_user("a@example.com")
    client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": PASSWORD})
    assert client.post("/api/v1/auth/refresh").status_code == 401
    csrf = client.get_cookie("csrf_refresh_token").value
    r = client.post("/api/v1/auth/refresh", headers={"X-CSRF-TOKEN": csrf})
    assert r.status_code == 200 and "access_token" in r.get_json()


def test_protected_route_without_token(client, app):
    r = client.get("/api/v1/users/me")
    assert r.status_code == 401 and r.get_json()["error"]["code"] == "unauthorized"
