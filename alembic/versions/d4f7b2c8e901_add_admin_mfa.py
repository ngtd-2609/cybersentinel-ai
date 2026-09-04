"""add administrator mfa state

Revision ID: d4f7b2c8e901
Revises: a91f3c6d2e40
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d4f7b2c8e901"
down_revision: str | Sequence[str] | None = "a91f3c6d2e40"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("mfa_enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("mfa_secret_encrypted", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("mfa_pending_secret_encrypted", sa.String(length=512), nullable=True),
    )

    op.create_table(
        "mfa_recovery_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mfa_recovery_codes_user_id", "mfa_recovery_codes", ["user_id"], unique=False
    )
    op.create_index(
        "ix_mfa_recovery_codes_code_hash", "mfa_recovery_codes", ["code_hash"], unique=True
    )
    op.create_index(
        "ix_mfa_recovery_codes_used_at", "mfa_recovery_codes", ["used_at"], unique=False
    )

    op.create_table(
        "mfa_challenges",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mfa_challenges_user_id", "mfa_challenges", ["user_id"], unique=False)
    op.create_index("ix_mfa_challenges_expires_at", "mfa_challenges", ["expires_at"], unique=False)
    op.create_index("ix_mfa_challenges_used_at", "mfa_challenges", ["used_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_mfa_challenges_used_at", table_name="mfa_challenges")
    op.drop_index("ix_mfa_challenges_expires_at", table_name="mfa_challenges")
    op.drop_index("ix_mfa_challenges_user_id", table_name="mfa_challenges")
    op.drop_table("mfa_challenges")
    op.drop_index("ix_mfa_recovery_codes_used_at", table_name="mfa_recovery_codes")
    op.drop_index("ix_mfa_recovery_codes_code_hash", table_name="mfa_recovery_codes")
    op.drop_index("ix_mfa_recovery_codes_user_id", table_name="mfa_recovery_codes")
    op.drop_table("mfa_recovery_codes")
    op.drop_column("users", "mfa_pending_secret_encrypted")
    op.drop_column("users", "mfa_secret_encrypted")
    op.drop_column("users", "mfa_enabled")
