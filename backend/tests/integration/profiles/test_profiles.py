from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.profiles.models import Profile
from tests.conftest import FakeEmailSender
from tests.integration.auth.helpers import PASSWORD, bearer, login, register_verified

P = "/api/v1/profiles"


async def _user(
    client: AsyncClient, mailbox: FakeEmailSender, email: str = "viewer@example.com"
) -> dict[str, str]:
    await register_verified(client, mailbox, email)
    return bearer(await login(client, email))


async def test_registration_creates_default_adult_profile(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _user(client, mailbox, "jane.doe@example.com")
    r = await client.get(P, headers=h)
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["name"] == "jane.doe" and items[0]["maturity_limit"] == "18+"


async def test_requires_authentication(client: AsyncClient, db: AsyncSession) -> None:
    assert (await client.get(P)).status_code == 401
    assert (await client.post(P, json={"name": "x"})).status_code == 401


async def test_create_with_defaults_and_custom_fields(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _user(client, mailbox)
    r = await client.post(P, headers=h, json={"name": "  Kids  "})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Kids" and body["maturity_limit"] == "13+"
    assert (
        body["autoplay_next"] is True and body["data_saver"] is False and body["language"] == "en"
    )
    r = await client.post(
        P,
        headers=h,
        json={
            "name": "Little",
            "avatar": "avatar-7",
            "language": "rw",
            "maturity_limit": "all",
            "data_saver": True,
            "subtitle_prefs": {"enabled": True, "language": "en", "size": "large"},
        },
    )
    assert r.status_code == 201
    assert r.json()["subtitle_prefs"] == {"enabled": True, "language": "en", "size": "large"}


async def test_validation_rejects_bad_input(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _user(client, mailbox)
    bad = [
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 41},
        {"name": "bad\x00name"},
        {"name": "ok", "maturity_limit": "21+"},
        {"name": "ok", "avatar": "../../etc/passwd"},
        {"name": "ok", "avatar": "avatar-13"},
        {"name": "ok", "language": "english"},
        {"name": "ok", "subtitle_prefs": {"size": "huge"}},
        {"name": "ok", "autoplay_next": "maybe"},
        {"name": "ok", "user_id": "00000000-0000-0000-0000-000000000000"},  # mass assignment
        {"name": "ok", "subtitle_prefs": {"extra": 1}},
    ]
    for payload in bad:
        r = await client.post(P, headers=h, json=payload)
        assert r.status_code == 422, payload


async def test_duplicate_name_is_case_insensitive_conflict(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _user(client, mailbox)
    assert (await client.post(P, headers=h, json={"name": "Kids"})).status_code == 201
    r = await client.post(P, headers=h, json={"name": "kIDS"})
    assert r.status_code == 409


async def test_same_name_allowed_for_different_accounts(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    a = await _user(client, mailbox, "a@example.com")
    b = await _user(client, mailbox, "b@example.com")
    assert (await client.post(P, headers=a, json={"name": "Shared"})).status_code == 201
    assert (await client.post(P, headers=b, json={"name": "Shared"})).status_code == 201


async def test_max_profiles_per_account(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _user(client, mailbox)  # 1 default
    for i in range(4):
        assert (await client.post(P, headers=h, json={"name": f"p{i}"})).status_code == 201
    r = await client.post(P, headers=h, json={"name": "one-too-many"})
    assert r.status_code == 409 and "at most 5" in r.json()["detail"]
    count = await db.scalar(select(func.count()).select_from(Profile))
    assert count == 5


async def test_patch_updates_only_given_fields(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _user(client, mailbox)
    created = (await client.post(P, headers=h, json={"name": "Kid", "maturity_limit": "7+"})).json()
    r = await client.patch(
        f"{P}/{created['id']}", headers=h, json={"data_saver": True, "maturity_limit": "13+"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["data_saver"] is True and body["maturity_limit"] == "13+" and body["name"] == "Kid"


async def test_patch_rejects_nulls_unknown_fields_and_duplicate_names(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _user(client, mailbox, "jane@example.com")
    kid = (await client.post(P, headers=h, json={"name": "Kid"})).json()
    url = f"{P}/{kid['id']}"
    assert (await client.patch(url, headers=h, json={"name": None})).status_code == 422
    assert (await client.patch(url, headers=h, json={"user_id": "x"})).status_code == 422
    assert (await client.patch(url, headers=h, json={"id": kid["id"]})).status_code == 422
    assert (
        await client.patch(url, headers=h, json={"name": "JANE"})
    ).status_code == 409  # default profile's name


async def test_other_accounts_profiles_are_invisible_and_untouchable(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    a = await _user(client, mailbox, "a@example.com")
    b = await _user(client, mailbox, "b@example.com")
    a_profile = (await client.get(P, headers=a)).json()[0]
    assert all(p["id"] != a_profile["id"] for p in (await client.get(P, headers=b)).json())
    url = f"{P}/{a_profile['id']}"
    assert (await client.patch(url, headers=b, json={"name": "hacked"})).status_code == 404
    assert (await client.delete(url, headers=b)).status_code == 404
    still = await db.scalar(select(Profile).where(Profile.id == a_profile["id"]))
    assert still is not None and still.name != "hacked"


async def test_unknown_or_malformed_id_is_404_or_422(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _user(client, mailbox)
    assert (
        await client.patch(f"{P}/00000000-0000-0000-0000-000000000000", headers=h, json={})
    ).status_code == 404
    assert (await client.delete(f"{P}/not-a-uuid", headers=h)).status_code == 422


async def test_delete_profile_but_never_the_last(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    h = await _user(client, mailbox)
    extra = (await client.post(P, headers=h, json={"name": "Extra"})).json()
    assert (await client.delete(f"{P}/{extra['id']}", headers=h)).status_code == 204
    only = (await client.get(P, headers=h)).json()
    assert len(only) == 1
    r = await client.delete(f"{P}/{only[0]['id']}", headers=h)
    assert r.status_code == 409


async def test_deleting_account_removes_profiles(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    await _user(client, mailbox)
    user = await db.scalar(select(User))
    assert user is not None
    await db.delete(user)
    await db.commit()
    assert await db.scalar(select(func.count()).select_from(Profile)) == 0


async def test_profile_header_dependency(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    a = await _user(client, mailbox, "a@example.com")
    b = await _user(client, mailbox, "b@example.com")
    a_id = (await client.get(P, headers=a)).json()[0]["id"]
    url = "/_test/profile-scoped"
    assert (await client.get(url)).status_code == 401
    assert (await client.get(url, headers=a)).status_code == 400  # header missing
    ok = await client.get(url, headers={**a, "X-Profile-Id": a_id})
    assert ok.status_code == 200 and ok.json()["maturity_limit"] == "18+"
    assert (await client.get(url, headers={**b, "X-Profile-Id": a_id})).status_code == 404
    assert (await client.get(url, headers={**a, "X-Profile-Id": "garbage"})).status_code == 404


async def test_duplicate_registration_creates_one_user_and_one_profile(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    for _ in range(2):  # duplicate registration must not add a second profile or user
        await client.post(
            "/api/v1/auth/register", json={"email": "dup@example.com", "password": PASSWORD}
        )
    assert await db.scalar(select(func.count()).select_from(User)) == 1
    assert await db.scalar(select(func.count()).select_from(Profile)) == 1


async def test_concurrent_creates_cannot_exceed_the_limit(
    client: AsyncClient, mailbox: FakeEmailSender, db: AsyncSession
) -> None:
    import asyncio

    h = await _user(client, mailbox)  # 1 default profile, cap is 5
    results = await asyncio.gather(
        *[client.post(P, headers=h, json={"name": f"race{i}"}) for i in range(8)]
    )
    codes = sorted(r.status_code for r in results)
    assert codes.count(201) == 4 and codes.count(409) == 4
    assert await db.scalar(select(func.count()).select_from(Profile)) == 5
