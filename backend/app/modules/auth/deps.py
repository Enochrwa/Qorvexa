"""FastAPI dependencies: current user and role enforcement."""

import uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import Forbidden, Unauthorized
from app.modules.auth.models import User
from app.modules.auth.security import ROLE_RANK, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: uuid.UUID
    email: str
    role: str
    email_verified: bool


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentUser:
    """Authenticate from the bearer token; role and status come from the DB, not the token."""
    claims = decode_access_token(creds.credentials) if creds else None
    if claims is None:
        raise Unauthorized("Not authenticated")
    user = await session.get(User, claims.user_id)
    if user is None or user.status != "active":
        raise Unauthorized("Not authenticated")
    return CurrentUser(user.id, user.email, user.role, user.email_verified_at is not None)


def require_role(
    minimum: str,
) -> Callable[..., Coroutine[Any, Any, CurrentUser]]:
    """Dependency factory: viewer < editor < admin. Unknown role names fail at import time."""
    if minimum not in ROLE_RANK:
        raise ValueError(f"unknown role: {minimum}")

    async def _dep(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if ROLE_RANK.get(user.role, -1) < ROLE_RANK[minimum]:
            raise Forbidden("Insufficient permissions")
        return user

    return _dep
