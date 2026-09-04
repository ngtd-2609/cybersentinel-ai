"""add account lockout state

Revision ID: a91f3c6d2e40
Revises: 4c2a7f19d8e3
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a91f3c6d2e40"
down_revision: str | Sequence[str] | None = "4c2a7f19d8e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("last_failed_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_users_locked_until",
        "users",
        ["locked_until"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_users_locked_until", table_name="users")
    op.drop_column("users", "last_failed_login_at")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
