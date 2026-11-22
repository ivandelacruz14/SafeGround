"""Portable spatial point type.

On MySQL 8 the column is `POINT SRID 4326` (spatially indexable) and values are written/read
with ST_GeomFromText / ST_AsText using lon-lat axis order. In Python a point is {"lat", "lng"}.
SQLite (used only by unit tests) stores WKT text; tests/spatial_sqlite.py registers stand-in functions.
"""
import re

from sqlalchemy import Text, func
from sqlalchemy.types import TypeDecorator, UserDefinedType

_WKT = re.compile(r"POINT\s*\(\s*([-+\d.eE]+)\s+([-+\d.eE]+)\s*\)", re.I)
AXIS = "axis-order=long-lat"


class MySQLPoint(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw):
        return "POINT SRID 4326"


class Point(TypeDecorator):
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "mysql":
            return dialect.type_descriptor(MySQLPoint())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        lat, lng = float(value["lat"]), float(value["lng"])
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError("Coordinates out of range")
        return f"POINT({lng} {lat})"

    def bind_expression(self, bindvalue):
        return func.ST_GeomFromText(bindvalue, 4326, AXIS)

    def column_expression(self, col):
        return func.ST_AsText(col, AXIS)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        m = _WKT.match(value)
        if not m:
            raise ValueError(f"Unexpected geometry value: {value!r}")
        return {"lat": float(m.group(2)), "lng": float(m.group(1))}


def bbox_wkt(west, south, east, north):
    return f"POLYGON(({west} {south},{east} {south},{east} {north},{west} {north},{west} {south}))"
