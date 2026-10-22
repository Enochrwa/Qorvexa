import datetime as dt
import hashlib
from collections.abc import Sequence
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.core.ratelimit import Limiter, client_ip, get_rate_limiter
from app.modules.catalog import service
from app.modules.catalog.service import Sort
from app.modules.profiles.deps import CurrentProfile, optional_profile

CATALOG_READS_PER_IP = (120, 60)  # docs/api/api-design.md


async def _limit_reads(
    request: Request, limiter: Annotated[Limiter, Depends(get_rate_limiter)]
) -> None:
    await limiter.enforce(f"rl:catalog:ip:{client_ip(request)}", *CATALOG_READS_PER_IP)


router = APIRouter(tags=["catalog"], dependencies=[Depends(_limit_reads)])

Session = Annotated[AsyncSession, Depends(get_session)]
Profile = Annotated[CurrentProfile | None, Depends(optional_profile)]
Slug = Annotated[str, Query(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=120)]


def _limit_for(profile: CurrentProfile | None) -> str:
    return profile.maturity_limit if profile else get_settings().public_maturity_limit


def _respond(request: Request, payload: BaseModel | Sequence[BaseModel]) -> Response:
    """JSON with a weak ETag; 304 when the client already has this exact body.

    Responses depend on the caller's profile, so they are private (never shared caches).
    """
    data: Any = (
        [p.model_dump(mode="json") for p in payload]
        if not isinstance(payload, BaseModel)
        else payload.model_dump(mode="json")
    )
    body = JSONResponse(data)
    etag = 'W/"' + hashlib.sha256(body.body).hexdigest()[:32] + '"'
    headers = {
        "ETag": etag,
        "Cache-Control": "private, no-cache",
        "Vary": "Authorization, X-Profile-Id",
    }
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    body.headers.update(headers)
    return body


@router.get("/titles")
async def list_titles(
    request: Request,
    session: Session,
    profile: Profile,
    type: Annotated[str | None, Query(pattern="^(movie|series)$")] = None,
    genre: Slug | None = None,
    year: Annotated[int | None, Query(ge=1888, le=2100)] = None,
    language: Annotated[str | None, Query(pattern=r"^[a-z]{2,3}(-[A-Za-z]{2,4})?$")] = None,
    sort: Sort = "added",
    limit: Annotated[int, Query(ge=1, le=50)] = 24,
    cursor: Annotated[str | None, Query(max_length=300)] = None,
) -> Response:
    result = await service.list_titles(
        session,
        now=dt.datetime.now(dt.UTC),
        maturity_limit=_limit_for(profile),
        title_type=type,
        genre=genre,
        year=year,
        language=language,
        sort=sort,
        limit=limit,
        cursor=cursor,
    )
    return _respond(request, result)


@router.get("/titles/{slug}")
async def get_title(request: Request, slug: str, session: Session, profile: Profile) -> Response:
    result = await service.get_title(session, slug, dt.datetime.now(dt.UTC), _limit_for(profile))
    return _respond(request, result)


@router.get("/titles/{slug}/seasons")
async def list_seasons(request: Request, slug: str, session: Session, profile: Profile) -> Response:
    result = await service.list_seasons(session, slug, dt.datetime.now(dt.UTC), _limit_for(profile))
    return _respond(request, result)


@router.get("/genres")
async def list_genres(request: Request, session: Session) -> Response:
    return _respond(request, await service.list_genres(session))
