import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.modules.auth.deps import CurrentUser, require_role
from app.modules.catalog import admin_service as svc
from app.modules.catalog.admin_schemas import (
    AdminEpisode,
    AdminSeason,
    AdminTitle,
    AdminTitleList,
    EpisodeCreate,
    EpisodePatch,
    PublishIn,
    ReorderIn,
    SeasonCreate,
    SeasonPatch,
    TitleCreate,
    TitlePatch,
)


async def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(_no_store)])

Session = Annotated[AsyncSession, Depends(get_session)]
# Every endpoint takes `Editor`; tests assert that no /admin route is reachable without it.
Editor = Annotated[CurrentUser, Depends(require_role("editor"))]


@router.get("/titles")
async def list_titles(
    _: Editor,
    session: Session,
    status: Annotated[str | None, Query(pattern="^(draft|scheduled|published|archived)$")] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0, le=100000)] = 0,
) -> AdminTitleList:
    return await svc.list_titles(session, status, q, limit, offset)


@router.post("/titles", status_code=201)
async def create_title(body: TitleCreate, user: Editor, session: Session) -> AdminTitle:
    return await svc.create_title(session, user.id, body)


@router.get("/titles/{title_id}")
async def get_title(title_id: uuid.UUID, _: Editor, session: Session) -> AdminTitle:
    return await svc.get_title(session, title_id)


@router.patch("/titles/{title_id}")
async def update_title(
    title_id: uuid.UUID, body: TitlePatch, user: Editor, session: Session
) -> AdminTitle:
    return await svc.update_title(session, user.id, title_id, body)


@router.delete("/titles/{title_id}", status_code=204)
async def delete_title(title_id: uuid.UUID, user: Editor, session: Session) -> None:
    await svc.delete_title(session, user.id, title_id)


@router.post("/titles/{title_id}/publish")
async def publish_title(
    title_id: uuid.UUID, user: Editor, session: Session, body: PublishIn | None = None
) -> AdminTitle:
    return await svc.publish_title(session, user.id, title_id, body or PublishIn())


@router.post("/titles/{title_id}/unpublish")
async def unpublish_title(title_id: uuid.UUID, user: Editor, session: Session) -> AdminTitle:
    return await svc.unpublish_title(session, user.id, title_id)


@router.get("/titles/{title_id}/seasons")
async def list_seasons(title_id: uuid.UUID, _: Editor, session: Session) -> list[AdminSeason]:
    return await svc.list_seasons(session, title_id)


@router.post("/titles/{title_id}/seasons", status_code=201)
async def create_season(
    title_id: uuid.UUID, body: SeasonCreate, user: Editor, session: Session
) -> AdminSeason:
    return await svc.create_season(session, user.id, title_id, body)


@router.patch("/seasons/{season_id}")
async def update_season(
    season_id: uuid.UUID, body: SeasonPatch, user: Editor, session: Session
) -> AdminSeason:
    return await svc.update_season(session, user.id, season_id, body)


@router.delete("/seasons/{season_id}", status_code=204)
async def delete_season(season_id: uuid.UUID, user: Editor, session: Session) -> None:
    await svc.delete_season(session, user.id, season_id)


@router.get("/seasons/{season_id}/episodes")
async def list_episodes(season_id: uuid.UUID, _: Editor, session: Session) -> list[AdminEpisode]:
    return await svc.list_episodes(session, season_id)


@router.post("/seasons/{season_id}/episodes", status_code=201)
async def create_episode(
    season_id: uuid.UUID, body: EpisodeCreate, user: Editor, session: Session
) -> AdminEpisode:
    return await svc.create_episode(session, user.id, season_id, body)


@router.post("/seasons/{season_id}/episodes/reorder")
async def reorder_episodes(
    season_id: uuid.UUID, body: ReorderIn, user: Editor, session: Session
) -> list[AdminEpisode]:
    return await svc.reorder_episodes(session, user.id, season_id, body.episode_ids)


@router.patch("/episodes/{episode_id}")
async def update_episode(
    episode_id: uuid.UUID, body: EpisodePatch, user: Editor, session: Session
) -> AdminEpisode:
    return await svc.update_episode(session, user.id, episode_id, body)


@router.delete("/episodes/{episode_id}", status_code=204)
async def delete_episode(episode_id: uuid.UUID, user: Editor, session: Session) -> None:
    await svc.delete_episode(session, user.id, episode_id)
