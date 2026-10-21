import os
from collections.abc import AsyncIterator

import pytest
from fastapi import APIRouter, Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-0123")

from app.core.config import get_settings
from app.core.db import get_session
from app.core.ratelimit import Limiter, MemoryBackend, get_rate_limiter
from app.main import create_app
from app.modules.auth.deps import CurrentUser, require_role
from app.modules.auth.email import get_email_sender
from app.modules.profiles.deps import CurrentProfile, require_profile


class FakeEmailSender:
    """Captures outgoing mail so tests can read verification and reset links."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))

    def last_token(self) -> str:
        body = self.sent[-1][2]
        return body.split("token=")[1].split()[0]


@pytest.fixture
def mailbox() -> FakeEmailSender:
    return FakeEmailSender()


def _wire_test_routes(app: FastAPI) -> None:
    """Throwaway routes to exercise require_role until real admin endpoints exist."""
    r = APIRouter(prefix="/_test")

    @r.get("/viewer")
    async def viewer(u: CurrentUser = Depends(require_role("viewer"))) -> dict[str, str]:  # noqa: B008
        return {"role": u.role}

    @r.get("/editor")
    async def editor(u: CurrentUser = Depends(require_role("editor"))) -> dict[str, str]:  # noqa: B008
        return {"role": u.role}

    @r.get("/admin")
    async def admin(u: CurrentUser = Depends(require_role("admin"))) -> dict[str, str]:  # noqa: B008
        return {"role": u.role}

    @r.get("/profile-scoped")
    async def scoped(p: CurrentProfile = Depends(require_profile)) -> dict[str, str]:  # noqa: B008
        return {"id": str(p.id), "maturity_limit": p.maturity_limit}

    app.include_router(r)


@pytest.fixture
def limiter() -> Limiter:
    """Fresh in-memory limiter per test, so tests never share counters or need Redis."""
    return Limiter(None, MemoryBackend())


@pytest.fixture
async def client(mailbox: FakeEmailSender, limiter: Limiter) -> AsyncIterator[AsyncClient]:
    """App client with a per-test NullPool engine and a fake mailer."""
    app = create_app()
    _wire_test_routes(app)
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def _session() -> AsyncIterator[AsyncSession]:
        async with maker() as s:
            yield s

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_email_sender] = lambda: mailbox
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    await engine.dispose()


@pytest.fixture
async def db() -> AsyncIterator[AsyncSession]:
    """Direct DB access for assertions; skips locally if Postgres is down, fails in CI."""
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("TRUNCATE users CASCADE"))
            await conn.commit()
    except OSError as exc:  # connection refused etc.
        await engine.dispose()
        if os.environ.get("CI"):
            raise
        pytest.skip(f"Postgres not available: {exc}")
    async with async_sessionmaker(engine, expire_on_commit=False)() as s:
        yield s
    async with engine.connect() as conn:
        await conn.execute(text("TRUNCATE users CASCADE"))
        await conn.commit()
    await engine.dispose()
