from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from cybersentinel_ai.db.database import Base


class DetectionEvent(Base):
    __tablename__ = "detection_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    source_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
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
    )

    severity: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
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
    )
