"""Auth use cases. Services own transactions; routers only translate HTTP."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import DomainError, Forbidden, Unauthorized
from app.modules.auth.email import EmailSender
from app.modules.auth.models import OneTimeToken, RefreshToken, User
from app.modules.auth.security import (
    create_access_token,
    hash_password,
    hash_token,
    new_opaque_token,
    verify_password,
)

VERIFY = "verify_email"
RESET = "password_reset"


class InvalidToken(DomainError):
    status = 400
    title = "Invalid or expired token"


def _now() -> datetime:
    return datetime.now(UTC)


async def _issue_one_time(session: AsyncSession, user: User, purpose: str, ttl: timedelta) -> str:
    raw, digest = new_opaque_token()
    session.add(
        OneTimeToken(user_id=user.id, purpose=purpose, token_hash=digest, expires_at=_now() + ttl)
    )
    return raw


async def register(session: AsyncSession, sender: EmailSender, email: str, password: str) -> None:
    """Create an account. Always looks the same to the caller (no account enumeration)."""
    password_hash = await asyncio.to_thread(hash_password, password)  # same cost either way
    existing = await session.scalar(select(User).where(User.email == email))
    if existing is not None:
        return
    user = User(email=email, password_hash=password_hash)
    session.add(user)
    try:
        await session.flush()
    except IntegrityError:  # concurrent registration of the same email
        await session.rollback()
        return
    settings = get_settings()
    raw = await _issue_one_time(
        session, user, VERIFY, timedelta(hours=settings.verify_email_ttl_hours)
    )
    await session.commit()
    link = f"{settings.frontend_url}/verify-email?token={raw}"
    await sender.send(email, "Verify your Qorvexa email", f"Welcome to Qorvexa.\nVerify: {link}\n")


async def _consume_one_time(session: AsyncSession, raw: str, purpose: str) -> OneTimeToken:
    tok = await session.scalar(
        select(OneTimeToken)
        .where(OneTimeToken.token_hash == hash_token(raw), OneTimeToken.purpose == purpose)
        .with_for_update()
    )
    if tok is None or tok.used_at is not None or tok.expires_at <= _now():
        raise InvalidToken("The link is invalid or has expired")
    tok.used_at = _now()
    return tok


async def verify_email(session: AsyncSession, raw: str) -> None:
    tok = await _consume_one_time(session, raw, VERIFY)
    user = await session.get(User, tok.user_id)
    if user is not None and user.email_verified_at is None:
        user.email_verified_at = _now()
    await session.commit()


async def _new_refresh(
    session: AsyncSession, user_id: uuid.UUID, family_id: uuid.UUID
) -> tuple[str, RefreshToken]:
    raw, digest = new_opaque_token()
    row = RefreshToken(
        user_id=user_id,
        family_id=family_id,
        token_hash=digest,
        expires_at=_now() + timedelta(days=get_settings().jwt_refresh_ttl_days),
    )
    session.add(row)
    await session.flush()
    return raw, row


async def login(session: AsyncSession, email: str, password: str) -> tuple[str, str]:
    """Return (access_token, refresh_token). Same 401 for unknown user and bad password."""
    user = await session.scalar(select(User).where(User.email == email))
    ok = await asyncio.to_thread(verify_password, password, user.password_hash if user else None)
    if user is None or not ok or user.status != "active":
        raise Unauthorized("Invalid credentials")
    if user.email_verified_at is None:
        raise Forbidden("Email not verified")
    refresh, _ = await _new_refresh(session, user.id, uuid.uuid4())
    await session.commit()
    return create_access_token(user.id, user.role), refresh


async def _revoke_family(session: AsyncSession, family_id: uuid.UUID) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=_now())
    )


async def refresh(session: AsyncSession, raw: str) -> tuple[str, str]:
    """Rotate a refresh token. Reuse of an already-rotated token revokes the whole family."""
    row = await session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw)).with_for_update()
    )
    if row is None:
        raise Unauthorized("Invalid session")
    if row.revoked_at is not None:
        await _revoke_family(session, row.family_id)
        await session.commit()  # persist the revocation before rejecting
        raise Unauthorized("Invalid session")
    if row.expires_at <= _now():
        raise Unauthorized("Session expired")
    user = await session.get(User, row.user_id)
    if user is None or user.status != "active":
        await _revoke_family(session, row.family_id)
        await session.commit()
        raise Unauthorized("Invalid session")
    new_raw, new_row = await _new_refresh(session, user.id, row.family_id)
    row.revoked_at = _now()
    row.replaced_by = new_row.id
    await session.commit()
    return create_access_token(user.id, user.role), new_raw


async def logout(session: AsyncSession, user_id: uuid.UUID, raw: str | None) -> None:
    if raw:
        row = await session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw))
        )
        if row is not None and row.user_id == user_id:
            await _revoke_family(session, row.family_id)
            await session.commit()


async def forgot_password(session: AsyncSession, sender: EmailSender, email: str) -> None:
    user = await session.scalar(select(User).where(User.email == email))
    if user is None or user.status != "active":
        return
    settings = get_settings()
    raw = await _issue_one_time(
        session, user, RESET, timedelta(hours=settings.password_reset_ttl_hours)
    )
    await session.commit()
    link = f"{settings.frontend_url}/reset-password?token={raw}"
    await sender.send(email, "Reset your Qorvexa password", f"Reset: {link}\nIgnore if not you.\n")


async def reset_password(session: AsyncSession, raw: str, new_password: str) -> None:
    new_hash = await asyncio.to_thread(hash_password, new_password)
    tok = await _consume_one_time(session, raw, RESET)
    user = await session.get(User, tok.user_id)
    if user is None or user.status != "active":
        raise InvalidToken("The link is invalid or has expired")
    user.password_hash = new_hash
    if user.email_verified_at is None:
        user.email_verified_at = _now()  # the link proved control of the mailbox
    await session.execute(  # sign out everywhere
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=_now())
    )
    await session.commit()
