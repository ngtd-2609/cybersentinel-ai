"""add audit logs table

Revision ID: 6090756c7de2
Revises: fc0b0494b18e
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "6090756c7de2"
down_revision: str | Sequence[str] | None = "fc0b0494b18e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "action",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "target_type",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "target_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "description",
            sa.String(length=1000),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
