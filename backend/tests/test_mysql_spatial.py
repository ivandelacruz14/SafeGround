"""Runs only against a real MySQL 8 (the one thing SQLite cannot prove):
TEST_MYSQL_URL=mysql+pymysql://user:pw@127.0.0.1:3306/saferoute_test pytest tests/test_mysql_spatial.py"""
import os

import pytest
from sqlalchemy import create_engine, text

URL = os.getenv("TEST_MYSQL_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_MYSQL_URL not set")


def test_point_roundtrip_and_mbr_query():
    eng = create_engine(URL)
    with eng.begin() as c:
        c.execute(text("DROP TABLE IF EXISTS _spatial_probe"))
        c.execute(text("CREATE TABLE _spatial_probe (id INT PRIMARY KEY, p POINT SRID 4326 NOT NULL, "
                       "SPATIAL INDEX(p))"))
        c.execute(text("INSERT INTO _spatial_probe VALUES (1, ST_GeomFromText('POINT(121.0 14.6)', 4326, "
                       "'axis-order=long-lat'))"))
        wkt = "POLYGON((120.9 14.5,121.1 14.5,121.1 14.7,120.9 14.7,120.9 14.5))"
        n = c.execute(text("SELECT COUNT(*) FROM _spatial_probe WHERE MBRContains("
                           "ST_GeomFromText(:w, 4326, 'axis-order=long-lat'), p)"), {"w": wkt}).scalar()
        back = c.execute(text("SELECT ST_AsText(p, 'axis-order=long-lat') FROM _spatial_probe")).scalar()
        c.execute(text("DROP TABLE _spatial_probe"))
    assert n == 1 and back.startswith("POINT(121")
