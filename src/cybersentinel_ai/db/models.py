from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cybersentinel_ai.db.database import Base


class DetectionEvent(Base):
    __tablename__ = "detection_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        unique=True,
        index=True,
    )

    source_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        index=True,
    )

    destination_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    destination_port: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    predicted_label: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    classifier_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    anomaly_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    rule_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        index=True,
    )

    requires_review: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="OPEN",
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    detection_event_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("detection_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    detection_event = relationship(
        "DetectionEvent",
        primaryjoin="Incident.detection_event_id==DetectionEvent.id",
        foreign_keys=[detection_event_id],
        lazy="joined",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )


class IncidentTimeline(Base):
    __tablename__ = "incident_timelines"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    incident_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="VIEWER",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    target_type: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    target_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )
