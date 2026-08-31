from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from cybersentinel_ai.db.models import DetectionEvent


def get_dashboard_summary(database: Session) -> dict:
    total_events = database.scalar(
        select(func.count()).select_from(DetectionEvent)
    ) or 0

    severity_rows = database.execute(
        select(
            func.upper(DetectionEvent.severity),
            func.count(DetectionEvent.id),
        ).group_by(func.upper(DetectionEvent.severity))
    ).all()

    severity_counts = {
        str(severity): int(count)
        for severity, count in severity_rows
    }

    requires_review = database.scalar(
        select(func.count())
        .select_from(DetectionEvent)
        .where(DetectionEvent.requires_review.is_(True))
    ) or 0

    average_risk_score = database.scalar(
        select(func.avg(DetectionEvent.risk_score))
    )

    attack_rows = database.execute(
        select(
            DetectionEvent.predicted_label,
            func.count(DetectionEvent.id).label("event_count"),
        )
        .group_by(DetectionEvent.predicted_label)
        .order_by(desc("event_count"))
        .limit(5)
    ).all()

    source_rows = database.execute(
        select(
            DetectionEvent.source_ip,
            func.count(DetectionEvent.id).label("event_count"),
            func.max(DetectionEvent.risk_score).label("max_risk_score"),
        )
        .where(DetectionEvent.source_ip.is_not(None))
        .group_by(DetectionEvent.source_ip)
        .order_by(desc("event_count"))
        .limit(5)
    ).all()

    current_hour = datetime.now(UTC).replace(
        minute=0,
        second=0,
        microsecond=0,
    )
    first_hour = current_hour - timedelta(hours=23)

    timeline_rows = database.execute(
        select(
            DetectionEvent.created_at,
            DetectionEvent.severity,
        ).where(
            DetectionEvent.created_at >= first_hour
        )
    ).all()

    buckets = {}

    for index in range(24):
        bucket_time = first_hour + timedelta(hours=index)

        buckets[bucket_time] = {
            "time": bucket_time,
            "total": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

    for created_at, severity in timeline_rows:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        else:
            created_at = created_at.astimezone(UTC)

        bucket_time = created_at.replace(
            minute=0,
            second=0,
            microsecond=0,
        )

        bucket = buckets.get(bucket_time)

        if bucket is None:
            continue

        bucket["total"] += 1

        severity_key = str(severity).lower()

        if severity_key in {"critical", "high", "medium", "low"}:
            bucket[severity_key] += 1

    timeline = list(buckets.values())

    recent_events = list(
        database.scalars(
            select(DetectionEvent)
            .order_by(DetectionEvent.created_at.desc())
            .limit(10)
        ).all()
    )

    return {
        "total_events": int(total_events),
        "critical_alerts": severity_counts.get("CRITICAL", 0),
        "high_alerts": severity_counts.get("HIGH", 0),
        "medium_alerts": severity_counts.get("MEDIUM", 0),
        "low_alerts": severity_counts.get("LOW", 0),
        "requires_review": int(requires_review),
        "average_risk_score": round(float(average_risk_score or 0.0), 2),
        "top_attack_types": [
            {
                "name": str(name),
                "count": int(count),
            }
            for name, count in attack_rows
        ],
        "top_threat_sources": [
            {
                "source_ip": str(source_ip),
                "count": int(count),
                "max_risk_score": round(float(max_risk_score), 2),
            }
            for source_ip, count, max_risk_score in source_rows
        ],
        "timeline": timeline,
        "recent_events": recent_events,
    }
