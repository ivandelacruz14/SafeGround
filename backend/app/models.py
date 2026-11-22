"""Phase 1 models. Later phases add flood, report, journey, notification and AI tables
through new migrations. Timestamps are naive UTC (MySQL DATETIME) and serialized with a Z suffix."""
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Index, Integer, UniqueConstraint

from .db_types import Point
from .extensions import db

BigPK = BigInteger().with_variant(Integer, "sqlite")


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(dt):
    return dt.isoformat() + "Z" if dt else None


class Timestamps:
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)


# ---------------------------------------------------------------- identity
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.String(255))


class User(Timestamps, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(80), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False, default="active", index=True)  # active|suspended
    email_verified_at = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)

    role = db.relationship("Role", lazy="joined")
    preferences = db.relationship("UserPreference", uselist=False, back_populates="user",
                                  cascade="all, delete-orphan")
    saved_places = db.relationship("SavedPlace", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_active(self):
        return self.status == "active"

    def to_dict(self):
        return {"id": self.id, "email": self.email, "display_name": self.display_name,
                "role": self.role.name, "status": self.status,
                "email_verified": self.email_verified_at is not None,
                "created_at": iso(self.created_at), "last_login_at": iso(self.last_login_at)}


class UserPreference(db.Model):
    __tablename__ = "user_preferences"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    default_mode_codes = db.Column(db.JSON, nullable=False, default=list)
    max_walk_meters = db.Column(db.Integer, nullable=False, default=800)
    avoid_flood_risk = db.Column(db.Boolean, nullable=False, default=True)
    language = db.Column(db.String(8), nullable=False, default="en")
    notify_flood = db.Column(db.Boolean, nullable=False, default=True)
    notify_closures = db.Column(db.Boolean, nullable=False, default=True)
    notify_disruptions = db.Column(db.Boolean, nullable=False, default=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    user = db.relationship("User", back_populates="preferences")

    FIELDS = ("default_mode_codes", "max_walk_meters", "avoid_flood_risk", "language",
              "notify_flood", "notify_closures", "notify_disruptions")

    def to_dict(self):
        d = {f: getattr(self, f) for f in self.FIELDS}
        d["updated_at"] = iso(self.updated_at)
        return d


class SavedPlace(Timestamps, db.Model):
    __tablename__ = "saved_places"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    label = db.Column(db.String(80), nullable=False)
    category = db.Column(db.String(16), nullable=False, default="other")  # home|work|other
    address = db.Column(db.String(255))
    location = db.Column(Point, nullable=False)
    user = db.relationship("User", back_populates="saved_places")
    __table_args__ = (Index("ix_saved_places_location", "location", mysql_prefix="SPATIAL"),)

    def to_dict(self):
        return {"id": self.id, "label": self.label, "category": self.category,
                "address": self.address, **self.location, "created_at": iso(self.created_at)}


# ---------------------------------------------------------------- data sources
class DataSource(db.Model):
    """Every imported or manually entered dataset points at a row here so the UI can show
    provenance, license and freshness. access_status records what has actually been verified."""
    __tablename__ = "data_sources"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(48), unique=True, nullable=False)
    name = db.Column(db.String(160), nullable=False)
    kind = db.Column(db.String(24), nullable=False)  # osm|gtfs|api|manual
    url = db.Column(db.String(255))
    license = db.Column(db.String(160))
    access_status = db.Column(db.String(24), nullable=False, default="unverified")
    # unverified | verified_access | unavailable | manual_only
    notes = db.Column(db.Text)
    last_checked_at = db.Column(db.DateTime)
    last_updated_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def to_dict(self):
        return {"id": self.id, "code": self.code, "name": self.name, "kind": self.kind,
                "url": self.url, "license": self.license, "access_status": self.access_status,
                "notes": self.notes, "last_checked_at": iso(self.last_checked_at),
                "last_updated_at": iso(self.last_updated_at)}


# ---------------------------------------------------------------- transport
class TransportMode(db.Model):
    __tablename__ = "transport_modes"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(24), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    color = db.Column(db.String(7), nullable=False, default="#3B82F6")
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {"id": self.id, "code": self.code, "name": self.name, "color": self.color}


class TransportOperator(Timestamps, db.Model):
    __tablename__ = "transport_operators"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    website = db.Column(db.String(255))
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"))


class TransportRoute(Timestamps, db.Model):
    __tablename__ = "transport_routes"
    id = db.Column(db.Integer, primary_key=True)
    mode_id = db.Column(db.Integer, db.ForeignKey("transport_modes.id"), nullable=False, index=True)
    operator_id = db.Column(db.Integer, db.ForeignKey("transport_operators.id"))
    code = db.Column(db.String(48), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    direction = db.Column(db.String(32), nullable=False, default="outbound")
    origin_label = db.Column(db.String(160))
    destination_label = db.Column(db.String(160))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    verification_status = db.Column(db.String(16), nullable=False, default="unverified")  # verified|unverified|demo
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"))
    source_updated_at = db.Column(db.DateTime)
    mode = db.relationship("TransportMode", lazy="joined")
    data_source = db.relationship("DataSource", lazy="joined")
    __table_args__ = (UniqueConstraint("mode_id", "code", "direction", name="uq_route_identity"),)

    def to_dict(self):
        return {"id": self.id, "mode": self.mode.code, "code": self.code, "name": self.name,
                "direction": self.direction, "origin": self.origin_label,
                "destination": self.destination_label, "verification_status": self.verification_status,
                "source": self.data_source.code if self.data_source else None,
                "source_updated_at": iso(self.source_updated_at)}


class RouteStop(Timestamps, db.Model):
    __tablename__ = "route_stops"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    stop_type = db.Column(db.String(16), nullable=False, default="stop")  # stop|terminal|station
    location = db.Column(Point, nullable=False)
    primary_mode_id = db.Column(db.Integer, db.ForeignKey("transport_modes.id"), index=True)
    external_ref = db.Column(db.String(96))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    verification_status = db.Column(db.String(16), nullable=False, default="unverified")
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"))
    source_updated_at = db.Column(db.DateTime)
    primary_mode = db.relationship("TransportMode", lazy="joined")
    data_source = db.relationship("DataSource", lazy="joined")
    __table_args__ = (Index("ix_route_stops_location", "location", mysql_prefix="SPATIAL"),
                      Index("ix_route_stops_ext", "data_source_id", "external_ref"))

    def to_dict(self):
        return {"id": self.id, "name": self.name, "stop_type": self.stop_type, **self.location,
                "mode": self.primary_mode.code if self.primary_mode else None,
                "verification_status": self.verification_status,
                "source": self.data_source.code if self.data_source else None,
                "source_updated_at": iso(self.source_updated_at)}


class RouteStopSequence(db.Model):
    __tablename__ = "route_stop_sequences"
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey("transport_routes.id", ondelete="CASCADE"), nullable=False)
    stop_id = db.Column(db.Integer, db.ForeignKey("route_stops.id"), nullable=False, index=True)
    sequence = db.Column(db.Integer, nullable=False)
    __table_args__ = (UniqueConstraint("route_id", "sequence", name="uq_route_sequence"),)


# ---------------------------------------------------------------- audit
class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(BigPK, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action = db.Column(db.String(64), nullable=False, index=True)
    entity_type = db.Column(db.String(48))
    entity_id = db.Column(db.String(48))
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    actor = db.relationship("User", lazy="joined")

    def to_dict(self):
        return {"id": self.id, "actor": self.actor.email if self.actor else None,
                "action": self.action, "entity_type": self.entity_type, "entity_id": self.entity_id,
                "details": self.details, "ip_address": self.ip_address, "created_at": iso(self.created_at)}
