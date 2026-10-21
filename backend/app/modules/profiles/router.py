import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.modules.auth.deps import CurrentUser, require_role
from app.modules.profiles import service
from app.modules.profiles.schemas import ProfileCreate, ProfileOut, ProfilePatch

router = APIRouter(prefix="/profiles", tags=["profiles"])

Session = Annotated[AsyncSession, Depends(get_session)]
Viewer = Annotated[CurrentUser, Depends(require_role("viewer"))]


@router.get("")
async def list_profiles(user: Viewer, session: Session) -> list[ProfileOut]:
    return [ProfileOut.model_validate(p) for p in await service.list_profiles(session, user.id)]


@router.post("", status_code=201)
async def create_profile(body: ProfileCreate, user: Viewer, session: Session) -> ProfileOut:
    return ProfileOut.model_validate(await service.create_profile(session, user.id, body))


@router.patch("/{profile_id}")
async def update_profile(
    profile_id: uuid.UUID, body: ProfilePatch, user: Viewer, session: Session
) -> ProfileOut:
    profile = await service.update_profile(session, user.id, profile_id, body.changes())
    return ProfileOut.model_validate(profile)


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(profile_id: uuid.UUID, user: Viewer, session: Session) -> None:
    await service.delete_profile(session, user.id, profile_id)
