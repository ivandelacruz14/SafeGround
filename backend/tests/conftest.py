import re

import pytest
from werkzeug.security import generate_password_hash

from tests import spatial_sqlite  # noqa: F401
from app import create_app, mailer
from app.cli import MODES, ROLES
from app.extensions import db
from app.models import DataSource, Role, RouteStop, TransportMode, User, UserPreference

PASSWORD = "correct-horse-battery"


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        for n, d in ROLES:
            db.session.add(Role(name=n, description=d))
        for i, (c, n, col) in enumerate(MODES):
            db.session.add(TransportMode(code=c, name=n, color=col, sort_order=i))
        db.session.add(DataSource(code="demo", name="Demo", kind="manual", access_status="manual_only"))
        db.session.commit()
        mailer.OUTBOX.clear()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def make_user(email, role="user", status="active"):
    u = User(email=email, display_name="Test User", role=Role.query.filter_by(name=role).one(),
             password_hash=generate_password_hash(PASSWORD), status=status)
    u.preferences = UserPreference()
    db.session.add(u)
    db.session.commit()
    return u


def login(client, email, password=PASSWORD):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.get_json()
    return {"Authorization": f"Bearer {r.get_json()['access_token']}"}


@pytest.fixture()
def user_headers(app, client):
    make_user("user@example.com")
    return login(client, "user@example.com")


@pytest.fixture()
def admin_headers(app, client):
    make_user("admin@example.com", role="admin")
    return login(client, "admin@example.com")


@pytest.fixture()
def demo_stops(app):
    src = DataSource.query.filter_by(code="demo").one()
    for name, lat, lng in [("Inside", 14.60, 121.00), ("Outside", 10.30, 123.90)]:
        db.session.add(RouteStop(name=name, location={"lat": lat, "lng": lng},
                                 verification_status="demo", data_source_id=src.id))
    db.session.commit()


def verification_token():
    return re.search(r"token=([^\s]+)", mailer.OUTBOX[-1]["body"]).group(1)
