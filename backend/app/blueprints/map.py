from flask import Blueprint, jsonify

from ..extensions import db
from ..models import RouteStop, TransportRoute, iso

bp = Blueprint("map", __name__, url_prefix="/api/v1/map")


@bp.get("/layers")
def layers():
    """Layer catalogue with honest availability. `status` is one of:
    available | no_data (supported, nothing imported yet) | planned (feature not built yet)."""
    stops = db.session.query(db.func.count(RouteStop.id), db.func.max(RouteStop.updated_at)).filter(
        RouteStop.is_active.is_(True)).one()
    routes = db.session.query(db.func.count(TransportRoute.id)).filter(TransportRoute.is_active.is_(True)).scalar()
    return jsonify({"items": [
        {"id": "transport_stops", "label": "Transport stops", "group": "transport",
         "status": "available" if stops[0] else "no_data", "count": stops[0], "last_updated": iso(stops[1]),
         "note": "Shows imported or admin-entered stops. Each marker states its verification status."},
        {"id": "transport_routes", "label": "Route lines", "group": "transport",
         "status": "no_data" if not routes else "planned", "count": routes, "last_updated": None,
         "note": "Route shapes arrive with Phase 2 data import."},
        {"id": "flood_official", "label": "Official flood warnings", "group": "flood",
         "status": "planned", "phase": 4, "note": "Needs a verified PAGASA or government data feed."},
        {"id": "flood_verified", "label": "Verified community flood reports", "group": "flood",
         "status": "planned", "phase": 4, "note": "Appears after moderators verify reports."},
        {"id": "flood_unverified", "label": "Unverified flood reports", "group": "flood",
         "status": "planned", "phase": 4, "note": "Shown separately and clearly marked."},
        {"id": "flood_historical", "label": "Historically flood-prone areas", "group": "flood",
         "status": "planned", "phase": 4, "note": "Historical only. Says nothing about current conditions."},
        {"id": "road_reports", "label": "Road conditions", "group": "roads",
         "status": "planned", "phase": 4, "note": "Traffic, closures, accidents and obstructions."}]})
