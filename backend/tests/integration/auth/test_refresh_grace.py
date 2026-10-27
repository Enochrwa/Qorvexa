"""Refresh-token reuse: a short grace for retries, but still theft detection otherwise."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.auth.models import RefreshToken, User
from tests.conftest import FakeEmailSender
from tests.integration.auth.helpers import CSRF, bearer, login, register_verified

API = "/api/v1/auth"


def _newest_cookie(client: AsyncClient) -> str:
    """The jar can hold the cookie we set by hand and the one the server set; take the latest."""
    values = [c.value for c in client.cookies.jar if c.name == "refresh_token"]
    return values[-1] if values else ""


async def _rotate(client: AsyncClient) -> tuple[str, str]:
    """Sign in, then rotate once. Returns (old cookie, new cookie)."""
    old = client.cookies.get("refresh_token") or ""
    assert (await client.post(f"{API}/refresh", headers=CSRF)).status_code == 200
    return old, client.cookies.get("refresh_token") or ""


async def _present(client: AsyncClient, token: str):
    """Send a refresh as a browser that still holds `token` (and no other cookie)."""
    client.cookies.clear()
    client.cookies.set("refresh_token", token, path="/api/v1/auth")
    return await client.post(f"{API}/refresh", headers=CSRF)


async def _age_rotations(db: AsyncSession, seconds: int) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.revoked_at.is_not(None))
        .values(revoked_at=datetime.now(UTC) - timedelta(seconds=seconds))
    )
    await db.commit()


async def _family_dead(db: AsyncSession) -> bool:
    rows = (await db.scalars(select(RefreshToken))).all()
    return bool(rows) and all(r.revoked_at is not None for r in rows)


async def _setup(client: AsyncClient, mailbox: FakeEmailSender) -> None:
    await register_verified(client, mailbox)
    await login(client)


async def test_a_lost_response_can_be_retried_with_the_old_token(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await _setup(client, mailbox)
    old, _new = await _rotate(client)  # the server rotated; imagine the browser never got `_new`
    retry = await _present(client, old)
    assert retry.status_code == 200 and retry.json()["access_token"]
    assert _newest_cookie(client) not in (old, _new)  # a fresh token was issued
    assert not await _family_dead(db)
    # Everything keeps working: the retry's token rotates normally.
    assert (await client.post(f"{API}/refresh", headers=CSRF)).status_code == 200
    me = await client.get(f"{API}/me", headers=bearer(retry))
    assert me.status_code == 200
    families = {r.family_id for r in (await db.scalars(select(RefreshToken))).all()}
    assert len(families) == 1  # still one session lineage


async def test_two_tabs_refreshing_at_the_same_moment_both_succeed(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await _setup(client, mailbox)
    token = client.cookies.get("refresh_token") or ""
    client.cookies.clear()
    headers = {"Cookie": f"refresh_token={token}", **CSRF}
    first, second = await asyncio.gather(
        client.post(f"{API}/refresh", headers=headers),
        client.post(f"{API}/refresh", headers=headers),
    )
    assert sorted([first.status_code, second.status_code]) == [200, 200]
    assert not await _family_dead(db)


async def test_replay_after_the_grace_window_is_theft(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await _setup(client, mailbox)
    old, new = await _rotate(client)
    await _age_rotations(db, get_settings().refresh_reuse_grace_seconds + 5)
    assert (await _present(client, old)).status_code == 401
    assert await _family_dead(db)
    assert (
        await _present(client, new)
    ).status_code == 401  # the legitimate holder is signed out too


async def test_replay_after_the_successor_was_used_is_theft_even_inside_the_window(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await _setup(client, mailbox)
    stolen, _second = await _rotate(client)
    assert (
        await client.post(f"{API}/refresh", headers=CSRF)
    ).status_code == 200  # legit holder moves on
    assert (await _present(client, stolen)).status_code == 401  # attacker replays at once
    assert await _family_dead(db)


async def test_grace_can_be_switched_off(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REFRESH_REUSE_GRACE_SECONDS", "0")
    get_settings.cache_clear()
    try:
        await _setup(client, mailbox)
        old, _ = await _rotate(client)
        assert (await _present(client, old)).status_code == 401
        assert await _family_dead(db)
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()


async def test_tokens_revoked_by_logout_never_get_grace(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    r = await login(client)
    old, new = await _rotate(client)
    assert (await client.post(f"{API}/logout", headers={**CSRF, **bearer(r)})).status_code == 204
    assert (await _present(client, new)).status_code == 401
    assert (await _present(client, old)).status_code == 401


async def test_tokens_revoked_by_password_reset_never_get_grace(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await _setup(client, mailbox)
    old, new = await _rotate(client)
    await client.post(f"{API}/password/forgot", json={"email": "viewer@example.com"})
    token = mailbox.last_token()
    body = {"token": token, "password": "another-long-password"}
    assert (await client.post(f"{API}/password/reset", json=body)).status_code == 204
    assert (await _present(client, new)).status_code == 401
    assert (await _present(client, old)).status_code == 401


async def test_a_suspended_user_gets_no_grace(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await _setup(client, mailbox)
    old, _new = await _rotate(client)
    await db.execute(update(User).values(status="suspended"))
    await db.commit()
    assert (await _present(client, old)).status_code == 401
    assert await _family_dead(db)


async def test_unknown_token_is_still_rejected(client: AsyncClient, db: AsyncSession) -> None:
    assert (await _present(client, "not-a-real-token")).status_code == 401
