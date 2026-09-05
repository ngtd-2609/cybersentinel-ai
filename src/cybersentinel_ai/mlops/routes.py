from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.db.database import atomic, get_db
from cybersentinel_ai.db.models import DetectionEvent, DetectionFeedback, ModelVersion
from cybersentinel_ai.mlops.schemas import (
    DetectionFeedbackCreate,
    DetectionFeedbackRead,
    DetectionProvenanceRead,
    FeedbackSummaryRead,
    ModelComparisonRead,
    ModelComparisonRequest,
    ModelPromotionRequest,
    ModelVersionCreate,
    ModelVersionRead,
    MonitoringReportCreate,
    MonitoringReportRead,
)
from cybersentinel_ai.mlops.service import (
    create_monitoring_report,
    feedback_summary,
    model_score,
    promote_model,
    validate_model_metrics,
)
from cybersentinel_ai.security.rbac import UserRole, require_role

router = APIRouter(prefix="/mlops", tags=["AI Reliability and MLOps"])
DatabaseSession = Annotated[Session, Depends(get_db)]
Authenticated = Depends(require_role(*tuple(UserRole)))


@router.get("/models", response_model=list[ModelVersionRead], dependencies=[Authenticated])
def list_models(database: DatabaseSession) -> list[ModelVersion]:
    return list(
        database.scalars(
            select(ModelVersion).order_by(ModelVersion.created_at.desc(), ModelVersion.id.desc())
        ).all()
    )


@router.post("/models", response_model=ModelVersionRead, status_code=201)
def register_model(
    payload: ModelVersionCreate,
    database: DatabaseSession,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.SENIOR_ANALYST)),
) -> ModelVersion:
    try:
        validate_model_metrics(payload.task, payload.metrics)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    with atomic(database):
        model = ModelVersion(**payload.model_dump(), stage="CANDIDATE")
        database.add(model)
        database.flush()
        log_action(
            database,
            current_user.id,
            "REGISTER_MODEL_VERSION",
            f"Registered {model.name}:{model.version}",
            "MODEL_VERSION",
            model.id,
            commit=False,
        )
    database.refresh(model)
    return model


@router.post("/models/{model_id}/promote", response_model=ModelVersionRead)
def promote(
    model_id: int,
    payload: ModelPromotionRequest,
    database: DatabaseSession,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.SENIOR_ANALYST)),
) -> ModelVersion:
    with atomic(database):
        model = database.get(ModelVersion, model_id)
        if model is None:
            raise HTTPException(status_code=404, detail="Model version not found")
        try:
            promote_model(
                database,
                model,
                target_stage=payload.target_stage,
                reason=payload.reason,
                actor_id=current_user.id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        log_action(
            database,
            current_user.id,
            "PROMOTE_MODEL_VERSION",
            f"Promoted {model.name}:{model.version} to {model.stage}",
            "MODEL_VERSION",
            model.id,
            commit=False,
        )
    database.refresh(model)
    return model


@router.post(
    "/models/compare",
    response_model=ModelComparisonRead,
    dependencies=[Authenticated],
)
def compare_models(
    payload: ModelComparisonRequest, database: DatabaseSession
) -> ModelComparisonRead:
    champion = database.get(ModelVersion, payload.champion_id)
    challenger = database.get(ModelVersion, payload.challenger_id)
    if champion is None or challenger is None:
        raise HTTPException(status_code=404, detail="Model version not found")
    if champion.task != challenger.task:
        raise HTTPException(status_code=409, detail="Models must have the same task")
    champion_score = model_score(champion)
    challenger_score = model_score(challenger)
    keys = set(champion.metrics) | set(challenger.metrics)
    return ModelComparisonRead(
        champion_id=champion.id,
        challenger_id=challenger.id,
        champion_score=champion_score,
        challenger_score=challenger_score,
        recommended_model_id=(
            challenger.id if challenger_score > champion_score else champion.id
        ),
        metric_deltas={
            key: round(
                float(challenger.metrics.get(key, 0.0))
                - float(champion.metrics.get(key, 0.0)),
                8,
            )
            for key in sorted(keys)
        },
    )


@router.post("/models/{model_id}/monitoring", response_model=MonitoringReportRead)
def monitor_model(
    model_id: int,
    payload: MonitoringReportCreate,
    database: DatabaseSession,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.SENIOR_ANALYST)),
) -> MonitoringReportRead:
    if database.get(ModelVersion, model_id) is None:
        raise HTTPException(status_code=404, detail="Model version not found")
    with atomic(database):
        report = create_monitoring_report(database, model_id, payload)
        log_action(
            database,
            current_user.id,
            "MONITOR_MODEL_DRIFT",
            f"Model {model_id} drift status {report.status}",
            "MODEL_VERSION",
            model_id,
            commit=False,
        )
    database.refresh(report)
    return report


@router.get(
    "/detections/{detection_id}/provenance",
    response_model=DetectionProvenanceRead,
    dependencies=[Authenticated],
)
def detection_provenance(
    detection_id: int, database: DatabaseSession
) -> DetectionProvenanceRead:
    event = database.get(DetectionEvent, detection_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Detection event not found")
    model = (
        database.get(ModelVersion, event.model_version_id)
        if event.model_version_id
        else None
    )
    return DetectionProvenanceRead(detection_event_id=event.id, model=model)


@router.put(
    "/detections/{detection_id}/feedback",
    response_model=DetectionFeedbackRead,
)
def submit_feedback(
    detection_id: int,
    payload: DetectionFeedbackCreate,
    database: DatabaseSession,
    current_user=Depends(
        require_role(UserRole.ADMIN, UserRole.SENIOR_ANALYST, UserRole.ANALYST)
    ),
) -> DetectionFeedback:
    if database.get(DetectionEvent, detection_id) is None:
        raise HTTPException(status_code=404, detail="Detection event not found")
    with atomic(database):
        feedback = database.scalar(
            select(DetectionFeedback).where(
                DetectionFeedback.detection_event_id == detection_id,
                DetectionFeedback.analyst_id == current_user.id,
            )
        )
        if feedback is None:
            feedback = DetectionFeedback(
                detection_event_id=detection_id,
                analyst_id=current_user.id,
            )
            database.add(feedback)
        feedback.verdict = payload.verdict
        feedback.notes = payload.notes
        database.flush()
        log_action(
            database,
            current_user.id,
            "LABEL_DETECTION_FEEDBACK",
            f"Marked detection {detection_id} as {payload.verdict}",
            "DETECTION_EVENT",
            detection_id,
            commit=False,
        )
    database.refresh(feedback)
    return feedback


@router.get(
    "/models/{model_id}/feedback-summary",
    response_model=FeedbackSummaryRead,
    dependencies=[Authenticated],
)
def get_feedback_summary(model_id: int, database: DatabaseSession) -> FeedbackSummaryRead:
    if database.get(ModelVersion, model_id) is None:
        raise HTTPException(status_code=404, detail="Model version not found")
    return FeedbackSummaryRead(**feedback_summary(database, model_id))
