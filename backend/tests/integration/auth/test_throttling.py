from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ratelimit import Limiter
from tests.conftest import FakeEmailSender
from tests.integration.auth.helpers import PASSWORD, login, register_verified

API = "/api/v1/auth"


async def test_login_locks_out_after_five_failures_even_for_correct_password(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    for _ in range(5):
        assert (await login(client, pw="wrong-password-123")).status_code == 401
    r = await login(client)  # correct password, but locked
    assert r.status_code == 429
    assert int(r.headers["retry-after"]) > 0
    assert r.headers["content-type"].startswith("application/problem+json")


async def test_lockout_is_identical_for_unknown_accounts(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    for _ in range(5):
        assert (await login(client, "ghost@example.com", "wrong-password-123")).status_code == 401
    assert (await login(client, "ghost@example.com", "wrong-password-123")).status_code == 429


async def test_successful_login_resets_the_failure_counter(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    for _ in range(4):
        await login(client, pw="wrong-password-123")
    assert (await login(client)).status_code == 200
    for _ in range(4):  # a fresh budget of failures
        assert (await login(client, pw="wrong-password-123")).status_code == 401


async def test_lockout_does_not_spill_to_other_emails(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox, "a@example.com")
    await register_verified(client, mailbox, "b@example.com")
    for _ in range(5):
        await login(client, "a@example.com", "wrong-password-123")
    assert (await login(client, "a@example.com")).status_code == 429
    assert (await login(client, "b@example.com")).status_code == 200


async def test_per_ip_login_budget(client: AsyncClient, db: AsyncSession, limiter: Limiter) -> None:
    for i in range(20):  # different emails so no pair lockout triggers
        assert (
            await login(client, f"user{i}@example.com", "wrong-password-123")
        ).status_code == 401
    assert (await login(client, "another@example.com", "wrong-password-123")).status_code == 429


async def test_register_is_limited_per_ip(client: AsyncClient, db: AsyncSession) -> None:
    for i in range(5):
        r = await client.post(
            f"{API}/register", json={"email": f"n{i}@example.com", "password": PASSWORD}
        )
        assert r.status_code == 202
    r = await client.post(f"{API}/register", json={"email": "n6@example.com", "password": PASSWORD})
    assert r.status_code == 429 and "retry-after" in r.headers


async def test_forgot_password_caps_mail_per_address_without_revealing_it(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await register_verified(client, mailbox)
    before = len(mailbox.sent)
    for _ in range(5):
        r = await client.post(f"{API}/password/forgot", json={"email": "viewer@example.com"})
        assert r.status_code == 202  # always 202, never a 429 that would hint the account exists
    assert len(mailbox.sent) - before == 3


async def test_verify_and_reset_endpoints_are_limited(
    client: AsyncClient, db: AsyncSession
) -> None:
    for _ in range(20):
        assert (
            await client.post(f"{API}/verify-email", json={"token": "x" * 20})
        ).status_code == 400
    assert (await client.post(f"{API}/verify-email", json={"token": "x" * 20})).status_code == 429
    body = {"token": "x" * 20, "password": "another-long-password"}
    for _ in range(10):
        assert (await client.post(f"{API}/password/reset", json=body)).status_code == 400
    assert (await client.post(f"{API}/password/reset", json=body)).status_code == 429
