"""add isolated portfolio sandboxes

Revision ID: b7e3c2a91f40
Revises: c4a7e91b2d60
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b7e3c2a91f40"
down_revision: str | Sequence[str] | None = "c4a7e91b2d60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table in ("detection_events", "incidents"):
        op.add_column(
            table,
            sa.Column("workspace", sa.String(length=16), nullable=False, server_default="DEMO"),
        )
        op.add_column(
            table,
            sa.Column(
                "owner_user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=True,
            ),
        )
        op.create_index(f"ix_{table}_workspace", table, ["workspace"])
        op.create_index(f"ix_{table}_owner_user_id", table, ["owner_user_id"])
    op.add_column(
        "detection_events",
        sa.Column("sandbox_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_detection_events_sandbox_expires_at",
        "detection_events",
        ["sandbox_expires_at"],
    )
    op.add_column(
        "incidents",
        sa.Column("sandbox_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_incidents_sandbox_expires_at", "incidents", ["sandbox_expires_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_incidents_sandbox_expires_at", table_name="incidents")
    op.drop_column("incidents", "sandbox_expires_at")
    op.drop_index("ix_detection_events_sandbox_expires_at", table_name="detection_events")
    op.drop_column("detection_events", "sandbox_expires_at")
    for table in ("incidents", "detection_events"):
        op.drop_index(f"ix_{table}_owner_user_id", table_name=table)
        op.drop_index(f"ix_{table}_workspace", table_name=table)
        op.drop_column(table, "owner_user_id")
        op.drop_column(table, "workspace")
