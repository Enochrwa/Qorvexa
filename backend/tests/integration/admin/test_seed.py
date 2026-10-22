import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli import seed
from app.core.config import get_settings
from app.modules.auth.models import User
from app.modules.catalog.models import Genre, Title
from app.modules.profiles.models import Profile
from tests.integration.auth.helpers import login

PW = "a-strong-seed-password"


async def test_genres_are_seeded_once(db: AsyncSession) -> None:
    assert await seed.seed_genres(db) == len(seed.GENRES)
    assert await seed.seed_genres(db) == 0
    assert await db.scalar(select(func.count()).select_from(Genre)) == len(seed.GENRES)
    assert await db.scalar(select(Genre.slug).where(Genre.name == "Sci-Fi")) == "sci-fi"


async def test_no_admin_without_credentials(db: AsyncSession) -> None:
    for email, pw in ((None, None), ("a@example.com", None), (None, PW), ("", "")):
        assert (await seed.seed_admin(db, email, pw)).startswith("skipped")
    assert await db.scalar(select(func.count()).select_from(User)) == 0


async def test_weak_or_invalid_credentials_are_refused_without_echoing_them(
    db: AsyncSession,
) -> None:
    for email, pw in (
        ("a@example.com", "short"),
        ("a@example.com", "password123"),
        ("not-an-email", PW),
    ):
        msg = await seed.seed_admin(db, email, pw)
        assert msg.startswith("skipped") and pw not in msg
    assert await db.scalar(select(func.count()).select_from(User)) == 0


async def test_admin_is_created_verified_with_profile_and_can_log_in(
    client: AsyncClient, db: AsyncSession
) -> None:
    assert await seed.seed_admin(db, "Boss@Example.com", PW) == "created"
    user = await db.scalar(select(User).where(User.email == "boss@example.com"))
    assert user is not None and user.role == "admin" and user.email_verified_at is not None
    assert PW not in user.password_hash and user.password_hash.startswith("$argon2id$")
    assert (
        await db.scalar(select(func.count()).select_from(Profile).where(Profile.user_id == user.id))
        == 1
    )
    assert (await login(client, "boss@example.com", PW)).status_code == 200


async def test_rerun_never_overwrites_an_existing_account(
    client: AsyncClient, db: AsyncSession
) -> None:
    await seed.seed_admin(db, "boss@example.com", PW)
    assert (await seed.seed_admin(db, "boss@example.com", "a-different-password")).startswith(
        "exists"
    )
    assert (await login(client, "boss@example.com", PW)).status_code == 200
    assert (await login(client, "boss@example.com", "a-different-password")).status_code == 401
    assert await db.scalar(select(func.count()).select_from(User)) == 1


async def test_seed_never_promotes_an_existing_viewer(db: AsyncSession) -> None:
    db.add(User(email="viewer@example.com", password_hash="x"))
    await db.commit()
    assert (await seed.seed_admin(db, "viewer@example.com", PW)).startswith("exists")
    assert await db.scalar(select(User.role).where(User.email == "viewer@example.com")) == "viewer"


async def test_sample_titles_are_idempotent_labelled_and_visible_by_audience(
    client: AsyncClient, db: AsyncSession
) -> None:
    await seed.seed_genres(db)
    assert await seed.seed_samples(db) == len(seed.SAMPLES)
    assert await seed.seed_samples(db) == 0
    names = list(await db.scalars(select(Title.name)))
    assert names and all(n.startswith("[Sample]") for n in names)
    public = {i["slug"] for i in (await client.get("/api/v1/titles")).json()["items"]}
    assert "sample-night-shift" not in public  # 16+ is hidden from the anonymous default
    assert "sample-market-day" in public


async def test_samples_refuse_to_run_in_production(
    db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "x" * 40)
    monkeypatch.setenv("COOKIE_SECURE", "true")
    get_settings.cache_clear()
    try:
        with pytest.raises(SystemExit, match="production"):
            await seed.seed_samples(db)
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
    assert await db.scalar(select(func.count()).select_from(Title)) == 0
