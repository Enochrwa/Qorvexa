import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app
from tests.conftest import FakeEmailSender
from tests.integration.admin.helpers import A, as_role


def _admin_routes() -> list[tuple[str, str]]:
    """Enumerate from the OpenAPI schema (the documented surface), not from router internals."""
    out = []
    for path, ops in create_app().openapi()["paths"].items():
        if not path.startswith("/api/v1/admin"):
            continue
        concrete = "/".join(
            str(uuid.uuid4()) if part.startswith("{") else part for part in path.split("/")
        )
        out += [(method.upper(), concrete) for method in ops]
    return out


async def _call(client: AsyncClient, method: str, path: str, h: dict[str, str] | None) -> int:
    r = await client.request(
        method, path, headers=h, json={} if method in ("POST", "PATCH") else None
    )
    return r.status_code


async def test_every_admin_route_requires_an_editor(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    routes = _admin_routes()
    # Pinned on purpose: adding or removing an admin route must update this number deliberately.
    assert len(routes) == 16
    viewer = await as_role(client, mailbox, db, "viewer")
    for method, path in routes:
        assert await _call(client, method, path, None) == 401, (method, path)
        assert await _call(client, method, path, viewer) == 403, (method, path)


async def test_editor_and_admin_pass_the_role_check(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    for role in ("editor", "admin"):
        h = await as_role(client, mailbox, db, role)
        assert (await client.get(f"{A}/titles", headers=h)).status_code == 200


async def test_admin_responses_are_never_cached(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await as_role(client, mailbox, db, "editor")
    assert (await client.get(f"{A}/titles", headers=h)).headers["cache-control"] == "no-store"
