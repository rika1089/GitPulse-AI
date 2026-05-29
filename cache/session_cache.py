"""
cache/session_cache.py
----------------------
In-memory TTL cache for GitHub API responses.

Why this exists:
  A single full_repo_assessment() call fans out into 6-8 GitHub API requests.
  Without caching, repeated calls within a session burn rate limit fast and
  add 2-5 seconds of latency for large repos. This cache stores raw API
  payloads keyed by URL for a configurable TTL (default 5 minutes).

Design decisions:
  - Dict-based, not Redis/SQLite — no infra dependency for local dev/MCP usage.
  - Thread-safe via asyncio.Lock — safe for concurrent tool calls.
  - TTL is per-entry, not global sweep — entries expire lazily on next read.
  - Cache is keyed by the exact GitHub API URL so it's transparent to callers.

Usage:
    from gitpulse_mcp.cache.session_cache import cache

    data = await cache.get("https://api.github.com/repos/facebook/react")
    if data is None:
        data = await fetch_from_github(...)
        await cache.set("https://api.github.com/repos/facebook/react", data)
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from gitpulse_mcp.config import settings


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl_seconds: int) -> None:
        self.value = value
        self.expires_at: float = time.monotonic() + ttl_seconds


class SessionCache:
    """
    Async-safe, TTL-based in-memory cache.

    All public methods are coroutines so the calling code is consistent
    regardless of whether we swap in an async Redis client later.
    """

    def __init__(self, ttl_seconds: int | None = None) -> None:
        self._ttl = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds
        self._store: dict[str, _CacheEntry] = {}
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Any | None:
        """
        Return the cached value for `key`, or None if missing / expired.
        Expired entries are deleted on read (lazy eviction).
        """
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.monotonic() > entry.expires_at:
                del self._store[key]
                return None
            return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """
        Store `value` under `key` with an optional per-entry TTL override.
        If TTL is 0 (disabled in settings), the write is a no-op.
        """
        effective_ttl = ttl_seconds if ttl_seconds is not None else self._ttl
        if effective_ttl == 0:
            return  # caching disabled
        async with self._lock:
            self._store[key] = _CacheEntry(value, effective_ttl)

    async def delete(self, key: str) -> None:
        """Explicitly remove a cache entry (e.g. after a write operation)."""
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        """Flush the entire cache — useful between test runs."""
        async with self._lock:
            self._store.clear()

    async def stats(self) -> dict[str, int]:
        """Return live/expired entry counts — useful for debugging."""
        now = time.monotonic()
        async with self._lock:
            total = len(self._store)
            expired = sum(
                1 for e in self._store.values() if now > e.expires_at
            )
        return {"total": total, "live": total - expired, "expired": expired}

    def __repr__(self) -> str:
        return f"SessionCache(ttl={self._ttl}s, entries={len(self._store)})"


# ---------------------------------------------------------------------------
# Module-level singleton — import and use directly
# ---------------------------------------------------------------------------

cache = SessionCache()
