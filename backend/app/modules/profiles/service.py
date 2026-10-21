import re
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import Conflict, NotFound
from app.modules.auth.models import User
from app.modules.profiles.models import Profile
from app.modules.profiles.schemas import ProfileCreate


def default_profile_name(email: str) -> str:
    local = re.sub(r"[^\w .'-]", "", email.split("@")[0], flags=re.UNICODE).strip()
    return (local[:40] or "Me").strip() or "Me"


def add_default_profile(session: AsyncSession, user_id: uuid.UUID, email: str) -> None:
    """Called at registration, inside the same transaction as the user insert."""
    session.add(Profile(user_id=user_id, name=default_profile_name(email), maturity_limit="18+"))


async def list_profiles(session: AsyncSession, user_id: uuid.UUID) -> list[Profile]:
    rows = await session.scalars(
        select(Profile).where(Profile.user_id == user_id).order_by(Profile.created_at, Profile.id)
    )
    return list(rows)


async def get_owned(session: AsyncSession, user_id: uuid.UUID, profile_id: uuid.UUID) -> Profile:
    """Another account's profile is indistinguishable from a missing one (404)."""
    profile = await session.scalar(
        select(Profile).where(Profile.id == profile_id, Profile.user_id == user_id)
    )
    if profile is None:
        raise NotFound("Profile not found")
    return profile


async def create_profile(session: AsyncSession, user_id: uuid.UUID, data: ProfileCreate) -> Profile:
    # Lock the account row so two concurrent creates cannot both pass the limit check.
    await session.execute(select(User.id).where(User.id == user_id).with_for_update())
    count = await session.scalar(
        select(func.count()).select_from(Profile).where(Profile.user_id == user_id)
    )
    limit = get_settings().max_profiles_per_account
    if (count or 0) >= limit:
        raise Conflict(f"An account can have at most {limit} profiles")
    profile = Profile(user_id=user_id, **data.model_dump())
    session.add(profile)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise Conflict("You already have a profile with that name") from exc
    return profile


async def update_profile(
    session: AsyncSession, user_id: uuid.UUID, profile_id: uuid.UUID, changes: dict[str, Any]
) -> Profile:
    profile = await get_owned(session, user_id, profile_id)
    for key, value in changes.items():
        setattr(profile, key, value)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise Conflict("You already have a profile with that name") from exc
    return profile


async def delete_profile(session: AsyncSession, user_id: uuid.UUID, profile_id: uuid.UUID) -> None:
    await session.execute(select(User.id).where(User.id == user_id).with_for_update())
    profile = await get_owned(session, user_id, profile_id)
    count = await session.scalar(
        select(func.count()).select_from(Profile).where(Profile.user_id == user_id)
    )
    if (count or 0) <= 1:
        raise Conflict("You cannot delete your only profile")
    await session.delete(profile)
    await session.commit()
