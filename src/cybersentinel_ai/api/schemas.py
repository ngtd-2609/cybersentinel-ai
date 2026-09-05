from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DetectionEventCreate(BaseModel):
    external_id: str | None = Field(default=None, max_length=128)
    source_type: str | None = Field(default=None, max_length=64)
    occurred_at: datetime | None = None
    asset_id: str | None = Field(default=None, max_length=128)
    hostname: str | None = Field(default=None, max_length=255)
    affected_user: str | None = Field(default=None, max_length=255)
    ioc_type: str | None = Field(default=None, max_length=32)
    ioc_value: str | None = Field(default=None, max_length=512)
    correlation_key: str | None = Field(default=None, max_length=255)
    model_version_id: int | None = Field(default=None, ge=1)
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

    @field_validator("occurred_at")
    @classmethod
    def normalize_occurred_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @field_validator("severity")
    @classmethod
    def normalize_severity(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            raise ValueError("invalid severity")
        return normalized



class DetectionEventBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_ip: str | None
    predicted_label: str
    risk_score: float
    severity: str


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


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    severity: str = Field(min_length=1, max_length=16)
    status: str = Field(default="OPEN", max_length=32)
    description: str | None = None
    detection_event_id: int | None = None


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    severity: str
    status: str
    description: str | None
    detection_event_id: int | None
    detection_event: DetectionEventBrief | None = None
    correlation_key: str | None = None
    event_count: int = 1
    last_event_at: datetime | None = None
    created_at: datetime


class IncidentUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=32)


class IncidentPage(BaseModel):
    items: list[IncidentRead]
    total: int
    limit: int
    offset: int


class IncidentTimelineBase(BaseModel):
    action: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=1000)


class IncidentTimelineCreate(IncidentTimelineBase):
    pass


class IncidentTimelineRead(IncidentTimelineBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    created_at: datetime


class IngestionEventCreate(DetectionEventCreate):
    external_id: str = Field(min_length=1, max_length=128)
    source_type: str = Field(min_length=1, max_length=64)

    @field_validator("occurred_at", mode="before")
    @classmethod
    def require_timestamp_timezone(
        cls, value: datetime | str | None
    ) -> datetime | str | None:
        if value is None:
            return None
        parsed = (
            value
            if isinstance(value, datetime)
            else datetime.fromisoformat(value)
        )
        if parsed.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")
        return value

    @field_validator("external_id", "source_type")
    @classmethod
    def strip_identity_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class IngestionBatchCreate(BaseModel):
    events: list[IngestionEventCreate] = Field(min_length=1, max_length=5000)


class IngestionItemResult(BaseModel):
    external_id: str
    job_id: int
    status: str
    duplicate: bool


class IngestionBatchResult(BaseModel):
    accepted: int
    duplicates: int
    items: list[IngestionItemResult]


class IngestionJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: str
    external_id: str
    status: str
    attempts: int
    max_attempts: int
    last_error: str | None
    next_retry_at: datetime | None
    detection_event_id: int | None
    received_at: datetime
    updated_at: datetime


class NotificationDeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detection_event_id: int
    incident_id: int | None
    channel: str
    status: str
    attempts: int
    max_attempts: int
    last_error: str | None
    next_retry_at: datetime | None
    created_at: datetime
    sent_at: datetime | None


class IngestionTraceRead(BaseModel):
    job: IngestionJobRead
    detection_event: DetectionEventRead | None
    incident_ids: list[int]
    notifications: list[NotificationDeliveryRead]


class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    enabled: bool = True
    priority: int = Field(default=100, ge=0, le=10000)
    min_risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    severities: list[str] = Field(default_factory=list, max_length=8)
    label_pattern: str | None = Field(default=None, max_length=128)
    require_review: bool = False
    auto_create_incident: bool = False
    notification_channels: list[str] = Field(default_factory=list, max_length=4)

    @field_validator("severities", mode="before")
    @classmethod
    def normalize_severities(cls, value: list[str] | str) -> list[str]:
        allowed = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        if isinstance(value, str):
            value = [item for item in value.split(",") if item]
        normalized = [item.upper() for item in value]
        if any(item not in allowed for item in normalized):
            raise ValueError("invalid severity")
        return list(dict.fromkeys(normalized))

    @field_validator("notification_channels", mode="before")
    @classmethod
    def normalize_channels(cls, value: list[str] | str) -> list[str]:
        allowed = {"webhook", "slack"}
        if isinstance(value, str):
            value = [item for item in value.split(",") if item]
        normalized = [item.lower() for item in value]
        if any(item not in allowed for item in normalized):
            raise ValueError("invalid notification channel")
        return list(dict.fromkeys(normalized))


class AlertRuleUpdate(BaseModel):
    enabled: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=10000)
    min_risk_score: float | None = Field(default=None, ge=0.0, le=100.0)
    severities: list[str] | None = Field(default=None, max_length=8)
    label_pattern: str | None = Field(default=None, max_length=128)
    require_review: bool | None = None
    auto_create_incident: bool | None = None
    notification_channels: list[str] | None = Field(default=None, max_length=4)

    @field_validator("severities")
    @classmethod
    def validate_severities(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return AlertRuleCreate.normalize_severities(value)

    @field_validator("notification_channels")
    @classmethod
    def validate_channels(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return AlertRuleCreate.normalize_channels(value)


class AlertRuleRead(AlertRuleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class DeadLetterRetryResult(BaseModel):
    job_id: int
    status: str
