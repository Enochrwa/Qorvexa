"""Password hashing, JWT access tokens and opaque token helpers. No I/O here."""

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import get_settings

_hasher = PasswordHasher()  # Argon2id with library defaults
# Verified against when the account does not exist, so timing does not reveal it.
_DUMMY_HASH = _hasher.hash("not-a-real-password")

ROLE_RANK = {"viewer": 0, "editor": 1, "admin": 2}

# Small deny-list of very common passwords; extend or swap for a full list later.
COMMON_PASSWORDS = frozenset(
    {
        "password12",
        "password123",
        "1234567890",
        "12345678910",
        "qwertyuiop",
        "iloveyou12",
        "letmein1234",
        "welcome123",
        "admin12345",
        "changeme123",
        "passw0rd123",
        "0123456789",
        "qwerty12345",
        "abc1234567",
        "monkey12345",
        "football123",
        "baseball123",
        "dragon12345",
    }
)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Constant-effort verify; a missing hash is checked against a dummy so timing is similar."""
    try:
        _hasher.verify(password_hash or _DUMMY_HASH, password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    return password_hash is not None


def new_opaque_token() -> tuple[str, str]:
    """Return (raw token to give the client, sha256 hex to store)."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class AccessClaims:
    user_id: uuid.UUID
    role: str


def create_access_token(user_id: uuid.UUID, role: str, now: datetime | None = None) -> str:
    settings = get_settings()
    issued = now or datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": issued,
        "exp": issued + timedelta(minutes=settings.jwt_access_ttl_minutes),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> AccessClaims | None:
    """Return claims, or None if the token is invalid, expired or malformed."""
    try:
        data = jwt.decode(
            token,
            get_settings().jwt_secret,
            algorithms=["HS256"],
            options={"require": ["sub", "role", "exp", "iat", "jti"]},
        )
        return AccessClaims(user_id=uuid.UUID(data["sub"]), role=str(data["role"]))
    except (jwt.PyJWTError, ValueError):
        return None
