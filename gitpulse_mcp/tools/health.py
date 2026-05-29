"""
tools/health.py
---------------
Input validation and dispatch for the get_repo_health MCP tool.
"""
from __future__ import annotations
import re
from typing import Any

from gitpulse_mcp.services.health_service import HealthService

_SLUG_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


def _validate_slug(value: str, field: str) -> str:
    v = value.strip()
    if not v:
        raise ValueError(f"'{field}' cannot be empty.")
    if not _SLUG_RE.match(v):
        raise ValueError(
            f"'{field}' contains invalid characters. "
            "GitHub names may only contain letters, digits, hyphens, underscores, and dots."
        )
    return v


async def run_get_repo_health(args: dict[str, Any]) -> dict[str, Any]:
    owner = _validate_slug(args.get("owner", ""), "owner")
    repo  = _validate_slug(args.get("repo", ""), "repo")
    svc = HealthService()
    result = await svc.analyse(owner, repo)
    return result.model_dump(by_alias=True)
