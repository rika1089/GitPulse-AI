"""
tests/test_github_client.py
----------------------------
Unit tests for GitHubClient using respx to mock HTTP responses.

Tests cover: successful GET, cache hits, 404 → NotFoundError,
429 → RateLimitError, 5xx retry logic, and paginated_get.
"""

from __future__ import annotations

import pytest
import respx
import httpx

from gitpulse_mcp.github.client import (
    GitHubClient,
    GitHubError,
    NotFoundError,
    RateLimitError,
)


BASE = "https://api.github.com"


@pytest.fixture
def client() -> GitHubClient:
    """Fresh client for each test — avoids shared cache state."""
    c = GitHubClient()
    # Disable cache for most tests to keep assertions clean
    return c


@pytest.mark.asyncio
@respx.mock
async def test_successful_get(client: GitHubClient) -> None:
    respx.get(f"{BASE}/repos/facebook/react").mock(
        return_value=httpx.Response(200, json={"name": "react", "stargazers_count": 200000})
    )

    data = await client.get("/repos/facebook/react", use_cache=False)

    assert data["name"] == "react"
    assert data["stargazers_count"] == 200000


@pytest.mark.asyncio
@respx.mock
async def test_404_raises_not_found(client: GitHubClient) -> None:
    respx.get(f"{BASE}/repos/nobody/norepo").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )

    with pytest.raises(NotFoundError):
        await client.get("/repos/nobody/norepo", use_cache=False)


@pytest.mark.asyncio
@respx.mock
async def test_rate_limit_raises_rate_limit_error(client: GitHubClient) -> None:
    respx.get(f"{BASE}/repos/x/y").mock(
        return_value=httpx.Response(
            403,
            json={"message": "API rate limit exceeded"},
            headers={"X-RateLimit-Reset": "9999999999", "X-RateLimit-Remaining": "0"},
        )
    )

    with pytest.raises(RateLimitError) as exc_info:
        await client.get("/repos/x/y", use_cache=False)

    assert exc_info.value.reset_at == 9999999999


@pytest.mark.asyncio
@respx.mock
async def test_server_error_raises_github_error(client: GitHubClient) -> None:
    # Max retries is 3 by default — mock all attempts
    respx.get(f"{BASE}/repos/a/b").mock(
        return_value=httpx.Response(500, json={"message": "Internal Server Error"})
    )

    with pytest.raises(GitHubError) as exc_info:
        await client.get("/repos/a/b", use_cache=False)

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
@respx.mock
async def test_paginated_get_collects_all_pages(client: GitHubClient) -> None:
    page1 = [{"id": i} for i in range(100)]
    page2 = [{"id": i} for i in range(100, 150)]

    respx.get(f"{BASE}/repos/a/b/issues").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
            httpx.Response(200, json=[]),  # empty page signals end
        ]
    )

    results = await client.paginated_get(
        "/repos/a/b/issues", max_pages=3, per_page=100
    )

    assert len(results) == 150


@pytest.mark.asyncio
@respx.mock
async def test_paginated_get_stops_on_partial_page(client: GitHubClient) -> None:
    """If a page has fewer items than per_page, it's the last page."""
    partial_page = [{"id": i} for i in range(42)]

    respx.get(f"{BASE}/repos/a/b/commits").mock(
        return_value=httpx.Response(200, json=partial_page)
    )

    results = await client.paginated_get(
        "/repos/a/b/commits", max_pages=5, per_page=100
    )

    # Should stop after first page since len(42) < 100
    assert len(results) == 42


@pytest.mark.asyncio
@respx.mock
async def test_cache_key_includes_params(client: GitHubClient) -> None:
    """Two calls with different params should be cached separately."""
    respx.get(f"{BASE}/repos/a/b/issues").mock(
        side_effect=[
            httpx.Response(200, json=[{"id": 1}]),
            httpx.Response(200, json=[{"id": 2}]),
        ]
    )

    r1 = await client.get(
        "/repos/a/b/issues", params={"state": "open"}, use_cache=True
    )
    r2 = await client.get(
        "/repos/a/b/issues", params={"state": "closed"}, use_cache=True
    )

    assert r1 != r2  # Different params → different cache keys → different results


@pytest.mark.asyncio
@respx.mock
async def test_cache_hit_avoids_second_request(client: GitHubClient) -> None:
    """The second call with use_cache=True should not hit the network."""
    route = respx.get(f"{BASE}/repos/cached/repo").mock(
        return_value=httpx.Response(200, json={"name": "cached"})
    )

    await client.get("/repos/cached/repo", use_cache=True)
    await client.get("/repos/cached/repo", use_cache=True)  # should be cache hit

    # Should have been called exactly once
    assert route.call_count == 1
