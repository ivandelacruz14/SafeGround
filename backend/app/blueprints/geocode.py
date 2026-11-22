import time

import requests
from flask import Blueprint, current_app, jsonify, request

from ..extensions import limiter
from ..utils import ApiError, validate

bp = Blueprint("geocode", __name__, url_prefix="/api/v1/geocode")
_cache = {}  # per-process; replace with Redis when running several workers
# Metro Manila bias box (west,north,east,south) - biases ranking, does not restrict it.
VIEWBOX = "120.90,14.82,121.18,14.35"


@bp.get("/search")
@limiter.limit("20 per minute")
def search():
    d = validate({"q": request.args.get("q")}, {"q": {"required": True, "min": 3, "max": 120}})
    q, cfg = d["q"].lower(), current_app.config
    hit = _cache.get(q)
    if hit and hit[0] > time.time():
        return jsonify(hit[1])
    try:
        r = requests.get(cfg["GEOCODER_URL"], timeout=cfg["GEOCODER_TIMEOUT"],
                         headers={"User-Agent": cfg["GEOCODER_USER_AGENT"]},
                         params={"q": d["q"], "format": "jsonv2", "countrycodes": "ph", "limit": 5,
                                 "viewbox": VIEWBOX, "bounded": 0})
        r.raise_for_status()
        rows = r.json()
    except (requests.RequestException, ValueError):
        raise ApiError(503, "geocoder_unavailable",
                       "Place search is unavailable right now. You can still pick a point on the map.")
    body = {"items": [{"label": x["display_name"], "lat": float(x["lat"]), "lng": float(x["lon"])} for x in rows],
            "source": {"name": "OpenStreetMap Nominatim", "attribution": "© OpenStreetMap contributors"}}
    _cache[q] = (time.time() + cfg["GEOCODER_CACHE_SECONDS"], body)
    if len(_cache) > 500:
        _cache.pop(next(iter(_cache)))
    return jsonify(body)
