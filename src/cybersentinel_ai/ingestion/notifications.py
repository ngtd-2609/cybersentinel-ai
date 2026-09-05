from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.models import DetectionEvent, Incident, NotificationDelivery


def next_due_deliveries(database: Session, limit: int = 100) -> list[int]:
    now = datetime.now(UTC)
    return list(
        database.scalars(
            select(NotificationDelivery.id)
            .where(
                NotificationDelivery.status.in_(("PENDING", "RETRY")),
                or_(
                    NotificationDelivery.next_retry_at.is_(None),
                    NotificationDelivery.next_retry_at <= now,
                ),
            )
            .order_by(NotificationDelivery.created_at.asc())
            .limit(limit)
        ).all()
    )


def deliver_notification(
    database: Session,
    delivery_id: int,
    *,
    transport: httpx.BaseTransport | None = None,
) -> str:
    delivery = database.get(NotificationDelivery, delivery_id)
    if delivery is None:
        return "MISSING"
    settings = get_settings()
    target = {
        "webhook": settings.notification_webhook_url,
        "slack": settings.notification_slack_webhook_url,
    }.get(delivery.channel)
    if not target:
        return _mark_delivery_failure(database, delivery, "channel is not configured")

    event = database.get(DetectionEvent, delivery.detection_event_id)
    incident = database.get(Incident, delivery.incident_id) if delivery.incident_id else None
    body = {
        "type": "security_alert",
        "severity": event.severity if event else "UNKNOWN",
        "event_id": delivery.detection_event_id,
        "incident_id": delivery.incident_id,
        "title": incident.title if incident else (event.predicted_label if event else "Alert"),
        "source_ip": event.source_ip if event else None,
        "hostname": event.hostname if event else None,
        "ioc": event.ioc_value if event else None,
    }
    try:
        with httpx.Client(timeout=10.0, transport=transport) as client:
            response = client.post(target, json=body)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return _mark_delivery_failure(database, delivery, str(exc))

    delivery.status = "SENT"
    delivery.attempts += 1
    delivery.sent_at = datetime.now(UTC)
    delivery.last_error = None
    delivery.next_retry_at = None
    database.commit()
    return delivery.status


def _mark_delivery_failure(
    database: Session, delivery: NotificationDelivery, error: str
) -> str:
    delivery.attempts += 1
    delivery.last_error = error[:2000]
    if delivery.attempts >= delivery.max_attempts:
        delivery.status = "DEAD_LETTER"
        delivery.next_retry_at = None
    else:
        delivery.status = "RETRY"
        delivery.next_retry_at = datetime.now(UTC) + timedelta(
            seconds=min(300, 2 ** delivery.attempts)
        )
    database.commit()
    return delivery.status
