"""Seed script: genres, admin account from environment variables, optional samples.

    python -m app.cli.seed            # genres + admin (if SEED_ADMIN_* are set)
    python -m app.cli.seed --sample   # also add sample titles (never in production)

Idempotent. Never prints or stores a password; there is no default admin password.
"""

import argparse
import asyncio
import os
import sys
import uuid

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_engine
from app.modules.auth.models import User
from app.modules.auth.schemas import RegisterIn
from app.modules.auth.security import hash_password
from app.modules.catalog.models import Genre, Title, TitleGenre
from app.modules.profiles.service import add_default_profile

GENRES = [
    "Action",
    "Adventure",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Family",
    "Fantasy",
    "Horror",
    "Romance",
    "Sci-Fi",
    "Thriller",
]

SAMPLES = [
    (
        "sample-the-long-road",
        "movie",
        "[Sample] The Long Road",
        2021,
        "13+",
        ["drama", "adventure"],
    ),
    ("sample-market-day", "movie", "[Sample] Market Day", 2019, "all", ["comedy", "family"]),
    ("sample-night-shift", "series", "[Sample] Night Shift", 2023, "16+", ["crime", "thriller"]),
    ("sample-lake-stories", "series", "[Sample] Lake Stories", 2022, "7+", ["drama", "family"]),
]


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("+", "plus")


async def seed_genres(session: AsyncSession) -> int:
    existing = set(await session.scalars(select(Genre.slug)))
    new = [Genre(name=n, slug=_slug(n)) for n in GENRES if _slug(n) not in existing]
    session.add_all(new)
    await session.commit()
    return len(new)


async def seed_admin(session: AsyncSession, email: str | None, password: str | None) -> str:
    if not email or not password:
        return "skipped (set SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD)"
    try:
        creds = RegisterIn(email=email, password=password)
    except ValidationError as exc:
        fields = sorted({str(e["loc"][-1]) for e in exc.errors()})
        hint = "password needs 10+ characters and must not be common"
        return f"skipped (invalid {', '.join(fields)}; {hint})"
    existing = await session.scalar(select(User).where(User.email == creds.email))
    if existing is not None:
        return "exists (left unchanged)"
    from datetime import UTC, datetime

    user = User(
        id=uuid.uuid4(),
        email=str(creds.email),
        password_hash=hash_password(creds.password),
        role="admin",
        email_verified_at=datetime.now(UTC),
    )
    session.add(user)
    add_default_profile(session, user.id, str(creds.email))
    await session.commit()
    return "created"


async def seed_samples(session: AsyncSession) -> int:
    if get_settings().app_env == "production":
        raise SystemExit("Refusing to add sample titles when APP_ENV=production")
    genres = {g.slug: g.id for g in await session.scalars(select(Genre))}
    created = 0
    for slug, type_, name, year, rating, genre_slugs in SAMPLES:
        if await session.scalar(select(Title.id).where(Title.slug == slug)):
            continue
        t = Title(
            id=uuid.uuid4(),
            slug=slug,
            type=type_,
            name=name,
            release_year=year,
            maturity_rating=rating,
            language="en",
            status="published",
            synopsis="Sample entry for development. Replace with real content.",
        )
        session.add(t)
        await session.flush()
        session.add_all(
            TitleGenre(title_id=t.id, genre_id=genres[g]) for g in genre_slugs if g in genres
        )
        created += 1
    await session.commit()
    return created


async def run(sample: bool) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    maker = async_sessionmaker(get_engine(), expire_on_commit=False)
    async with maker() as session:
        print(f"genres added: {await seed_genres(session)}")
        email, password = os.environ.get("SEED_ADMIN_EMAIL"), os.environ.get("SEED_ADMIN_PASSWORD")
        print(f"admin: {await seed_admin(session, email, password)}")
        if sample:
            print(f"sample titles added: {await seed_samples(session)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--sample", action="store_true", help="add sample titles (development only)"
    )
    args = parser.parse_args()
    asyncio.run(run(args.sample))
    sys.exit(0)


if __name__ == "__main__":
    main()
