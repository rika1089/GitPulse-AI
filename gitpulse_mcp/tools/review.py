"""
tools/review.py
---------------
Input validation and dispatch for review_file and review_pull_request MCP tools.
"""
from __future__ import annotations
import re
from typing import Any

from gitpulse_mcp.services.review_service import ReviewService

_SLUG_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
_REF_RE  = re.compile(r"^[A-Za-z0-9._/\-]{1,200}$")


def _validate_slug(value: str, field: str) -> str:
    v = value.strip()
    if not v or not _SLUG_RE.match(v):
        raise ValueError(f"Invalid GitHub {field}: '{v}'")
    return v


def _validate_file_path(path: str) -> str:
    p = path.strip().lstrip("/")
    if not p:
        raise ValueError("'path' cannot be empty.")
    if ".." in p:
        raise ValueError("'path' must not contain '..' (directory traversal not allowed).")
    return p


async def run_review_file(args: dict[str, Any]) -> dict[str, Any]:
    owner = _validate_slug(args.get("owner", ""), "owner")
    repo  = _validate_slug(args.get("repo", ""), "repo")
    path  = _validate_file_path(args.get("path", ""))
    ref   = args.get("ref", "HEAD").strip() or "HEAD"
    if not _REF_RE.match(ref):
        raise ValueError(f"Invalid ref: '{ref}'")
    svc = ReviewService()
    return await svc.review_file(owner, repo, path, ref)


async def run_review_pull_request(args: dict[str, Any]) -> dict[str, Any]:
    owner = _validate_slug(args.get("owner", ""), "owner")
    repo  = _validate_slug(args.get("repo", ""), "repo")
    try:
        pr_number = int(args.get("pr_number", 0))
    except (TypeError, ValueError):
        raise ValueError("'pr_number' must be a positive integer.")
    if pr_number < 1:
        raise ValueError("'pr_number' must be >= 1.")
    svc = ReviewService()
    return await svc.review_pull_request(owner, repo, pr_number)
