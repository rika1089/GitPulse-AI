"""
github/client.py
----------------
Low-level async GitHub REST API client.

Responsibilities:
  - Attach authentication and API-version headers to every request.
  - Enforce per-call timeouts and a configurable retry policy.
  - Respect GitHub's rate limit: parse X-RateLimit-* headers and back off
    when the remaining budget is near zero (< 10 requests left).
  - Cache GET responses via SessionCache to avoid redundant calls within a session.
  - Expose paginated_get() for endpoints that return multi-page results.

All other github/* modules use this client — they never create httpx sessions
directly. This keeps auth and error-handling logic in one place.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from gitpulse_mcp.cache.session_cache import cache
from gitpulse_mcp.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class GitHubError(Exception):
    """Raised when the GitHub API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str, url: str) -> None:
        self.status_code = status_code
        self.url = url
        super().__init__(f"GitHub API error {status_code} for {url}: {message}")


class RateLimitError(GitHubError):
    """Raised when we hit GitHub's primary rate limit (403/429)."""

    def __init__(self, reset_at: int, url: str) -> None:
        self.reset_at = reset_at  # Unix timestamp when limit resets
        super().__init__(
            status_code=429,
            message=f"Rate limit exceeded. Resets at Unix timestamp {reset_at}.",
            url=url,
        )


class NotFoundError(GitHubError):
    """Raised on 404 — repository or resource does not exist."""

    def __init__(self, url: str) -> None:
        super().__init__(status_code=404, message="Resource not found.", url=url)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class GitHubClient:
    """
    Async GitHub REST API client.

    Instantiate once and reuse — it holds an httpx.AsyncClient connection pool.
    Call close() when done (or use as an async context manager).

    Example:
        async with GitHubClient() as gh:
            repo = await gh.get("/repos/facebook/react")
    """

    _BASE_URL = settings.github_base_url
    _HEADERS = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": settings.github_api_version,
    }
    _LOW_RATE_LIMIT_THRESHOLD = 10  # pause below this many remaining requests

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=self._BASE_URL,
            headers=self._HEADERS,
            timeout=httpx.Timeout(settings.github_timeout_seconds),
            follow_redirects=True,
        )
        self._rate_limit_remaining: int = 5000
        self._rate_limit_reset: int = 0

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Core request method
    # ------------------------------------------------------------------

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Any:
        """
        Make a GET request to `path` (relative to base URL).

        Args:
            path:       API path e.g. "/repos/facebook/react"
            params:     Query parameters dict e.g. {"per_page": 100}
            use_cache:  If True, check session cache before hitting the API.

        Returns:
            Parsed JSON response (dict or list).

        Raises:
            NotFoundError:    404 response.
            RateLimitError:   403/429 with rate-limit headers.
            GitHubError:      Any other non-2xx response.
        """
        # Build a deterministic cache key from path + sorted params
        cache_key = self._build_cache_key(path, params)

        if use_cache:
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit: %s", cache_key)
                return cached

        # Rate-limit pre-check — pause if budget is very low
        await self._wait_if_rate_limited()

        response = await self._request_with_retry("GET", path, params=params)
        self._update_rate_limit_state(response)

        data = response.json()

        if use_cache:
            await cache.set(cache_key, data)

        return data

    # ------------------------------------------------------------------
    # Paginated requests
    # ------------------------------------------------------------------

    async def paginated_get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        max_pages: int = 10,
        per_page: int = 100,
    ) -> list[Any]:
        """
        Fetch all pages of a paginated GitHub endpoint.

        Stops after `max_pages` pages to avoid unbounded requests on
        large repositories (e.g. repos with thousands of issues).

        Args:
            path:       API path.
            params:     Additional query parameters.
            max_pages:  Hard ceiling on number of pages fetched.
            per_page:   Items per page (max 100 per GitHub API).

        Returns:
            Flattened list of all items across pages.
        """
        results: list[Any] = []
        merged_params = {**(params or {}), "per_page": per_page, "page": 1}

        for page_num in range(1, max_pages + 1):
            merged_params["page"] = page_num
            # Don't cache individual pages — cache the assembled result if needed
            page_data = await self.get(path, params=merged_params, use_cache=False)

            if not page_data:
                break  # GitHub returns [] on the page after the last one

            results.extend(page_data if isinstance(page_data, list) else [page_data])

            if len(page_data) < per_page:
                break  # Last page — less than full page means no more data

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """
        Execute an HTTP request with exponential-backoff retry.

        Retries on:
          - 5xx server errors (GitHub-side transient failures)
          - httpx.TimeoutException

        Does NOT retry on 4xx client errors (404, 401, 422 etc.)
        except for 429 rate-limit responses which are handled separately.
        """
        last_exc: Exception | None = None
        for attempt in range(settings.github_max_retries + 1):
            try:
                response = await self._client.request(method, path, params=params)
                self._raise_for_status(response)
                return response

            except RateLimitError:
                raise  # Don't retry rate limit errors — propagate to caller

            except GitHubError as exc:
                if exc.status_code < 500:
                    raise  # 4xx errors are not transient — raise immediately

                last_exc = exc
                wait_seconds = 2**attempt  # 1s, 2s, 4s ...
                logger.warning(
                    "GitHub %s error on attempt %d/%d — retrying in %ds",
                    exc.status_code,
                    attempt + 1,
                    settings.github_max_retries + 1,
                    wait_seconds,
                )
                await asyncio.sleep(wait_seconds)

            except httpx.TimeoutException as exc:
                last_exc = exc
                wait_seconds = 2**attempt
                logger.warning(
                    "Timeout on attempt %d/%d for %s — retrying in %ds",
                    attempt + 1,
                    settings.github_max_retries + 1,
                    path,
                    wait_seconds,
                )
                await asyncio.sleep(wait_seconds)

        raise GitHubError(
            status_code=500,
            message=f"All {settings.github_max_retries + 1} attempts failed. Last error: {last_exc}",
            url=path,
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Convert HTTP error responses into typed exceptions."""
        if response.is_success:
            return

        url = str(response.url)
        if response.status_code == 404:
            raise NotFoundError(url=url)

        if response.status_code in (403, 429):
            reset_ts = int(response.headers.get("X-RateLimit-Reset", 0))
            raise RateLimitError(reset_at=reset_ts, url=url)

        # Generic error — extract GitHub's message field if present
        try:
            body = response.json()
            message = body.get("message", response.text)
        except Exception:
            message = response.text

        raise GitHubError(
            status_code=response.status_code,
            message=message,
            url=url,
        )

    async def _wait_if_rate_limited(self) -> None:
        """
        If remaining rate-limit budget is critically low, sleep until reset.
        This is a proactive check — we'd rather wait a few seconds than
        hammer the API and get a hard 403.
        """
        if self._rate_limit_remaining < self._LOW_RATE_LIMIT_THRESHOLD:
            import time

            wait = max(0, self._rate_limit_reset - time.time()) + 1
            logger.warning(
                "Rate limit nearly exhausted (%d remaining). Sleeping %.1fs.",
                self._rate_limit_remaining,
                wait,
            )
            await asyncio.sleep(wait)

    def _update_rate_limit_state(self, response: httpx.Response) -> None:
        """Parse rate-limit headers and update internal counters."""
        try:
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset = response.headers.get("X-RateLimit-Reset")
            if remaining is not None:
                self._rate_limit_remaining = int(remaining)
            if reset is not None:
                self._rate_limit_reset = int(reset)
        except (ValueError, TypeError):
            pass  # Header missing or malformed — not critical

    @staticmethod
    def _build_cache_key(path: str, params: dict[str, Any] | None) -> str:
        """Build a deterministic cache key from path + sorted query params."""
        if not params:
            return path
        sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{path}?{sorted_params}"


# ---------------------------------------------------------------------------
# Module-level singleton — shared across all github/* modules
# ---------------------------------------------------------------------------

# Instantiated lazily on first access to avoid startup errors if .env is missing
_client: GitHubClient | None = None


def get_client() -> GitHubClient:
    """
    Return the module-level GitHub client singleton.

    Import this function instead of instantiating GitHubClient directly.
    The singleton is created once on first call and reused.
    """
    global _client
    if _client is None:
        _client = GitHubClient()
    return _client
