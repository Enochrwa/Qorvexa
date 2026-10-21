from httpx import AsyncClient, Response

from tests.conftest import FakeEmailSender

PASSWORD = "a-long-enough-pass"
CSRF = {"X-Qorvexa-Client": "web"}


async def register_verified(
    client: AsyncClient, mailbox: FakeEmailSender, email: str = "viewer@example.com"
) -> None:
    r = await client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 202
    r = await client.post("/api/v1/auth/verify-email", json={"token": mailbox.last_token()})
    assert r.status_code == 204


async def login(
    client: AsyncClient, email: str = "viewer@example.com", pw: str = PASSWORD
) -> Response:
    return await client.post("/api/v1/auth/login", json={"email": email, "password": pw})


def bearer(resp: Response) -> dict[str, str]:
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
