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
        "recent_events": recent_events,
    }
