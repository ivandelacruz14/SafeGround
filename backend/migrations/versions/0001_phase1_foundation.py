"""Phase 1 foundation: identity, saved places, data sources, transport reference, audit.

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.types import UserDefinedType

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


class Point(UserDefinedType):
    """MySQL 8 POINT in SRID 4326. NOT NULL is required for a SPATIAL index."""
    def get_col_spec(self, **kw):
        return "POINT SRID 4326"


def ts():
    return [sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=False)]


def upgrade():
    mysql_opts = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}

    op.create_table("roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(32), nullable=False, unique=True),
        sa.Column("description", sa.String(255)), **mysql_opts)

    op.create_table("users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("email_verified_at", sa.DateTime),
        sa.Column("last_login_at", sa.DateTime), *ts(), **mysql_opts)
    op.create_index("ix_users_role_id", "users", ["role_id"])
    op.create_index("ix_users_status", "users", ["status"])

    op.create_table("user_preferences",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("default_mode_codes", sa.JSON, nullable=False),
        sa.Column("max_walk_meters", sa.Integer, nullable=False, server_default="800"),
        sa.Column("avoid_flood_risk", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("language", sa.String(8), nullable=False, server_default="en"),
        sa.Column("notify_flood", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("notify_closures", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("notify_disruptions", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime, nullable=False), **mysql_opts)

    op.create_table("saved_places",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("category", sa.String(16), nullable=False, server_default="other"),
        sa.Column("address", sa.String(255)),
        sa.Column("location", Point(), nullable=False), *ts(), **mysql_opts)
    op.create_index("ix_saved_places_user_id", "saved_places", ["user_id"])
    op.create_index("ix_saved_places_location", "saved_places", ["location"], mysql_prefix="SPATIAL")

    op.create_table("data_sources",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(48), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("url", sa.String(255)),
        sa.Column("license", sa.String(160)),
        sa.Column("access_status", sa.String(24), nullable=False, server_default="unverified"),
        sa.Column("notes", sa.Text),
        sa.Column("last_checked_at", sa.DateTime),
        sa.Column("last_updated_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False), **mysql_opts)

    op.create_table("transport_modes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(24), nullable=False, unique=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("color", sa.String(7), nullable=False, server_default="#3B82F6"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()), **mysql_opts)

    op.create_table("transport_operators",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("website", sa.String(255)),
        sa.Column("data_source_id", sa.Integer, sa.ForeignKey("data_sources.id")), *ts(), **mysql_opts)
    op.create_index("ix_transport_operators_name", "transport_operators", ["name"])

    op.create_table("transport_routes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("mode_id", sa.Integer, sa.ForeignKey("transport_modes.id"), nullable=False),
        sa.Column("operator_id", sa.Integer, sa.ForeignKey("transport_operators.id")),
        sa.Column("code", sa.String(48), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("direction", sa.String(32), nullable=False, server_default="outbound"),
        sa.Column("origin_label", sa.String(160)),
        sa.Column("destination_label", sa.String(160)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("verification_status", sa.String(16), nullable=False, server_default="unverified"),
        sa.Column("data_source_id", sa.Integer, sa.ForeignKey("data_sources.id")),
        sa.Column("source_updated_at", sa.DateTime), *ts(),
        sa.UniqueConstraint("mode_id", "code", "direction", name="uq_route_identity"), **mysql_opts)
    op.create_index("ix_transport_routes_mode_id", "transport_routes", ["mode_id"])

    op.create_table("route_stops",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("stop_type", sa.String(16), nullable=False, server_default="stop"),
        sa.Column("location", Point(), nullable=False),
        sa.Column("primary_mode_id", sa.Integer, sa.ForeignKey("transport_modes.id")),
        sa.Column("external_ref", sa.String(96)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("verification_status", sa.String(16), nullable=False, server_default="unverified"),
        sa.Column("data_source_id", sa.Integer, sa.ForeignKey("data_sources.id")),
        sa.Column("source_updated_at", sa.DateTime), *ts(), **mysql_opts)
    op.create_index("ix_route_stops_name", "route_stops", ["name"])
    op.create_index("ix_route_stops_primary_mode_id", "route_stops", ["primary_mode_id"])
    op.create_index("ix_route_stops_ext", "route_stops", ["data_source_id", "external_ref"])
    op.create_index("ix_route_stops_location", "route_stops", ["location"], mysql_prefix="SPATIAL")

    op.create_table("route_stop_sequences",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("route_id", sa.Integer, sa.ForeignKey("transport_routes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stop_id", sa.Integer, sa.ForeignKey("route_stops.id"), nullable=False),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.UniqueConstraint("route_id", "sequence", name="uq_route_sequence"), **mysql_opts)
    op.create_index("ix_route_stop_sequences_stop_id", "route_stop_sequences", ["stop_id"])

    op.create_table("audit_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(48)),
        sa.Column("entity_id", sa.String(48)),
        sa.Column("details", sa.JSON),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime, nullable=False), **mysql_opts)
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade():
    for t in ("audit_logs", "route_stop_sequences", "route_stops", "transport_routes", "transport_operators",
              "transport_modes", "data_sources", "saved_places", "user_preferences", "users", "roles"):
        op.drop_table(t)
