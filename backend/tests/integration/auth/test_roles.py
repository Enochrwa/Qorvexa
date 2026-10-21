from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from tests.conftest import FakeEmailSender
from tests.integration.auth.helpers import bearer, login, register_verified


async def _as_role(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, role: str
) -> dict[str, str]:
    await register_verified(client, mailbox, f"{role}@example.com")
    await db.execute(update(User).where(User.email == f"{role}@example.com").values(role=role))
    await db.commit()
    return bearer(await login(client, f"{role}@example.com"))


async def test_anonymous_gets_401_with_challenge(client: AsyncClient, db: AsyncSession) -> None:
    for path in ("viewer", "editor", "admin"):
        r = await client.get(f"/_test/{path}")
        assert r.status_code == 401 and r.headers["www-authenticate"] == "Bearer"


async def test_viewer_cannot_reach_editor_or_admin(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _as_role(client, mailbox, db, "viewer")
    assert (await client.get("/_test/viewer", headers=h)).status_code == 200
    assert (await client.get("/_test/editor", headers=h)).status_code == 403
    assert (await client.get("/_test/admin", headers=h)).status_code == 403


async def test_editor_cannot_reach_admin_only(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _as_role(client, mailbox, db, "editor")
    assert (await client.get("/_test/viewer", headers=h)).status_code == 200
    assert (await client.get("/_test/editor", headers=h)).status_code == 200
    assert (await client.get("/_test/admin", headers=h)).status_code == 403


async def test_admin_reaches_everything(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _as_role(client, mailbox, db, "admin")
    for path in ("viewer", "editor", "admin"):
        assert (await client.get(f"/_test/{path}", headers=h)).status_code == 200


async def test_role_change_applies_to_existing_token(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    """Role comes from the DB, so demoting an admin takes effect before the token expires."""
    h = await _as_role(client, mailbox, db, "admin")
    assert (await client.get("/_test/admin", headers=h)).status_code == 200
    await db.execute(update(User).values(role="viewer"))
    await db.commit()
    assert (await client.get("/_test/admin", headers=h)).status_code == 403


async def test_garbage_and_forged_tokens_rejected(client: AsyncClient, db: AsyncSession) -> None:
    for tok in ("garbage", "a.b.c"):
        r = await client.get("/_test/viewer", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 401
