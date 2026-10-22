import datetime as dt

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.catalog.models import Genre, Title
from tests.conftest import FakeEmailSender
from tests.integration.admin.helpers import PUB, A, as_role, make_title, publishable

HOUR = dt.timedelta(hours=1)


async def _editor(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> dict[str, str]:
    return await as_role(client, mailbox, db, "editor")


async def test_create_minimal_title_defaults_are_safe(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = await make_title(client, h, name="  Café Nights!  ")
    assert t["slug"] == "cafe-nights" and t["name"] == "Café Nights!"
    assert t["status"] == "draft" and t["state"] == "draft"
    assert t["maturity_rating"] == "18+" and t["downloads_enabled"] is False
    assert (
        await client.get(f"{PUB}/titles/cafe-nights")
    ).status_code == 404  # drafts are invisible


async def test_auto_slug_gets_a_suffix_but_explicit_slug_conflicts(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    first = await make_title(client, h, name="Same Name")
    second = await make_title(client, h, name="Same Name")
    assert (first["slug"], second["slug"]) == ("same-name", "same-name-2")
    r = await client.post(
        f"{A}/titles", headers=h, json={"type": "movie", "name": "X", "slug": "same-name"}
    )
    assert r.status_code == 409


async def test_genres_and_cast_are_set_and_replaced(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    db.add_all([Genre(name="Drama", slug="drama"), Genre(name="Comedy", slug="comedy")])
    await db.commit()
    t = await make_title(
        client,
        h,
        genres=["drama"],
        cast=[
            {"name": "Amy Lead", "role": "actor", "billing_order": 1},
            {"name": "Dee Rector", "role": "director"},
        ],
    )
    assert t["genres"] == ["drama"] and [c["name"] for c in t["cast"]] == ["Dee Rector", "Amy Lead"]  # type: ignore[attr-defined,union-attr]
    r = await client.patch(
        f"{A}/titles/{t['id']}", headers=h, json={"genres": ["comedy"], "cast": []}
    )
    assert r.json()["genres"] == ["comedy"] and r.json()["cast"] == []
    r = await client.patch(f"{A}/titles/{t['id']}", headers=h, json={"name": "Renamed"})
    assert r.json()["genres"] == ["comedy"]  # untouched when not sent


async def test_validation_rejects_bad_input(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    base = {"type": "movie", "name": "Ok"}
    bad = [
        {"type": "book"},
        {"name": ""},
        {"name": "x" * 201},
        {"name": "bad\x00name"},
        {"slug": "Bad Slug"},
        {"slug": "-leading"},
        {"maturity_rating": "21+"},
        {"poster_url": "http://insecure.example.com/p.jpg"},
        {"poster_url": "javascript:alert(1)"},
        {"poster_url": "https://a b.example.com"},
        {"backdrop_url": "https://x.com/" + "a" * 2100},
        {"release_year": 1500},
        {"country": "rwanda"},
        {"language": "english"},
        {"synopsis": "x" * 5001},
        {"genres": ["no-such-genre"]},
        {"genres": ["a", "a"]},
        {"cast": [{"name": "A", "role": "producer"}]},
        {"cast": [{"name": "A", "role": "actor"}, {"name": "a", "role": "actor"}]},
        {"status": "published"},
        {"id": "00000000-0000-0000-0000-000000000000"},
        {"created_at": "2020-01-01"},
    ]
    for extra in bad:
        r = await client.post(f"{A}/titles", headers=h, json={**base, **extra})
        assert r.status_code == 422, extra


async def test_patch_cannot_change_slug_type_status_and_rejects_bad_nulls(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = await make_title(client, h, synopsis="old")
    url = f"{A}/titles/{t['id']}"
    for body in (
        {"slug": "new"},
        {"type": "series"},
        {"status": "published"},
        {"name": None},
        {"maturity_rating": None},
        {"genres": None},
    ):
        assert (await client.patch(url, headers=h, json=body)).status_code == 422, body
    r = await client.patch(
        url, headers=h, json={"synopsis": None}
    )  # nullable fields can be cleared
    assert r.status_code == 200 and r.json()["synopsis"] is None


async def test_unknown_ids_are_404(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    ghost = "00000000-0000-0000-0000-000000000000"
    assert (await client.get(f"{A}/titles/{ghost}", headers=h)).status_code == 404
    assert (await client.patch(f"{A}/titles/{ghost}", headers=h, json={})).status_code == 404
    assert (await client.delete(f"{A}/titles/{ghost}", headers=h)).status_code == 404
    assert (await client.post(f"{A}/titles/{ghost}/publish", headers=h)).status_code == 404
    assert (await client.get(f"{A}/titles/not-a-uuid", headers=h)).status_code == 422


async def test_cannot_publish_until_synopsis_and_poster_exist(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = await make_title(client, h)
    r = await client.post(f"{A}/titles/{t['id']}/publish", headers=h)
    assert (
        r.status_code == 409
        and "synopsis" in r.json()["detail"]
        and "poster_url" in r.json()["detail"]
    )


async def test_publish_makes_it_public_and_unpublish_hides_it(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = await publishable(client, h, name="Live One")
    r = await client.post(f"{A}/titles/{t['id']}/publish", headers=h)
    assert r.status_code == 200 and r.json()["state"] == "live"
    assert (await client.get(f"{PUB}/titles/live-one")).status_code == 200
    r = await client.post(f"{A}/titles/{t['id']}/unpublish", headers=h)
    assert r.json()["state"] == "draft"
    assert (await client.get(f"{PUB}/titles/live-one")).status_code == 404


async def test_publish_respects_maturity_for_public_callers(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = await make_title(
        client, h, name="Adults", synopsis="s", poster_url="https://i.example.com/a.jpg"
    )
    await client.post(f"{A}/titles/{t['id']}/publish", headers=h)  # default rating is 18+
    assert (
        await client.get(f"{PUB}/titles/adults")
    ).status_code == 404  # hidden from anonymous (13+)


async def test_scheduled_publish_is_embargoed_until_its_time(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = await publishable(client, h, name="Later")
    when = (dt.datetime.now(dt.UTC) + HOUR).isoformat()
    r = await client.post(f"{A}/titles/{t['id']}/publish", headers=h, json={"publish_at": when})
    assert r.status_code == 200 and r.json()["state"] == "scheduled"
    assert (await client.get(f"{PUB}/titles/later")).status_code == 404


async def test_publish_window_validation(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = await publishable(client, h)
    url = f"{A}/titles/{t['id']}/publish"
    now = dt.datetime.now(dt.UTC)
    assert (
        await client.post(url, headers=h, json={"publish_at": "2030-01-01T00:00:00"})
    ).status_code == 422  # naive
    past = (now - HOUR).isoformat()
    assert (await client.post(url, headers=h, json={"available_until": past})).status_code == 422
    soon, later = (now + HOUR).isoformat(), (now + 2 * HOUR).isoformat()
    assert (
        await client.post(url, headers=h, json={"publish_at": later, "available_until": soon})
    ).status_code == 422
    assert (await client.post(url, headers=h, json={"available_until": later})).status_code == 200


async def test_expired_title_state_and_public_hiding(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = await publishable(client, h, name="Short Lived")
    await client.post(f"{A}/titles/{t['id']}/publish", headers=h)
    row = await db.scalar(select(Title).where(Title.slug == "short-lived"))
    assert row is not None
    row.available_until = dt.datetime.now(dt.UTC) - HOUR
    await db.commit()
    assert (await client.get(f"{A}/titles/{t['id']}", headers=h)).json()["state"] == "expired"
    assert (await client.get(f"{PUB}/titles/short-lived")).status_code == 404


async def test_delete_requires_unpublish_first_and_cascades(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = await publishable(client, h, type="series", name="Show")
    await client.post(f"{A}/titles/{t['id']}/seasons", headers=h, json={"number": 1})
    await client.post(f"{A}/titles/{t['id']}/publish", headers=h)
    assert (await client.delete(f"{A}/titles/{t['id']}", headers=h)).status_code == 409
    await client.post(f"{A}/titles/{t['id']}/unpublish", headers=h)
    assert (await client.delete(f"{A}/titles/{t['id']}", headers=h)).status_code == 204
    assert (await client.get(f"{A}/titles/{t['id']}", headers=h)).status_code == 404


async def test_list_filters_search_escapes_wildcards_and_paginates(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    await make_title(client, h, name="100% Real")
    await make_title(client, h, name="Other Film")
    await make_title(client, h, name="Under_score")
    body = (await client.get(f"{A}/titles?q=%25", headers=h)).json()  # literal "%"
    assert [i["name"] for i in body["items"]] == ["100% Real"] and body["total"] == 1
    assert (await client.get(f"{A}/titles?q=_", headers=h)).json()["total"] == 1  # literal "_"
    page = (await client.get(f"{A}/titles?limit=2&offset=0", headers=h)).json()
    assert len(page["items"]) == 2 and page["total"] == 3
    assert len((await client.get(f"{A}/titles?limit=2&offset=2", headers=h)).json()["items"]) == 1
    assert (await client.get(f"{A}/titles?status=published", headers=h)).json()["total"] == 0
    for bad in ("status=weird", "limit=0", "limit=101", "offset=-1"):
        assert (await client.get(f"{A}/titles?{bad}", headers=h)).status_code == 422, bad


async def test_audit_log_records_actor_and_survives_deletion(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    t = await publishable(client, h, name="Audited")
    await client.patch(f"{A}/titles/{t['id']}", headers=h, json={"downloads_enabled": True})
    await client.post(f"{A}/titles/{t['id']}/publish", headers=h)
    await client.post(f"{A}/titles/{t['id']}/unpublish", headers=h)
    await client.delete(f"{A}/titles/{t['id']}", headers=h)
    rows = list(await db.scalars(select(AuditLog).order_by(AuditLog.created_at)))
    assert [r.action for r in rows] == [
        "title.create",
        "title.update",
        "title.publish",
        "title.unpublish",
        "title.delete",
    ]
    actor = await db.scalar(select(User.id).where(User.email == "editor@example.com"))
    assert all(r.actor_id == actor for r in rows)
    assert rows[1].detail == {"fields": ["downloads_enabled"]}  # field names only, never content
    assert rows[-1].detail["slug"] == "audited"


async def test_failed_requests_leave_no_audit_row(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _editor(client, mailbox, db)
    await client.post(
        f"{A}/titles", headers=h, json={"type": "movie", "name": "X", "genres": ["nope"]}
    )
    assert list(await db.scalars(select(AuditLog))) == []
    assert list(await db.scalars(select(Title))) == []  # and no half-created title
