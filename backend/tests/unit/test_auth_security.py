import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.modules.auth.schemas import RegisterIn
from app.modules.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    hash_token,
    new_opaque_token,
    verify_password,
)


def test_password_hash_roundtrip_is_argon2id() -> None:
    h = hash_password("correct horse battery")
    assert h.startswith("$argon2id$")
    assert verify_password("correct horse battery", h)
    assert not verify_password("wrong password!!", h)


def test_verify_against_missing_hash_is_false() -> None:
    assert verify_password("anything-long-enough", None) is False


def test_opaque_tokens_are_random_and_stored_hashed() -> None:
    raw1, h1 = new_opaque_token()
    raw2, _ = new_opaque_token()
    assert raw1 != raw2
    assert h1 == hash_token(raw1) and raw1 not in h1


def test_access_token_roundtrip() -> None:
    uid = uuid.uuid4()
    claims = decode_access_token(create_access_token(uid, "editor"))
    assert claims is not None and claims.user_id == uid and claims.role == "editor"


def test_expired_access_token_rejected() -> None:
    old = datetime.now(UTC) - timedelta(hours=1)
    assert decode_access_token(create_access_token(uuid.uuid4(), "viewer", now=old)) is None


def test_tampered_or_wrong_alg_tokens_rejected() -> None:
    good = create_access_token(uuid.uuid4(), "viewer")
    assert decode_access_token(good[:-2] + "xx") is None
    none_alg = jwt.encode({"sub": str(uuid.uuid4()), "role": "admin"}, "", algorithm="none")
    assert decode_access_token(none_alg) is None
    assert decode_access_token("not-a-jwt") is None


def test_password_policy() -> None:
    with pytest.raises(ValidationError):
        RegisterIn(email="a@example.com", password="short")
    with pytest.raises(ValidationError):
        RegisterIn(email="a@example.com", password="password123")
    assert RegisterIn(email="a@example.com", password="a-long-enough-pass").password


def test_production_requires_real_secrets() -> None:
    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        Settings(app_env="production", jwt_secret="dev-only-change-me", cookie_secure=True)
    with pytest.raises(ValidationError):
        Settings(app_env="production", jwt_secret="x" * 40, cookie_secure=False)
    assert Settings(app_env="production", jwt_secret="x" * 40, cookie_secure=True)
