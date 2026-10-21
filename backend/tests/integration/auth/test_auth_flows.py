from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import OneTimeToken, RefreshToken, User
from tests.conftest import FakeEmailSender
from tests.integration.auth.helpers import CSRF, PASSWORD, bearer, login, register_verified

API = "/api/v1/auth"


async def test_register_creates_unverified_user_and_sends_link(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    r = await client.post(
        f"{API}/register", json={"email": "New@Example.com", "password": PASSWORD}
    )
    assert r.status_code == 202
    user = await db.scalar(select(User).where(User.email == "new@example.com"))
    assert user is not None and user.email_verified_at is None
    assert user.password_hash.startswith("$argon2id$") and PASSWORD not in user.password_hash
    assert len(mailbox.sent) == 1 and "verify-email?token=" in mailbox.sent[0][2]


async def test_register_duplicate_looks_identical_and_sends_nothing(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    sent_before = len(mailbox.sent)
    r = await client.post(
        f"{API}/register", json={"email": "viewer@example.com", "password": PASSWORD}
    )
    assert r.status_code == 202 and r.json() == {"status": "accepted"}
    assert len(mailbox.sent) == sent_before


async def test_register_rejects_weak_password_and_bad_email(
    client: AsyncClient, db: AsyncSession
) -> None:
    r = await client.post(f"{API}/register", json={"email": "a@example.com", "password": "short"})
    assert r.status_code == 422 and r.headers["content-type"].startswith("application/problem+json")
    r = await client.post(f"{API}/register", json={"email": "nope", "password": PASSWORD})
    assert r.status_code == 422


async def test_unverified_user_cannot_login(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await client.post(f"{API}/register", json={"email": "u@example.com", "password": PASSWORD})
    r = await login(client, "u@example.com")
    assert r.status_code == 403


async def test_verify_token_is_single_use_and_expires(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await client.post(f"{API}/register", json={"email": "u@example.com", "password": PASSWORD})
    token = mailbox.last_token()
    assert (await client.post(f"{API}/verify-email", json={"token": token})).status_code == 204
    assert (await client.post(f"{API}/verify-email", json={"token": token})).status_code == 400

    await client.post(f"{API}/register", json={"email": "v@example.com", "password": PASSWORD})
    await db.execute(
        update(OneTimeToken).values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
    )
    await db.commit()
    assert (
        await client.post(f"{API}/verify-email", json={"token": mailbox.last_token()})
    ).status_code == 400


async def test_login_success_sets_httponly_cookie_and_returns_access_token(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    r = await login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["expires_in"] == 900
    cookie = r.headers["set-cookie"].lower()
    assert "refresh_token=" in cookie and "httponly" in cookie and "samesite=lax" in cookie
    me = await client.get(f"{API}/me", headers=bearer(r))
    assert me.status_code == 200 and me.json()["email"] == "viewer@example.com"


async def test_bad_credentials_are_indistinguishable(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    wrong_pw = await login(client, pw="not-the-password")
    unknown = await login(client, "ghost@example.com")
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json()["detail"] == unknown.json()["detail"]
    assert wrong_pw.headers["www-authenticate"] == "Bearer"


async def test_suspended_user_cannot_login_or_use_existing_token(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    r = await login(client)
    await db.execute(update(User).values(status="suspended"))
    await db.commit()
    assert (await client.get(f"{API}/me", headers=bearer(r))).status_code == 401
    assert (await login(client)).status_code == 401


async def test_refresh_requires_csrf_header_and_cookie(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    await login(client)
    assert (await client.post(f"{API}/refresh")).status_code == 403  # cookie but no header
    client.cookies.clear()
    assert (
        await client.post(f"{API}/refresh", headers=CSRF)
    ).status_code == 401  # header, no cookie


async def test_refresh_rotates_token(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    await login(client)
    old_cookie = client.cookies.get("refresh_token")
    r = await client.post(f"{API}/refresh", headers=CSRF)
    assert r.status_code == 200 and r.json()["access_token"]
    assert client.cookies.get("refresh_token") != old_cookie
    rows = (await db.scalars(select(RefreshToken))).all()
    assert len(rows) == 2 and len({x.family_id for x in rows}) == 1
    assert sum(x.revoked_at is not None for x in rows) == 1


async def test_refresh_token_reuse_revokes_the_whole_family(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    await login(client)
    stolen = client.cookies.get("refresh_token")
    assert (await client.post(f"{API}/refresh", headers=CSRF)).status_code == 200  # legit rotation
    legit_new = client.cookies.get("refresh_token")

    client.cookies.clear()
    client.cookies.set("refresh_token", stolen or "", path="/api/v1/auth")
    reuse = await client.post(f"{API}/refresh", headers=CSRF)  # attacker replays the old token
    assert reuse.status_code == 401

    client.cookies.clear()
    client.cookies.set("refresh_token", legit_new or "", path="/api/v1/auth")
    assert (await client.post(f"{API}/refresh", headers=CSRF)).status_code == 401  # family dead
    rows = (await db.scalars(select(RefreshToken))).all()
    assert rows and all(x.revoked_at is not None for x in rows)


async def test_expired_refresh_token_rejected(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    await login(client)
    await db.execute(update(RefreshToken).values(expires_at=datetime.now(UTC) - timedelta(days=1)))
    await db.commit()
    assert (await client.post(f"{API}/refresh", headers=CSRF)).status_code == 401


async def test_logout_revokes_family_and_requires_auth(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    r = await login(client)
    assert (await client.post(f"{API}/logout", headers=CSRF)).status_code == 401
    assert (await client.post(f"{API}/logout", headers={**CSRF, **bearer(r)})).status_code == 204
    assert (await client.post(f"{API}/refresh", headers=CSRF)).status_code == 401
    rows = (await db.scalars(select(RefreshToken))).all()
    assert rows and all(x.revoked_at is not None for x in rows)


async def test_logout_cannot_revoke_another_users_session(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox, "a@example.com")
    await login(client, "a@example.com")
    a_cookie = client.cookies.get("refresh_token")
    await register_verified(client, mailbox, "b@example.com")
    rb = await login(client, "b@example.com")
    client.cookies.clear()
    client.cookies.set("refresh_token", a_cookie or "", path="/api/v1/auth")
    await client.post(f"{API}/logout", headers={**CSRF, **bearer(rb)})  # B presents A's cookie
    rows = (await db.scalars(select(RefreshToken))).all()
    a_row = next(x for x in rows if x.revoked_at is None)
    assert a_row is not None  # A's session is untouched


async def test_password_reset_flow(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    await login(client)
    f = await client.post(f"{API}/password/forgot", json={"email": "viewer@example.com"})
    assert f.status_code == 202
    token = mailbox.last_token()
    new_pw = "another-long-password"
    assert (
        await client.post(f"{API}/password/reset", json={"token": token, "password": new_pw})
    ).status_code == 204
    assert (
        await client.post(f"{API}/password/reset", json={"token": token, "password": new_pw})
    ).status_code == 400
    assert (await login(client, pw=PASSWORD)).status_code == 401
    assert (await login(client, pw=new_pw)).status_code == 200
    first_family = (
        await db.scalars(select(RefreshToken).order_by(RefreshToken.created_at))
    ).first()
    assert first_family is not None and first_family.revoked_at is not None  # signed out everywhere


async def test_forgot_password_is_202_for_unknown_email_and_sends_nothing(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    r = await client.post(f"{API}/password/forgot", json={"email": "ghost@example.com"})
    assert r.status_code == 202 and mailbox.sent == []


async def test_reset_rejects_verify_token_and_weak_password(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await client.post(f"{API}/register", json={"email": "u@example.com", "password": PASSWORD})
    verify_token = mailbox.last_token()
    r = await client.post(
        f"{API}/password/reset", json={"token": verify_token, "password": "another-long-password"}
    )
    assert r.status_code == 400  # wrong purpose
    r = await client.post(
        f"{API}/password/reset", json={"token": verify_token, "password": "short"}
    )
    assert r.status_code == 422


async def test_refresh_fails_and_family_dies_when_user_suspended(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    await login(client)
    await db.execute(update(User).values(status="suspended"))
    await db.commit()
    assert (await client.post(f"{API}/refresh", headers=CSRF)).status_code == 401
    rows = (await db.scalars(select(RefreshToken))).all()
    assert rows and all(x.revoked_at is not None for x in rows)


async def test_logout_without_cookie_is_ok(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    r = await login(client)
    client.cookies.clear()
    assert (await client.post(f"{API}/logout", headers={**CSRF, **bearer(r)})).status_code == 204


async def test_reset_for_suspended_user_is_rejected(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    await client.post(f"{API}/password/forgot", json={"email": "viewer@example.com"})
    token = mailbox.last_token()
    await db.execute(update(User).values(status="suspended"))
    await db.commit()
    body = {"token": token, "password": "another-long-password"}
    assert (await client.post(f"{API}/password/reset", json=body)).status_code == 400
