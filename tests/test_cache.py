"""
tests/test_cache.py
-------------------
Unit tests for the SessionCache.

Tests cover: get/set/delete, TTL expiry, cache-disable (TTL=0),
concurrent access, and stats reporting.
"""

import asyncio
import time

import pytest

from gitpulse_mcp.cache.session_cache import SessionCache


@pytest.fixture
def cache() -> SessionCache:
    return SessionCache(ttl_seconds=60)


@pytest.mark.asyncio
async def test_set_and_get(cache: SessionCache) -> None:
    await cache.set("key1", {"data": 42})
    result = await cache.get("key1")
    assert result == {"data": 42}


@pytest.mark.asyncio
async def test_missing_key_returns_none(cache: SessionCache) -> None:
    result = await cache.get("does-not-exist")
    assert result is None


@pytest.mark.asyncio
async def test_delete(cache: SessionCache) -> None:
    await cache.set("key2", "hello")
    await cache.delete("key2")
    assert await cache.get("key2") is None


@pytest.mark.asyncio
async def test_ttl_expiry() -> None:
    short_cache = SessionCache(ttl_seconds=1)
    await short_cache.set("expiring", "value")

    # Should be present immediately
    assert await short_cache.get("expiring") == "value"

    # Wait for TTL to expire
    await asyncio.sleep(1.1)
    assert await short_cache.get("expiring") is None


@pytest.mark.asyncio
async def test_disabled_cache_no_op() -> None:
    """TTL=0 means caching is disabled — set is a no-op."""
    disabled = SessionCache(ttl_seconds=0)
    await disabled.set("k", "v")
    assert await disabled.get("k") is None


@pytest.mark.asyncio
async def test_clear(cache: SessionCache) -> None:
    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.clear()
    assert await cache.get("a") is None
    assert await cache.get("b") is None


@pytest.mark.asyncio
async def test_stats(cache: SessionCache) -> None:
    await cache.set("x", 1)
    await cache.set("y", 2)
    stats = await cache.stats()
    assert stats["live"] == 2
    assert stats["expired"] == 0
    assert stats["total"] == 2


@pytest.mark.asyncio
async def test_per_entry_ttl_override(cache: SessionCache) -> None:
    """Per-entry TTL should override the cache default."""
    await cache.set("short", "v", ttl_seconds=1)
    await cache.set("long", "v", ttl_seconds=120)

    await asyncio.sleep(1.1)

    assert await cache.get("short") is None   # expired
    assert await cache.get("long") == "v"     # still live


@pytest.mark.asyncio
async def test_concurrent_writes(cache: SessionCache) -> None:
    """Concurrent sets should not raise or corrupt data."""
    async def write(i: int) -> None:
        await cache.set(f"key-{i}", i)

    await asyncio.gather(*[write(i) for i in range(50)])
    stats = await cache.stats()
    assert stats["live"] == 50
