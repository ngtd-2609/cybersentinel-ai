from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.auth.schemas import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from cybersentinel_ai.auth.service import (
    authenticate_user,
    register_user,
)
from cybersentinel_ai.db.database import get_db
from cybersentinel_ai.security.dependencies import get_current_user
from cybersentinel_ai.security.jwt import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserResponse,
)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        return register_user(
            db,
            payload,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        payload.email,
        payload.password,
    )

    if not user:
        log_action(
            db,
            None,
            "LOGIN_FAILED",
            f"Failed login attempt for {payload.email}",
            "USER",
            None,
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    log_action(
        db,
        user.id,
        "LOGIN_SUCCESS",
        f"User {user.email} logged in",
        "USER",
        user.id,
    )

    return TokenResponse(
        access_token=create_access_token(
            user.email
        )
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user=Depends(get_current_user),
):
    return current_user
