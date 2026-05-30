"""
api/main.py
-----------
FastAPI REST server that wraps the MCP services and exposes them as
HTTP endpoints the React frontend can call via fetch().

Run with:
    uvicorn gitpulse_mcp.api.main:app --reload --port 8000

Endpoints:
    GET  /api/repos                          List + health-score multiple repos
    GET  /api/health/{owner}/{repo}          Single repo health analysis
    GET  /api/assess/{owner}/{repo}          Full RepoDetails (all 4 sections + insights)
    POST /api/review/file                    File code review
    POST /api/review/pr                      PR review
    GET  /api/triage/{owner}/{repo}          Issue triage
    GET  /api/stats                          Aggregate DashboardStats across tracked repos
    GET  /health                             Server health check
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from gitpulse_mcp.github.client import GitHubError, NotFoundError, RateLimitError

logger = logging.getLogger(__name__)

app = FastAPI(
    title="GitPulse AI API",
    description="GitHub repository health analysis, code review, and issue triage powered by AI.",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the React dev server (Vite default: 5173)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # CRA dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class FileReviewRequest(BaseModel):
    owner: str
    repo: str
    path: str
    ref: str = "HEAD"


class PRReviewRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int


class RepoListRequest(BaseModel):
    repos: list[dict[str, str]]   # [{"owner": "facebook", "repo": "react"}, ...]


# ---------------------------------------------------------------------------
# Error handler helper
# ---------------------------------------------------------------------------

def _handle_github_error(exc: GitHubError) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(
            status_code=404,
            detail=f"Repository not found: {exc.url}. "
                   "Check the owner and repo name — only public repos are supported.",
        )
    if isinstance(exc, RateLimitError):
        import time
        wait = max(1, (exc.reset_at - int(time.time())) // 60)
        return HTTPException(
            status_code=429,
            detail=f"GitHub API rate limit reached. Resets in ~{wait} minute(s).",
        )
    return HTTPException(status_code=502, detail=f"GitHub API error: {exc}")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def server_health() -> dict[str, str]:
    """Health check — use this to verify the server is running."""
    return {"status": "ok", "service": "gitpulse-ai"}


@app.get("/api/health/{owner}/{repo}")
async def get_repo_health(owner: str, repo: str) -> dict[str, Any]:
    """
    Analyse the health of a single GitHub repository.

    Returns repository metadata, health score (0-100), classification,
    and AI-generated insights (summary, strengths, risks, recommendations).

    The React frontend uses this to populate:
    - RepoTable rows (healthScore, classification, activityStatus)
    - AIInsightsPanel (insights.summary, strengths, risks, recommendations)
    """
    try:
        from gitpulse_mcp.tools.health import run_get_repo_health
        return await run_get_repo_health({"owner": owner, "repo": repo})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except GitHubError as exc:
        raise _handle_github_error(exc)


@app.get("/api/assess/{owner}/{repo}")
async def get_full_assessment(owner: str, repo: str) -> dict[str, Any]:
    """
    Full repository assessment — the most complete view.

    Returns the complete RepoDetails shape the React frontend expects:
    - repository (all fields)
    - readmeQuality, security, ciCd, contributionHealth (scored check lists)
    - contributors[]
    - timeline[]
    - insights (summary, strengths, risks, recommendations)

    The React frontend uses this to populate:
    - RepoDetailsPage (all 4 check sections + timeline)
    - AIInsightsPanel (insights block + diagnostic scores)

    Note: This is the most expensive endpoint (~10-15s for large repos).
    Consider caching the result in the frontend for the session.
    """
    try:
        from gitpulse_mcp.tools.assessment import run_full_repo_assessment
        return await run_full_repo_assessment({"owner": owner, "repo": repo})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except GitHubError as exc:
        raise _handle_github_error(exc)


@app.post("/api/review/file")
async def review_file(request: FileReviewRequest) -> dict[str, Any]:
    """
    Review a single file for code quality, bugs, and style issues.

    Returns structured review with severity-ranked issues and suggestions.
    """
    try:
        from gitpulse_mcp.tools.review import run_review_file
        return await run_review_file({
            "owner": request.owner,
            "repo": request.repo,
            "path": request.path,
            "ref": request.ref,
        })
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except GitHubError as exc:
        raise _handle_github_error(exc)


@app.post("/api/review/pr")
async def review_pull_request(request: PRReviewRequest) -> dict[str, Any]:
    """
    Review all changed files in a pull request.

    Returns verdict (APPROVE/REQUEST_CHANGES/COMMENT), per-file reviews,
    blockers, and suggestions.
    """
    try:
        from gitpulse_mcp.tools.review import run_review_pull_request
        return await run_review_pull_request({
            "owner": request.owner,
            "repo": request.repo,
            "pr_number": request.pr_number,
        })
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except GitHubError as exc:
        raise _handle_github_error(exc)


@app.get("/api/triage/{owner}/{repo}")
async def triage_issues(
    owner: str,
    repo: str,
    max_issues: int = Query(default=50, ge=1, le=100),
) -> dict[str, Any]:
    """
    Triage and classify open issues.

    Returns categorised issues (bugs, good-first-issues, stale, docs, features)
    with maintainer recommendations.
    """
    try:
        from gitpulse_mcp.tools.triage import run_triage_issues
        return await run_triage_issues({
            "owner": owner,
            "repo": repo,
            "max_issues": max_issues,
        })
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except GitHubError as exc:
        raise _handle_github_error(exc)


@app.post("/api/repos")
async def get_multiple_repos(request: RepoListRequest) -> dict[str, Any]:
    """
    Fetch health data for multiple repositories in parallel.

    Used by the Dashboard page to populate the RepoTable and MetricCards.
    Pass a list of {owner, repo} objects — returns health data for all of them
    plus aggregated DashboardStats.

    Example request body:
        {
          "repos": [
            {"owner": "facebook", "repo": "react"},
            {"owner": "vercel", "repo": "next.js"}
          ]
        }
    """
    if not request.repos:
        raise HTTPException(status_code=422, detail="repos list cannot be empty.")
    if len(request.repos) > 20:
        raise HTTPException(
            status_code=422,
            detail="Maximum 20 repositories per request. Split into multiple calls.",
        )

    from gitpulse_mcp.tools.health import run_get_repo_health

    # Run all health analyses concurrently
    tasks = [
        run_get_repo_health({"owner": r["owner"], "repo": r["repo"]})
        for r in request.repos
        if r.get("owner") and r.get("repo")
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    repositories = []
    errors = []

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            repo_id = f"{request.repos[i].get('owner')}/{request.repos[i].get('repo')}"
            logger.warning("Failed to fetch %s: %s", repo_id, result)
            errors.append({"repo": repo_id, "error": str(result)})
        else:
            repositories.append(result.get("repository", {}))

    # Compute aggregate DashboardStats from successful results
    stats = _compute_dashboard_stats(repositories)

    return {
        "repositories": repositories,
        "stats": stats,
        "errors": errors,
    }


@app.get("/api/stats")
async def get_dashboard_stats(
    repos: str = Query(
        description="Comma-separated owner/repo pairs e.g. facebook/react,vercel/next.js"
    ),
) -> dict[str, Any]:
    """
    Convenience endpoint: fetch stats for repos specified as a query param.

    Usage: GET /api/stats?repos=facebook/react,vercel/next.js
    """
    if not repos:
        raise HTTPException(status_code=422, detail="repos query param is required.")

    repo_list = []
    for pair in repos.split(","):
        pair = pair.strip()
        if "/" not in pair:
            continue
        owner, repo = pair.split("/", 1)
        repo_list.append({"owner": owner.strip(), "repo": repo.strip()})

    if not repo_list:
        raise HTTPException(status_code=422, detail="No valid owner/repo pairs found.")

    return await get_multiple_repos(RepoListRequest(repos=repo_list))


# ---------------------------------------------------------------------------
# Stats helper
# ---------------------------------------------------------------------------

def _compute_dashboard_stats(repositories: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute aggregate DashboardStats from a list of repository dicts.
    Mirrors the DashboardStats TypeScript interface exactly.
    """
    if not repositories:
        return {
            "totalRepos": 0,
            "openIssues": 0,
            "openPRs": 0,
            "avgHealthScore": 0.0,
            "avgResponseTimeDays": 0.0,
            "totalContributors": 0,
        }

    total_repos = len(repositories)
    open_issues = sum(r.get("openIssuesCount", 0) for r in repositories)
    open_prs = sum(r.get("openPRsCount", 0) for r in repositories)
    scores = [r.get("healthScore", 0) for r in repositories]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    response_times = [r.get("avgResponseTimeDays", 0) for r in repositories]
    avg_response = round(sum(response_times) / len(response_times), 1) if response_times else 0.0

    # Contributor count isn't in the health endpoint — use a rough proxy
    # (full count requires the assess endpoint)
    total_contributors = total_repos * 5  # placeholder until assess is called

    return {
        "totalRepos": total_repos,
        "openIssues": open_issues,
        "openPRs": open_prs,
        "avgHealthScore": avg_score,
        "avgResponseTimeDays": avg_response,
        "totalContributors": total_contributors,
    }
