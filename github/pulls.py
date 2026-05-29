"""
github/pulls.py
---------------
Fetches pull request metrics, open PR list, and diffs for code review.

Endpoints used:
  GET /repos/{owner}/{repo}/pulls?state=all     — PR list for metrics
  GET /repos/{owner}/{repo}/pulls/{pr}/files    — changed files + diffs
  GET /repos/{owner}/{repo}/pulls/{pr}          — single PR detail

The PR merge ratio (merged / total PRs) is a 25%-weight component in the
health score formula. A high merge ratio indicates the project is actively
accepting contributions.
"""

from __future__ import annotations

import logging
from typing import Any

from gitpulse_mcp.github.client import get_client

logger = logging.getLogger(__name__)

_SAMPLE_MAX_PAGES = 2  # Sample up to 200 PRs for merge ratio calculation


async def fetch_pr_metrics(owner: str, repo: str) -> dict[str, Any]:
    """
    Fetch and compute pull request health metrics.

    Returns:
        {
            "open_count": int,
            "merged_count": int,        # from sampled closed PRs
            "closed_unmerged_count": int,
            "pr_merge_ratio": float,    # merged / (merged + closed_unmerged)
            "avg_merge_time_days": float,
        }
    """
    client = get_client()

    # Fetch a mix of open and recently-closed PRs for metric computation
    all_prs = await client.paginated_get(
        f"/repos/{owner}/{repo}/pulls",
        params={"state": "all", "sort": "updated", "direction": "desc"},
        max_pages=_SAMPLE_MAX_PAGES,
        per_page=100,
    )

    open_prs = [pr for pr in all_prs if pr["state"] == "open"]
    closed_prs = [pr for pr in all_prs if pr["state"] == "closed"]

    # GitHub PR list endpoint marks merged PRs via merged_at being non-null
    merged_prs = [pr for pr in closed_prs if pr.get("merged_at")]
    unmerged_prs = [pr for pr in closed_prs if not pr.get("merged_at")]

    total_resolved = len(merged_prs) + len(unmerged_prs)
    merge_ratio = len(merged_prs) / total_resolved if total_resolved > 0 else 0.0

    # Average time from open to merge for merged PRs
    merge_times: list[float] = []
    for pr in merged_prs[:50]:
        created = pr.get("created_at")
        merged = pr.get("merged_at")
        if created and merged:
            from datetime import datetime
            c = datetime.fromisoformat(created.replace("Z", "+00:00"))
            m = datetime.fromisoformat(merged.replace("Z", "+00:00"))
            merge_times.append((m - c).total_seconds() / 86400)

    avg_merge_days = (
        sum(merge_times) / len(merge_times) if merge_times else 0.0
    )

    return {
        "open_count": len(open_prs),
        "merged_count": len(merged_prs),
        "closed_unmerged_count": len(unmerged_prs),
        "pr_merge_ratio": round(merge_ratio, 3),
        "avg_merge_time_days": round(avg_merge_days, 1),
    }


async def fetch_pr_files(
    owner: str,
    repo: str,
    pr_number: int,
) -> list[dict[str, Any]]:
    """
    Fetch the list of changed files in a pull request, including their patches
    (unified diffs).

    Each item has:
      - filename
      - status: 'added' | 'modified' | 'removed' | 'renamed'
      - additions, deletions, changes
      - patch: unified diff string (may be absent for binary files or very large diffs)

    Returns:
        List of file change objects.
    """
    client = get_client()
    files = await client.paginated_get(
        f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
        max_pages=3,  # max 300 files per PR for review
        per_page=100,
    )
    return files


async def fetch_pr_detail(
    owner: str,
    repo: str,
    pr_number: int,
) -> dict[str, Any]:
    """
    Fetch full detail for a single pull request.

    Includes: title, body, user, head/base branch info, merge status,
    created_at, merged_at, labels, requested_reviewers.
    """
    client = get_client()
    pr: dict[str, Any] = await client.get(
        f"/repos/{owner}/{repo}/pulls/{pr_number}"
    )
    return pr


async def fetch_recent_pr_events(
    owner: str,
    repo: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Fetch recently updated PRs for the activity timeline.
    Returns `limit` most-recently-updated PRs (any state).
    """
    client = get_client()
    prs = await client.paginated_get(
        f"/repos/{owner}/{repo}/pulls",
        params={"state": "all", "sort": "updated", "direction": "desc"},
        max_pages=1,
        per_page=limit,
    )
    return prs[:limit]


def estimate_diff_tokens(files: list[dict[str, Any]]) -> int:
    """
    Rough estimate of token count for a PR diff.

    Used to decide whether to chunk before sending to the LLM.
    Rule of thumb: 1 token ≈ 4 characters in code patches.
    """
    total_chars = sum(len(f.get("patch", "")) for f in files)
    return total_chars // 4
