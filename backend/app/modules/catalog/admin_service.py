"""Admin catalog use cases. Every mutation writes an audit row in the same transaction."""

import datetime as dt
import re
import unicodedata
import uuid
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflict, DomainError, NotFound
from app.modules.audit import service as audit
from app.modules.catalog.admin_schemas import (
    AdminEpisode,
    AdminSeason,
    AdminTitle,
    AdminTitleItem,
    AdminTitleList,
    CastIn,
    CastOut,
    EpisodeCreate,
    EpisodePatch,
    PublishIn,
    SeasonCreate,
    SeasonPatch,
    TitleCreate,
    TitlePatch,
    changed_fields,
)
from app.modules.catalog.models import (
    Episode,
    Genre,
    Person,
    Season,
    Title,
    TitleGenre,
    TitlePerson,
)


class Invalid(DomainError):
    status = 422
    title = "Validation error"


def slugify(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")[:120].strip("-")
    return slug or "title"


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _state(t: Title, now: dt.datetime) -> str:
    if t.status in ("draft", "archived"):
        return t.status
    if t.status == "scheduled":
        return "draft"
    if t.publish_at is not None and t.publish_at > now:
        return "scheduled"
    if t.available_until is not None and t.available_until <= now:
        return "expired"
    return "live"


def _item(t: Title, now: dt.datetime) -> AdminTitleItem:
    return AdminTitleItem(
        id=t.id,
        slug=t.slug,
        type=t.type,
        name=t.name,
        status=t.status,
        state=_state(t, now),
        maturity_rating=t.maturity_rating,
        release_year=t.release_year,
        publish_at=t.publish_at,
        available_until=t.available_until,
        updated_at=t.updated_at,
    )


async def _detail(session: AsyncSession, t: Title) -> AdminTitle:
    genres = await session.scalars(
        select(Genre.slug)
        .join(TitleGenre, TitleGenre.genre_id == Genre.id)
        .where(TitleGenre.title_id == t.id)
        .order_by(Genre.slug)
    )
    cast = await session.execute(
        select(Person.name, TitlePerson.role, TitlePerson.billing_order)
        .join(TitlePerson, TitlePerson.person_id == Person.id)
        .where(TitlePerson.title_id == t.id)
        .order_by(TitlePerson.billing_order, Person.name)
    )
    base = _item(t, _now()).model_dump()
    return AdminTitle(
        **base,
        original_name=t.original_name,
        synopsis=t.synopsis,
        language=t.language,
        country=t.country,
        poster_url=t.poster_url,
        backdrop_url=t.backdrop_url,
        downloads_enabled=t.downloads_enabled,
        created_at=t.created_at,
        genres=list(genres),
        cast=[CastOut(name=n, role=r, billing_order=o) for n, r, o in cast],
    )


async def _get_title(session: AsyncSession, title_id: uuid.UUID) -> Title:
    t = await session.get(Title, title_id)
    if t is None:
        raise NotFound("Title not found")
    return t


async def _set_genres(session: AsyncSession, title_id: uuid.UUID, slugs: list[str]) -> None:
    rows = list(await session.scalars(select(Genre).where(Genre.slug.in_(slugs)))) if slugs else []
    missing = sorted(set(slugs) - {g.slug for g in rows})
    if missing:
        raise Invalid(f"Unknown genre(s): {', '.join(missing)}")
    await session.execute(delete(TitleGenre).where(TitleGenre.title_id == title_id))
    session.add_all(TitleGenre(title_id=title_id, genre_id=g.id) for g in rows)


async def _set_cast(session: AsyncSession, title_id: uuid.UUID, cast: list[CastIn]) -> None:
    await session.execute(delete(TitlePerson).where(TitlePerson.title_id == title_id))
    for c in cast:
        slug = slugify(c.name)
        person = await session.scalar(select(Person).where(Person.slug == slug))
        if person is None:
            person = Person(name=c.name, slug=slug)
            session.add(person)
            await session.flush()
        session.add(
            TitlePerson(
                title_id=title_id, person_id=person.id, role=c.role, billing_order=c.billing_order
            )
        )
        await session.flush()


# ---- titles ----------------------------------------------------------------------------------


async def list_titles(
    session: AsyncSession, status: str | None, q: str | None, limit: int, offset: int
) -> AdminTitleList:
    cond = []
    if status:
        cond.append(Title.status == status)
    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        cond.append(Title.name.ilike(f"%{escaped}%", escape="\\"))
    total = await session.scalar(select(func.count()).select_from(Title).where(*cond))
    rows = await session.scalars(
        select(Title)
        .where(*cond)
        .order_by(Title.created_at.desc(), Title.id.desc())
        .limit(limit)
        .offset(offset)
    )
    now = _now()
    return AdminTitleList(items=[_item(t, now) for t in rows], total=total or 0)


async def create_title(session: AsyncSession, actor: uuid.UUID, data: TitleCreate) -> AdminTitle:
    explicit = data.slug is not None
    slug = data.slug or slugify(data.name)
    if not explicit:  # auto slugs get a numeric suffix instead of failing
        base, n = slug, 1
        while await session.scalar(select(Title.id).where(Title.slug == slug)):
            n += 1
            slug = f"{base[:110]}-{n}"
    title = Title(slug=slug, **data.model_dump(exclude={"slug", "genres", "cast"}))
    session.add(title)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise Conflict("A title with that slug already exists") from exc
    await _set_genres(session, title.id, data.genres)
    await _set_cast(session, title.id, data.cast)
    audit.record(session, actor, "title.create", "title", title.id, slug=slug)
    await session.commit()
    return await _detail(session, title)


async def get_title(session: AsyncSession, title_id: uuid.UUID) -> AdminTitle:
    return await _detail(session, await _get_title(session, title_id))


async def update_title(
    session: AsyncSession, actor: uuid.UUID, title_id: uuid.UUID, patch: TitlePatch
) -> AdminTitle:
    title = await _get_title(session, title_id)
    changes = patch.model_dump(exclude_unset=True, exclude={"genres", "cast"})
    for key, value in changes.items():
        setattr(title, key, value)
    if patch.genres is not None:
        await _set_genres(session, title.id, patch.genres)
    if patch.cast is not None:
        await _set_cast(session, title.id, patch.cast)
    title.updated_at = _now()
    audit.record(session, actor, "title.update", "title", title.id, fields=changed_fields(patch))
    await session.commit()
    return await _detail(session, title)


async def delete_title(session: AsyncSession, actor: uuid.UUID, title_id: uuid.UUID) -> None:
    title = await _get_title(session, title_id)
    if title.status == "published":
        raise Conflict("Unpublish the title before deleting it")
    audit.record(
        session, actor, "title.delete", "title", title.id, slug=title.slug, name=title.name
    )
    await session.delete(title)
    await session.commit()


async def publish_title(
    session: AsyncSession, actor: uuid.UUID, title_id: uuid.UUID, body: PublishIn
) -> AdminTitle:
    title = await _get_title(session, title_id)
    missing = [f for f in ("synopsis", "poster_url") if not getattr(title, f)]
    if missing:
        raise Conflict(f"Title is not ready to publish: missing {', '.join(missing)}")
    now = _now()
    if "publish_at" in body.model_fields_set:
        title.publish_at = body.publish_at
    if title.publish_at is None:
        title.publish_at = now
    if "available_until" in body.model_fields_set:
        title.available_until = body.available_until
    if title.available_until is not None and title.available_until <= max(title.publish_at, now):
        raise Invalid("available_until must be in the future and after publish_at")
    title.status = "published"
    title.updated_at = now
    audit.record(
        session,
        actor,
        "title.publish",
        "title",
        title.id,
        publish_at=title.publish_at.isoformat(),
        available_until=title.available_until.isoformat() if title.available_until else None,
    )
    await session.commit()
    return await _detail(session, title)


async def unpublish_title(
    session: AsyncSession, actor: uuid.UUID, title_id: uuid.UUID
) -> AdminTitle:
    title = await _get_title(session, title_id)
    title.status = "draft"
    title.updated_at = _now()
    audit.record(session, actor, "title.unpublish", "title", title.id)
    await session.commit()
    return await _detail(session, title)


# ---- seasons and episodes --------------------------------------------------------------------


def _ep(e: Episode) -> AdminEpisode:
    return AdminEpisode(
        id=e.id,
        number=e.number,
        name=e.name,
        synopsis=e.synopsis,
        runtime_seconds=e.runtime_seconds,
        air_date=e.air_date,
        intro_start=e.intro_start,
        intro_end=e.intro_end,
        recap_end=e.recap_end,
        status=e.status,
    )


def _season(s: Season, episodes: list[Episode] | None = None) -> AdminSeason:
    return AdminSeason(
        id=s.id,
        title_id=s.title_id,
        number=s.number,
        name=s.name,
        synopsis=s.synopsis,
        episodes=[_ep(e) for e in episodes or []],
    )


async def _get_season(session: AsyncSession, season_id: uuid.UUID) -> Season:
    s = await session.get(Season, season_id)
    if s is None:
        raise NotFound("Season not found")
    return s


async def _get_episode(session: AsyncSession, episode_id: uuid.UUID) -> Episode:
    e = await session.get(Episode, episode_id)
    if e is None:
        raise NotFound("Episode not found")
    return e


def _check_times(
    runtime_seconds: int | None,
    intro_start: int | None,
    intro_end: int | None,
    recap_end: int | None,
) -> None:
    if intro_start is not None and intro_end is not None and intro_end < intro_start:
        raise Invalid("intro_end must not be before intro_start")
    if runtime_seconds is not None:
        for name, value in (
            ("intro_start", intro_start),
            ("intro_end", intro_end),
            ("recap_end", recap_end),
        ):
            if value is not None and value > runtime_seconds:
                raise Invalid(f"{name} must not exceed runtime_seconds")


async def list_seasons(session: AsyncSession, title_id: uuid.UUID) -> list[AdminSeason]:
    await _get_title(session, title_id)
    seasons = list(
        await session.scalars(
            select(Season).where(Season.title_id == title_id).order_by(Season.number)
        )
    )
    eps = await session.scalars(
        select(Episode)
        .where(Episode.season_id.in_([s.id for s in seasons]))
        .order_by(Episode.number)
    )
    by: dict[uuid.UUID, list[Episode]] = {s.id: [] for s in seasons}
    for e in eps:
        by[e.season_id].append(e)
    return [_season(s, by[s.id]) for s in seasons]


async def create_season(
    session: AsyncSession, actor: uuid.UUID, title_id: uuid.UUID, data: SeasonCreate
) -> AdminSeason:
    title = await _get_title(session, title_id)
    if title.type != "series":
        raise Conflict("Only series have seasons")
    season = Season(id=uuid.uuid4(), title_id=title_id, **data.model_dump())
    session.add(season)
    audit.record(session, actor, "season.create", "season", season.id, title_id=str(title_id))
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise Conflict("That season number already exists") from exc
    return _season(season)


async def update_season(
    session: AsyncSession, actor: uuid.UUID, season_id: uuid.UUID, patch: SeasonPatch
) -> AdminSeason:
    season = await _get_season(session, season_id)
    for key, value in patch.model_dump(exclude_unset=True).items():
        setattr(season, key, value)
    audit.record(session, actor, "season.update", "season", season.id, fields=changed_fields(patch))
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise Conflict("That season number already exists") from exc
    return _season(season)


async def delete_season(session: AsyncSession, actor: uuid.UUID, season_id: uuid.UUID) -> None:
    season = await _get_season(session, season_id)
    audit.record(
        session,
        actor,
        "season.delete",
        "season",
        season.id,
        title_id=str(season.title_id),
        number=season.number,
    )
    await session.delete(season)
    await session.commit()


async def list_episodes(session: AsyncSession, season_id: uuid.UUID) -> list[AdminEpisode]:
    await _get_season(session, season_id)
    eps = await session.scalars(
        select(Episode).where(Episode.season_id == season_id).order_by(Episode.number)
    )
    return [_ep(e) for e in eps]


async def create_episode(
    session: AsyncSession, actor: uuid.UUID, season_id: uuid.UUID, data: EpisodeCreate
) -> AdminEpisode:
    await _get_season(session, season_id)
    _check_times(
        runtime_seconds=data.runtime_seconds,
        intro_start=data.intro_start,
        intro_end=data.intro_end,
        recap_end=data.recap_end,
    )
    ep = Episode(id=uuid.uuid4(), season_id=season_id, **data.model_dump())
    session.add(ep)
    audit.record(session, actor, "episode.create", "episode", ep.id, season_id=str(season_id))
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise Conflict("That episode number already exists in this season") from exc
    return _ep(ep)


async def update_episode(
    session: AsyncSession, actor: uuid.UUID, episode_id: uuid.UUID, patch: EpisodePatch
) -> AdminEpisode:
    ep = await _get_episode(session, episode_id)
    changes: dict[str, Any] = patch.model_dump(exclude_unset=True)
    merged = {
        k: changes.get(k, getattr(ep, k))
        for k in ("runtime_seconds", "intro_start", "intro_end", "recap_end")
    }
    _check_times(**merged)
    for key, value in changes.items():
        setattr(ep, key, value)
    audit.record(session, actor, "episode.update", "episode", ep.id, fields=changed_fields(patch))
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise Conflict("That episode number already exists in this season") from exc
    return _ep(ep)


async def delete_episode(session: AsyncSession, actor: uuid.UUID, episode_id: uuid.UUID) -> None:
    ep = await _get_episode(session, episode_id)
    audit.record(
        session,
        actor,
        "episode.delete",
        "episode",
        ep.id,
        season_id=str(ep.season_id),
        number=ep.number,
    )
    await session.delete(ep)
    await session.commit()


async def reorder_episodes(
    session: AsyncSession, actor: uuid.UUID, season_id: uuid.UUID, ids: list[uuid.UUID]
) -> list[AdminEpisode]:
    """Renumber a season's episodes 1..n in the given order, atomically."""
    await _get_season(session, season_id)
    current = set(await session.scalars(select(Episode.id).where(Episode.season_id == season_id)))
    if len(ids) != len(set(ids)) or set(ids) != current:
        raise Invalid("episode_ids must list every episode of the season exactly once")
    # Two phases so the unique (season_id, number) constraint is never violated mid-way.
    await session.execute(
        update(Episode).where(Episode.season_id == season_id).values(number=Episode.number + 10000)
    )
    for position, episode_id in enumerate(ids, start=1):
        await session.execute(
            update(Episode).where(Episode.id == episode_id).values(number=position)
        )
    audit.record(session, actor, "episode.reorder", "season", season_id, count=len(ids))
    await session.commit()
    return await list_episodes(session, season_id)
