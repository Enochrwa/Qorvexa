import datetime as dt

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ratelimit import Limiter
from tests.conftest import FakeEmailSender
from tests.integration.auth.helpers import bearer, login, register_verified
from tests.integration.catalog import factories as f

API = "/api/v1"
HOUR = dt.timedelta(hours=1)


async def _profile_headers(
    client: AsyncClient, mailbox: FakeEmailSender, limit: str, email: str = "viewer@example.com"
) -> dict[str, str]:
    await register_verified(client, mailbox, email)
    h = bearer(await login(client, email))
    r = await client.post(
        f"{API}/profiles", headers=h, json={"name": f"p-{limit}", "maturity_limit": limit}
    )
    return {**h, "X-Profile-Id": r.json()["id"]}


async def _slugs(
    client: AsyncClient, path: str = "/titles", headers: dict[str, str] | None = None
) -> list[str]:
    r = await client.get(f"{API}{path}", headers=headers)
    assert r.status_code == 200, r.text
    return [i["slug"] for i in r.json()["items"]]


# ---- visibility ----------------------------------------------------------------------------


async def test_only_published_titles_inside_their_window_are_listed(
    client: AsyncClient, db: AsyncSession
) -> None:
    now = dt.datetime.now(dt.UTC)
    await f.title(db, slug="live")
    await f.title(db, slug="draft", status="draft")
    await f.title(db, slug="scheduled", status="scheduled")
    await f.title(db, slug="archived", status="archived")
    await f.title(db, slug="embargoed", publish_at=now + HOUR)
    await f.title(db, slug="expired", available_until=now - HOUR)
    await f.title(db, slug="in-window", publish_at=now - HOUR, available_until=now + HOUR)
    assert sorted(await _slugs(client)) == ["in-window", "live"]


async def test_hidden_title_detail_looks_like_a_missing_one(
    client: AsyncClient, db: AsyncSession
) -> None:
    await f.title(db, slug="secret", status="draft")
    hidden = await client.get(f"{API}/titles/secret")
    missing = await client.get(f"{API}/titles/does-not-exist")
    assert hidden.status_code == missing.status_code == 404
    assert hidden.json()["detail"] == missing.json()["detail"]
    assert (await client.get(f"{API}/titles/secret/seasons")).status_code == 404


async def test_anonymous_default_limit_hides_16_and_18(
    client: AsyncClient, db: AsyncSession
) -> None:
    for rating in ("all", "7+", "13+", "16+", "18+"):
        await f.title(db, slug=f"r-{rating.replace('+', 'plus')}", maturity_rating=rating)
    assert sorted(await _slugs(client)) == ["r-13plus", "r-7plus", "r-all"]
    assert (await client.get(f"{API}/titles/r-18plus")).status_code == 404


async def test_profile_limit_controls_what_is_visible(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    for rating in ("all", "7+", "13+", "16+", "18+"):
        await f.title(db, slug=f"r-{rating.replace('+', 'plus')}", maturity_rating=rating)
    kid = await _profile_headers(client, mailbox, "all")
    assert await _slugs(client, headers=kid) == ["r-all"]
    adult = await _profile_headers(client, mailbox, "18+", "adult@example.com")
    assert len(await _slugs(client, headers=adult)) == 5
    assert (await client.get(f"{API}/titles/r-18plus", headers=kid)).status_code == 404
    assert (await client.get(f"{API}/titles/r-18plus", headers=adult)).status_code == 200


async def test_profile_header_must_be_authenticated_and_owned(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    a = await _profile_headers(client, mailbox, "18+", "a@example.com")
    b = await _profile_headers(client, mailbox, "all", "b@example.com")
    pid = a["X-Profile-Id"]
    assert (await client.get(f"{API}/titles", headers={"X-Profile-Id": pid})).status_code == 401
    assert (
        await client.get(f"{API}/titles", headers={**b, "X-Profile-Id": pid})
    ).status_code == 404
    assert (
        await client.get(f"{API}/titles", headers={**b, "X-Profile-Id": "junk"})
    ).status_code == 404


# ---- filters -------------------------------------------------------------------------------


async def test_filters(client: AsyncClient, db: AsyncSession) -> None:
    drama, comedy = await f.genre(db, "Drama"), await f.genre(db, "Comedy")
    a = await f.title(db, slug="a", type="series", release_year=2021, language="rw")
    b = await f.title(db, slug="b", type="movie", release_year=2021, language="en")
    c = await f.title(db, slug="c", type="movie", release_year=2019, language="en")
    await f.link_genre(db, a, drama)
    await f.link_genre(db, b, drama)
    await f.link_genre(db, b, comedy)
    await f.link_genre(db, c, comedy)
    assert sorted(await _slugs(client, "/titles?type=movie")) == ["b", "c"]
    assert sorted(await _slugs(client, "/titles?genre=drama")) == ["a", "b"]
    assert sorted(await _slugs(client, "/titles?genre=drama&type=movie&year=2021")) == ["b"]
    assert await _slugs(client, "/titles?language=rw") == ["a"]
    assert await _slugs(client, "/titles?genre=unknown-genre") == []


async def test_invalid_query_parameters_are_422(client: AsyncClient, db: AsyncSession) -> None:
    for q in (
        "type=book",
        "limit=0",
        "limit=51",
        "year=1500",
        "sort=popular",
        "genre=Bad Slug!",
        "language=english",
        "cursor=" + "x" * 301,
    ):
        assert (await client.get(f"{API}/titles?{q}")).status_code == 422, q


# ---- pagination ----------------------------------------------------------------------------


async def _walk(client: AsyncClient, sort: str, limit: int) -> list[str]:
    seen: list[str] = []
    cursor: str | None = None
    for _ in range(20):
        url = f"{API}/titles?sort={sort}&limit={limit}" + (f"&cursor={cursor}" if cursor else "")
        body = (await client.get(url)).json()
        seen += [i["slug"] for i in body["items"]]
        cursor = body["next_cursor"]
        if cursor is None:
            return seen
    raise AssertionError("pagination did not terminate")


async def test_cursor_pagination_is_complete_and_ordered_for_every_sort(
    client: AsyncClient, db: AsyncSession
) -> None:
    years = [2020, 2020, 2020, 2018, 2018, 2022, None]  # ties and a missing year
    names = ["Beta", "alpha", "Alpha", "Gamma", "beta", "Delta", "Echo"]  # case ties
    for i, (y, n) in enumerate(zip(years, names, strict=True)):
        await f.title(db, slug=f"t{i}", name=n, release_year=y)
    for sort in ("added", "name", "year"):
        everything = await _walk(client, sort, limit=50)
        paged = await _walk(client, sort, limit=3)
        assert paged == everything, sort
        assert len(set(paged)) == 7, sort  # nothing duplicated or dropped
    assert (await _walk(client, "year", 2))[-1] == "t6"  # missing year sorts last (newest first)
    names_sorted = [
        (await client.get(f"{API}/titles?sort=name&limit=50")).json()["items"][k]["name"].lower()
        for k in range(7)
    ]
    assert names_sorted == sorted(names_sorted)


async def test_last_page_has_no_cursor_and_empty_catalog_is_ok(
    client: AsyncClient, db: AsyncSession
) -> None:
    assert (await client.get(f"{API}/titles")).json() == {"items": [], "next_cursor": None}
    await f.title(db)
    body = (await client.get(f"{API}/titles?limit=1")).json()
    assert len(body["items"]) == 1 and body["next_cursor"] is None


async def test_tampered_or_mismatched_cursors_are_rejected(
    client: AsyncClient, db: AsyncSession
) -> None:
    for _ in range(3):
        await f.title(db)
    cursor = (await client.get(f"{API}/titles?limit=1&sort=added")).json()["next_cursor"]
    assert cursor
    assert (await client.get(f"{API}/titles?limit=1&sort=name&cursor={cursor}")).status_code == 422
    for bad in ("garbage", cursor[:-3], "e30"):
        assert (await client.get(f"{API}/titles?sort=added&cursor={bad}")).status_code == 422, bad


async def test_cursor_does_not_leak_titles_hidden_from_the_profile(
    client: AsyncClient, db: AsyncSession
) -> None:
    for i in range(4):
        await f.title(db, slug=f"ok{i}")
    await f.title(db, slug="adult", maturity_rating="18+")
    assert "adult" not in await _walk(client, "added", 2)


# ---- detail, seasons, genres ----------------------------------------------------------------


async def test_title_detail(client: AsyncClient, db: AsyncSession) -> None:
    t = await f.title(
        db, slug="show", type="series", synopsis="A story", original_name="Original", country="RW"
    )
    g = await f.genre(db, "Drama")
    await f.link_genre(db, t, g)
    await f.person(db, t, "Zed Actor", "actor", 2)
    await f.person(db, t, "Amy Lead", "actor", 1)
    await f.person(db, t, "Dee Rector", "director", 0)
    await f.season(db, t, 1, [(1, "published")])
    await f.season(db, t, 2, [])
    body = (await client.get(f"{API}/titles/show")).json()
    assert body["synopsis"] == "A story" and body["season_count"] == 2 and body["country"] == "RW"
    assert body["genres"] == [{"name": "Drama", "slug": "drama"}]
    assert [c["name"] for c in body["cast"]] == ["Dee Rector", "Amy Lead", "Zed Actor"]
    assert body["downloads_enabled"] is False


async def test_seasons_list_only_published_episodes_in_order(
    client: AsyncClient, db: AsyncSession
) -> None:
    t = await f.title(db, slug="show", type="series")
    await f.season(db, t, 2, [(1, "published")])
    await f.season(db, t, 1, [(2, "published"), (1, "published"), (3, "draft")])
    seasons = (await client.get(f"{API}/titles/show/seasons")).json()
    assert [s["number"] for s in seasons] == [1, 2]
    assert [e["number"] for e in seasons[0]["episodes"]] == [1, 2]  # draft episode 3 hidden
    movie = await f.title(db, slug="film")
    assert movie is not None and (await client.get(f"{API}/titles/film/seasons")).json() == []


async def test_genres_endpoint_is_sorted(client: AsyncClient, db: AsyncSession) -> None:
    for name in ("Thriller", "Action", "Drama"):
        await f.genre(db, name)
    assert [g["name"] for g in (await client.get(f"{API}/genres")).json()] == [
        "Action",
        "Drama",
        "Thriller",
    ]


# ---- caching and limits --------------------------------------------------------------------


async def test_etag_returns_304_and_varies_with_profile(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await f.title(db, slug="plain", maturity_rating="13+")
    await f.title(db, slug="adult", maturity_rating="18+")
    first = await client.get(f"{API}/titles")
    etag = first.headers["etag"]
    assert first.headers["cache-control"] == "private, no-cache"
    again = await client.get(f"{API}/titles", headers={"If-None-Match": etag})
    assert again.status_code == 304 and again.content == b""
    adult = await _profile_headers(client, mailbox, "18+")
    other = await client.get(f"{API}/titles", headers={**adult, "If-None-Match": etag})
    assert (
        other.status_code == 200 and other.headers["etag"] != etag
    )  # different audience, different body


async def test_catalog_reads_are_rate_limited_per_ip(
    client: AsyncClient, db: AsyncSession, limiter: Limiter
) -> None:
    for _ in range(120):
        assert (await client.get(f"{API}/genres")).status_code == 200
    r = await client.get(f"{API}/genres")
    assert r.status_code == 429 and "retry-after" in r.headers
