import datetime as dt
import itertools

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import (
    Episode,
    Genre,
    Person,
    Season,
    Title,
    TitleGenre,
    TitlePerson,
)

_n = itertools.count(1)
NOW = dt.datetime.now(dt.UTC)


async def title(db: AsyncSession, **kw: object) -> Title:
    i = next(_n)
    data: dict[str, object] = {
        "slug": f"title-{i}",
        "type": "movie",
        "name": f"Title {i}",
        "status": "published",
        "maturity_rating": "13+",
        "release_year": 2020,
        "language": "en",
        "created_at": NOW - dt.timedelta(minutes=i),
    }
    data.update(kw)
    t = Title(**data)
    db.add(t)
    await db.commit()
    return t


async def genre(db: AsyncSession, name: str, slug: str | None = None) -> Genre:
    g = Genre(name=name, slug=slug or name.lower())
    db.add(g)
    await db.commit()
    return g


async def link_genre(db: AsyncSession, t: Title, g: Genre) -> None:
    db.add(TitleGenre(title_id=t.id, genre_id=g.id))
    await db.commit()


async def person(db: AsyncSession, t: Title, name: str, role: str, order: int) -> None:
    p = Person(name=name, slug=name.lower().replace(" ", "-"))
    db.add(p)
    await db.flush()
    db.add(TitlePerson(title_id=t.id, person_id=p.id, role=role, billing_order=order))
    await db.commit()


async def season(db: AsyncSession, t: Title, number: int, episodes: list[tuple[int, str]]) -> None:
    s = Season(title_id=t.id, number=number, name=f"Season {number}")
    db.add(s)
    await db.flush()
    for num, status in episodes:
        db.add(
            Episode(
                season_id=s.id, number=num, name=f"Ep {num}", status=status, runtime_seconds=2400
            )
        )
    await db.commit()
