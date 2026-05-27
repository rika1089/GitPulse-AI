"""
github/repo.py
--------------
Fetches repository-level metadata from GitHub REST API.

Endpoints used:
  GET /repos/{owner}/{repo}               — core metadata
  GET /repos/{owner}/{repo}/languages     — language breakdown
  GET /repos/{owner}/{repo}/contributors  — contributor list (paginated)
  GET /repos/{owner}/{repo}/releases      — latest release info
"""

from __future__ import annotations

import logging
from typing import Any

from gitpulse_mcp.github.client import get_client

logger = logging.getLogger(__name__)


async def fetch_repo_metadata(owner: str, repo: str) -> dict[str, Any]:
    """
    Fetch core repository metadata.

    Returns the raw GitHub API response dict. Key fields used downstream:
      - name, description, stargazers_count, forks_count, watchers_count
      - open_issues_count, license.spdx_id
      - pushed_at (ISO timestamp of last push)
      - topics (from Accept header: application/vnd.github.mercy-preview+json)

    Raises:
        NotFoundError: if the repository does not exist or is private.
    """
    client = get_client()
    data: dict[str, Any] = await client.get(f"/repos/{owner}/{repo}")
    logger.debug("Fetched metadata for %s/%s", owner, repo)
    return data


async def fetch_languages(owner: str, repo: str) -> dict[str, int]:
    """
    Fetch language byte counts for the repository.

    Returns a dict like: {"JavaScript": 1234567, "TypeScript": 890123, ...}
    We convert to percentages in the service layer.

    GitHub returns languages sorted by byte count descending.
    """
    client = get_client()
    data: dict[str, int] = await client.get(f"/repos/{owner}/{repo}/languages")
    return data


async def fetch_contributors(
    owner: str,
    repo: str,
    max_pages: int = 2,
) -> list[dict[str, Any]]:
    """
    Fetch top contributors for the repository.

    Fetches up to `max_pages * 100` contributors sorted by commit count.
    We cap at 2 pages (200 contributors) — more than enough for health scoring.

    Each item in the returned list has:
      - login, avatar_url, contributions (commit count from GitHub's metric)
    """
    client = get_client()
    contributors = await client.paginated_get(
        f"/repos/{owner}/{repo}/contributors",
        params={"anon": "false"},
        max_pages=max_pages,
        per_page=100,
    )
    return contributors


async def fetch_latest_release(owner: str, repo: str) -> dict[str, Any] | None:
    """
    Fetch the latest release. Returns None if the repo has no releases.

    Used to populate the 'release' event type in the activity timeline.
    """
    client = get_client()
    try:
        release: dict[str, Any] = await client.get(
            f"/repos/{owner}/{repo}/releases/latest"
        )
        return release
    except Exception:
        # Repos without releases raise 404 — treat as "no release"
        return None


def parse_license(raw_metadata: dict[str, Any]) -> str:
    """
    Extract a clean license name from raw GitHub metadata.

    GitHub nests license info under metadata['license']['spdx_id'].
    Falls back to 'Unknown' if absent.
    """
    lic = raw_metadata.get("license")
    if not lic:
        return "Unknown"
    return lic.get("spdx_id") or lic.get("name") or "Unknown"


def compute_language_percentages(
    language_bytes: dict[str, int],
) -> list[dict[str, Any]]:
    """
    Convert raw byte counts to percentage breakdown with hex color codes.

    GitHub doesn't return colors via the languages API — we maintain a
    curated map of the top 20 languages. Unknown languages default to
    the neutral gray color.

    Returns a list sorted by percentage descending, matching the frontend's
    LanguageBreakdown type: { name, percentage, color }
    """
    LANGUAGE_COLORS: dict[str, str] = {
        "Python": "#3572A5",
        "JavaScript": "#f1e05a",
        "TypeScript": "#3178c6",
        "Java": "#b07219",
        "Go": "#00ADD8",
        "Rust": "#dea584",
        "C": "#555555",
        "C++": "#f34b7d",
        "C#": "#178600",
        "Ruby": "#701516",
        "PHP": "#4F5D95",
        "Swift": "#F05138",
        "Kotlin": "#A97BFF",
        "Dart": "#00B4AB",
        "Shell": "#89e051",
        "HTML": "#e34c26",
        "CSS": "#563d7c",
        "SCSS": "#c6538c",
        "Vue": "#41b883",
        "Markdown": "#083fa1",
    }
    DEFAULT_COLOR = "#8e8e8e"

    total_bytes = sum(language_bytes.values())
    if total_bytes == 0:
        return []

    result = [
        {
            "name": lang,
            "percentage": round((count / total_bytes) * 100, 1),
            "color": LANGUAGE_COLORS.get(lang, DEFAULT_COLOR),
        }
        for lang, count in language_bytes.items()
    ]
    return sorted(result, key=lambda x: x["percentage"], reverse=True)
