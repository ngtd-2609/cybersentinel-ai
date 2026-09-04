import base64
import hashlib
import hmac
import secrets
import struct
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import quote, urlencode

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from cybersentinel_ai.auth.session_service import revoke_all_user_sessions
from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.models import MfaChallenge, MfaRecoveryCode, User
from cybersentinel_ai.security.jwt import (
    create_mfa_challenge_token,
    decode_mfa_challenge_token,
    verify_password,
)

RECOVERY_CODE_COUNT = 10


class InvalidMfaChallengeError(ValueError):
    pass


class InvalidMfaCodeError(ValueError):
    pass


@dataclass(frozen=True)
class MfaChallengeResult:
    token: str
    expires_in: int


def _fernet() -> Fernet:
    digest = hashlib.sha256(get_settings().secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_totp_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode("ascii")).decode("ascii")


def decrypt_totp_secret(encrypted_secret: str) -> str:
    try:
        return _fernet().decrypt(encrypted_secret.encode("ascii")).decode("ascii")
    except InvalidToken as exc:
        raise InvalidMfaCodeError("MFA secret cannot be decrypted") from exc


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def generate_totp_code(secret: str, at_time: int | None = None) -> str:
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded, casefold=True)
    counter = int(time.time() if at_time is None else at_time) // 30
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


def verify_totp_code(secret: str, code: str, at_time: int | None = None) -> bool:
    normalized = code.strip().replace(" ", "")
    if len(normalized) != 6 or any(character not in "0123456789" for character in normalized):
        return False
    timestamp = int(time.time() if at_time is None else at_time)
    return any(
        hmac.compare_digest(generate_totp_code(secret, timestamp + offset * 30), normalized)
        for offset in (-1, 0, 1)
    )


def _normalize_recovery_code(code: str) -> str:
    return code.strip().replace("-", "").replace(" ", "").upper()


def hash_recovery_code(code: str) -> str:
    return hmac.new(
        get_settings().secret_key.encode("utf-8"),
        _normalize_recovery_code(code).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _generate_recovery_codes() -> list[str]:
    return [
        f"{secrets.token_hex(5)[:5]}-{secrets.token_hex(5)[:5]}".upper()
        for _ in range(RECOVERY_CODE_COUNT)
    ]


def start_enrollment(user: User) -> tuple[str, str]:
    if user.role != "ADMIN":
        raise ValueError("MFA enrollment is restricted to administrators")
    if user.mfa_enabled:
        raise ValueError("MFA is already enabled")
    secret = generate_totp_secret()
    user.mfa_pending_secret_encrypted = encrypt_totp_secret(secret)
    account = quote(user.email, safe="")
    issuer = get_settings().app_name
    uri = f"otpauth://totp/{quote(issuer, safe='')}:{account}?{urlencode({'secret': secret, 'issuer': issuer, 'algorithm': 'SHA1', 'digits': 6, 'period': 30})}"
    return secret, uri


def confirm_enrollment(db: Session, user_id: int, code: str) -> list[str]:
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None or user.role != "ADMIN" or not user.mfa_pending_secret_encrypted:
        raise InvalidMfaCodeError("No MFA enrollment is pending")
    secret = decrypt_totp_secret(user.mfa_pending_secret_encrypted)
    if not verify_totp_code(secret, code):
        raise InvalidMfaCodeError("Invalid authentication code")

    recovery_codes = _generate_recovery_codes()
    db.execute(delete(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user.id))
    db.add_all(
        MfaRecoveryCode(user_id=user.id, code_hash=hash_recovery_code(item))
        for item in recovery_codes
    )
    user.mfa_secret_encrypted = user.mfa_pending_secret_encrypted
    user.mfa_pending_secret_encrypted = None
    user.mfa_enabled = True
    revoke_all_user_sessions(db, user.id)
    db.flush()
    return recovery_codes


def create_mfa_challenge(
    db: Session,
    user: User,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> MfaChallengeResult:
    settings = get_settings()
    challenge = MfaChallenge(
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(minutes=settings.mfa_challenge_expire_minutes),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(challenge)
    db.flush()
    return MfaChallengeResult(
        token=create_mfa_challenge_token(user.email, challenge.id),
        expires_in=settings.mfa_challenge_expire_minutes * 60,
    )


def _consume_recovery_code(db: Session, user_id: int, code: str, now: datetime) -> bool:
    candidate = db.scalar(
        select(MfaRecoveryCode)
        .where(
            MfaRecoveryCode.user_id == user_id,
            MfaRecoveryCode.code_hash == hash_recovery_code(code),
            MfaRecoveryCode.used_at.is_(None),
        )
        .with_for_update()
    )
    if candidate is None:
        return False
    candidate.used_at = now
    return True


def verify_mfa_challenge(db: Session, token: str, code: str) -> User | None:
    try:
        payload = decode_mfa_challenge_token(token)
    except JWTError as exc:
        raise InvalidMfaChallengeError("Invalid or expired MFA challenge") from exc

    now = datetime.now(UTC)
    challenge = db.scalar(
        select(MfaChallenge).where(MfaChallenge.id == payload["cid"]).with_for_update()
    )
    if challenge is None or challenge.used_at is not None or _as_utc(challenge.expires_at) <= now:
        raise InvalidMfaChallengeError("Invalid or expired MFA challenge")
    user = db.scalar(select(User).where(User.id == challenge.user_id).with_for_update())
    if (
        user is None
        or not user.is_active
        or not user.mfa_enabled
        or not user.mfa_secret_encrypted
        or user.email != payload["sub"]
    ):
        challenge.used_at = now
        raise InvalidMfaChallengeError("Invalid or expired MFA challenge")

    valid = verify_totp_code(decrypt_totp_secret(user.mfa_secret_encrypted), code)
    if not valid:
        valid = _consume_recovery_code(db, user.id, code, now)
    if not valid:
        challenge.failed_attempts += 1
        if challenge.failed_attempts >= get_settings().mfa_challenge_max_attempts:
            challenge.used_at = now
        db.flush()
        return None

    challenge.used_at = now
    db.flush()
    return user


def disable_mfa(db: Session, user_id: int, current_password: str, code: str) -> None:
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None or not user.mfa_enabled or not user.mfa_secret_encrypted:
        raise ValueError("MFA is not enabled")
    if not verify_password(current_password, user.hashed_password):
        raise ValueError("Current password is incorrect")
    now = datetime.now(UTC)
    valid = verify_totp_code(decrypt_totp_secret(user.mfa_secret_encrypted), code)
    if not valid:
        valid = _consume_recovery_code(db, user.id, code, now)
    if not valid:
        raise InvalidMfaCodeError("Invalid authentication code")

    user.mfa_enabled = False
    user.mfa_secret_encrypted = None
    user.mfa_pending_secret_encrypted = None
    db.execute(delete(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user.id))
    revoke_all_user_sessions(db, user.id)
    db.flush()


def get_mfa_status(db: Session, user: User) -> tuple[bool, bool, int]:
    remaining = db.scalar(
        select(func.count(MfaRecoveryCode.id)).where(
            MfaRecoveryCode.user_id == user.id,
            MfaRecoveryCode.used_at.is_(None),
        )
    )
    return user.mfa_enabled, user.mfa_pending_secret_encrypted is not None, int(remaining or 0)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
