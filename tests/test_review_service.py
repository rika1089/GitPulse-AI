"""
tests/test_review_service.py
-----------------------------
Tests for ReviewService: file review, language detection, diff chunking,
and PR synthesis. All IO mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gitpulse_mcp.llm.schemas import FileReviewResponse, PRReviewResponse, PRBlocker
from gitpulse_mcp.services.review_service import ReviewService, _detect_language


# ------------------------------------------------------------------
# Language detection
# ------------------------------------------------------------------

@pytest.mark.parametrize("path,expected", [
    ("src/app.py", "Python"),
    ("index.ts", "TypeScript"),
    ("app.tsx", "TypeScript"),
    ("main.go", "Go"),
    ("lib.rs", "Rust"),
    ("build.sh", "Shell"),
    ("README.md", "Markdown"),
    ("config.yml", "YAML"),
    ("data.json", "JSON"),
    ("something.unknown", "Unknown"),
])
def test_detect_language(path, expected):
    assert _detect_language(path) == expected


# ------------------------------------------------------------------
# File review
# ------------------------------------------------------------------

FAKE_FILE_DATA = {
    "path": "src/auth.py",
    "content": "def login(user, password):\n    return user == 'admin'",
    "size_bytes": 56,
    "sha": "abc123",
    "encoding": "base64",
    "truncated": False,
}

FAKE_FILE_REVIEW = FileReviewResponse(
    summary="The file has a critical security issue.",
    strengths=["Simple function structure"],
    issues=[{
        "severity": "HIGH",
        "title": "Hardcoded credentials",
        "description": "Admin credentials are hardcoded in the login function.",
        "suggestion": "Use proper authentication with hashed passwords.",
    }],
    suggestions=["Add type annotations"],
    overall_quality_score=30,
)


@pytest.mark.asyncio
async def test_review_file_success():
    with (
        patch("gitpulse_mcp.services.review_service.fetch_file_content", new_callable=AsyncMock, return_value=FAKE_FILE_DATA),
        patch("gitpulse_mcp.services.review_service.get_llm_client") as mock_llm,
    ):
        mock_llm.return_value.generate = AsyncMock(return_value=FAKE_FILE_REVIEW)
        svc = ReviewService()
        result = await svc.review_file("owner", "repo", "src/auth.py")

    assert result["file"] == "src/auth.py"
    assert result["language"] == "Python"
    assert result["review"]["summary"] != ""
    assert result["review"]["overall_quality_score"] == 30
    assert len(result["review"]["issues"]) == 1
    assert result["review"]["issues"][0]["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_review_file_llm_failure_returns_graceful_result():
    """Should not raise when LLM fails — returns a graceful error result."""
    with (
        patch("gitpulse_mcp.services.review_service.fetch_file_content", new_callable=AsyncMock, return_value=FAKE_FILE_DATA),
        patch("gitpulse_mcp.services.review_service.get_llm_client") as mock_llm,
    ):
        mock_llm.return_value.generate = AsyncMock(side_effect=Exception("LLM unavailable"))
        svc = ReviewService()
        result = await svc.review_file("owner", "repo", "src/auth.py")

    assert result["file"] == "src/auth.py"
    assert "could not be completed" in result["review"]["summary"]


# ------------------------------------------------------------------
# PR review
# ------------------------------------------------------------------

FAKE_PR_DETAIL = {
    "number": 42,
    "title": "Add user authentication",
    "body": "Implements login/logout flow",
    "user": {"login": "alice", "avatar_url": ""},
    "base": {"ref": "main"},
    "merged_at": None,
}

FAKE_PR_FILES = [
    {
        "filename": "src/auth.py",
        "status": "modified",
        "additions": 25,
        "deletions": 5,
        "changes": 30,
        "patch": "+def login(user, password):\n+    return check_password(user, password)",
    },
    {
        "filename": "tests/test_auth.py",
        "status": "added",
        "additions": 40,
        "deletions": 0,
        "changes": 40,
        "patch": "+def test_login():\n+    assert login('alice', 'pw') == True",
    },
]

FAKE_PR_REVIEW = PRReviewResponse(
    verdict="APPROVE",
    summary="Clean PR implementing authentication correctly.",
    highlights=["Tests included", "Well-scoped change"],
    blockers=[],
    suggestions=[],
    test_coverage_comment="Tests cover the new login function.",
    documentation_comment="No docs needed for internal utility.",
)


@pytest.mark.asyncio
async def test_review_pull_request_success():
    with (
        patch("gitpulse_mcp.services.review_service.fetch_pr_detail", new_callable=AsyncMock, return_value=FAKE_PR_DETAIL),
        patch("gitpulse_mcp.services.review_service.fetch_pr_files", new_callable=AsyncMock, return_value=FAKE_PR_FILES),
        patch("gitpulse_mcp.services.review_service.get_llm_client") as mock_llm,
    ):
        mock_llm.return_value.generate = AsyncMock(return_value=FAKE_FILE_REVIEW)
        mock_llm.return_value.generate.side_effect = [
            FAKE_FILE_REVIEW,  # file 1
            FAKE_FILE_REVIEW,  # file 2
            FAKE_PR_REVIEW,    # synthesis
        ]
        svc = ReviewService()
        result = await svc.review_pull_request("owner", "repo", 42)

    assert result["pr_number"] == 42
    assert result["verdict"] == "APPROVE"
    assert result["stats"]["files"] == 2
    assert len(result["file_reviews"]) == 2


@pytest.mark.asyncio
async def test_review_pr_no_reviewable_files():
    """PR with only deleted files should return graceful COMMENT verdict."""
    deleted_files = [{"filename": "old.py", "status": "removed", "patch": None}]
    with (
        patch("gitpulse_mcp.services.review_service.fetch_pr_detail", new_callable=AsyncMock, return_value=FAKE_PR_DETAIL),
        patch("gitpulse_mcp.services.review_service.fetch_pr_files", new_callable=AsyncMock, return_value=deleted_files),
    ):
        svc = ReviewService()
        result = await svc.review_pull_request("owner", "repo", 42)

    assert result["verdict"] == "COMMENT"
    assert result["file_reviews"] == []
