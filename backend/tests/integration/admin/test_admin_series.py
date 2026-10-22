from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Episode
from tests.conftest import FakeEmailSender
from tests.integration.admin.helpers import PUB, A, as_role, make_title, publishable


async def _series(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> tuple[dict[str, str], dict[str, object], str]:
    h = await as_role(client, mailbox, db, "editor")
    t = await publishable(client, h, type="series", name="Show")
    s = (
        await client.post(
            f"{A}/titles/{t['id']}/seasons", headers=h, json={"number": 1, "name": "One"}
        )
    ).json()
    return h, t, s["id"]


async def _ep(
    client: AsyncClient, h: dict[str, str], season_id: str, number: int, **kw: object
) -> dict[str, object]:
    body: dict[str, object] = {"number": number, "name": f"Ep {number}"}
    body.update(kw)
    r = await client.post(f"{A}/seasons/{season_id}/episodes", headers=h, json=body)
    assert r.status_code == 201, r.text
    data: dict[str, object] = r.json()
    return data


async def test_only_series_can_have_seasons(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await as_role(client, mailbox, db, "editor")
    movie = await make_title(client, h)
    r = await client.post(f"{A}/titles/{movie['id']}/seasons", headers=h, json={"number": 1})
    assert r.status_code == 409


async def test_season_crud_and_duplicate_numbers(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h, t, s1 = await _series(client, mailbox, db)
    dup = await client.post(f"{A}/titles/{t['id']}/seasons", headers=h, json={"number": 1})
    assert dup.status_code == 409
    s2 = (await client.post(f"{A}/titles/{t['id']}/seasons", headers=h, json={"number": 2})).json()
    assert (
        await client.patch(f"{A}/seasons/{s2['id']}", headers=h, json={"number": 1})
    ).status_code == 409
    assert (
        await client.patch(f"{A}/seasons/{s2['id']}", headers=h, json={"number": None})
    ).status_code == 422
    assert (await client.patch(f"{A}/seasons/{s2['id']}", headers=h, json={"name": "Two"})).json()[
        "name"
    ] == "Two"
    listed = (await client.get(f"{A}/titles/{t['id']}/seasons", headers=h)).json()
    assert [s["number"] for s in listed] == [1, 2]
    assert (await client.delete(f"{A}/seasons/{s2['id']}", headers=h)).status_code == 204
    assert (await client.delete(f"{A}/seasons/{s2['id']}", headers=h)).status_code == 404
    assert s1


async def test_episode_validation(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h, _, season = await _series(client, mailbox, db)
    url = f"{A}/seasons/{season}/episodes"
    bad = [
        {"number": 0, "name": "x"},
        {"number": 501, "name": "x"},
        {"number": 1, "name": ""},
        {"number": 1, "name": "x", "runtime_seconds": 0},
        {"number": 1, "name": "x", "runtime_seconds": 50000},
        {"number": 1, "name": "x", "intro_start": -1},
        {"number": 1, "name": "x", "status": "archived"},
        {"number": 1, "name": "x", "intro_start": 50, "intro_end": 10},
        {"number": 1, "name": "x", "runtime_seconds": 100, "intro_end": 200},
        {"number": 1, "name": "x", "runtime_seconds": 100, "recap_end": 101},
        {"number": 1, "name": "x", "air_date": "not-a-date"},
        {"number": 1, "name": "x", "season_id": "z"},
    ]
    for body in bad:
        assert (await client.post(url, headers=h, json=body)).status_code == 422, body
    assert (
        await client.post(
            url,
            headers=h,
            json={
                "number": 1,
                "name": "ok",
                "runtime_seconds": 100,
                "intro_start": 5,
                "intro_end": 20,
                "recap_end": 4,
            },
        )
    ).status_code == 201


async def test_episode_patch_validates_against_existing_values(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h, _, season = await _series(client, mailbox, db)
    e1 = await _ep(client, h, season, 1, runtime_seconds=100, intro_start=10)
    await _ep(client, h, season, 2)
    url = f"{A}/episodes/{e1['id']}"
    assert (
        await client.patch(url, headers=h, json={"intro_end": 5})
    ).status_code == 422  # before intro_start
    assert (
        await client.patch(url, headers=h, json={"intro_end": 500})
    ).status_code == 422  # beyond runtime
    assert (await client.patch(url, headers=h, json={"number": 2})).status_code == 409
    assert (await client.patch(url, headers=h, json={"name": None})).status_code == 422
    assert (await client.patch(url, headers=h, json={"intro_end": 50})).status_code == 200


async def test_duplicate_episode_number_is_conflict(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h, _, season = await _series(client, mailbox, db)
    await _ep(client, h, season, 1)
    r = await client.post(
        f"{A}/seasons/{season}/episodes", headers=h, json={"number": 1, "name": "again"}
    )
    assert r.status_code == 409


async def test_reorder_renumbers_atomically(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h, _, season = await _series(client, mailbox, db)
    e = [await _ep(client, h, season, n) for n in (1, 2, 3)]
    ids = [e[2]["id"], e[0]["id"], e[1]["id"]]
    r = await client.post(
        f"{A}/seasons/{season}/episodes/reorder", headers=h, json={"episode_ids": ids}
    )
    assert r.status_code == 200
    assert [(x["id"], x["number"]) for x in r.json()] == [(ids[0], 1), (ids[1], 2), (ids[2], 3)]
    for bad in (
        [ids[0]],
        [*ids, ids[0]],
        [ids[0], ids[0], ids[1]],
        [*ids[:2], "00000000-0000-0000-0000-000000000000"],
        [],
    ):
        assert (
            await client.post(
                f"{A}/seasons/{season}/episodes/reorder", headers=h, json={"episode_ids": bad}
            )
        ).status_code == 422
    after = (await client.get(f"{A}/seasons/{season}/episodes", headers=h)).json()
    assert [x["number"] for x in after] == [1, 2, 3] and [
        x["id"] for x in after
    ] == ids  # failed attempts changed nothing


async def test_reorder_cannot_touch_another_seasons_episodes(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h, t, s1 = await _series(client, mailbox, db)
    s2 = (await client.post(f"{A}/titles/{t['id']}/seasons", headers=h, json={"number": 2})).json()[
        "id"
    ]
    a = await _ep(client, h, s1, 1)
    b = await _ep(client, h, s2, 1)
    r = await client.post(
        f"{A}/seasons/{s1}/episodes/reorder", headers=h, json={"episode_ids": [a["id"], b["id"]]}
    )
    assert r.status_code == 422


async def test_public_view_shows_only_published_episodes_in_order(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h, t, season = await _series(client, mailbox, db)
    await _ep(client, h, season, 1, status="published")
    draft = await _ep(client, h, season, 2)
    await _ep(client, h, season, 3, status="published")
    await client.post(f"{A}/titles/{t['id']}/publish", headers=h)
    public = (await client.get(f"{PUB}/titles/show/seasons")).json()
    assert [e["number"] for e in public[0]["episodes"]] == [1, 3]
    await client.patch(f"{A}/episodes/{draft['id']}", headers=h, json={"status": "published"})
    public = (await client.get(f"{PUB}/titles/show/seasons")).json()
    assert [e["number"] for e in public[0]["episodes"]] == [1, 2, 3]


async def test_deleting_season_and_episode(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h, _, season = await _series(client, mailbox, db)
    e1, _e2 = await _ep(client, h, season, 1), await _ep(client, h, season, 2)
    assert (await client.delete(f"{A}/episodes/{e1['id']}", headers=h)).status_code == 204
    assert (await client.delete(f"{A}/episodes/{e1['id']}", headers=h)).status_code == 404
    assert (await client.delete(f"{A}/seasons/{season}", headers=h)).status_code == 204
    assert await db.scalar(select(func.count()).select_from(Episode)) == 0  # cascaded
