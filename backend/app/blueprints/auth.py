from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (create_access_token, create_refresh_token, get_jwt_identity,
                                jwt_required, set_refresh_cookies, unset_jwt_cookies)
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db, limiter
from ..mailer import send_mail
from ..models import Role, User, UserPreference, utcnow
from ..utils import ApiError, audit, validate

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
_DUMMY_HASH = generate_password_hash("not-a-real-password")


def check_password_strength(pw):
    if len(pw) < 10:
        raise ApiError(422, "validation_error", "Some fields are invalid.",
                       {"password": "Use at least 10 characters."})
    if pw.isdigit() or pw.lower() in {"password123", "1234567890"}:
        raise ApiError(422, "validation_error", "Some fields are invalid.",
                       {"password": "Choose a less guessable password."})


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="email-verify")


def send_verification(user):
    token = _serializer().dumps({"uid": user.id, "email": user.email})
    link = f"{current_app.config['FRONTEND_URL']}/verify-email?token={token}"
    send_mail(user.email, "Verify your SafeRoute email",
              f"Hi {user.display_name},\n\nConfirm your email to finish setting up SafeRoute:\n{link}\n\n"
              "The link expires in 24 hours. If you did not sign up, ignore this message.")


def _issue(user):
    claims = {"role": user.role.name}
    resp = jsonify({"access_token": create_access_token(str(user.id), additional_claims=claims),
                    "user": user.to_dict()})
    set_refresh_cookies(resp, create_refresh_token(str(user.id), additional_claims=claims))
    return resp


@bp.post("/register")
@limiter.limit("5 per minute; 30 per hour")
def register():
    d = validate(request.get_json(silent=True), {
        "email": {"required": True, "email": True, "max": 254},
        "password": {"required": True, "min": 1, "max": 128},
        "display_name": {"required": True, "min": 2, "max": 80}})
    check_password_strength(d["password"])
    email = d["email"].lower()
    # Same response whether or not the email exists, so registration cannot be used to probe accounts.
    if not User.query.filter_by(email=email).first():
        role = Role.query.filter_by(name="user").one()
        user = User(email=email, display_name=d["display_name"], role=role,
                    password_hash=generate_password_hash(d["password"]))
        user.preferences = UserPreference()
        db.session.add(user)
        db.session.flush()
        audit("user.register", "user", user.id, actor_id=user.id)
        db.session.commit()
        send_verification(user)
    return jsonify({"message": "If this email can be registered, a verification link has been sent."}), 201


@bp.post("/verify-email")
@limiter.limit("20 per hour")
def verify_email():
    d = validate(request.get_json(silent=True), {"token": {"required": True, "max": 1024}})
    try:
        data = _serializer().loads(d["token"], max_age=current_app.config["EMAIL_TOKEN_MAX_AGE"])
    except SignatureExpired:
        raise ApiError(400, "token_expired", "This link has expired. Request a new verification email.")
    except BadSignature:
        raise ApiError(400, "token_invalid", "This verification link is not valid.")
    user = db.session.get(User, data["uid"])
    if not user or user.email != data["email"]:
        raise ApiError(400, "token_invalid", "This verification link is not valid.")
    if not user.email_verified_at:
        user.email_verified_at = utcnow()
        audit("user.email_verified", "user", user.id, actor_id=user.id)
        db.session.commit()
    return jsonify({"message": "Email verified."})


@bp.post("/resend-verification")
@limiter.limit("3 per hour")
def resend_verification():
    d = validate(request.get_json(silent=True), {"email": {"required": True, "email": True}})
    user = User.query.filter_by(email=d["email"].lower()).first()
    if user and user.is_active and not user.email_verified_at:
        send_verification(user)
    return jsonify({"message": "If the account needs verification, a new link has been sent."})


@bp.post("/login")
@limiter.limit("10 per minute; 60 per hour")
def login():
    d = validate(request.get_json(silent=True), {
        "email": {"required": True, "max": 254}, "password": {"required": True, "max": 128}})
    user = User.query.filter_by(email=d["email"].lower()).first()
    ok = check_password_hash(user.password_hash if user else _DUMMY_HASH, d["password"])
    if not (user and ok):
        raise ApiError(401, "invalid_credentials", "Invalid email or password.")
    if not user.is_active:
        raise ApiError(403, "account_suspended", "This account has been suspended.")
    user.last_login_at = utcnow()
    audit("user.login", "user", user.id, actor_id=user.id)
    db.session.commit()
    return _issue(user)


@bp.post("/refresh")
@jwt_required(refresh=True, locations=["cookies"])
def refresh():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user or not user.is_active:
        raise ApiError(401, "account_inactive", "This account is not active.")
    return _issue(user)


@bp.post("/logout")
def logout():
    resp = jsonify({"message": "Signed out."})
    unset_jwt_cookies(resp)
    return resp
