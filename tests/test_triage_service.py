"""
tests/test_triage_service.py
-----------------------------
Tests for TriageService: rule-based pre-classification and LLM fallback.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gitpulse_mcp.services.triage_service import TriageService


def _make_issue(number: int, title: str, labels: list[str] = None, days_old: int = 10, body: str = "") -> dict:
    created = (datetime.now(tz=timezone.utc) - timedelta(days=days_old)).isoformat()
    return {
        "number": number,
        "title": title,
        "body": body,
        "labels": [{"name": l} for l in (labels or [])],
        "comments": 0,
        "state": "open",
        "created_at": created,
        "updated_at": created,
        "user": {"login": "user1"},
    }


# ------------------------------------------------------------------
# Pre-classification rules
# ------------------------------------------------------------------


def test_pre_classify_bug_by_keyword():
    svc = TriageService()
    issues = [_make_issue(1, "App crash on startup when user logs in")]
    result = svc._pre_classify(issues)
    assert result[1] == "high_priority_bug"


def test_pre_classify_bug_by_body_keyword():
    svc = TriageService()
    issues = [_make_issue(2, "Something weird", body="Getting a null pointer exception")]
    result = svc._pre_classify(issues)
    assert result[2] == "high_priority_bug"


def test_pre_classify_stale_by_age():
    svc = TriageService()
    old_issue = _make_issue(3, "Old feature request", days_old=120)
    result = svc._pre_classify([old_issue])
    assert result[3] == "stale"


def test_pre_classify_good_first_issue_by_label():
    svc = TriageService()
    issues = [_make_issue(4, "Add tooltip to button", labels=["good first issue"])]
    result = svc._pre_classify(issues)
    assert result[4] == "good_first_issue"


def test_pre_classify_documentation():
    svc = TriageService()
    issues = [_make_issue(5, "Update README for new API")]
    result = svc._pre_classify(issues)
    assert result[5] == "documentation_request"


def test_pre_classify_feature_request_default():
    svc = TriageService()
    issues = [_make_issue(6, "Add dark mode support")]
    result = svc._pre_classify(issues)
    assert result[6] == "feature_request"


def test_pre_classify_bug_takes_priority_over_stale():
    """A bug keyword should win over stale age."""
    svc = TriageService()
    issues = [_make_issue(7, "Critical crash in production", days_old=200)]
    result = svc._pre_classify(issues)
    assert result[7] == "high_priority_bug"


# ------------------------------------------------------------------
# Full triage (mocked IO)
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_triage_no_issues():
    with patch("gitpulse_mcp.services.triage_service.fetch_open_issues", new_callable=AsyncMock, return_value=[]):
        svc = TriageService()
        result = await svc.triage("owner", "repo")

    assert result["issue_count"] == 0
    assert "no open issues" in result["summary"].lower()


@pytest.mark.asyncio
async def test_triage_with_issues_uses_llm():
    from gitpulse_mcp.llm.schemas import TriageResponse, TriageCategories, HealthSignals
    fake_triage = TriageResponse(
        summary="3 issues found, 1 high priority.",
        categories=TriageCategories(),
        recommendations=["Close stale issues"],
        health_signals=HealthSignals(estimated_backlog_health="Fair"),
    )
    issues = [
        _make_issue(1, "App crash on login"),
        _make_issue(2, "Add dark mode", days_old=5),
        _make_issue(3, "Update docs", days_old=3),
    ]
    with (
        patch("gitpulse_mcp.services.triage_service.fetch_open_issues", new_callable=AsyncMock, return_value=issues),
        patch("gitpulse_mcp.services.triage_service.get_llm_client") as mock_llm,
    ):
        mock_llm.return_value.generate = AsyncMock(return_value=fake_triage)
        svc = TriageService()
        result = await svc.triage("owner", "repo", max_issues=10)

    assert result["issue_count"] == 3
    assert result["summary"] == "3 issues found, 1 high priority."


@pytest.mark.asyncio
async def test_triage_falls_back_when_llm_fails():
    issues = [_make_issue(1, "Critical null exception crash")]
    with (
        patch("gitpulse_mcp.services.triage_service.fetch_open_issues", new_callable=AsyncMock, return_value=issues),
        patch("gitpulse_mcp.services.triage_service.get_llm_client") as mock_llm,
    ):
        mock_llm.return_value.generate = AsyncMock(side_effect=Exception("LLM down"))
        svc = TriageService()
        result = await svc.triage("owner", "repo")

    assert result["issue_count"] == 1
    assert result["summary"] != ""
    # Rule-based fallback should classify the crash issue as a bug
    bugs = result["categories"].get("high_priority_bugs", [])
    assert len(bugs) == 1
