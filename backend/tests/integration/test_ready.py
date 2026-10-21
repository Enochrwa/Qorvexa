from httpx import AsyncClient


async def test_ready_reports_status(client: AsyncClient) -> None:
    """With Postgres and Redis up (CI / docker compose) /ready is 200; otherwise 503."""
    r = await client.get("/ready")
    assert r.status_code in (200, 503)
    body = r.json()
    assert set(body) == {"status", "database", "redis"}
    assert (r.status_code == 200) == (body["status"] == "ok")
