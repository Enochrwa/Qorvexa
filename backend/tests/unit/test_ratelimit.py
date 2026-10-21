import os

import pytest
from fastapi import Request
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.errors import TooManyRequests
from app.core.ratelimit import Limiter, MemoryBackend, RedisBackend, client_ip


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


async def test_blocks_after_limit_and_resets_after_window() -> None:
    clock = Clock()
    lim = Limiter(None, MemoryBackend(clock), clock)
    for _ in range(3):
        assert (await lim.hit("k", 3, 60))[0] is True
    allowed, retry = await lim.hit("k", 3, 60)
    assert allowed is False and 1 <= retry <= 60
    clock.now += 61
    assert (await lim.hit("k", 3, 60))[0] is True


async def test_enforce_raises_with_retry_after() -> None:
    lim = Limiter(None, MemoryBackend())
    await lim.enforce("k", 1, 30)
    with pytest.raises(TooManyRequests) as exc:
        await lim.enforce("k", 1, 30)
    assert exc.value.status == 429 and exc.value.retry_after >= 1


async def test_check_does_not_count_and_reset_clears() -> None:
    lim = Limiter(None, MemoryBackend())
    await lim.check("k", 1)  # nothing counted yet
    await lim.hit("k", 5, 60)
    with pytest.raises(TooManyRequests):
        await lim.check("k", 1)
    await lim.reset("k")
    await lim.check("k", 1)


async def test_keys_are_independent() -> None:
    lim = Limiter(None, MemoryBackend())
    await lim.hit("a", 1, 60)
    assert (await lim.hit("b", 1, 60))[0] is True


class BrokenBackend:
    async def incr(self, key: str, window: int) -> tuple[int, int]:
        raise OSError("redis down")

    async def get(self, key: str) -> tuple[int, int]:
        raise OSError("redis down")

    async def delete(self, key: str) -> None:
        raise OSError("redis down")


async def test_falls_back_to_memory_when_redis_is_down() -> None:
    lim = Limiter(BrokenBackend(), MemoryBackend())
    assert (await lim.hit("k", 1, 60))[0] is True
    assert (await lim.hit("k", 1, 60))[0] is False  # still limited, not disabled


def _request(headers: dict[str, str], host: str = "10.0.0.9") -> Request:
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": (host, 1234),
    }
    return Request(scope)


def test_client_ip_ignores_forwarded_header_by_default() -> None:
    get_settings.cache_clear()
    assert client_ip(_request({"X-Forwarded-For": "6.6.6.6"})) == "10.0.0.9"


def test_client_ip_uses_trusted_hop_not_spoofable_left_side(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRUSTED_PROXY_COUNT", "1")
    get_settings.cache_clear()
    try:
        # attacker sends "6.6.6.6"; the trusted proxy appends the real peer 203.0.113.5
        assert client_ip(_request({"X-Forwarded-For": "6.6.6.6, 203.0.113.5"})) == "203.0.113.5"
        assert client_ip(_request({})) == "10.0.0.9"  # header missing: fall back to the peer
    finally:
        monkeypatch.delenv("TRUSTED_PROXY_COUNT")
        get_settings.cache_clear()


@pytest.fixture
async def redis_backend() -> RedisBackend:
    client = Redis.from_url(get_settings().redis_url, socket_connect_timeout=0.5)
    try:
        await client.ping()
    except OSError as exc:
        if os.environ.get("CI"):
            raise
        pytest.skip(f"Redis not available: {exc}")
    await client.flushdb()
    return RedisBackend(client)


async def test_redis_backend_counts_expires_and_deletes(redis_backend: RedisBackend) -> None:
    import asyncio

    assert await redis_backend.incr("t:k", 1) == (1, 1)
    assert (await redis_backend.incr("t:k", 1))[0] == 2
    assert (await redis_backend.get("t:k"))[0] == 2
    await asyncio.sleep(1.2)
    assert await redis_backend.get("t:k") == (0, 0)  # window ended
    await redis_backend.incr("t:d", 60)
    await redis_backend.delete("t:d")
    assert await redis_backend.get("t:d") == (0, 0)
