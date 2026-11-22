import os
from datetime import datetime, timezone

import click
from werkzeug.security import generate_password_hash

from .extensions import db
from .models import DataSource, Role, RouteStop, TransportMode, User, UserPreference

ROLES = [("user", "Commuter"), ("moderator", "Verifies community reports"),
         ("admin", "Full administrative access")]
MODES = [("jeepney", "Jeepney", "#F59E0B"), ("modern_jeepney", "Modern jeepney", "#EAB308"),
         ("bus", "Bus", "#22C55E"), ("uv_express", "UV Express", "#A855F7"),
         ("mrt", "MRT", "#3B82F6"), ("lrt", "LRT", "#22D3EE"), ("tricycle", "Tricycle", "#F472B6")]
# access_status records what is actually verified. Nothing here claims an API exists.
SOURCES = [
    ("osm", "OpenStreetMap", "osm", "https://www.openstreetmap.org", "ODbL 1.0 (attribution required)",
     "verified_access", "Base map data. The public tile server is not for production traffic."),
    ("gtfs_ph", "Philippine GTFS feeds (to investigate)", "gtfs", None, None, "unverified",
     "Availability, license and freshness have not been verified yet."),
    ("pagasa", "PAGASA flood/weather data", "api", "https://www.pagasa.dost.gov.ph", None, "unverified",
     "API access and licensing not verified. Manual entry is the fallback."),
    ("floodcaster", "FloodCaster", "api", None, None, "unverified", "Access and licensing not verified."),
    ("mmda", "MMDA road and traffic data", "api", "https://mmda.gov.ph", None, "unverified",
     "No public API assumed. Manual entry is the fallback."),
    ("ltfrb", "LTFRB franchise and fare data", "manual", "https://ltfrb.gov.ph", None, "manual_only",
     "Fare matrices must be entered by an admin from official issuances."),
    ("dotr", "DOTr transport data", "manual", "https://dotr.gov.ph", None, "unverified",
     "Rail data access not verified."),
    ("demo", "SafeRoute demonstration data", "manual", None, None, "manual_only",
     "Fictional sample data for local development. Never shown as real."),
]


def register_cli(app):
    @app.cli.command("seed")
    def seed():
        """Idempotent reference data: roles, transport modes, data sources, optional admin."""
        for name, desc in ROLES:
            if not Role.query.filter_by(name=name).first():
                db.session.add(Role(name=name, description=desc))
        for i, (code, name, color) in enumerate(MODES):
            if not TransportMode.query.filter_by(code=code).first():
                db.session.add(TransportMode(code=code, name=name, color=color, sort_order=i))
        for code, name, kind, url, lic, status, notes in SOURCES:
            if not DataSource.query.filter_by(code=code).first():
                db.session.add(DataSource(code=code, name=name, kind=kind, url=url, license=lic,
                                          access_status=status, notes=notes))
        db.session.commit()
        email, pw = os.getenv("SEED_ADMIN_EMAIL"), os.getenv("SEED_ADMIN_PASSWORD")
        if email and pw:
            if len(pw) < 12:
                raise click.ClickException("SEED_ADMIN_PASSWORD must be at least 12 characters.")
            if not User.query.filter_by(email=email.lower()).first():
                u = User(email=email.lower(), display_name="Administrator",
                         role=Role.query.filter_by(name="admin").one(),
                         password_hash=generate_password_hash(pw),
                         email_verified_at=datetime.now(timezone.utc).replace(tzinfo=None))
                u.preferences = UserPreference()
                db.session.add(u)
                db.session.commit()
                click.echo(f"Admin created: {email}")
        else:
            click.echo("SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD not set: no admin created.")
        click.echo("Seed complete.")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Three FICTIONAL stops so the map has something to show in local development."""
        src = DataSource.query.filter_by(code="demo").first()
        if not src:
            raise click.ClickException("Run `flask seed` first.")
        for name, lat, lng in [("DEMO stop A (not a real stop)", 14.5995, 120.9842),
                               ("DEMO stop B (not a real stop)", 14.6091, 121.0223),
                               ("DEMO stop C (not a real stop)", 14.5547, 121.0244)]:
            if not RouteStop.query.filter_by(name=name).first():
                db.session.add(RouteStop(name=name, location={"lat": lat, "lng": lng},
                                         verification_status="demo", data_source_id=src.id))
        db.session.commit()
        click.echo("Demo stops added. They are labeled DEMO and will never appear as verified.")
