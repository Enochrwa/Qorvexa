import base64
import binascii
import datetime as dt
import json
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import ColumnElement, Select, func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError, NotFound
from app.modules.catalog.models import (
    Episode,
    Genre,
    Person,
    Season,
    Title,
    TitleGenre,
    TitlePerson,
)
from app.modules.catalog.schemas import (
    EpisodeOut,
    GenreOut,
    PersonCredit,
    SeasonOut,
    TitleDetail,
    TitleList,
    TitleListItem,
)
from app.modules.catalog.visibility import visible_title

Sort = Literal["added", "name", "year"]


class InvalidCursor(DomainError):
    status = 422
    title = "Invalid cursor"


@dataclass(frozen=True)
class _SortSpec:
    key: ColumnElement[Any]
    descending: bool
    parse: Any


_SORTS: dict[str, _SortSpec] = {
    "added": _SortSpec(Title.created_at.expression, True, dt.datetime.fromisoformat),
    "name": _SortSpec(func.lower(Title.name), False, str),
    "year": _SortSpec(func.coalesce(Title.release_year, 0), True, int),
}


def _encode(sort: str, key: Any, title_id: Any) -> str:
    if isinstance(key, dt.datetime):
        key = key.isoformat()
    raw = json.dumps({"s": sort, "k": key, "i": str(title_id)}, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def _decode(cursor: str, sort: str) -> tuple[Any, Any]:
    import uuid

    try:
        pad = "=" * (-len(cursor) % 4)
        data = json.loads(base64.urlsafe_b64decode(cursor + pad))
        if data["s"] != sort:
            raise ValueError("sort mismatch")
        return _SORTS[sort].parse(data["k"]), uuid.UUID(data["i"])
    except (ValueError, KeyError, TypeError, binascii.Error, json.JSONDecodeError) as exc:
        raise InvalidCursor("The cursor is invalid for this request") from exc


async def _genres_for(session: AsyncSession, title_ids: list[Any]) -> dict[Any, list[GenreOut]]:
    out: dict[Any, list[GenreOut]] = {t: [] for t in title_ids}
    if not title_ids:
        return out
    rows = await session.execute(
        select(TitleGenre.title_id, Genre.name, Genre.slug)
        .join(Genre, Genre.id == TitleGenre.genre_id)
        .where(TitleGenre.title_id.in_(title_ids))
        .order_by(Genre.name)
    )
    for title_id, name, slug in rows:
        out[title_id].append(GenreOut(name=name, slug=slug))
    return out


def _item(t: Title, genres: list[GenreOut]) -> dict[str, Any]:
    return {
        "id": t.id,
        "slug": t.slug,
        "type": t.type,
        "name": t.name,
        "release_year": t.release_year,
        "maturity_rating": t.maturity_rating,
        "language": t.language,
        "poster_url": t.poster_url,
        "genres": genres,
    }


async def list_titles(
    session: AsyncSession,
    *,
    now: dt.datetime,
    maturity_limit: str,
    title_type: str | None,
    genre: str | None,
    year: int | None,
    language: str | None,
    sort: Sort,
    limit: int,
    cursor: str | None,
) -> TitleList:
    spec = _SORTS[sort]
    stmt: Select[Any] = select(Title, spec.key.label("sort_key")).where(
        visible_title(now, maturity_limit)
    )
    if title_type:
        stmt = stmt.where(Title.type == title_type)
    if year is not None:
        stmt = stmt.where(Title.release_year == year)
    if language:
        stmt = stmt.where(Title.language == language)
    if genre:
        stmt = stmt.where(
            Title.id.in_(
                select(TitleGenre.title_id)
                .join(Genre, Genre.id == TitleGenre.genre_id)
                .where(Genre.slug == genre)
            )
        )
    if cursor:
        key, last_id = _decode(cursor, sort)
        pair, bound = tuple_(spec.key, Title.id), tuple_(key, last_id)
        stmt = stmt.where(pair < bound if spec.descending else pair > bound)
    if spec.descending:
        stmt = stmt.order_by(spec.key.desc(), Title.id.desc())
    else:
        stmt = stmt.order_by(spec.key.asc(), Title.id.asc())
    rows = (await session.execute(stmt.limit(limit + 1))).all()
    page = rows[:limit]
    genres = await _genres_for(session, [r[0].id for r in page])
    items = [TitleListItem(**_item(r[0], genres[r[0].id])) for r in page]
    next_cursor = _encode(sort, page[-1][1], page[-1][0].id) if len(rows) > limit else None
    return TitleList(items=items, next_cursor=next_cursor)


async def _visible_by_slug(
    session: AsyncSession, slug: str, now: dt.datetime, maturity_limit: str
) -> Title:
    title = await session.scalar(
        select(Title).where(Title.slug == slug, visible_title(now, maturity_limit))
    )
    if title is None:
        raise NotFound("Title not found")  # hidden and missing look the same
    return title


async def get_title(
    session: AsyncSession, slug: str, now: dt.datetime, maturity_limit: str
) -> TitleDetail:
    t = await _visible_by_slug(session, slug, now, maturity_limit)
    genres = (await _genres_for(session, [t.id]))[t.id]
    cast_rows = await session.execute(
        select(Person.name, Person.slug, TitlePerson.role)
        .join(TitlePerson, TitlePerson.person_id == Person.id)
        .where(TitlePerson.title_id == t.id)
        .order_by(TitlePerson.billing_order, Person.name)
    )
    seasons = await session.scalar(
        select(func.count()).select_from(Season).where(Season.title_id == t.id)
    )
    return TitleDetail(
        **_item(t, genres),
        original_name=t.original_name,
        synopsis=t.synopsis,
        country=t.country,
        backdrop_url=t.backdrop_url,
        downloads_enabled=t.downloads_enabled,
        cast=[PersonCredit(name=n, slug=s, role=r) for n, s, r in cast_rows],
        season_count=seasons or 0,
    )


async def list_seasons(
    session: AsyncSession, slug: str, now: dt.datetime, maturity_limit: str
) -> list[SeasonOut]:
    t = await _visible_by_slug(session, slug, now, maturity_limit)
    seasons = list(
        await session.scalars(select(Season).where(Season.title_id == t.id).order_by(Season.number))
    )
    episodes = await session.scalars(
        select(Episode)
        .where(Episode.season_id.in_([s.id for s in seasons]), Episode.status == "published")
        .order_by(Episode.number)
    )
    by_season: dict[Any, list[EpisodeOut]] = {s.id: [] for s in seasons}
    for e in episodes:
        by_season[e.season_id].append(
            EpisodeOut(
                id=e.id,
                number=e.number,
                name=e.name,
                synopsis=e.synopsis,
                runtime_seconds=e.runtime_seconds,
                air_date=e.air_date,
            )
        )
    return [
        SeasonOut(number=s.number, name=s.name, synopsis=s.synopsis, episodes=by_season[s.id])
        for s in seasons
    ]


async def list_genres(session: AsyncSession) -> list[GenreOut]:
    rows = await session.scalars(select(Genre).order_by(Genre.name))
    return [GenreOut(name=g.name, slug=g.slug) for g in rows]
