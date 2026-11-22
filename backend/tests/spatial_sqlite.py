"""Stand-ins for MySQL spatial functions so unit tests can run on in-memory SQLite.
Spatial behavior on real MySQL is covered by tests/test_mysql_spatial.py (set TEST_MYSQL_URL)."""
import re
import sqlite3

from sqlalchemy import event
from sqlalchemy.engine import Engine

_NUM = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


def _mbr_contains(poly_wkt, point_wkt):
    if poly_wkt is None or point_wkt is None:
        return None
    pts = [float(x) for x in _NUM.findall(poly_wkt)]
    xs, ys = pts[0::2], pts[1::2]
    px, py = (float(x) for x in _NUM.findall(point_wkt)[:2])
    return int(min(xs) <= px <= max(xs) and min(ys) <= py <= max(ys))


@event.listens_for(Engine, "connect")
def _register(dbapi_conn, _rec):
    if isinstance(dbapi_conn, sqlite3.Connection):
        dbapi_conn.create_function("ST_GeomFromText", -1, lambda wkt, *a: wkt)
        dbapi_conn.create_function("ST_AsText", -1, lambda g, *a: g)
        dbapi_conn.create_function("MBRContains", 2, _mbr_contains)
