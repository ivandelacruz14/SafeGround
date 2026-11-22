"""Configuration. All secrets come from environment variables (see .env.example)."""
import logging
import os
import secrets
from datetime import timedelta

log = logging.getLogger(__name__)


def _bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    # Access token travels in the Authorization header (kept in memory by the SPA).
    # Refresh token lives in an httpOnly cookie protected by a CSRF double-submit token.
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15")))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "14")))
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_REFRESH_COOKIE_PATH = "/api/v1/auth/"
    JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")
    JWT_COOKIE_SECURE = False

    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    TRUST_PROXY = _bool("TRUST_PROXY", False)

    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "300 per hour")
    RATELIMIT_ENABLED = True

    # Email. "console" logs the message instead of sending (development only).
    MAIL_BACKEND = os.getenv("MAIL_BACKEND", "console")
    MAIL_HOST = os.getenv("MAIL_HOST", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = _bool("MAIL_USE_TLS", True)
    MAIL_FROM = os.getenv("MAIL_FROM", "SafeRoute <no-reply@localhost>")
    EMAIL_TOKEN_MAX_AGE = 60 * 60 * 24  # seconds

    # Geocoding (Nominatim-compatible). Public nominatim.openstreetmap.org has a strict
    # usage policy: identify your app, max 1 req/s, no autocomplete. Self-host for production.
    GEOCODER_URL = os.getenv("GEOCODER_URL", "https://nominatim.openstreetmap.org/search")
    GEOCODER_USER_AGENT = os.getenv("GEOCODER_USER_AGENT", "SafeRoute/0.1 (set-contact-email)")
    GEOCODER_TIMEOUT = float(os.getenv("GEOCODER_TIMEOUT", "6"))
    GEOCODER_CACHE_SECONDS = int(os.getenv("GEOCODER_CACHE_SECONDS", "3600"))

    MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # request cap (uploads arrive in Phase 4)
    MAX_SAVED_PLACES = 50


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret-with-enough-length-for-hs256"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    RATELIMIT_ENABLED = False
    JWT_COOKIE_CSRF_PROTECT = True
    MAIL_BACKEND = "memory"


class ProductionConfig(Config):
    DEBUG = False
    JWT_COOKIE_SECURE = True


def load_config(name=None):
    name = (name or os.getenv("APP_ENV", "development")).lower()
    return {"development": DevelopmentConfig, "testing": TestingConfig,
            "production": ProductionConfig}[name]


def finalize(app):
    """Fail fast on missing/weak secrets in production; use ephemeral keys in development."""
    for key in ("SECRET_KEY", "JWT_SECRET_KEY"):
        val = app.config.get(key)
        weak = (not val) or val.startswith("change-me") or len(val) < 32
        if not weak:
            continue
        if app.config.get("DEBUG") or app.config.get("TESTING"):
            app.config[key] = val or secrets.token_urlsafe(48)
            if not val:
                log.warning("%s not set; using an ephemeral key (sessions reset on restart).", key)
        else:
            raise RuntimeError(f"{key} must be set to a random value of 32+ characters in production.")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL is not set. See .env.example.")
