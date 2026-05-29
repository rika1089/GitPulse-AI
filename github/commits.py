"""
github/commits.py
-----------------
Fetches commit activity metrics and recent commit history.

Endpoints used:
  GET /repos/{owner}/{repo}/commits          — recent commits (paginated)
  GET /repos/{owner}/{repo}/stats/commit_activity — weekly commit counts (52 weeks)

Commit frequency is one of the highest-weight inputs (30%) in the health score,
so getting accurate numbers matters. We use two complementary approaches:

  1. stats/commit_activity — GitHub pre-aggregates weekly totals for 52 weeks.
     Fast and cheap (1 API call), but can be empty for recently-created repos or
     when GitHub hasn't finished caching it (returns 202 Accepted). We handle
     that gracefully.

  2. Direct commit listing — Fall back to listing commits with a `since` param
     and counting them. More API calls but always accurate.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from gitpulse_mcp.config import settings
from gitpulse_mcp.github.client import GitHubError, get_client

logger = logging.getLogger(__name__)


async def fetch_commit_activity(owner: str, repo: str) -> list[dict[str, Any]]:
    """
    Fetch GitHub's pre-aggregated weekly commit activity (52 weeks).

    Each item has:
      - week: Unix timestamp of the week start (Sunday)
      - total: total commits that week
      - days: list of 7 daily counts [Sun, Mon, ..., Sat]

    Returns [] if GitHub returns 202 (still computing) or on error.
    Callers should fall back to count_commits_since() in that case.
    """
    client = get_client()
    try:
        data = await client.get(
            f"/repos/{owner}/{repo}/stats/commit_activity",
            use_cache=True,
        )
        if not isinstance(data, list):
            return []
        return data
    except GitHubError as exc:
        if exc.status_code == 202:
            # GitHub is computing stats — common for repos with large history
            logger.info(
                "GitHub is computing commit stats for %s/%s (202). "
                "Falling back to direct commit count.",
                owner,
                repo,
            )
        else:
            logger.warning("Could not fetch commit activity: %s", exc)
        return []


async def count_commits_since(
    owner: str,
    repo: str,
    days: int | None = None,
) -> int:
    """
    Count commits in the last `days` days by listing commits with `since`.

    This is the fallback when stats/commit_activity returns 202 or empty data.
    We fetch at most 1 page (100 commits) and return the count — accurate enough
    for the health score formula unless the repo has > 100 commits/month.

    For very active repos (100 commits returned), we fetch a second page
    to get a more accurate count up to 200.
    """
    lookback = days if days is not None else settings.activity_lookback_days
    since_dt = datetime.now(tz=timezone.utc) - timedelta(days=lookback)
    since_iso = since_dt.isoformat().replace("+00:00", "Z")

    client = get_client()
    commits = await client.paginated_get(
        f"/repos/{owner}/{repo}/commits",
        params={"since": since_iso},
        max_pages=2,
        per_page=100,
    )
    return len(commits)


async def get_commit_metrics(
    owner: str,
    repo: str,
) -> dict[str, Any]:
    """
    Return commit frequency metrics for health scoring and display.

    Returns:
        {
            "commits_last_30_days": int,
            "commits_last_90_days": int,
            "weekly_trend": list[int],   # 12 most recent weekly totals
            "avg_commits_per_week": float,
        }
    """
    activity = await fetch_commit_activity(owner, repo)

    if activity:
        # stats/commit_activity returned data — compute from it
        recent_weeks = activity[-13:]  # last 13 weeks ≈ 90 days
        weekly_totals = [week["total"] for week in recent_weeks]

        commits_last_90 = sum(weekly_totals)
        commits_last_30 = sum(w["total"] for w in activity[-5:])  # ~4.3 weeks
        avg_per_week = commits_last_90 / 13 if weekly_totals else 0.0

        return {
            "commits_last_30_days": commits_last_30,
            "commits_last_90_days": commits_last_90,
            "weekly_trend": weekly_totals[-12:],  # trim to 12 for chart display
            "avg_commits_per_week": round(avg_per_week, 1),
        }

    # Fallback: direct commit listing
    logger.debug("Using fallback commit count for %s/%s", owner, repo)
    commits_30 = await count_commits_since(owner, repo, days=30)
    commits_90 = await count_commits_since(owner, repo, days=90)

    return {
        "commits_last_30_days": commits_30,
        "commits_last_90_days": commits_90,
        "weekly_trend": [],  # not available from fallback method
        "avg_commits_per_week": round(commits_90 / 13, 1),
    }


async def fetch_recent_commits(
    owner: str,
    repo: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Fetch the most recent commits for the activity timeline.

    Each item includes: sha, commit.message, commit.author.name,
    commit.author.date, author.avatar_url (if available).
    """
    client = get_client()
    commits = await client.paginated_get(
        f"/repos/{owner}/{repo}/commits",
        max_pages=1,
        per_page=limit,
    )
    return commits[:limit]
