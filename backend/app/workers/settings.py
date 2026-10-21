"""ARQ worker settings (jobs are added from Sprint 2)."""

from typing import ClassVar

from arq.connections import RedisSettings

from app.core.config import get_settings


class WorkerSettings:
    functions: ClassVar[list[object]] = []
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
