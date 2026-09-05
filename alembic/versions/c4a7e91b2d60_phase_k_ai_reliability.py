"""phase k ai reliability and model provenance

Revision ID: c4a7e91b2d60
Revises: f2b9c7d1a450
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c4a7e91b2d60"
down_revision: str | None = "f2b9c7d1a450"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("task", sa.String(64), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False, server_default="CANDIDATE"),
        sa.Column("artifact_uri", sa.String(512), nullable=False),
        sa.Column("artifact_hash", sa.String(128), nullable=False),
        sa.Column("dataset_uri", sa.String(512), nullable=False),
        sa.Column("dataset_hash", sa.String(128), nullable=False),
        sa.Column("git_commit", sa.String(64), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
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
        sa.UniqueConstraint("name", "version", name="uq_model_name_version"),
    )
    for name in ("name", "task", "stage"):
        op.create_index(f"ix_model_versions_{name}", "model_versions", [name])

    op.add_column("detection_events", sa.Column("model_version_id", sa.Integer()))
    op.create_foreign_key(
        "fk_detection_events_model_version_id",
        "detection_events",
        "model_versions",
        ["model_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_detection_events_model_version_id",
        "detection_events",
        ["model_version_id"],
    )

    op.create_table(
        "model_stage_transitions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "model_version_id",
            sa.Integer(),
            sa.ForeignKey("model_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_stage", sa.String(32), nullable=False),
        sa.Column("to_stage", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(1000), nullable=False),
        sa.Column(
            "actor_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_model_stage_transitions_model_version_id",
        "model_stage_transitions",
        ["model_version_id"],
    )
    op.create_index(
        "ix_model_stage_transitions_actor_id", "model_stage_transitions", ["actor_id"]
    )

    op.create_table(
        "model_monitoring_reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "model_version_id",
            sa.Integer(),
            sa.ForeignKey("model_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("feature_drift_score", sa.Float(), nullable=False),
        sa.Column("prediction_drift_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_model_monitoring_reports_model_version_id",
        "model_monitoring_reports",
        ["model_version_id"],
    )
    op.create_index(
        "ix_model_monitoring_reports_status", "model_monitoring_reports", ["status"]
    )

    op.create_table(
        "detection_feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "detection_event_id",
            sa.Integer(),
            sa.ForeignKey("detection_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "analyst_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("verdict", sa.String(32), nullable=False),
        sa.Column("notes", sa.String(1000)),
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
        sa.UniqueConstraint(
            "detection_event_id", "analyst_id", name="uq_detection_feedback_analyst"
        ),
    )
    for name in ("detection_event_id", "analyst_id", "verdict"):
        op.create_index(f"ix_detection_feedback_{name}", "detection_feedback", [name])

    registry = sa.table(
        "model_versions",
        sa.column("name", sa.String),
        sa.column("version", sa.String),
        sa.column("task", sa.String),
        sa.column("stage", sa.String),
        sa.column("artifact_uri", sa.String),
        sa.column("artifact_hash", sa.String),
        sa.column("dataset_uri", sa.String),
        sa.column("dataset_hash", sa.String),
        sa.column("git_commit", sa.String),
        sa.column("metrics", sa.JSON),
    )
    op.bulk_insert(
        registry,
        [
            {
                "name": "xgboost-binary",
                "version": "1.0.0",
                "task": "BINARY_CLASSIFICATION",
                "stage": "PRODUCTION",
                "artifact_uri": "artifacts/xgboost/model.joblib.dvc",
                "artifact_hash": "35755c3ff01fa2973db3a8673f4f9e03",
                "dataset_uri": "data/processed/cicids2017_binary.dvc",
                "dataset_hash": "136d82c2aa02afd4668d9bcc18d39a1a.dir",
                "git_commit": "11efc789e64a19f0b2a748e23eb4441e234d7abc",
                "metrics": {
                    "accuracy": 0.7037433611330333,
                    "precision": 0.9988979692917286,
                    "recall": 0.2792128006423857,
                    "f1": 0.43643337670382465,
                    "false_positive_rate": 0.000214809,
                    "roc_auc": 0.7775898320765913,
                    "pr_auc": 0.7802497441360099,
                },
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("detection_feedback")
    op.drop_table("model_monitoring_reports")
    op.drop_table("model_stage_transitions")
    op.drop_index("ix_detection_events_model_version_id", table_name="detection_events")
    op.drop_constraint(
        "fk_detection_events_model_version_id", "detection_events", type_="foreignkey"
    )
    op.drop_column("detection_events", "model_version_id")
    op.drop_table("model_versions")
