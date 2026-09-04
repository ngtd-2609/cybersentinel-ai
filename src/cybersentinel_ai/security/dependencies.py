from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from cybersentinel_ai.auth.repository import get_user_by_email
from cybersentinel_ai.auth.session_service import is_user_session_active
from cybersentinel_ai.db.database import get_db
from cybersentinel_ai.security.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_access_token(token)

        email = payload.get("sub")
        session_id = payload.get("sid")

    except JWTError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        ) from exc

    user = get_user_by_email(
        db,
        email,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Inactive user",
        )

    if not is_user_session_active(db, session_id, user.id):
        raise HTTPException(
            status_code=401,
            detail="Session revoked or expired",
        )

    return user
