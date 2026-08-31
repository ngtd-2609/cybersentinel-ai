from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DetectionEventCreate(BaseModel):
    source_ip: str | None = None
    destination_ip: str | None = None
    destination_port: int | None = Field(default=None, ge=0, le=65535)

    predicted_label: str = Field(min_length=1, max_length=128)
    classifier_confidence: float = Field(ge=0.0, le=1.0)
    anomaly_score: float = Field(ge=0.0, le=1.0)
    rule_score: float = Field(ge=0.0, le=1.0, default=0.0)

    risk_score: float = Field(ge=0.0, le=100.0)
    severity: str = Field(min_length=1, max_length=16)
    requires_review: bool = False


class DetectionEventRead(DetectionEventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class DashboardAttackType(BaseModel):
    name: str
    count: int


class DashboardThreatSource(BaseModel):
    source_ip: str
    count: int
    max_risk_score: float


class DashboardTimelinePoint(BaseModel):
    time: datetime
    total: int
    critical: int
    high: int
    medium: int
    low: int


class DashboardSummary(BaseModel):
    total_events: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    requires_review: int
    average_risk_score: float
    top_attack_types: list[DashboardAttackType]
    top_threat_sources: list[DashboardThreatSource]
    timeline: list[DashboardTimelinePoint]
    recent_events: list[DetectionEventRead]


class DetectionEventPage(BaseModel):
    items: list[DetectionEventRead]
    total: int
    limit: int
    offset: int
