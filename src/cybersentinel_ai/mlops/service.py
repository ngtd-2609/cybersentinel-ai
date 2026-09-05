from __future__ import annotations

from math import isfinite, log

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.models import (
    DetectionEvent,
    DetectionFeedback,
    ModelMonitoringReport,
    ModelStageTransition,
    ModelVersion,
)
from cybersentinel_ai.mlops.schemas import MonitoringReportCreate

BINARY_METRICS = ("precision", "recall", "f1", "false_positive_rate")


def validate_model_metrics(task: str, metrics: dict[str, float]) -> None:
    if task.upper() != "BINARY_CLASSIFICATION":
        return
    missing = [name for name in BINARY_METRICS if name not in metrics]
    if missing:
        raise ValueError(f"missing required metrics: {', '.join(missing)}")
    if any(
        not isfinite(float(metrics[name])) or not 0.0 <= float(metrics[name]) <= 1.0
        for name in BINARY_METRICS
    ):
        raise ValueError("classification metrics must be between 0 and 1")


def metric_gate_failures(model: ModelVersion) -> list[str]:
    if model.task.upper() != "BINARY_CLASSIFICATION":
        return []
    validate_model_metrics(model.task, model.metrics)
    settings = get_settings()
    checks = {
        "precision": (model.metrics["precision"], settings.model_min_precision, ">="),
        "recall": (model.metrics["recall"], settings.model_min_recall, ">="),
        "f1": (model.metrics["f1"], settings.model_min_f1, ">="),
        "false_positive_rate": (
            model.metrics["false_positive_rate"],
            settings.model_max_false_positive_rate,
            "<=",
        ),
    }
    return [
        f"{name} must be {operator} {threshold}"
        for name, (value, threshold, operator) in checks.items()
        if (operator == ">=" and value < threshold)
        or (operator == "<=" and value > threshold)
    ]


def promote_model(
    database: Session,
    model: ModelVersion,
    *,
    target_stage: str,
    reason: str,
    actor_id: int,
) -> ModelVersion:
    allowed = {"CANDIDATE": "STAGING", "STAGING": "PRODUCTION"}
    if allowed.get(model.stage) != target_stage:
        raise ValueError(f"invalid promotion {model.stage} -> {target_stage}")
    failures = metric_gate_failures(model)
    if failures:
        raise ValueError("model quality gate failed: " + "; ".join(failures))
    if target_stage == "PRODUCTION":
        latest_report = database.scalar(
            select(ModelMonitoringReport)
            .where(ModelMonitoringReport.model_version_id == model.id)
            .order_by(ModelMonitoringReport.window_end.desc())
            .limit(1)
        )
        if latest_report is None or latest_report.status != "HEALTHY":
            raise ValueError("a healthy monitoring report is required for production")
        current = database.scalars(
            select(ModelVersion).where(
                ModelVersion.task == model.task,
                ModelVersion.stage == "PRODUCTION",
                ModelVersion.id != model.id,
            )
        ).all()
        for champion in current:
            champion.stage = "ARCHIVED"
            database.add(
                ModelStageTransition(
                    model_version_id=champion.id,
                    from_stage="PRODUCTION",
                    to_stage="ARCHIVED",
                    reason=f"Superseded by {model.name}:{model.version}",
                    actor_id=actor_id,
                )
            )
    previous = model.stage
    model.stage = target_stage
    database.add(
        ModelStageTransition(
            model_version_id=model.id,
            from_stage=previous,
            to_stage=target_stage,
            reason=reason,
            actor_id=actor_id,
        )
    )
    database.flush()
    return model


def model_score(model: ModelVersion) -> float:
    metrics = model.metrics
    return round(
        0.3 * float(metrics.get("precision", 0.0))
        + 0.35 * float(metrics.get("recall", 0.0))
        + 0.35 * float(metrics.get("f1", metrics.get("macro_f1", 0.0)))
        - 0.2 * float(metrics.get("false_positive_rate", 0.0)),
        8,
    )


def population_stability_index(reference: list[float], current: list[float]) -> float:
    if any(not isfinite(value) for value in [*reference, *current]):
        raise ValueError("drift samples must contain finite values")
    low = min(min(reference), min(current))
    high = max(max(reference), max(current))
    if low == high:
        return 0.0
    boundaries = np.linspace(low, high, 11)
    reference_counts, _ = np.histogram(reference, bins=boundaries)
    current_counts, _ = np.histogram(current, bins=boundaries)
    reference_ratio = reference_counts / max(len(reference), 1)
    current_ratio = current_counts / max(len(current), 1)
    epsilon = 1e-6
    return round(
        float(
            sum(
                (max(current_value, epsilon) - max(reference_value, epsilon))
                * log(max(current_value, epsilon) / max(reference_value, epsilon))
                for reference_value, current_value in zip(
                    reference_ratio, current_ratio, strict=True
                )
            )
        ),
        8,
    )


def create_monitoring_report(
    database: Session,
    model_id: int,
    payload: MonitoringReportCreate,
) -> ModelMonitoringReport:
    feature_scores = {
        name: population_stability_index(samples.reference, samples.current)
        for name, samples in payload.features.items()
    }
    feature_score = max(feature_scores.values(), default=0.0)
    prediction_score = population_stability_index(
        payload.predictions.reference, payload.predictions.current
    )
    maximum = max(feature_score, prediction_score)
    settings = get_settings()
    if maximum >= settings.drift_critical_threshold:
        status = "CRITICAL"
    elif maximum >= settings.drift_warning_threshold:
        status = "WARNING"
    else:
        status = "HEALTHY"
    report = ModelMonitoringReport(
        model_version_id=model_id,
        window_start=payload.window_start,
        window_end=payload.window_end,
        feature_drift_score=feature_score,
        prediction_drift_score=prediction_score,
        status=status,
        details={"feature_psi": feature_scores},
    )
    database.add(report)
    database.flush()
    return report


def feedback_summary(database: Session, model_id: int) -> dict[str, int | float | None]:
    rows = database.execute(
        select(DetectionFeedback.verdict, func.count(DetectionFeedback.id))
        .join(DetectionEvent, DetectionEvent.id == DetectionFeedback.detection_event_id)
        .where(DetectionEvent.model_version_id == model_id)
        .group_by(DetectionFeedback.verdict)
    ).all()
    counts = {verdict: count for verdict, count in rows}
    true_positive = int(counts.get("TRUE_POSITIVE", 0))
    false_positive = int(counts.get("FALSE_POSITIVE", 0))
    total = true_positive + false_positive
    return {
        "model_version_id": model_id,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "confirmed_precision": round(true_positive / total, 6) if total else None,
    }
