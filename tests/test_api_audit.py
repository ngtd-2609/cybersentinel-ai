from collections.abc import Generator
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from cybersentinel_ai.api.audit_routes import router
from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.db.database import Base, get_db
from cybersentinel_ai.security.dependencies import get_current_user

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def override_get_db() -> Generator[Session, None, None]:
    database = TestingSession()
    try:
        yield database
    finally:
        database.close()


app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
    id=1,
    role="ADMIN",
    is_active=True,
)
client = TestClient(app)


def test_audit_logs_support_pagination_and_filters():
    with TestingSession() as database:
        log_action(
            database,
            1,
            "LOGIN_SUCCESS",
            "Successful login",
            "USER",
            1,
        )
        log_action(
            database,
            2,
            "UPDATE_STATUS",
            "Disabled account",
            "USER",
            2,
        )

    response = client.get(
        "/admin/audit-logs",
        params={
            "limit": 1,
            "offset": 0,
            "action": "update_status",
            "target_type": "user",
            "user_id": 2,
        },
    )

    assert response.status_code == 200
    page = response.json()
    assert page["total"] == 1
    assert page["limit"] == 1
    assert page["offset"] == 0
    assert len(page["items"]) == 1
    assert page["items"][0]["action"] == "UPDATE_STATUS"
    assert page["items"][0]["user_id"] == 2
