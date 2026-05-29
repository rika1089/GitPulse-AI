"""
tests/test_health_service.py
-----------------------------
Tests for HealthService: scoring formula, classification, model assembly,
and LLM fallback behaviour.
All GitHub API calls and LLM calls are mocked — no network required.
"""

from __future__ import annotations

import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gitpulse_mcp.llm.schemas import HealthNarrativeResponse
from gitpulse_mcp.models.repository import HealthClassification
from gitpulse_mcp.services.health_service import HealthService


# ------------------------------------------------------------------
# Fixtures — fake GitHub data
# ------------------------------------------------------------------

FAKE_METADATA = {
    "name": "testrepo",
    "description": "A test repository",
    "stargazers_count": 1200,
    "forks_count": 340,
    "watchers_count": 80,
    "license": {"spdx_id": "MIT"},
    "pushed_at": "2026-05-20T10:00:00Z",
    "language": "Python",
    "topics": ["python", "testing"],
}

FAKE_COMMIT_METRICS = {
    "commits_last_30_days": 22,
    "commits_last_90_days": 68,
    "weekly_trend": [5, 6, 4, 7, 5, 8, 4, 6, 5, 7, 6, 5],
    "avg_commits_per_week": 5.2,
}

FAKE_ISSUE_METRICS = {
    "open_count": 18,
    "closed_count": 140,
    "issue_close_rate": 0.89,
    "avg_resolution_time_days": 4.2,
    "avg_response_time_days": 1.8,
}

FAKE_PR_METRICS = {
    "open_count": 6,
    "merged_count": 85,
    "closed_unmerged_count": 10,
    "pr_merge_ratio": 0.89,
    "avg_merge_time_days": 2.1,
}

FAKE_LANGUAGES = {"Python": 85000, "Shell": 10000, "Makefile": 5000}

FAKE_CONTRIBUTORS = [
    {"login": "alice", "avatar_url": "https://example.com/alice.png", "contributions": 320},
    {"login": "bob", "avatar_url": "https://example.com/bob.png", "contributions": 180},
    {"login": "carol", "avatar_url": "https://example.com/carol.png", "contributions": 95},
]

FAKE_NARRATIVE = HealthNarrativeResponse(
    classification="Healthy",
    summary="This repository is in excellent health with consistent commit activity.",
    strengths=["High PR merge ratio of 89%", "Strong issue resolution rate"],
    risks=["Dependency on top 3 contributors"],
    recommendations=[],
)


def _patch_github(test_fn):
    """Decorator that patches all GitHub API calls used by HealthService."""
    return (
        patch("gitpulse_mcp.services.health_service.fetch_repo_metadata", new_callable=AsyncMock, return_value=FAKE_METADATA)
    )(
        patch("gitpulse_mcp.services.health_service.get_commit_metrics", new_callable=AsyncMock, return_value=FAKE_COMMIT_METRICS)(
        patch("gitpulse_mcp.services.health_service.fetch_issue_metrics", new_callable=AsyncMock, return_value=FAKE_ISSUE_METRICS)(
        patch("gitpulse_mcp.services.health_service.fetch_pr_metrics", new_callable=AsyncMock, return_value=FAKE_PR_METRICS)(
        patch("gitpulse_mcp.services.health_service.fetch_languages", new_callable=AsyncMock, return_value=FAKE_LANGUAGES)(
        patch("gitpulse_mcp.services.health_service.fetch_contributors", new_callable=AsyncMock, return_value=FAKE_CONTRIBUTORS)(
        patch("gitpulse_mcp.services.health_service.get_llm_client")(
            test_fn
        )))))))


# ------------------------------------------------------------------
# Scoring unit tests (no IO at all)
# ------------------------------------------------------------------


def test_score_components_commit_normalisation():
    svc = HealthService()
    # 0 commits → 0.0
    components = svc._compute_score_components(
        {"commits_last_30_days": 0, "avg_commits_per_week": 0},
        {"issue_close_rate": 1.0},
        {"pr_merge_ratio": 1.0},
        [],
    )
    assert components["commit_frequency"] == 0.0

    # 30 commits → ~1.0
    components = svc._compute_score_components(
        {"commits_last_30_days": 30, "avg_commits_per_week": 1},
        {"issue_close_rate": 1.0},
        {"pr_merge_ratio": 1.0},
        [1, 2, 3],
    )
    assert components["commit_frequency"] >= 0.95


def test_score_components_contributor_normalisation():
    svc = HealthService()
    # 0 contributors → 0.0
    c0 = svc._compute_score_components(
        {"commits_last_30_days": 10}, {"issue_close_rate": 0.5}, {"pr_merge_ratio": 0.5}, []
    )
    assert c0["contributor_activity"] == 0.0

    # 5 contributors → tanh(1) ≈ 0.76
    c5 = svc._compute_score_components(
        {"commits_last_30_days": 10}, {"issue_close_rate": 0.5}, {"pr_merge_ratio": 0.5}, [1] * 5
    )
    assert 0.7 < c5["contributor_activity"] < 1.0


def test_weighted_score_perfect():
    """All components at 1.0 should give score of 100."""
    svc = HealthService()
    perfect = {"commit_frequency": 1.0, "pr_merge_ratio": 1.0, "issue_close_rate": 1.0, "contributor_activity": 1.0}
    assert svc._weighted_score(perfect) == 100


def test_weighted_score_zero():
    svc = HealthService()
    zeroes = {"commit_frequency": 0.0, "pr_merge_ratio": 0.0, "issue_close_rate": 0.0, "contributor_activity": 0.0}
    assert svc._weighted_score(zeroes) == 0


def test_weighted_score_clamped():
    """Score must never exceed 100 or go below 0."""
    svc = HealthService()
    over = {"commit_frequency": 2.0, "pr_merge_ratio": 2.0, "issue_close_rate": 2.0, "contributor_activity": 2.0}
    assert svc._weighted_score(over) == 100


# ------------------------------------------------------------------
# Classification helpers
# ------------------------------------------------------------------


def test_classify_activity():
    svc = HealthService()
    from gitpulse_mcp.models.repository import ActivityStatus
    assert svc._classify_activity(80) == ActivityStatus.HIGH
    assert svc._classify_activity(55) == ActivityStatus.MODERATE
    assert svc._classify_activity(30) == ActivityStatus.LOW
    assert svc._classify_activity(10) == ActivityStatus.INACTIVE


def test_human_readable_date_today():
    from datetime import datetime, timezone
    now_iso = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert HealthService._human_readable_date(now_iso) == "today"


def test_human_readable_date_unknown():
    assert HealthService._human_readable_date(None) == "Unknown"


# ------------------------------------------------------------------
# Rule-based narrative fallback
# ------------------------------------------------------------------


def test_rule_based_narrative_healthy():
    svc = HealthService()
    metrics = {
        "health_score": 80,
        "commits_last_30_days": 20,
        "pr_merge_ratio": 0.85,
        "issue_close_rate": 0.90,
        "contributor_count": 5,
        "last_push_days_ago": 3,
    }
    result = svc._rule_based_narrative(metrics)
    assert result.classification == "Healthy"


def test_rule_based_narrative_archived():
    svc = HealthService()
    metrics = {
        "health_score": 10,
        "commits_last_30_days": 0,
        "pr_merge_ratio": 0.0,
        "issue_close_rate": 0.0,
        "contributor_count": 0,
        "last_push_days_ago": 400,
    }
    result = svc._rule_based_narrative(metrics)
    assert result.classification == "Archived"


def test_rule_based_narrative_at_risk():
    svc = HealthService()
    metrics = {
        "health_score": 25,
        "commits_last_30_days": 2,
        "pr_merge_ratio": 0.3,
        "issue_close_rate": 0.2,
        "contributor_count": 1,
        "last_push_days_ago": 30,
    }
    result = svc._rule_based_narrative(metrics)
    assert result.classification == "At Risk"


# ------------------------------------------------------------------
# Full integration test (all IO mocked)
# ------------------------------------------------------------------


@pytest.mark.asyncio
@_patch_github
async def test_analyse_returns_healthy_result(mock_llm, *_):
    """analyse() should return a RepoHealthResult with correct model shape."""
    mock_llm_instance = MagicMock()
    mock_llm_instance.generate = AsyncMock(return_value=FAKE_NARRATIVE)
    mock_llm.return_value = mock_llm_instance

    svc = HealthService()
    result = await svc.analyse("testowner", "testrepo")

    assert result.repository.name == "testrepo"
    assert result.repository.health_score >= 0
    assert result.repository.health_score <= 100
    assert result.repository.classification == HealthClassification.HEALTHY
    assert result.insights.summary != ""
    assert len(result.insights.strengths) > 0


@pytest.mark.asyncio
@_patch_github
async def test_analyse_uses_fallback_when_llm_fails(mock_llm, *_):
    """analyse() should not raise when LLM throws — uses rule-based fallback."""
    mock_llm_instance = MagicMock()
    mock_llm_instance.generate = AsyncMock(side_effect=Exception("LLM timeout"))
    mock_llm.return_value = mock_llm_instance

    svc = HealthService()
    result = await svc.analyse("testowner", "testrepo")

    # Should still complete successfully with fallback narrative
    assert result.repository.health_score >= 0
    assert result.insights.summary != ""


@pytest.mark.asyncio
@_patch_github
async def test_analyse_serialises_to_camel_case(mock_llm, *_):
    """model_dump(by_alias=True) should produce camelCase keys for frontend."""
    mock_llm_instance = MagicMock()
    mock_llm_instance.generate = AsyncMock(return_value=FAKE_NARRATIVE)
    mock_llm.return_value = mock_llm_instance

    svc = HealthService()
    result = await svc.analyse("testowner", "testrepo")
    data = result.model_dump(by_alias=True)

    repo = data["repository"]
    assert "healthScore" in repo
    assert "openIssuesCount" in repo
    assert "mergedPRsCount" in repo
    assert "activityStatus" in repo
    assert "primaryLanguage" in repo
