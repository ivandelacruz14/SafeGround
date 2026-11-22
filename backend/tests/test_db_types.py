import pytest

from app.db_types import Point, bbox_wkt


def test_point_bind_and_parse():
    p = Point()
    assert p.process_bind_param({"lat": 14.5, "lng": 121.0}, None) == "POINT(121.0 14.5)"
    assert p.process_result_value("POINT(121 14.5)", None) == {"lat": 14.5, "lng": 121.0}


def test_point_rejects_out_of_range():
    with pytest.raises(ValueError):
        Point().process_bind_param({"lat": 91, "lng": 0}, None)


def test_bbox_wkt_is_closed_ring():
    wkt = bbox_wkt(1, 2, 3, 4)
    assert wkt.startswith("POLYGON((1 2,") and wkt.endswith("1 2))")
