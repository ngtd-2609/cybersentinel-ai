from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.database import get_db
from cybersentinel_ai.db.models import IngestionJob, NotificationDelivery
from cybersentinel_ai.security.dependencies import get_current_user

router = APIRouter(prefix="/status", tags=["Platform Status"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def _counts(database: Session, model, statuses: tuple[str, ...]) -> dict[str, int]:
    values = {status: 0 for status in statuses}
    rows = database.execute(
        select(model.status, func.count(model.id))
        .where(model.status.in_(statuses))
        .group_by(model.status)
    ).all()
    values.update({str(status): int(count) for status, count in rows})
    return values


@router.get("/components")
def component_status(
    database: DatabaseSession,
    _: object = Depends(get_current_user),
) -> dict:
    """Report only directly observed or configuration-level component states."""
    settings = get_settings()
    ingestion = _counts(database, IngestionJob, ("PENDING", "RETRY", "DEAD_LETTER"))
    notifications = _counts(
        database, NotificationDelivery, ("PENDING", "RETRY", "DEAD_LETTER")
    )
    return {
        "components": [
            {"name": "API", "state": "OPERATIONAL", "basis": "This endpoint responded"},
            {"name": "PostgreSQL", "state": "CONNECTED", "basis": "Status queries succeeded"},
            {
                "name": "Redis",
                "state": "CONFIGURED" if settings.redis_url else "NOT_CONFIGURED",
                "basis": "Configuration only; connectivity is not asserted",
            },
            {
                "name": "Ingestion worker",
                "state": "ENABLED" if settings.embedded_worker_enabled else "EXTERNAL_OR_DISABLED",
                "basis": "Embedded worker configuration",
            },
            {
                "name": "SSE",
                "state": "REDIS_BACKED" if settings.redis_url else "LOCAL_FALLBACK",
                "basis": "Transport configuration; client connection is shown per page",
            },
            {
                "name": "SOC Copilot",
                "state": "EXTERNAL_ENABLED" if settings.allow_external_ai else "GROUNDED_FALLBACK",
                "basis": "External AI policy; local grounded fallback remains available",
            },
            {
                "name": "AbuseIPDB",
                "state": "CONFIGURED" if settings.abuseipdb_api_key else "NOT_CONFIGURED",
                "basis": "Key presence only; live availability is shown after enrichment",
            },
        ],
        "queues": {
            "pending_jobs": ingestion["PENDING"],
            "retry_jobs": ingestion["RETRY"],
            "dead_letter_jobs": ingestion["DEAD_LETTER"],
            "pending_notifications": notifications["PENDING"],
            "retry_notifications": notifications["RETRY"],
            "failed_notifications": notifications["DEAD_LETTER"],
        },
    }
