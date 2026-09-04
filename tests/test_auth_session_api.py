from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from cybersentinel_ai.auth.router import router
from cybersentinel_ai.db.database import Base, build_engine, get_db
from cybersentinel_ai.db.models import AuditLog, User
from cybersentinel_ai.security.jwt import hash_password


def test_login_refresh_rotation_and_logout_revoke(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'auth-session.db'}")
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    with testing_session() as database:
        database.add(
            User(
                email="analyst@example.test",
                username="analyst",
                hashed_password=hash_password("StrongPassword123!"),
                role="ANALYST",
                is_active=True,
            )
        )
        database.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as database:
            yield database

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    login = client.post(
        "/auth/login",
        json={
            "email": "analyst@example.test",
            "password": "StrongPassword123!",
        },
    )
    assert login.status_code == 200
    first = login.json()
    assert first["expires_in"] == 15 * 60
    assert first["refresh_expires_in"] == 7 * 24 * 60 * 60

    first_headers = {"Authorization": f"Bearer {first['access_token']}"}
    assert client.get("/auth/me", headers=first_headers).status_code == 200

    refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": first["refresh_token"]},
    )
    assert refresh.status_code == 200
    second = refresh.json()
    assert second["refresh_token"] != first["refresh_token"]
    second_headers = {"Authorization": f"Bearer {second['access_token']}"}
    assert client.get("/auth/me", headers=second_headers).status_code == 200

    assert client.get("/auth/me", headers=first_headers).status_code == 401
    reused = client.post(
        "/auth/refresh",
        json={"refresh_token": first["refresh_token"]},
    )
    assert reused.status_code == 401

    assert client.get("/auth/me", headers=second_headers).status_code == 401

    third = client.post(
        "/auth/login",
        json={
            "email": "analyst@example.test",
            "password": "StrongPassword123!",
        },
    ).json()
    third_headers = {"Authorization": f"Bearer {third['access_token']}"}
    wrong_password = client.post(
        "/auth/change-password",
        headers=third_headers,
        json={
            "current_password": "WrongPassword123!",
            "new_password": "NewStrongPassword456!",
        },
    )
    assert wrong_password.status_code == 400
    changed = client.post(
        "/auth/change-password",
        headers=third_headers,
        json={
            "current_password": "StrongPassword123!",
            "new_password": "NewStrongPassword456!",
        },
    )
    assert changed.status_code == 204
    assert client.get("/auth/me", headers=third_headers).status_code == 401

    old_login = client.post(
        "/auth/login",
        json={
            "email": "analyst@example.test",
            "password": "StrongPassword123!",
        },
    )
    assert old_login.status_code == 401

    fourth = client.post(
        "/auth/login",
        json={
            "email": "analyst@example.test",
            "password": "NewStrongPassword456!",
        },
    ).json()
    fourth_headers = {"Authorization": f"Bearer {fourth['access_token']}"}
    assert client.get("/auth/me", headers=fourth_headers).status_code == 200

    logout = client.post(
        "/auth/logout",
        headers=fourth_headers,
        json={"refresh_token": fourth["refresh_token"]},
    )
    assert logout.status_code == 204
    assert client.get("/auth/me", headers=fourth_headers).status_code == 401

    with testing_session() as database:
        actions = set(database.scalars(select(AuditLog.action)).all())
    assert "REFRESH_TOKEN_REUSE" in actions
    assert "PASSWORD_CHANGED" in actions

    engine.dispose()
