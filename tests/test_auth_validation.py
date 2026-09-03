from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from cybersentinel_ai.auth import service
from cybersentinel_ai.auth.schemas import UserCreate, UserLogin


def valid_user_payload(**overrides):
    payload = {
        "email": "analyst@example.com",
        "username": "soc.analyst",
        "password": "StrongPass123!",
        "full_name": "SOC Analyst",
    }
    payload.update(overrides)
    return payload


def test_user_create_normalizes_email_and_username():
    payload = UserCreate(
        **valid_user_payload(
            email="  Analyst@Example.COM ",
            username="  soc.analyst  ",
        )
    )

    assert payload.email == "analyst@example.com"
    assert payload.username == "soc.analyst"


@pytest.mark.parametrize(
    "password",
    [
        "Short1!",
        "alllowercase1!",
        "ALLUPPERCASE1!",
        "NoNumbersHere!",
        "NoSpecial1234",
    ],
)
def test_user_create_rejects_weak_password(password):
    with pytest.raises(ValidationError):
        UserCreate(**valid_user_payload(password=password))


def test_user_create_rejects_invalid_email_and_username():
    with pytest.raises(ValidationError):
        UserCreate(**valid_user_payload(email="invalid-email"))

    with pytest.raises(ValidationError):
        UserCreate(**valid_user_payload(username="invalid username"))


def test_login_normalizes_email():
    payload = UserLogin(
        email="  Analyst@Example.COM ",
        password="any-password",
    )

    assert payload.email == "analyst@example.com"


def test_register_user_rejects_duplicate_username(monkeypatch):
    existing_user = SimpleNamespace(username="soc.analyst")
    monkeypatch.setattr(
        service,
        "get_user_by_email",
        lambda db, email: None,
    )
    monkeypatch.setattr(
        service,
        "get_user_by_username",
        lambda db, username: existing_user,
    )

    with pytest.raises(ValueError, match="Username already exists"):
        service.register_user(
            db=object(),
            payload=UserCreate(**valid_user_payload()),
        )
