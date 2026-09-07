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
    Asset,
    DetectionEvent,
    Incident,
    IncidentAsset,
    IncidentDetection,
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
        ("RANSOMWARE", "CRITICAL", 97.5, "198.51.100.23", "prod-web-01", "prod-web-01", 1),
        ("SSH-BRUTE-FORCE", "HIGH", 88.4, "203.0.113.44", "prod-web-01", "prod-web-01", 18),
        ("PRIVILEGE-ESCALATION", "HIGH", 86.2, "203.0.113.44", "prod-web-01", "prod-web-01", 11),
        ("MALICIOUS-PROCESS", "HIGH", 84.8, "203.0.113.44", "prod-web-01", "prod-web-01", 7),
        ("C2-TRAFFIC", "CRITICAL", 94.1, "203.0.113.109", "prod-web-01", "prod-web-01", 4),
        ("SUSPICIOUS-LOGIN", "MEDIUM", 71.5, "203.0.113.44", "prod-web-01", "prod-web-01", 15),
        ("WEB-ATTACK", "HIGH", 82.7, "198.51.100.158", "customer-portal", "customer-portal", 45),
        ("BENIGN", "LOW", 12.3, "192.0.2.10", "monitoring-01", "monitoring-01", 60),
    ]
    events = []
    for index, (
        label,
        severity,
        risk,
        source_ip,
        asset_id,
        hostname,
        minutes_ago,
    ) in enumerate(
        templates,
        start=1,
    ):
        ransomware_chain = index <= 6
        events.append(
            {
                "idempotency_key": f"{DEMO_PREFIX}event:{index}",
                "external_id": f"DEMO-{index:04d}",
                "source_type": "portfolio-seed",
                "occurred_at": now - timedelta(minutes=minutes_ago),
                "asset_id": asset_id,
                "hostname": hostname,
                "affected_user": "demo.user",
                "ioc_type": "ipv4",
                "ioc_value": source_ip,
                "correlation_key": (
                    "prod-web-01:ransomware-chain"
                    if ransomware_chain
                    else f"demo-{label.lower()}"
                ),
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
                "created_at": now - timedelta(minutes=minutes_ago),
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
        full_name="CyberSentinel Portfolio Viewer",
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
            role="VIEWER",
        )
        database.add(user)
        database.flush()
    else:
        user.username = payload.username
        user.full_name = payload.full_name
        user.role = "VIEWER"
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
        asset_templates = (
            {
                "id": "prod-web-01",
                "hostname": "PROD-WEB-01",
                "primary_ip": "10.20.0.15",
                "operating_system": "Ubuntu 24.04 LTS",
                "environment": "PROD",
                "criticality": "CRITICAL",
                "owner_team": "Platform Team",
                "internet_facing": True,
                "status": "ONLINE",
                "last_seen_at": now,
            },
            {
                "id": "customer-portal",
                "hostname": "CUSTOMER-PORTAL",
                "primary_ip": "10.20.0.20",
                "operating_system": "Debian 13",
                "environment": "PROD",
                "criticality": "HIGH",
                "owner_team": "Web Platform",
                "internet_facing": True,
                "status": "ONLINE",
                "last_seen_at": now - timedelta(minutes=45),
            },
            {
                "id": "monitoring-01",
                "hostname": "MONITORING-01",
                "primary_ip": "10.20.0.30",
                "operating_system": "Ubuntu 24.04 LTS",
                "environment": "PROD",
                "criticality": "MEDIUM",
                "owner_team": "SRE",
                "internet_facing": False,
                "status": "ONLINE",
                "last_seen_at": now - timedelta(minutes=60),
            },
        )
        for asset_values in asset_templates:
            asset = database.get(Asset, asset_values["id"])
            if asset is None:
                database.add(Asset(**asset_values))
            elif reset:
                for field, value in asset_values.items():
                    setattr(asset, field, value)
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
        if reset:
            canonical_titles = {template[0] for template in incident_templates}
            extra_incident_ids = list(
                database.scalars(
                    select(Incident.id).where(
                        Incident.detection_event_id.in_([event.id for event in events]),
                        Incident.title.not_in(canonical_titles),
                    )
                )
            )
            if extra_incident_ids:
                database.execute(
                    delete(IncidentTimeline).where(
                        IncidentTimeline.incident_id.in_(extra_incident_ids)
                    )
                )
                database.execute(
                    delete(Incident).where(Incident.id.in_(extra_incident_ids))
                )
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
                "priority": "P1" if severity == "CRITICAL" else "P2",
                "tags": ["portfolio", "attack-chain" if event_index == 0 else "triage"],
                "first_seen_at": events[event_index].created_at,
                "last_event_at": events[event_index].created_at,
                "resolved_at": now if incident_status == "RESOLVED" else None,
                "resolution_reason": (
                    "Validated and safely contained in the synthetic scenario."
                    if incident_status == "RESOLVED"
                    else None
                ),
            }
            if incident is None:
                incident = Incident(title=title, **values)
                database.add(incident)
                database.flush()
                incident.display_id = f"CS-{now.year}-{incident.id:04d}"
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

        ransomware_incident = incidents[0]
        ransomware_incident.event_count = 6
        ransomware_incident.first_seen_at = events[1].created_at
        ransomware_incident.last_event_at = events[0].created_at
        for event in events[:6]:
            link = database.get(IncidentDetection, (ransomware_incident.id, event.id))
            if link is None:
                database.add(
                    IncidentDetection(
                        incident_id=ransomware_incident.id,
                        detection_event_id=event.id,
                    )
                )
        for incident in incidents:
            event = next(item for item in events if item.id == incident.detection_event_id)
            already_linked_in_chain = (
                incident.id == ransomware_incident.id and event in events[:6]
            )
            if (
                not already_linked_in_chain
                and database.get(IncidentDetection, (incident.id, event.id)) is None
            ):
                database.add(
                    IncidentDetection(
                        incident_id=incident.id,
                        detection_event_id=event.id,
                    )
                )
            if event.asset_id and database.get(IncidentAsset, (incident.id, event.asset_id)) is None:
                database.add(IncidentAsset(incident_id=incident.id, asset_id=event.asset_id))

        rule_templates = (
            ("Ransomware containment", 10, 85, "CRITICAL,HIGH", "RANSOMWARE", True, True),
            ("C2 traffic escalation", 20, 85, "CRITICAL,HIGH", "C2-TRAFFIC", True, True),
            ("Data exfiltration review", 30, 85, "CRITICAL,HIGH", "DATA-EXFILTRATION", True, True),
            ("Privilege escalation", 40, 80, "CRITICAL,HIGH", "PRIVILEGE-ESCALATION", True, True),
            ("SSH credential brute force", 50, 75, "CRITICAL,HIGH", "SSH-BRUTE-FORCE", True, True),
            ("Web attack", 60, 75, "CRITICAL,HIGH", "WEB-ATTACK", True, True),
            ("Malicious process", 70, 75, "CRITICAL,HIGH", "MALICIOUS-PROCESS", True, True),
            ("Port scanning reconnaissance", 80, 60, "HIGH,MEDIUM", "PORT-SCAN", True, False),
            ("Suspicious login review", 90, 60, "HIGH,MEDIUM", "SUSPICIOUS-LOGIN", True, False),
            ("High-risk generic detection", 100, 90, "CRITICAL,HIGH", None, True, True),
        )
        for name, priority, risk, severities, label, review, auto_incident in rule_templates:
            rule = database.scalar(select(AlertRule).where(AlertRule.name == name))
            values = {
                "enabled": True,
                "priority": priority,
                "min_risk_score": risk,
                "severities": severities,
                "label_pattern": label,
                "require_review": review,
                "auto_create_incident": auto_incident,
                "notification_channels": "",
            }
            if rule is None:
                database.add(AlertRule(name=name, **values))
            elif reset:
                for field, value in values.items():
                    setattr(rule, field, value)

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
