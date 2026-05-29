"""
tools/triage.py
---------------
Input validation and dispatch for the triage_issues MCP tool.
"""
from __future__ import annotations
import re
from typing import Any

from gitpulse_mcp.services.triage_service import TriageService

_SLUG_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
_MAX_ISSUES_LIMIT = 100


async def run_triage_issues(args: dict[str, Any]) -> dict[str, Any]:
    owner = args.get("owner", "").strip()
    repo  = args.get("repo", "").strip()
    if not owner or not _SLUG_RE.match(owner):
        raise ValueError(f"Invalid GitHub owner: '{owner}'")
    if not repo or not _SLUG_RE.match(repo):
        raise ValueError(f"Invalid GitHub repo: '{repo}'")
    try:
        max_issues = int(args.get("max_issues", 50))
    except (TypeError, ValueError):
        raise ValueError("'max_issues' must be an integer.")
    if max_issues < 1:
        raise ValueError("'max_issues' must be at least 1.")
    max_issues = min(max_issues, _MAX_ISSUES_LIMIT)
    svc = TriageService()
    return await svc.triage(owner, repo, max_issues)
