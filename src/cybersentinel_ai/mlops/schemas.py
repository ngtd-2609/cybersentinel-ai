from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ModelVersionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    task: str = Field(min_length=1, max_length=64)
    artifact_uri: str = Field(min_length=1, max_length=512)
    artifact_hash: str = Field(min_length=8, max_length=128)
    dataset_uri: str = Field(min_length=1, max_length=512)
    dataset_hash: str = Field(min_length=8, max_length=128)
    git_commit: str = Field(min_length=7, max_length=64)
    metrics: dict[str, float]

    @field_validator("task")
    @classmethod
    def normalize_task(cls, value: str) -> str:
        normalized = value.strip().upper()
        allowed = {
            "BINARY_CLASSIFICATION",
            "MULTICLASS_CLASSIFICATION",
            "ANOMALY_DETECTION",
            "RAG_COPILOT",
        }
        if normalized not in allowed:
            raise ValueError("unsupported model task")
        return normalized


class ModelVersionRead(ModelVersionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stage: str
    created_at: datetime
    updated_at: datetime


class ModelPromotionRequest(BaseModel):
    target_stage: Literal["STAGING", "PRODUCTION"]
    reason: str = Field(min_length=5, max_length=1000)


class ModelComparisonRequest(BaseModel):
    champion_id: int = Field(ge=1)
    challenger_id: int = Field(ge=1)


class ModelComparisonRead(BaseModel):
    champion_id: int
    challenger_id: int
    champion_score: float
    challenger_score: float
    recommended_model_id: int
    metric_deltas: dict[str, float]


class DriftSamples(BaseModel):
    reference: list[float] = Field(min_length=20, max_length=100000)
    current: list[float] = Field(min_length=20, max_length=100000)


class MonitoringReportCreate(BaseModel):
    window_start: datetime
    window_end: datetime
    features: dict[str, DriftSamples] = Field(min_length=1, max_length=100)
    predictions: DriftSamples

    @model_validator(mode="after")
    def validate_window(self) -> "MonitoringReportCreate":
        if self.window_start.tzinfo is None or self.window_end.tzinfo is None:
            raise ValueError("monitoring window timestamps must include a timezone")
        self.window_start = self.window_start.astimezone(UTC)
        self.window_end = self.window_end.astimezone(UTC)
        if self.window_end <= self.window_start:
            raise ValueError("window_end must be after window_start")
        return self


class MonitoringReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_version_id: int
    window_start: datetime
    window_end: datetime
    feature_drift_score: float
    prediction_drift_score: float
    status: str
    details: dict
    created_at: datetime


class DetectionProvenanceRead(BaseModel):
    detection_event_id: int
    model: ModelVersionRead | None


class DetectionFeedbackCreate(BaseModel):
    verdict: Literal["TRUE_POSITIVE", "FALSE_POSITIVE"]
    notes: str | None = Field(default=None, max_length=1000)


class DetectionFeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detection_event_id: int
    analyst_id: int | None
    verdict: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class FeedbackSummaryRead(BaseModel):
    model_version_id: int
    true_positive: int
    false_positive: int
    confirmed_precision: float | None
