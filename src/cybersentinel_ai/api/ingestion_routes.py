from __future__ import annotations

from hmac import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import (
    DeadLetterRetryResult,
    IngestionBatchCreate,
    IngestionBatchResult,
    IngestionItemResult,
    IngestionJobRead,
    IngestionTraceRead,
)
from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.database import atomic, get_db
from cybersentinel_ai.db.models import (
    DetectionEvent,
    IncidentDetection,
    IngestionJob,
    NotificationDelivery,
)
from cybersentinel_ai.ingestion.realtime import publish_update
from cybersentinel_ai.ingestion.service import create_ingestion_job, ingestion_key
from cybersentinel_ai.security.rbac import UserRole, require_role

router = APIRouter(prefix="/ingest", tags=["Event Ingestion"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def require_ingestion_key(
    supplied_key: Annotated[str | None, Header(alias="X-Ingestion-Key")] = None,
) -> None:
    configured = get_settings().ingestion_api_key_list
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Event ingestion is not configured",
        )
    if supplied_key is None or not any(
        compare_digest(supplied_key, expected) for expected in configured
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ingestion credentials",
        )


@router.post(
    "/events",
    response_model=IngestionBatchResult,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_ingestion_key)],
)
async def ingest_events(
    payload: IngestionBatchCreate,
    database: DatabaseSession,
) -> IngestionBatchResult:
    settings = get_settings()
    if len(payload.events) > settings.ingestion_batch_size:
        raise HTTPException(status_code=413, detail="Batch exceeds configured limit")

    results: list[IngestionItemResult] = []
    accepted = 0
    duplicates = 0
    with atomic(database):
        for event in payload.events:
            try:
                with database.begin_nested():
                    job, duplicate = create_ingestion_job(
                        database,
                        event,
                        max_attempts=settings.ingestion_max_attempts,
                    )
            except IntegrityError:
                job = database.scalar(
                    select(IngestionJob).where(
                        IngestionJob.idempotency_key
                        == ingestion_key(event.source_type, event.external_id)
                    )
                )
                if job is None:
                    raise
                duplicate = True
            accepted += int(not duplicate)
            duplicates += int(duplicate)
            results.append(
                IngestionItemResult(
                    external_id=event.external_id,
                    job_id=job.id,
                    status=job.status,
                    duplicate=duplicate,
                )
            )

    await publish_update(
        {"type": "ingestion.queued", "accepted": accepted, "duplicates": duplicates}
    )
    return IngestionBatchResult(
        accepted=accepted,
        duplicates=duplicates,
        items=results,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=IngestionJobRead,
    dependencies=[
        Depends(require_role(UserRole.ADMIN, UserRole.SENIOR_ANALYST, UserRole.ANALYST))
    ],
)
def get_ingestion_job(job_id: int, database: DatabaseSession) -> IngestionJob:
    job = database.get(IngestionJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    return job


@router.get(
    "/jobs/{job_id}/trace",
    response_model=IngestionTraceRead,
    dependencies=[
        Depends(require_role(UserRole.ADMIN, UserRole.SENIOR_ANALYST, UserRole.ANALYST))
    ],
)
def get_ingestion_trace(job_id: int, database: DatabaseSession) -> IngestionTraceRead:
    job = database.get(IngestionJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    event = (
        database.get(DetectionEvent, job.detection_event_id)
        if job.detection_event_id
        else None
    )
    incident_ids = (
        list(
            database.scalars(
                select(IncidentDetection.incident_id).where(
                    IncidentDetection.detection_event_id == job.detection_event_id
                )
            ).all()
        )
        if job.detection_event_id
        else []
    )
    notifications = (
        list(
            database.scalars(
                select(NotificationDelivery)
                .where(
                    NotificationDelivery.detection_event_id == job.detection_event_id
                )
                .order_by(NotificationDelivery.id.asc())
            ).all()
        )
        if job.detection_event_id
        else []
    )
    return IngestionTraceRead(
        job=job,
        detection_event=event,
        incident_ids=incident_ids,
        notifications=notifications,
    )


@router.get(
    "/dead-letter",
    response_model=list[IngestionJobRead],
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.SENIOR_ANALYST))],
)
def list_dead_letters(database: DatabaseSession) -> list[IngestionJob]:
    return list(
        database.scalars(
            select(IngestionJob)
            .where(IngestionJob.status == "DEAD_LETTER")
            .order_by(IngestionJob.updated_at.desc())
            .limit(200)
        ).all()
    )


@router.post(
    "/jobs/{job_id}/retry",
    response_model=DeadLetterRetryResult,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.SENIOR_ANALYST))],
)
def retry_dead_letter(job_id: int, database: DatabaseSession) -> DeadLetterRetryResult:
    with atomic(database):
        job = database.get(IngestionJob, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Ingestion job not found")
        if job.status != "DEAD_LETTER":
            raise HTTPException(status_code=409, detail="Job is not dead-lettered")
        job.status = "PENDING"
        job.attempts = 0
        job.last_error = None
        job.next_retry_at = None
    return DeadLetterRetryResult(job_id=job.id, status=job.status)
