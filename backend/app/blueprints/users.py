from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import SavedPlace, TransportMode, UserPreference
from ..utils import ApiError, audit, auth_required, validate
from .auth import check_password_strength

bp = Blueprint("users", __name__, url_prefix="/api/v1/users/me")


@bp.get("")
@auth_required
def me(user):
    return jsonify(user.to_dict())


@bp.patch("")
@auth_required
def update_me(user):
    d = validate(request.get_json(silent=True), {"display_name": {"min": 2, "max": 80}})
    if "display_name" in d:
        user.display_name = d["display_name"]
    db.session.commit()
    return jsonify(user.to_dict())


@bp.post("/password")
@auth_required
def change_password(user):
    d = validate(request.get_json(silent=True), {
        "current_password": {"required": True, "max": 128}, "new_password": {"required": True, "max": 128}})
    if not check_password_hash(user.password_hash, d["current_password"]):
        raise ApiError(403, "invalid_credentials", "Current password is incorrect.")
    check_password_strength(d["new_password"])
    user.password_hash = generate_password_hash(d["new_password"])
    audit("user.password_changed", "user", user.id, actor_id=user.id)
    db.session.commit()
    return jsonify({"message": "Password updated."})


def _prefs(user):
    if not user.preferences:
        user.preferences = UserPreference()
        db.session.flush()
    return user.preferences


@bp.get("/preferences")
@auth_required
def get_preferences(user):
    p = _prefs(user)
    db.session.commit()
    return jsonify(p.to_dict())


@bp.put("/preferences")
@auth_required
def put_preferences(user):
    d = validate(request.get_json(silent=True), {
        "default_mode_codes": {"type": list}, "max_walk_meters": {"type": int, "min": 100, "max": 5000},
        "avoid_flood_risk": {"type": bool}, "language": {"enum": ["en", "fil"]},
        "notify_flood": {"type": bool}, "notify_closures": {"type": bool},
        "notify_disruptions": {"type": bool}})
    if "default_mode_codes" in d:
        known = {m.code for m in TransportMode.query.all()}
        bad = [c for c in d["default_mode_codes"] if c not in known]
        if bad:
            raise ApiError(422, "validation_error", "Some fields are invalid.",
                           {"default_mode_codes": f"Unknown modes: {', '.join(map(str, bad))}."})
    p = _prefs(user)
    for k, v in d.items():
        setattr(p, k, v)
    db.session.commit()
    return jsonify(p.to_dict())


_PLACE = {"label": {"required": True, "min": 1, "max": 80},
          "category": {"enum": ["home", "work", "other"]}, "address": {"max": 255},
          "lat": {"required": True, "type": float, "min": -90, "max": 90},
          "lng": {"required": True, "type": float, "min": -180, "max": 180}}


@bp.get("/saved-places")
@auth_required
def list_places(user):
    places = SavedPlace.query.filter_by(user_id=user.id).order_by(SavedPlace.created_at.desc()).all()
    return jsonify({"items": [p.to_dict() for p in places]})


@bp.post("/saved-places")
@auth_required
def create_place(user):
    d = validate(request.get_json(silent=True), _PLACE)
    if SavedPlace.query.filter_by(user_id=user.id).count() >= current_app.config["MAX_SAVED_PLACES"]:
        raise ApiError(409, "limit_reached", "You have reached the saved places limit.")
    place = SavedPlace(user_id=user.id, label=d["label"], category=d.get("category", "other"),
                       address=d.get("address"), location={"lat": d["lat"], "lng": d["lng"]})
    db.session.add(place)
    db.session.commit()
    return jsonify(place.to_dict()), 201


@bp.delete("/saved-places/<int:place_id>")
@auth_required
def delete_place(user, place_id):
    place = SavedPlace.query.filter_by(id=place_id, user_id=user.id).first()
    if not place:  # also covers other users' places: no existence leak
        raise ApiError(404, "not_found", "Saved place not found.")
    db.session.delete(place)
    db.session.commit()
    return "", 204
