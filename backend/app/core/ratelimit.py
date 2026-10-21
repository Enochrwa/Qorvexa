"""Fixed-window rate limiting on Redis, with an in-process fallback if Redis is down.

Failure mode (documented in docs/backend/auth.md): if Redis is unreachable the limiter keeps
working per process from memory, so limits are weaker (not shared between instances) but never
disabled and never block all logins.
"""

import logging
import time
from collections.abc import Callable
from functools import lru_cache
from typing import Any, Protocol

from fastapi import Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.core.errors import TooManyRequests

log = logging.getLogger(__name__)

_LUA_INCR = """
local n = redis.call('INCR', KEYS[1])
if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return {n, redis.call('TTL', KEYS[1])}
"""


class Backend(Protocol):
    async def incr(self, key: str, window: int) -> tuple[int, int]:
        """Increment and return (count, seconds until the window ends)."""

    async def get(self, key: str) -> tuple[int, int]:
        """Return (count, seconds left) without incrementing; (0, 0) if absent."""

    async def delete(self, key: str) -> None: ...


class MemoryBackend:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._data: dict[str, tuple[int, float]] = {}

    def _live(self, key: str) -> tuple[int, float] | None:
        item = self._data.get(key)
        if item is None:
            return None
        if item[1] <= self._clock():
            del self._data[key]
            return None
        return item

    async def incr(self, key: str, window: int) -> tuple[int, int]:
        item = self._live(key)
        if item is None:
            self._data[key] = (1, self._clock() + window)
            return 1, window
        count, expires = item[0] + 1, item[1]
        self._data[key] = (count, expires)
        return count, max(1, int(expires - self._clock()))

    async def get(self, key: str) -> tuple[int, int]:
        item = self._live(key)
        if item is None:
            return 0, 0
        return item[0], max(1, int(item[1] - self._clock()))

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)


class RedisBackend:
    def __init__(self, client: Redis) -> None:
        self._r = client
        self._script: Any = client.register_script(_LUA_INCR)

    async def incr(self, key: str, window: int) -> tuple[int, int]:
        n, ttl = await self._script(keys=[key], args=[window])
        return int(n), max(1, int(ttl))

    async def get(self, key: str) -> tuple[int, int]:
        pipe = self._r.pipeline()
        pipe.get(key)
        pipe.ttl(key)
        raw, ttl = await pipe.execute()
        return (int(raw), max(1, int(ttl))) if raw is not None else (0, 0)

    async def delete(self, key: str) -> None:
        await self._r.delete(key)


class Limiter:
    def __init__(
        self,
        primary: Backend | None,
        fallback: Backend | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._primary = primary
        self._fallback: Backend = fallback or MemoryBackend(clock)
        self._clock = clock
        self._down_until = 0.0

    async def _run(self, op: str, *args: Any) -> Any:
        if self._primary is not None and self._clock() >= self._down_until:
            try:
                return await getattr(self._primary, op)(*args)
            except (RedisError, OSError, TimeoutError):
                self._down_until = self._clock() + 10  # do not retry Redis on every request
                log.warning("rate limiter: Redis unavailable, using in-process fallback")
        return await getattr(self._fallback, op)(*args)

    async def hit(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Count one event. Returns (allowed, retry_after_seconds)."""
        count, ttl = await self._run("incr", key, window)
        return count <= limit, ttl

    async def enforce(self, key: str, limit: int, window: int) -> None:
        allowed, retry = await self.hit(key, limit, window)
        if not allowed:
            raise TooManyRequests(retry)

    async def check(self, key: str, limit: int) -> None:
        """Raise if the counter has already reached the limit (does not count)."""
        count, ttl = await self._run("get", key)
        if count >= limit:
            raise TooManyRequests(ttl)

    async def reset(self, key: str) -> None:
        await self._run("delete", key)


@lru_cache
def get_rate_limiter() -> Limiter:
    settings = get_settings()
    client = Redis.from_url(
        settings.redis_url, socket_timeout=0.5, socket_connect_timeout=0.5, decode_responses=True
    )
    return Limiter(RedisBackend(client))


def client_ip(request: Request) -> str:
    """Client IP. X-Forwarded-For is honoured only for the configured number of trusted proxies."""
    hops = get_settings().trusted_proxy_count
    if hops > 0:
        parts = [
            p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()
        ]
        if len(parts) >= hops:
            return parts[-hops]  # the address the outermost trusted proxy saw
    return request.client.host if request.client else "unknown"
