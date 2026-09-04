from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.auth.mfa_service import (
    InvalidMfaChallengeError,
    InvalidMfaCodeError,
    confirm_enrollment,
    create_mfa_challenge,
    disable_mfa,
    get_mfa_status,
    start_enrollment,
    verify_mfa_challenge,
)
from cybersentinel_ai.auth.schemas import (
    MfaChallengeResponse,
    MfaCodeRequest,
    MfaDisableRequest,
    MfaEnrollmentResponse,
    MfaRecoveryCodesResponse,
    MfaStatusResponse,
    MfaVerifyRequest,
    PasswordChangeRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from cybersentinel_ai.auth.service import (
    AccountLockedError,
    authenticate_user,
    change_user_password,
    register_user,
)
from cybersentinel_ai.auth.session_service import (
    InvalidRefreshTokenError,
    RefreshTokenReuseError,
    issue_user_session,
    revoke_rotated_session_family,
    revoke_user_session,
    rotate_user_session,
)
from cybersentinel_ai.core.config import Settings, get_settings
from cybersentinel_ai.db.database import atomic, get_db
from cybersentinel_ai.security.dependencies import get_current_user
from cybersentinel_ai.security.rbac import UserRole, require_role

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
    settings: Settings = Depends(get_settings),
):
    if not settings.public_registration_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is disabled",
        )
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
    response_model=TokenResponse | MfaChallengeResponse,
)
def login(
    payload: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        user = authenticate_user(
            db,
            payload.email,
            payload.password,
        )
    except AccountLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    if user.role == UserRole.ADMIN.value and user.mfa_enabled:
        with atomic(db):
            challenge = create_mfa_challenge(
                db,
                user,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
            )
            log_action(
                db,
                user.id,
                "MFA_CHALLENGE_ISSUED",
                f"Issued MFA challenge for {user.email}",
                "USER",
                user.id,
                commit=False,
            )
        response.status_code = status.HTTP_202_ACCEPTED
        return MfaChallengeResponse(
            mfa_token=challenge.token,
            expires_in=challenge.expires_in,
        )

    with atomic(db):
        tokens = issue_user_session(
            db,
            user,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        log_action(
            db,
            user.id,
            "LOGIN_SUCCESS",
            f"User {user.email} logged in",
            "USER",
            user.id,
            commit=False,
        )

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
        refresh_expires_in=tokens.refresh_expires_in,
    )


@router.post(
    "/mfa/verify",
    response_model=TokenResponse,
)
def verify_mfa(
    payload: MfaVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    invalid_code = False
    try:
        with atomic(db):
            user = verify_mfa_challenge(db, payload.mfa_token, payload.code)
            if user is None:
                invalid_code = True
            else:
                tokens = issue_user_session(
                    db,
                    user,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent"),
                )
                log_action(
                    db,
                    user.id,
                    "MFA_VERIFIED",
                    f"Verified MFA and logged in {user.email}",
                    "USER",
                    user.id,
                    commit=False,
                )
    except (InvalidMfaChallengeError, InvalidMfaCodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    if invalid_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication code",
        )
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
        refresh_expires_in=tokens.refresh_expires_in,
    )


@router.post(
    "/mfa/enroll",
    response_model=MfaEnrollmentResponse,
)
def enroll_mfa(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    try:
        with atomic(db):
            secret, provisioning_uri = start_enrollment(current_user)
            log_action(
                db,
                current_user.id,
                "MFA_ENROLLMENT_STARTED",
                f"Started MFA enrollment for {current_user.email}",
                "USER",
                current_user.id,
                commit=False,
            )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MfaEnrollmentResponse(secret=secret, provisioning_uri=provisioning_uri)


@router.post(
    "/mfa/confirm",
    response_model=MfaRecoveryCodesResponse,
)
def confirm_mfa(
    payload: MfaCodeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    try:
        with atomic(db):
            recovery_codes = confirm_enrollment(db, current_user.id, payload.code)
            log_action(
                db,
                current_user.id,
                "MFA_ENABLED",
                f"Enabled MFA and revoked all sessions for {current_user.email}",
                "USER",
                current_user.id,
                commit=False,
            )
    except InvalidMfaCodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MfaRecoveryCodesResponse(recovery_codes=recovery_codes)


@router.post(
    "/mfa/disable",
    status_code=status.HTTP_204_NO_CONTENT,
)
def disable_user_mfa(
    payload: MfaDisableRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
) -> Response:
    try:
        with atomic(db):
            disable_mfa(db, current_user.id, payload.current_password, payload.code)
            log_action(
                db,
                current_user.id,
                "MFA_DISABLED",
                f"Disabled MFA and revoked all sessions for {current_user.email}",
                "USER",
                current_user.id,
                commit=False,
            )
    except (InvalidMfaCodeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/mfa/status",
    response_model=MfaStatusResponse,
)
def mfa_status(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    enabled, pending, remaining = get_mfa_status(db, current_user)
    return MfaStatusResponse(
        enabled=enabled,
        enrollment_pending=pending,
        recovery_codes_remaining=remaining,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        with atomic(db):
            user, tokens = rotate_user_session(
                db,
                payload.refresh_token,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
            )
            log_action(
                db,
                user.id,
                "REFRESH_SESSION",
                f"Rotated session for {user.email}",
                "USER",
                user.id,
                commit=False,
            )
    except RefreshTokenReuseError as exc:
        with atomic(db):
            revoked = revoke_rotated_session_family(
                db,
                payload.refresh_token,
                exc.user_id,
            )
            if revoked:
                log_action(
                    db,
                    exc.user_id,
                    "REFRESH_TOKEN_REUSE",
                    "Detected refresh-token reuse and revoked the session family",
                    "USER",
                    exc.user_id,
                    commit=False,
                )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
        refresh_expires_in=tokens.refresh_expires_in,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Response:
    with atomic(db):
        revoked = revoke_user_session(
            db,
            payload.refresh_token,
            current_user.id,
        )
        if revoked:
            log_action(
                db,
                current_user.id,
                "LOGOUT",
                f"Revoked session for {current_user.email}",
                "USER",
                current_user.id,
                commit=False,
            )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
)
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Response:
    try:
        change_user_password(
            db,
            current_user.id,
            payload.current_password,
            payload.new_password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user=Depends(get_current_user),
):
    return current_user
