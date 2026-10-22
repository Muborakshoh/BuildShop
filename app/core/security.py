from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


UNUSABLE_PASSWORD_PREFIX = "!"


def is_password_usable(hashed_password: str) -> bool:
    """Return False for accounts that cannot log in with a password (e.g. Telegram-only)."""
    return bool(hashed_password) and not hashed_password.startswith(UNUSABLE_PASSWORD_PREFIX)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not is_password_usable(hashed_password):
        return False
    return pwd_context.verify(plain_password, hashed_password)


def create_token(subject: str, token_type: str, expires_delta: timedelta, extra_claims: dict[str, Any] | None = None) -> str:
    expire = datetime.now(UTC) + expires_delta
    payload: dict[str, Any] = {"sub": subject, "type": token_type, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

