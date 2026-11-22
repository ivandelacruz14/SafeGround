import re
from functools import wraps

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request

from .extensions import db
from .models import AuditLog, User


class ApiError(Exception):
    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


def error_response(status, code, message, details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def validate(data, rules):
    """rules: {field: {type, required, min, max, enum, email}} -> cleaned dict of present fields."""
    if not isinstance(data, dict):
        raise ApiError(400, "invalid_body", "Request body must be a JSON object.")
    errors, clean = {}, {}
    for name, r in rules.items():
        v = data.get(name)
        if isinstance(v, str):
            v = v.strip()
        if v is None or v == "":
            if r.get("required"):
                errors[name] = "This field is required."
            continue
        t = r.get("type", str)
        if t is float and isinstance(v, (int, float)) and not isinstance(v, bool):
            v = float(v)
        elif t is int and isinstance(v, bool):
            errors[name] = "Must be a whole number."
            continue
        elif not isinstance(v, t):
            errors[name] = f"Must be of type {t.__name__}."
            continue
        if t is str:
            if len(v) < r.get("min", 0):
                errors[name] = f"Must be at least {r['min']} characters."
                continue
            if len(v) > r.get("max", 255):
                errors[name] = f"Must be at most {r.get('max', 255)} characters."
                continue
            if r.get("email") and not EMAIL_RE.match(v):
                errors[name] = "Enter a valid email address."
                continue
        if t in (int, float):
            if "min" in r and v < r["min"] or "max" in r and v > r["max"]:
                errors[name] = f"Must be between {r.get('min')} and {r.get('max')}."
                continue
        if "enum" in r and v not in r["enum"]:
            errors[name] = f"Must be one of: {', '.join(map(str, r['enum']))}."
            continue
        clean[name] = v
    if errors:
        raise ApiError(422, "validation_error", "Some fields are invalid.", errors)
    return clean


def paginate(query, serializer, default=20, maximum=100):
    from flask import request as rq
    page = max(rq.args.get("page", 1, type=int) or 1, 1)
    per = min(max(rq.args.get("per_page", default, type=int) or default, 1), maximum)
    p = db.paginate(query, page=page, per_page=per, error_out=False)
    return {"items": [serializer(i) for i in p.items], "page": page, "per_page": per,
            "total": p.total, "pages": p.pages}


def audit(action, entity_type=None, entity_id=None, details=None, actor_id=None):
    db.session.add(AuditLog(actor_id=actor_id, action=action, entity_type=entity_type,
                            entity_id=str(entity_id) if entity_id is not None else None,
                            details=details, ip_address=request.remote_addr))


def current_user():
    """Authenticated user, re-read from the DB so suspensions apply immediately."""
    user = db.session.get(User, int(get_jwt_identity()))
    if not user or not user.is_active:
        raise ApiError(401, "account_inactive", "This account is not active.")
    return user


def auth_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*a, **kw):
        return fn(current_user(), *a, **kw)
    return wrapper


def roles_required(*roles):
    def deco(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*a, **kw):
            user = current_user()
            if user.role.name not in roles:
                raise ApiError(403, "forbidden", "You do not have permission to do this.")
            return fn(user, *a, **kw)
        return wrapper
    return deco
