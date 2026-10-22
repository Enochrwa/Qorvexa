import pytest
from httpx import AsyncClient

ORIGIN = "http://localhost:5173"  # the default CORS_ORIGINS


async def _preflight(
    client: AsyncClient, path: str, method: str, headers: str, origin: str = ORIGIN
):
    return await client.options(
        path,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )


@pytest.mark.parametrize(
    ("path", "method", "headers"),
    [
        ("/api/v1/auth/refresh", "POST", "x-qorvexa-client"),
        ("/api/v1/auth/logout", "POST", "authorization,x-qorvexa-client"),
        ("/api/v1/titles", "GET", "x-profile-id,if-none-match"),
        ("/api/v1/profiles", "POST", "authorization,content-type"),
        ("/api/v1/auth/login", "POST", "content-type,x-request-id"),
    ],
)
async def test_preflight_allows_the_headers_the_frontend_sends(
    client: AsyncClient, path: str, method: str, headers: str
) -> None:
    r = await _preflight(client, path, method, headers)
    assert r.status_code == 200, r.text
    assert r.headers["access-control-allow-origin"] == ORIGIN
    assert r.headers["access-control-allow-credentials"] == "true"  # the refresh cookie needs it


async def test_preflight_rejects_unknown_headers_and_other_origins(client: AsyncClient) -> None:
    assert (await _preflight(client, "/api/v1/titles", "GET", "x-evil-header")).status_code == 400
    other = await _preflight(
        client, "/api/v1/auth/refresh", "POST", "x-qorvexa-client", "https://evil.example.com"
    )
    assert other.status_code == 400
    assert "access-control-allow-origin" not in other.headers


async def test_browser_javascript_can_read_retry_after_and_etag(client: AsyncClient) -> None:
    r = await client.get("/health", headers={"Origin": ORIGIN})
    exposed = {h.strip().lower() for h in r.headers["access-control-expose-headers"].split(",")}
    assert {"retry-after", "etag", "x-request-id"} <= exposed


async def test_methods_are_limited(client: AsyncClient) -> None:
    r = await _preflight(client, "/api/v1/titles", "TRACE", "content-type")
    assert r.status_code == 400
