"""
github/issues.py
----------------
Fetches issue metrics and open issue data for health scoring and triage.

Endpoints used:
  GET /repos/{owner}/{repo}/issues?state=all    — all issues (paginated)
  GET /repos/{owner}/{repo}/issues?state=open   — open issues for triage

Note: GitHub's /issues endpoint includes pull requests in its results.
We filter them out using the absence of the `pull_request` key.

Metrics computed here feed into two health score components:
  - issue_close_rate (25% weight):  closed / (closed + open)
  - avg_resolution_time (display):  mean days from open to close
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from gitpulse_mcp.github.client import get_client

logger = logging.getLogger(__name__)

# We sample up to 200 issues for metric computation.
# Fetching all issues for a repo with 10,000+ issues would be impractical.
_SAMPLE_MAX_PAGES = 2


def _is_issue(item: dict[str, Any]) -> bool:
    """Return True if the item is an issue (not a PR)."""
    return "pull_request" not in item


def _parse_dt(iso_string: str | None) -> datetime | None:
    """Parse a GitHub ISO timestamp into a UTC-aware datetime."""
    if not iso_string:
        return None
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


async def fetch_issue_metrics(owner: str, repo: str) -> dict[str, Any]:
    """
    Fetch and compute issue health metrics.

    Samples up to 200 most-recent issues (open + closed) to compute:
      - open_count
      - closed_count
      - issue_close_rate (0.0 – 1.0)
      - avg_resolution_time_days (for closed issues)
      - avg_response_time_days (time to first comment/label/close)

    Returns:
        {
            "open_count": int,
            "closed_count": int,
            "issue_close_rate": float,       # 0.0 – 1.0
            "avg_resolution_time_days": float,
            "avg_response_time_days": float,
        }
    """
    client = get_client()

    # Fetch a sample of recent issues (both states) to estimate the close rate
    # and resolution time without paging through thousands of issues.
    all_sample = await client.paginated_get(
        f"/repos/{owner}/{repo}/issues",
        params={"state": "all", "sort": "updated", "direction": "desc"},
        max_pages=_SAMPLE_MAX_PAGES,
        per_page=100,
    )
    issues_only = [item for item in all_sample if _is_issue(item)]

    open_issues = [i for i in issues_only if i["state"] == "open"]
    closed_issues = [i for i in issues_only if i["state"] == "closed"]

    total = len(open_issues) + len(closed_issues)
    close_rate = len(closed_issues) / total if total > 0 else 0.0

    # Compute average resolution time from closed issues in our sample
    resolution_times: list[float] = []
    for issue in closed_issues:
        created = _parse_dt(issue.get("created_at"))
        closed = _parse_dt(issue.get("closed_at"))
        if created and closed:
            delta_days = (closed - created).total_seconds() / 86400
            resolution_times.append(delta_days)

    avg_resolution = (
        sum(resolution_times) / len(resolution_times) if resolution_times else 0.0
    )

    # avg_response_time: approximate as avg time from creation to first update
    # (GitHub doesn't give first-comment time in the list endpoint;
    # we use updated_at - created_at as a proxy for closed issues)
    response_times: list[float] = []
    for issue in closed_issues[:50]:  # limit computation to most-recent 50
        created = _parse_dt(issue.get("created_at"))
        updated = _parse_dt(issue.get("updated_at"))
        if created and updated:
            delta = (updated - created).total_seconds() / 86400
            response_times.append(min(delta, 30.0))  # cap at 30 days to avoid outliers

    avg_response = (
        sum(response_times) / len(response_times) if response_times else 0.0
    )

    return {
        "open_count": len(open_issues),
        "closed_count": len(closed_issues),
        "issue_close_rate": round(close_rate, 3),
        "avg_resolution_time_days": round(avg_resolution, 1),
        "avg_response_time_days": round(avg_response, 1),
    }


async def fetch_open_issues(
    owner: str,
    repo: str,
    max_issues: int = 50,
) -> list[dict[str, Any]]:
    """
    Fetch open issues (excluding PRs) for triage analysis.

    Each item includes: number, title, body, labels, created_at,
    updated_at, comments, user.login.

    Args:
        max_issues: Maximum issues to fetch (capped to avoid huge costs).
    """
    client = get_client()
    max_pages = max(1, max_issues // 100)
    per_page = min(max_issues, 100)

    all_open = await client.paginated_get(
        f"/repos/{owner}/{repo}/issues",
        params={"state": "open", "sort": "created", "direction": "desc"},
        max_pages=max_pages,
        per_page=per_page,
    )
    issues_only = [item for item in all_open if _is_issue(item)]
    return issues_only[:max_issues]


async def fetch_recent_issue_events(
    owner: str,
    repo: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Fetch recently opened/closed issues for the activity timeline.
    Returns up to `limit` issues sorted by most recently updated.
    """
    client = get_client()
    items = await client.paginated_get(
        f"/repos/{owner}/{repo}/issues",
        params={"state": "all", "sort": "updated", "direction": "desc"},
        max_pages=1,
        per_page=limit * 2,  # fetch extras since PRs will be filtered out
    )
    return [item for item in items if _is_issue(item)][:limit]


def classify_issue_age(created_at: str | None) -> str:
    """
    Return a human-readable age label for an issue.

    Used in triage reporting to quickly surface stale issues.
    """
    if not created_at:
        return "unknown"
    created = _parse_dt(created_at)
    if not created:
        return "unknown"
    age_days = (datetime.now(tz=timezone.utc) - created).days
    if age_days < 7:
        return "this week"
    if age_days < 30:
        return f"{age_days} days ago"
    if age_days < 90:
        return f"{age_days // 30} months ago"
    return f"over {age_days // 30} months ago"
