"""
tools/assessment.py
-------------------
Input validation and dispatch for the full_repo_assessment MCP tool.
"""
from __future__ import annotations
import re
from typing import Any

from gitpulse_mcp.services.assessment_service import AssessmentService

_SLUG_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


async def run_full_repo_assessment(args: dict[str, Any]) -> dict[str, Any]:
    owner = args.get("owner", "").strip()
    repo  = args.get("repo", "").strip()
    if not owner or not _SLUG_RE.match(owner):
        raise ValueError(f"Invalid GitHub owner: '{owner}'")
    if not repo or not _SLUG_RE.match(repo):
        raise ValueError(f"Invalid GitHub repo: '{repo}'")
    svc = AssessmentService()
    result = await svc.assess(owner, repo)
    return result.model_dump(by_alias=True)
