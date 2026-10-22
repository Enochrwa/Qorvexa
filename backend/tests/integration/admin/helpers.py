from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from tests.conftest import FakeEmailSender
from tests.integration.auth.helpers import bearer, login, register_verified

A = "/api/v1/admin"
PUB = "/api/v1"


async def as_role(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession, role: str
) -> dict[str, str]:
    email = f"{role}@example.com"
    await register_verified(client, mailbox, email)
    await db.execute(update(User).where(User.email == email).values(role=role))
    await db.commit()
    return bearer(await login(client, email))


async def make_title(client: AsyncClient, h: dict[str, str], **kw: object) -> dict[str, object]:
    body: dict[str, object] = {"type": "movie", "name": "My Movie"}
    body.update(kw)
    r = await client.post(f"{A}/titles", headers=h, json=body)
    assert r.status_code == 201, r.text
    data: dict[str, object] = r.json()
    return data


async def publishable(client: AsyncClient, h: dict[str, str], **kw: object) -> dict[str, object]:
    return await make_title(
        client,
        h,
        synopsis="A synopsis",
        poster_url="https://img.example.com/p.jpg",
        maturity_rating="13+",
        **kw,
    )
