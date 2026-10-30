from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture
def dist(tmp_path: Path) -> Path:
    root = tmp_path / "dist"
    (root / "assets").mkdir(parents=True)
    (root / "index.html").write_text("<!doctype html><title>Qorvexa</title><div id=root></div>")
    (root / "assets" / "app-abc123.js").write_text("console.log('app')")
    (root / "assets" / "app-abc123.css").write_text("body{margin:0}")
    (root / "favicon.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
    (tmp_path / "secret.txt").write_text("TOP SECRET OUTSIDE THE BUILD")
    return root


@pytest.fixture
async def spa(dist: Path, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    monkeypatch.setenv("FRONTEND_DIST_DIR", str(dist))
    get_settings.cache_clear()
    try:
        async with AsyncClient(
            transport=ASGITransport(app=create_app()), base_url="http://test"
        ) as c:
            yield c
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()


async def test_home_and_client_routes_get_the_app_with_security_headers(spa: AsyncClient) -> None:
    for path in ("/", "/browse", "/titles/some-slug", "/admin/titles/new", "/profiles/manage"):
        r = await spa.get(path)
        assert r.status_code == 200, path
        assert "<title>Qorvexa</title>" in r.text, path
        assert r.headers["cache-control"] == "no-cache"
        assert r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["x-frame-options"] == "DENY"
        assert r.headers["referrer-policy"] == "no-referrer"
        csp = r.headers["content-security-policy"]
        assert (
            "script-src 'self'" in csp
            and "object-src 'none'" in csp
            and "frame-ancestors 'none'" in csp
        )
        assert "unsafe-inline" not in csp.split("script-src")[1].split(";")[0]  # never for scripts


async def test_hashed_assets_are_cached_forever(spa: AsyncClient) -> None:
    for name, kind in (("app-abc123.js", "javascript"), ("app-abc123.css", "css")):
        r = await spa.get(f"/assets/{name}")
        assert r.status_code == 200 and kind in r.headers["content-type"]
        assert r.headers["cache-control"] == "public, max-age=31536000, immutable"


async def test_other_static_files_are_served_without_the_html_policy(spa: AsyncClient) -> None:
    r = await spa.get("/favicon.svg")
    assert r.status_code == 200 and "svg" in r.headers["content-type"]
    assert "content-security-policy" not in r.headers


async def test_missing_files_and_api_paths_are_real_404s_not_the_app(spa: AsyncClient) -> None:
    for path in (
        "/assets/missing.js",
        "/missing.png",
        "/nope.css",
        "/api/v1/does-not-exist",
        "/api/nothing",
    ):
        r = await spa.get(path)
        assert r.status_code == 404, path
        assert "<title>Qorvexa</title>" not in r.text, path


async def test_api_and_probes_still_win_over_the_app(spa: AsyncClient) -> None:
    health = await spa.get("/health")
    assert health.json() == {"status": "ok"}
    assert (await spa.get("/openapi.json")).json()["info"]["title"] == "Qorvexa"
    docs = await spa.get("/docs")
    assert docs.status_code == 200 and "swagger" in docs.text.lower()


async def test_unknown_api_paths_keep_the_problem_json_shape(spa: AsyncClient) -> None:
    r = await spa.get("/api/v1/does-not-exist")
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["status"] == 404


@pytest.mark.parametrize(
    "path",
    [
        "/../secret.txt",
        "/%2e%2e/secret.txt",
        "/..%2fsecret.txt",
        "/assets/../../secret.txt",
        "/assets/%2e%2e/%2e%2e/secret.txt",
        "/%2e%2e%2fsecret.txt",
        "//secret.txt",
    ],
)
async def test_path_traversal_never_reaches_files_outside_the_build(
    spa: AsyncClient, path: str
) -> None:
    r = await spa.get(path)
    assert "TOP SECRET" not in r.text
    assert r.status_code in (200, 400, 404)  # 200 only ever means the app shell


async def test_only_reads_are_answered_by_the_app(spa: AsyncClient) -> None:
    assert (await spa.post("/browse")).status_code in (404, 405)
    assert (await spa.delete("/")).status_code in (404, 405)


async def test_without_a_build_directory_nothing_is_served(client: AsyncClient) -> None:
    assert (await client.get("/")).status_code == 404  # default: API only


async def test_a_missing_build_fails_at_startup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FRONTEND_DIST_DIR", str(tmp_path / "empty"))
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match=r"no index\.html"):
            create_app()
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
