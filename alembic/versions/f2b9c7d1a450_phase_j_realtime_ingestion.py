"""phase j realtime ingestion pipeline

Revision ID: f2b9c7d1a450
Revises: e83a1d6f4b20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f2b9c7d1a450"
down_revision: str | None = "e83a1d6f4b20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for name, column in (
        ("external_id", sa.Column("external_id", sa.String(128), nullable=True)),
        ("source_type", sa.Column("source_type", sa.String(64), nullable=True)),
        ("occurred_at", sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True)),
        ("asset_id", sa.Column("asset_id", sa.String(128), nullable=True)),
        ("hostname", sa.Column("hostname", sa.String(255), nullable=True)),
        ("affected_user", sa.Column("affected_user", sa.String(255), nullable=True)),
        ("ioc_type", sa.Column("ioc_type", sa.String(32), nullable=True)),
        ("ioc_value", sa.Column("ioc_value", sa.String(512), nullable=True)),
        ("correlation_key", sa.Column("correlation_key", sa.String(255), nullable=True)),
    ):
        op.add_column("detection_events", column)
        if name != "ioc_type":
            op.create_index(f"ix_detection_events_{name}", "detection_events", [name])

    op.add_column(
        "incidents", sa.Column("correlation_key", sa.String(255), nullable=True)
    )
    op.add_column(
        "incidents",
        sa.Column("event_count", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "incidents", sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index("ix_incidents_correlation_key", "incidents", ["correlation_key"])
    op.create_index("ix_incidents_last_event_at", "incidents", ["last_event_at"])

    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("min_risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("severities", sa.String(128), nullable=False, server_default=""),
        sa.Column("label_pattern", sa.String(128), nullable=True),
        sa.Column("require_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "auto_create_incident", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "notification_channels", sa.String(128), nullable=False, server_default=""
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_alert_rules_enabled", "alert_rules", ["enabled"])

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "detection_event_id",
            sa.Integer(),
            sa.ForeignKey("detection_events.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    for name in (
        "idempotency_key",
        "source_type",
        "external_id",
        "status",
        "next_retry_at",
        "detection_event_id",
    ):
        op.create_index(f"ix_ingestion_jobs_{name}", "ingestion_jobs", [name])

    op.create_table(
        "incident_detections",
        sa.Column(
            "incident_id",
            sa.Integer(),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "detection_event_id",
            sa.Integer(),
            sa.ForeignKey("detection_events.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "detection_event_id",
            sa.Integer(),
            sa.ForeignKey("detection_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "incident_id",
            sa.Integer(),
            sa.ForeignKey("incidents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "detection_event_id", "channel", name="uq_notification_event_channel"
        ),
    )
    for name in (
        "detection_event_id",
        "incident_id",
        "channel",
        "status",
        "next_retry_at",
    ):
        op.create_index(
            f"ix_notification_deliveries_{name}", "notification_deliveries", [name]
        )

    rules = sa.table(
        "alert_rules",
        sa.column("name", sa.String),
        sa.column("enabled", sa.Boolean),
        sa.column("priority", sa.Integer),
        sa.column("min_risk_score", sa.Float),
        sa.column("severities", sa.String),
        sa.column("require_review", sa.Boolean),
        sa.column("auto_create_incident", sa.Boolean),
        sa.column("notification_channels", sa.String),
    )
    op.bulk_insert(
        rules,
        [
            {
                "name": "High-confidence incident correlation",
                "enabled": True,
                "priority": 10,
                "min_risk_score": 85.0,
                "severities": "CRITICAL,HIGH",
                "require_review": True,
                "auto_create_incident": True,
                "notification_channels": "",
            },
            {
                "name": "Critical webhook routing",
                "enabled": False,
                "priority": 20,
                "min_risk_score": 90.0,
                "severities": "CRITICAL",
                "require_review": False,
                "auto_create_incident": True,
                "notification_channels": "webhook,slack",
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("notification_deliveries")
    op.drop_table("incident_detections")
    op.drop_table("ingestion_jobs")
    op.drop_table("alert_rules")
    op.drop_index("ix_incidents_last_event_at", table_name="incidents")
    op.drop_index("ix_incidents_correlation_key", table_name="incidents")
    op.drop_column("incidents", "last_event_at")
    op.drop_column("incidents", "event_count")
    op.drop_column("incidents", "correlation_key")
    for name in (
        "correlation_key",
        "ioc_value",
        "affected_user",
        "hostname",
        "asset_id",
        "occurred_at",
        "source_type",
        "external_id",
    ):
        op.drop_index(f"ix_detection_events_{name}", table_name="detection_events")
        op.drop_column("detection_events", name)
    op.drop_column("detection_events", "ioc_type")
