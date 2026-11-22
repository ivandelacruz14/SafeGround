from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..db_types import AXIS, bbox_wkt
from ..extensions import db
from ..models import RouteStop, TransportMode, TransportRoute
from ..utils import ApiError, paginate

bp = Blueprint("transport", __name__, url_prefix="/api/v1/transport")
MAX_BBOX_DEGREES = 1.5


@bp.get("/modes")
def modes():
    rows = TransportMode.query.filter_by(is_active=True).order_by(TransportMode.sort_order).all()
    return jsonify({"items": [m.to_dict() for m in rows]})


def _parse_bbox(raw):
    try:
        w, s, e, n = (float(x) for x in raw.split(","))
    except ValueError:
        raise ApiError(400, "invalid_bbox", "bbox must be west,south,east,north as numbers.")
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
        raise ApiError(400, "invalid_bbox", "bbox coordinates are out of range or reversed.")
    if e - w > MAX_BBOX_DEGREES or n - s > MAX_BBOX_DEGREES:
        raise ApiError(400, "bbox_too_large", "Zoom in to load stops for this area.")
    return w, s, e, n


@bp.get("/stops")
def stops():
    q = db.select(RouteStop).where(RouteStop.is_active.is_(True))
    if request.args.get("bbox"):
        q = q.where(func.MBRContains(func.ST_GeomFromText(bbox_wkt(*_parse_bbox(request.args["bbox"])), 4326, AXIS),
                                     RouteStop.location))
    if request.args.get("verification_status"):
        q = q.where(RouteStop.verification_status == request.args["verification_status"])
    if request.args.get("mode"):
        q = q.join(TransportMode, RouteStop.primary_mode_id == TransportMode.id).where(
            TransportMode.code == request.args["mode"])
    return jsonify(paginate(q.order_by(RouteStop.id), lambda r: r.to_dict(), default=200, maximum=500))


@bp.get("/routes")
def routes():
    q = db.select(TransportRoute).where(TransportRoute.is_active.is_(True))
    if request.args.get("mode"):
        q = q.join(TransportMode, TransportRoute.mode_id == TransportMode.id).where(
            TransportMode.code == request.args["mode"])
    if request.args.get("q"):
        like = f"%{request.args['q'][:60]}%"
        q = q.where(TransportRoute.name.like(like) | TransportRoute.code.like(like))
    return jsonify(paginate(q.order_by(TransportRoute.code), lambda r: r.to_dict()))
