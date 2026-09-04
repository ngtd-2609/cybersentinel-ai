import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import DetectionEventCreate, IncidentCreate
from cybersentinel_ai.db.database import Base, atomic, build_engine
from cybersentinel_ai.db.models import DetectionEvent, Incident, IncidentTimeline
from cybersentinel_ai.db.repository import create_detection_event, create_incident


def detection_payload() -> DetectionEventCreate:
    return DetectionEventCreate(
        source_ip="198.51.100.10",
        destination_ip="203.0.113.20",
        destination_port=443,
        predicted_label="Web Attack",
        classifier_confidence=0.97,
        anomaly_score=0.88,
        rule_score=0.75,
        risk_score=92.0,
        severity="CRITICAL",
        requires_review=True,
    )


def test_atomic_rolls_back_a_partially_created_business_action():
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as database:
        with pytest.raises(RuntimeError, match="audit failed"), atomic(database):
            create_detection_event(database, detection_payload(), commit=False)
            raise RuntimeError("audit failed")

        count = database.scalar(select(func.count()).select_from(DetectionEvent))

    assert count == 0


def test_foreign_keys_reject_orphans_and_cascade_timelines():
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as database:
        with pytest.raises(IntegrityError), atomic(database):
            create_incident(
                database,
                IncidentCreate(
                    title="Orphan incident",
                    severity="HIGH",
                    detection_event_id=999999,
                ),
                commit=False,
            )

        with atomic(database):
            event = create_detection_event(database, detection_payload(), commit=False)
            incident = create_incident(
                database,
                IncidentCreate(
                    title="Linked incident",
                    severity="CRITICAL",
                    detection_event_id=event.id,
                ),
                commit=False,
            )
            incident_id = incident.id

        timeline_count = database.scalar(
            select(func.count())
            .select_from(IncidentTimeline)
            .where(IncidentTimeline.incident_id == incident_id)
        )
        assert timeline_count == 2

        with atomic(database):
            database.delete(database.get(Incident, incident_id))

        timeline_count = database.scalar(
            select(func.count())
            .select_from(IncidentTimeline)
            .where(IncidentTimeline.incident_id == incident_id)
        )

    assert timeline_count == 0
