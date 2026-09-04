from collections.abc import Generator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from cybersentinel_ai.auth.mfa_service import generate_totp_code
from cybersentinel_ai.auth.router import router
from cybersentinel_ai.db.database import Base, build_engine, get_db
from cybersentinel_ai.db.models import AuditLog, MfaRecoveryCode, User
from cybersentinel_ai.security.jwt import hash_password


def build_client(tmp_path) -> tuple[TestClient, sessionmaker]:
    engine = build_engine(f"sqlite:///{tmp_path / 'admin-mfa.db'}")
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    with testing_session() as database:
        database.add_all(
            [
                User(
                    email="admin@example.test",
                    username="admin",
                    hashed_password=hash_password("StrongPassword123!"),
                    role="ADMIN",
                    is_active=True,
                ),
                User(
                    email="analyst@example.test",
                    username="analyst",
                    hashed_password=hash_password("StrongPassword123!"),
                    role="ANALYST",
                    is_active=True,
                ),
            ]
        )
        database.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as database:
            yield database

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), testing_session


def login(client: TestClient, email: str = "admin@example.test"):
    return client.post(
        "/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )


def test_admin_mfa_enrollment_login_recovery_and_disable(tmp_path):
    client, testing_session = build_client(tmp_path)
    initial = login(client)
    assert initial.status_code == 200
    initial_token = initial.json()
    initial_headers = {"Authorization": f"Bearer {initial_token['access_token']}"}

    enrollment = client.post("/auth/mfa/enroll", headers=initial_headers)
    assert enrollment.status_code == 200
    secret = enrollment.json()["secret"]
    assert enrollment.json()["provisioning_uri"].startswith("otpauth://totp/")

    bad_confirmation = client.post(
        "/auth/mfa/confirm", headers=initial_headers, json={"code": "000000"}
    )
    assert bad_confirmation.status_code == 400
    confirmation = client.post(
        "/auth/mfa/confirm",
        headers=initial_headers,
        json={"code": generate_totp_code(secret)},
    )
    assert confirmation.status_code == 200
    recovery_codes = confirmation.json()["recovery_codes"]
    assert len(recovery_codes) == 10
    assert client.get("/auth/me", headers=initial_headers).status_code == 401

    with testing_session() as database:
        admin = database.scalar(select(User).where(User.email == "admin@example.test"))
        assert admin is not None
        assert admin.mfa_enabled
        assert admin.mfa_secret_encrypted != secret
        stored_codes = database.scalars(
            select(MfaRecoveryCode).where(MfaRecoveryCode.user_id == admin.id)
        ).all()
        assert len(stored_codes) == 10
        assert all(item.code_hash not in recovery_codes for item in stored_codes)

    challenge = login(client)
    assert challenge.status_code == 202
    challenge_body = challenge.json()
    assert challenge_body["mfa_required"] is True
    assert "access_token" not in challenge_body

    verified = client.post(
        "/auth/mfa/verify",
        json={
            "mfa_token": challenge_body["mfa_token"],
            "code": recovery_codes[0],
        },
    )
    assert verified.status_code == 200
    verified_headers = {"Authorization": f"Bearer {verified.json()['access_token']}"}
    assert client.get("/auth/me", headers=verified_headers).status_code == 200
    assert (
        client.post(
            "/auth/mfa/verify",
            json={
                "mfa_token": challenge_body["mfa_token"],
                "code": recovery_codes[0],
            },
        ).status_code
        == 401
    )

    second_challenge = login(client).json()["mfa_token"]
    reused_recovery = client.post(
        "/auth/mfa/verify",
        json={"mfa_token": second_challenge, "code": recovery_codes[0]},
    )
    assert reused_recovery.status_code == 401
    totp_verified = client.post(
        "/auth/mfa/verify",
        json={"mfa_token": second_challenge, "code": generate_totp_code(secret)},
    )
    assert totp_verified.status_code == 200

    disable_headers = {"Authorization": f"Bearer {totp_verified.json()['access_token']}"}
    disabled = client.post(
        "/auth/mfa/disable",
        headers=disable_headers,
        json={
            "current_password": "StrongPassword123!",
            "code": generate_totp_code(secret),
        },
    )
    assert disabled.status_code == 204
    assert client.get("/auth/me", headers=disable_headers).status_code == 401
    assert login(client).status_code == 200

    with testing_session() as database:
        actions = set(database.scalars(select(AuditLog.action)).all())
        assert {"MFA_ENABLED", "MFA_VERIFIED", "MFA_DISABLED"} <= actions


def test_mfa_enrollment_is_admin_only(tmp_path):
    client, _ = build_client(tmp_path)
    analyst = login(client, "analyst@example.test").json()
    response = client.post(
        "/auth/mfa/enroll",
        headers={"Authorization": f"Bearer {analyst['access_token']}"},
    )
    assert response.status_code == 403
