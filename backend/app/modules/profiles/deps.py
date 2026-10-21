"""Profile-scoped endpoints: X-Profile-Id must belong to the authenticated account."""

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import DomainError, NotFound
from app.modules.auth.deps import CurrentUser, require_role
from app.modules.profiles import service


class MissingProfile(DomainError):
    status = 400
    title = "Profile required"


@dataclass(frozen=True)
class CurrentProfile:
    id: uuid.UUID
    user_id: uuid.UUID
    maturity_limit: str


async def require_profile(
    user: Annotated[CurrentUser, Depends(require_role("viewer"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    x_profile_id: Annotated[str | None, Header()] = None,
) -> CurrentProfile:
    if not x_profile_id:
        raise MissingProfile("X-Profile-Id header is required")
    try:
        pid = uuid.UUID(x_profile_id)
    except ValueError as exc:
        raise NotFound("Profile not found") from exc
    profile = await service.get_owned(session, user.id, pid)
    return CurrentProfile(profile.id, profile.user_id, profile.maturity_limit)
