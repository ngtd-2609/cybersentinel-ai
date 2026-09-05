import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from cybersentinel_ai.auth.schemas import UserCreate
from cybersentinel_ai.core.config import Settings, get_settings
from cybersentinel_ai.db.database import SessionLocal, atomic
from cybersentinel_ai.db.models import (
    AlertRule,
    DetectionEvent,
    Incident,
    IncidentTimeline,
    ModelVersion,
    User,
    UserSession,
)
from cybersentinel_ai.security.jwt import hash_password

DEMO_PREFIX = "portfolio-demo:"


@dataclass(frozen=True)
class DemoSeedResult:
    user_id: int
    events: int
    incidents: int
    reset: bool


def _demo_events(now: datetime) -> list[dict]:
    templates = [
        ("RANSOMWARE", "CRITICAL", 97.5, "198.51.100.23", "finance-ws-07", 1),
        ("SSH-BRUTE-FORCE", "HIGH", 88.4, "203.0.113.44", "bastion-01", 3),
        ("MALWARE", "HIGH", 84.2, "192.0.2.91", "engineering-lt-12", 5),
        ("PORT-SCAN", "MEDIUM", 67.8, "198.51.100.77", "dmz-web-02", 7),
        ("DATA-EXFILTRATION", "CRITICAL", 94.1, "203.0.113.109", "db-prod-01", 9),
        ("PHISHING", "MEDIUM", 61.5, "192.0.2.36", "mail-gateway", 12),
        ("WEB-ATTACK", "HIGH", 82.7, "198.51.100.158", "customer-portal", 16),
        ("BENIGN", "LOW", 12.3, "192.0.2.10", "monitoring-01", 20),
    ]
    events = []
    for index, (label, severity, risk, source_ip, hostname, hours_ago) in enumerate(
        templates,
        start=1,
    ):
        events.append(
            {
                "idempotency_key": f"{DEMO_PREFIX}event:{index}",
                "external_id": f"DEMO-{index:04d}",
                "source_type": "portfolio-seed",
                "occurred_at": now - timedelta(hours=hours_ago),
                "asset_id": f"asset-{index:03d}",
                "hostname": hostname,
                "affected_user": "demo.user",
                "ioc_type": "ipv4",
                "ioc_value": source_ip,
                "correlation_key": f"demo-{label.lower()}",
                "source_ip": source_ip,
                "destination_ip": "10.20.0.15",
                "destination_port": 443 if index % 2 else 22,
                "predicted_label": label,
                "classifier_confidence": min(0.99, risk / 100 + 0.02),
                "anomaly_score": min(0.99, risk / 100),
                "rule_score": min(0.99, risk / 110),
                "risk_score": risk,
                "severity": severity,
                "requires_review": severity in {"CRITICAL", "HIGH"},
                "created_at": now - timedelta(hours=hours_ago),
            }
        )
    return events


def _upsert_demo_user(
    database: Session,
    settings: Settings,
    *,
    reset: bool,
) -> User:
    password = settings.demo_user_password
    if password is None:
        raise ValueError("Demo password is required")
    payload = UserCreate(
        email=settings.demo_user_email,
        username=settings.demo_user_username,
        password=password.get_secret_value(),
        full_name="CyberSentinel Portfolio Analyst",
    )
    user = database.scalar(select(User).where(User.email == payload.email))
    username_owner = database.scalar(
        select(User).where(User.username == payload.username)
    )
    if username_owner is not None and username_owner is not user:
        raise ValueError("Demo username belongs to another account")
    if user is not None and user.role == "ADMIN":
        raise ValueError("Refusing to convert an administrator into a demo user")
    if user is None:
        user = User(
            email=payload.email,
            username=payload.username,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role="ANALYST",
        )
        database.add(user)
        database.flush()
    else:
        user.username = payload.username
        user.full_name = payload.full_name
        user.role = "ANALYST"
        user.is_active = True
        user.failed_login_attempts = 0
        user.locked_until = None
        if reset:
            user.hashed_password = hash_password(payload.password)
            database.execute(delete(UserSession).where(UserSession.user_id == user.id))
    return user


def seed_demo_data(
    database: Session,
    settings: Settings,
    *,
    reset: bool = False,
) -> DemoSeedResult:
    if not settings.demo_seed_enabled or settings.environment.lower() != "portfolio":
        raise ValueError("Demo seed is only available in the portfolio environment")

    now = datetime.now(UTC).replace(microsecond=0)
    with atomic(database):
        user = _upsert_demo_user(database, settings, reset=reset)
        model = database.scalar(
            select(ModelVersion).where(
                ModelVersion.name == "CyberSentinel Portfolio Classifier",
                ModelVersion.version == "demo-1.0",
            )
        )
        if model is None:
            model = ModelVersion(
                name="CyberSentinel Portfolio Classifier",
                version="demo-1.0",
                task="network-intrusion-detection",
                stage="PRODUCTION",
                artifact_uri="demo://models/network-classifier",
                artifact_hash="demo-artifact-no-sensitive-data",
                dataset_uri="demo://datasets/synthetic-portfolio-events",
                dataset_hash="demo-dataset-no-sensitive-data",
                git_commit="portfolio-demo",
                metrics={"precision": 0.94, "recall": 0.91, "f1": 0.925},
            )
            database.add(model)
            database.flush()

        events: list[DetectionEvent] = []
        for values in _demo_events(now):
            event = database.scalar(
                select(DetectionEvent).where(
                    DetectionEvent.idempotency_key == values["idempotency_key"]
                )
            )
            if event is None:
                event = DetectionEvent(**values)
                database.add(event)
            elif reset:
                for field, value in values.items():
                    setattr(event, field, value)
            event.model_version_id = model.id
            events.append(event)
        database.flush()

        incident_templates = [
            ("[DEMO] Ransomware containment", "CRITICAL", "IN_PROGRESS", 0),
            ("[DEMO] SSH brute-force investigation", "HIGH", "OPEN", 1),
            ("[DEMO] Possible data exfiltration", "CRITICAL", "RESOLVED", 4),
        ]
        incidents: list[Incident] = []
        for title, severity, incident_status, event_index in incident_templates:
            incident = database.scalar(select(Incident).where(Incident.title == title))
            values = {
                "severity": severity,
                "status": incident_status,
                "description": "Synthetic portfolio incident for safe SOC workflow demonstration.",
                "detection_event_id": events[event_index].id,
                "correlation_key": events[event_index].correlation_key,
                "event_count": 1,
                "last_event_at": events[event_index].created_at,
            }
            if incident is None:
                incident = Incident(title=title, **values)
                database.add(incident)
                database.flush()
            elif reset:
                for field, value in values.items():
                    setattr(incident, field, value)

            timeline_entries = (
                ("INCIDENT_CREATED", "Synthetic detection promoted to a demo incident."),
                ("TRIAGE_NOTE", "Analyst preserved evidence and reviewed affected assets."),
            )
            if reset:
                database.execute(
                    delete(IncidentTimeline).where(
                        IncidentTimeline.incident_id == incident.id
                    )
                )
            for action, description in timeline_entries:
                existing = database.scalar(
                    select(IncidentTimeline).where(
                        IncidentTimeline.incident_id == incident.id,
                        IncidentTimeline.action == action,
                        IncidentTimeline.description == description,
                    )
                )
                if existing is None:
                    database.add(
                        IncidentTimeline(
                            incident_id=incident.id,
                            action=action,
                            description=description,
                        )
                    )
            incidents.append(incident)

        rule = database.scalar(
            select(AlertRule).where(AlertRule.name == "Portfolio critical detections")
        )
        if rule is None:
            database.add(
                AlertRule(
                    name="Portfolio critical detections",
                    enabled=True,
                    priority=10,
                    min_risk_score=85,
                    severities="CRITICAL,HIGH",
                    require_review=True,
                    auto_create_incident=True,
                    notification_channels="webhook",
                )
            )

    return DemoSeedResult(
        user_id=user.id,
        events=len(events),
        incidents=len(incidents),
        reset=reset,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed safe CyberSentinel portfolio data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Restore canonical demo state and revoke demo sessions",
    )
    args = parser.parse_args()
    settings = get_settings()
    with SessionLocal() as database:
        result = seed_demo_data(database, settings, reset=args.reset)
    values = asdict(result)
    print(
        "DEMO_SEED_OK "
        f"user_id={values['user_id']} events={values['events']} "
        f"incidents={values['incidents']} reset={str(values['reset']).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
