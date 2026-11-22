import logging
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / "backend" / ".env")

from .config import finalize, load_config  # noqa: E402  (env must load first)
from .extensions import cors, db, jwt, limiter, migrate  # noqa: E402
from .utils import ApiError, error_response  # noqa: E402


def create_app(config_name=None):
    app = Flask(__name__)
    app.config.from_object(load_config(config_name))
    finalize(app)
    logging.basicConfig(level=logging.DEBUG if app.debug else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if app.config["TRUST_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db, directory="migrations")
    jwt.init_app(app)
    limiter.init_app(app)
    if app.config["CORS_ORIGINS"]:
        cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
                      supports_credentials=True)

    from . import models  # noqa: F401  (register tables)
    from .blueprints import admin, auth, geocode, map, system, transport, users
    for m in (system, auth, users, transport, map, geocode, admin):
        app.register_blueprint(m.bp)

    register_errors(app)
    from .cli import register_cli
    register_cli(app)

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if request_is_api():
            resp.headers.setdefault("Cache-Control", "no-store")
        return resp

    return app


def request_is_api():
    from flask import request
    return request.path.startswith("/api/") and not request.path.startswith("/api/v1/docs")


def register_errors(app):
    @app.errorhandler(ApiError)
    def api_error(e):
        return error_response(e.status, e.code, e.message, e.details)

    @app.errorhandler(HTTPException)
    def http_error(e):
        code = {404: "not_found", 405: "method_not_allowed", 413: "payload_too_large",
                429: "rate_limited"}.get(e.code, "http_error")
        msg = "Too many requests. Try again shortly." if e.code == 429 else e.description
        return error_response(e.code, code, msg)

    @app.errorhandler(Exception)
    def unexpected(e):
        app.logger.exception("Unhandled error")
        db.session.rollback()
        return error_response(500, "server_error", "Something went wrong on our side.")

    for loader, status, code, msg in (
            (jwt.unauthorized_loader, 401, "unauthorized", "Sign in to continue."),
            (jwt.expired_token_loader, 401, "token_expired", "Your session expired. Sign in again."),
            (jwt.invalid_token_loader, 401, "token_invalid", "Your session is not valid. Sign in again.")):
        def make(s=status, c=code, m=msg):
            return lambda *a, **k: error_response(s, c, m)
        loader(make())
