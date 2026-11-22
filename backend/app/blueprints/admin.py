from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import AuditLog, DataSource, Role, User
from ..utils import ApiError, audit, paginate, roles_required, validate

bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


@bp.get("/users")
@roles_required("admin")
def list_users(actor):
    q = db.select(User).join(Role)
    if request.args.get("q"):
        like = f"%{request.args['q'][:80]}%"
        q = q.where(User.email.like(like) | User.display_name.like(like))
    if request.args.get("role"):
        q = q.where(Role.name == request.args["role"])
    if request.args.get("status"):
        q = q.where(User.status == request.args["status"])
    return jsonify(paginate(q.order_by(User.id.desc()), lambda u: u.to_dict()))


@bp.patch("/users/<int:user_id>")
@roles_required("admin")
def update_user(actor, user_id):
    d = validate(request.get_json(silent=True), {
        "role": {"enum": ["user", "moderator", "admin"]}, "status": {"enum": ["active", "suspended"]}})
    user = db.session.get(User, user_id)
    if not user:
        raise ApiError(404, "not_found", "User not found.")
    if user.id == actor.id:
        raise ApiError(409, "self_change", "You cannot change your own role or status.")
    before = {"role": user.role.name, "status": user.status}
    if "role" in d:
        user.role = Role.query.filter_by(name=d["role"]).one()
    if "status" in d:
        user.status = d["status"]
    audit("admin.user_update", "user", user.id, {"before": before, "after": d}, actor_id=actor.id)
    db.session.commit()
    return jsonify(user.to_dict())


@bp.get("/audit-logs")
@roles_required("admin")
def audit_logs(actor):
    q = db.select(AuditLog)
    if request.args.get("action"):
        q = q.where(AuditLog.action == request.args["action"])
    if request.args.get("actor_id", type=int):
        q = q.where(AuditLog.actor_id == request.args.get("actor_id", type=int))
    return jsonify(paginate(q.order_by(AuditLog.id.desc()), lambda a: a.to_dict(), default=50))


@bp.get("/data-sources")
@roles_required("admin", "moderator")
def data_sources(actor):
    rows = DataSource.query.order_by(DataSource.code).all()
    return jsonify({"items": [r.to_dict() for r in rows]})
