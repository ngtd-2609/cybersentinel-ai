"""add SOC investigation depth

Revision ID: d9f4a6b2c180
Revises: b7e3c2a91f40
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d9f4a6b2c180"
down_revision: str | Sequence[str] | None = "b7e3c2a91f40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("hostname", sa.String(255), nullable=False),
        sa.Column("primary_ip", sa.String(45), nullable=True),
        sa.Column("operating_system", sa.String(128), nullable=True),
        sa.Column("environment", sa.String(16), nullable=False, server_default="DEV"),
        sa.Column("criticality", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column("owner_team", sa.String(128), nullable=True),
        sa.Column("internet_facing", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(16), nullable=False, server_default="UNKNOWN"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("hostname", "primary_ip", "environment", "criticality", "status", "last_seen_at"):
        op.create_index(f"ix_assets_{column}", "assets", [column])

    op.add_column("incidents", sa.Column("display_id", sa.String(32), nullable=True))
    op.add_column("incidents", sa.Column("priority", sa.String(8), nullable=False, server_default="P3"))
    op.add_column("incidents", sa.Column("assignee_user_id", sa.Integer(), nullable=True))
    op.add_column("incidents", sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("incidents", sa.Column("resolution_reason", sa.String(1000), nullable=True))
    op.add_column("incidents", sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("incidents", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_incidents_assignee_user_id_users",
        "incidents",
        "users",
        ["assignee_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    connection = op.get_bind()
    incidents = connection.execute(sa.text("SELECT id, created_at, last_event_at FROM incidents"))
    for row in incidents:
        connection.execute(
            sa.text(
                "UPDATE incidents SET display_id=:display_id, first_seen_at=:first_seen_at "
                "WHERE id=:incident_id"
            ),
            {
                "display_id": f"CS-{row.created_at.year}-{row.id:04d}",
                "first_seen_at": row.last_event_at or row.created_at,
                "incident_id": row.id,
            },
        )
    op.create_index("ix_incidents_display_id", "incidents", ["display_id"], unique=True)
    op.create_index("ix_incidents_priority", "incidents", ["priority"])
    op.create_index("ix_incidents_assignee_user_id", "incidents", ["assignee_user_id"])
    op.create_index("ix_incidents_first_seen_at", "incidents", ["first_seen_at"])
    op.create_index("ix_incidents_resolved_at", "incidents", ["resolved_at"])

    op.create_table(
        "incident_assets",
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("asset_id", sa.String(128), sa.ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "response_actions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="SIMULATED_SUCCESS"),
        sa.Column("result", sa.String(1000), nullable=False),
        sa.Column("simulation", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_response_actions_incident_id", "response_actions", ["incident_id"])
    op.create_index("ix_response_actions_requested_by", "response_actions", ["requested_by"])
    op.create_index("ix_response_actions_status", "response_actions", ["status"])

    op.create_table(
        "threat_intel_cache",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("indicator_type", sa.String(32), nullable=False),
        sa.Column("indicator", sa.String(512), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider", "indicator_type", "indicator", name="uq_ti_indicator"),
    )
    op.create_index("ix_threat_intel_cache_provider", "threat_intel_cache", ["provider"])
    op.create_index("ix_threat_intel_cache_indicator", "threat_intel_cache", ["indicator"])
    op.create_index("ix_threat_intel_cache_expires_at", "threat_intel_cache", ["expires_at"])


def downgrade() -> None:
    for name in ("ix_threat_intel_cache_expires_at", "ix_threat_intel_cache_indicator", "ix_threat_intel_cache_provider"):
        op.drop_index(name, table_name="threat_intel_cache")
    op.drop_table("threat_intel_cache")
    for name in ("ix_response_actions_status", "ix_response_actions_requested_by", "ix_response_actions_incident_id"):
        op.drop_index(name, table_name="response_actions")
    op.drop_table("response_actions")
    op.drop_table("incident_assets")
    for name in (
        "ix_incidents_resolved_at",
        "ix_incidents_first_seen_at",
        "ix_incidents_assignee_user_id",
        "ix_incidents_priority",
        "ix_incidents_display_id",
    ):
        op.drop_index(name, table_name="incidents")
    op.drop_constraint("fk_incidents_assignee_user_id_users", "incidents", type_="foreignkey")
    for column in (
        "resolved_at",
        "first_seen_at",
        "resolution_reason",
        "tags",
        "assignee_user_id",
        "priority",
        "display_id",
    ):
        op.drop_column("incidents", column)
    for column in ("last_seen_at", "status", "criticality", "environment", "primary_ip", "hostname"):
        op.drop_index(f"ix_assets_{column}", table_name="assets")
    op.drop_table("assets")
