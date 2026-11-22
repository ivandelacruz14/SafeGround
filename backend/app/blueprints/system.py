from pathlib import Path

from flask import Blueprint, Response, jsonify
from sqlalchemy import text

from ..extensions import db

bp = Blueprint("system", __name__, url_prefix="/api/v1")
SPEC = Path(__file__).resolve().parent.parent / "openapi.yaml"


@bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "database": "ok"})
    except Exception:
        return jsonify({"status": "degraded", "database": "unavailable"}), 503


@bp.get("/openapi.yaml")
def openapi():
    return Response(SPEC.read_text(encoding="utf-8"), mimetype="application/yaml")


@bp.get("/docs")
def docs():
    html = """<!doctype html><html><head><title>SafeRoute API</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"></head>
<body><div id="ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url:"/api/v1/openapi.yaml",dom_id:"#ui"})</script></body></html>"""
    return Response(html, mimetype="text/html")
