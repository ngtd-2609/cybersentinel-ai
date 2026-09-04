"""add relational integrity and query indexes

Revision ID: 8b7d1e9c4a21
Revises: 6090756c7de2
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "8b7d1e9c4a21"
down_revision: str | Sequence[str] | None = "6090756c7de2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "detection_events",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_detection_events_idempotency_key",
        "detection_events",
        ["idempotency_key"],
        unique=True,
    )

    op.create_foreign_key(
        "fk_incidents_detection_event_id_detection_events",
        "incidents",
        "detection_events",
        ["detection_event_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_incident_timelines_incident_id_incidents",
        "incident_timelines",
        "incidents",
        ["incident_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_audit_logs_user_id_users",
        "audit_logs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    indexes = (
        ("ix_detection_events_source_ip", "detection_events", ["source_ip"]),
        ("ix_detection_events_risk_score", "detection_events", ["risk_score"]),
        ("ix_detection_events_severity", "detection_events", ["severity"]),
        ("ix_detection_events_created_at", "detection_events", ["created_at"]),
        ("ix_incidents_status", "incidents", ["status"]),
        ("ix_incidents_detection_event_id", "incidents", ["detection_event_id"]),
        ("ix_incidents_created_at", "incidents", ["created_at"]),
        ("ix_incident_timelines_incident_id", "incident_timelines", ["incident_id"]),
        ("ix_incident_timelines_created_at", "incident_timelines", ["created_at"]),
        ("ix_audit_logs_user_id", "audit_logs", ["user_id"]),
        ("ix_audit_logs_action", "audit_logs", ["action"]),
        ("ix_audit_logs_target_type", "audit_logs", ["target_type"]),
        ("ix_audit_logs_created_at", "audit_logs", ["created_at"]),
    )
    for name, table_name, columns in indexes:
        op.create_index(name, table_name, columns, unique=False)


def downgrade() -> None:
    indexes = (
        ("ix_audit_logs_created_at", "audit_logs"),
        ("ix_audit_logs_target_type", "audit_logs"),
        ("ix_audit_logs_action", "audit_logs"),
        ("ix_audit_logs_user_id", "audit_logs"),
        ("ix_incident_timelines_created_at", "incident_timelines"),
        ("ix_incident_timelines_incident_id", "incident_timelines"),
        ("ix_incidents_created_at", "incidents"),
        ("ix_incidents_detection_event_id", "incidents"),
        ("ix_incidents_status", "incidents"),
        ("ix_detection_events_created_at", "detection_events"),
        ("ix_detection_events_severity", "detection_events"),
        ("ix_detection_events_risk_score", "detection_events"),
        ("ix_detection_events_source_ip", "detection_events"),
    )
    for name, table_name in indexes:
        op.drop_index(name, table_name=table_name)

    op.drop_constraint(
        "fk_audit_logs_user_id_users",
        "audit_logs",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_incident_timelines_incident_id_incidents",
        "incident_timelines",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_incidents_detection_event_id_detection_events",
        "incidents",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_detection_events_idempotency_key",
        table_name="detection_events",
    )
    op.drop_column("detection_events", "idempotency_key")
