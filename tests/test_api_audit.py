from collections.abc import Generator
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from cybersentinel_ai.api.audit_routes import router
from cybersentinel_ai.audit.context import (
    RequestAuditContext,
    reset_request_context,
    set_request_context,
)
from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.db.database import Base, get_db
from cybersentinel_ai.db.models import AuditLog
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


def test_audit_log_captures_request_metadata():
    token = set_request_context(
        RequestAuditContext(
            request_id="audit-request-123",
            ip_address="203.0.113.9",
            user_agent="Audit test agent",
        )
    )
    try:
        with TestingSession() as database:
            created = log_action(database, None, "TEST_CONTEXT", "Context metadata")
            stored = database.scalar(select(AuditLog).where(AuditLog.id == created.id))
            assert stored is not None
            assert stored.request_id == "audit-request-123"
            assert stored.ip_address == "203.0.113.9"
            assert stored.user_agent == "Audit test agent"
    finally:
        reset_request_context(token)
