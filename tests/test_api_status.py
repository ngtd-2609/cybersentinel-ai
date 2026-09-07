from collections.abc import Generator
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from cybersentinel_ai.api.main import app
from cybersentinel_ai.db.database import Base, get_db
from cybersentinel_ai.security.dependencies import get_current_user


def test_component_status_separates_observed_and_configured_states() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def database_override() -> Generator[Session, None, None]:
        with factory() as database:
            yield database

    app.dependency_overrides[get_db] = database_override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, role="ADMIN", is_active=True
    )
    try:
        response = TestClient(app).get("/status/components")
        assert response.status_code == 200
        payload = response.json()
        assert payload["components"][0]["state"] == "OPERATIONAL"
        assert payload["components"][1]["state"] == "CONNECTED"
        assert "basis" in payload["components"][2]
        assert payload["queues"]["dead_letter_jobs"] == 0
        assert payload["queues"]["failed_notifications"] == 0
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
