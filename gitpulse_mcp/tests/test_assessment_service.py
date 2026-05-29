"""
tests/test_assessment_service.py
---------------------------------
Tests for AssessmentService: quality checks, timeline builder,
full assess() orchestration, and RepoDetails model shape.
All IO mocked — no network required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gitpulse_mcp.llm.schemas import AssessmentInsightsResponse, LLMRecommendation
from gitpulse_mcp.models.repository import (
    CheckStatus,
    HealthClassification,
    ActivityStatus,
    Repository,
    RepoInsights,
    ScoredSection,
    CheckItem,
)
from gitpulse_mcp.services.assessment_service import AssessmentService


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _real_section(score: int = 75) -> ScoredSection:
    """Return a real ScoredSection instance (not a MagicMock)."""
    return ScoredSection(
        score=score,
        checks=[
            CheckItem(
                name="Test check",
                description="A test check item",
                status=CheckStatus.PASSED,
                feedback="Looks good.",
            )
        ],
    )


def _make_fake_health_result():
    repo = Repository(
        id="owner-repo", name="repo", owner="owner", description="desc",
        stars=100, forks=20, watchers=5, license="MIT",
        open_issues_count=10, closed_issues_count=80,
        open_prs_count=3, merged_prs_count=40,
        avg_response_time_days=1.2, avg_close_time_days=3.5,
        last_push_date="2 days ago", health_score=82,
        classification=HealthClassification.HEALTHY,
        activity_status=ActivityStatus.HIGH,
        primary_language="Python",
        languages=[], topics=[],
    )
    insights = RepoInsights(
        summary="Healthy repo.", strengths=["Active commits"], risks=[], recommendations=[]
    )
    result = MagicMock()
    result.repository = repo
    result.insights = insights
    result.raw_metrics = {
        "health_score": 82, "commits_last_30_days": 18, "pr_merge_ratio": 0.87,
        "issue_close_rate": 0.89, "contributor_count": 4, "contributors": [],
    }
    return result


FAKE_TRIAGE_RESULT = {
    "summary": "12 open issues, 2 high-priority bugs.",
    "categories": {
        "high_priority_bugs": [], "good_first_issues": [], "stale_issues": [],
        "documentation_requests": [], "feature_requests": [],
    },
    "recommendations": ["Close stale issues"],
    "health_signals": {"estimated_backlog_health": "Fair"},
}

FAKE_INSIGHTS = AssessmentInsightsResponse(
    summary="Comprehensive assessment: score 82/100.",
    strengths=["Active contributors", "CI/CD configured", "Good PR merge ratio"],
    risks=["No SECURITY.md found"],
    recommendations=[
        LLMRecommendation(
            title="Add security policy",
            description="Create SECURITY.md",
            impact="High",
            category="Security",
        )
    ],
)


# ------------------------------------------------------------------
# Quality check tests — rule-based, no LLM/GitHub calls
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_check_readme_all_present():
    with patch(
        "gitpulse_mcp.services.assessment_service.check_file_exists",
        new_callable=AsyncMock, return_value=True,
    ):
        svc = AssessmentService()
        section = await svc._check_readme("owner", "repo")

    assert section.score > 0
    assert all(c.status == CheckStatus.PASSED for c in section.checks)


@pytest.mark.asyncio
async def test_check_readme_nothing_present():
    with patch(
        "gitpulse_mcp.services.assessment_service.check_file_exists",
        new_callable=AsyncMock, return_value=False,
    ):
        svc = AssessmentService()
        section = await svc._check_readme("owner", "repo")

    assert section.score == 0
    statuses = {c.status for c in section.checks}
    assert CheckStatus.PASSED not in statuses


@pytest.mark.asyncio
async def test_check_security_all_present():
    with patch(
        "gitpulse_mcp.services.assessment_service.check_file_exists",
        new_callable=AsyncMock, return_value=True,
    ):
        svc = AssessmentService()
        section = await svc._check_security("owner", "repo")

    assert section.score == 100
    assert len(section.checks) == 3
    assert all(c.status == CheckStatus.PASSED for c in section.checks)


@pytest.mark.asyncio
async def test_check_security_nothing_present():
    with patch(
        "gitpulse_mcp.services.assessment_service.check_file_exists",
        new_callable=AsyncMock, return_value=False,
    ):
        svc = AssessmentService()
        section = await svc._check_security("owner", "repo")

    assert section.score == 0


@pytest.mark.asyncio
async def test_check_cicd_with_workflows():
    fake_workflows = [
        {"name": "ci.yml"}, {"name": "test.yml"}, {"name": "deploy.yml"}
    ]
    with patch(
        "gitpulse_mcp.services.assessment_service.list_workflows",
        new_callable=AsyncMock, return_value=fake_workflows,
    ):
        svc = AssessmentService()
        section = await svc._check_cicd("owner", "repo")

    assert section.score > 0
    check_names = [c.name for c in section.checks]
    assert any("Actions" in n for n in check_names)


@pytest.mark.asyncio
async def test_check_cicd_no_workflows():
    with patch(
        "gitpulse_mcp.services.assessment_service.list_workflows",
        new_callable=AsyncMock, return_value=[],
    ):
        svc = AssessmentService()
        section = await svc._check_cicd("owner", "repo")

    assert section.score == 0
    failed = [c for c in section.checks if c.status == CheckStatus.FAILED]
    assert len(failed) >= 1


@pytest.mark.asyncio
async def test_check_contribution_health_all_present():
    with patch(
        "gitpulse_mcp.services.assessment_service.check_file_exists",
        new_callable=AsyncMock, return_value=True,
    ):
        svc = AssessmentService()
        section = await svc._check_contribution_health("owner", "repo")

    assert section.score == 100


@pytest.mark.asyncio
async def test_check_contribution_health_nothing_present():
    with patch(
        "gitpulse_mcp.services.assessment_service.check_file_exists",
        new_callable=AsyncMock, return_value=False,
    ):
        svc = AssessmentService()
        section = await svc._check_contribution_health("owner", "repo")

    assert section.score == 0


# ------------------------------------------------------------------
# Score bounds across all sections
# ------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("check_method", [
    "_check_readme",
    "_check_security",
    "_check_contribution_health",
])
async def test_section_score_always_in_bounds(check_method):
    with patch(
        "gitpulse_mcp.services.assessment_service.check_file_exists",
        new_callable=AsyncMock, return_value=True,
    ):
        svc = AssessmentService()
        section = await getattr(svc, check_method)("owner", "repo")

    assert 0 <= section.score <= 100


# ------------------------------------------------------------------
# Timeline builder
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_timeline_returns_commit_items():
    fake_commits = [{
        "sha": "abc123def",
        "commit": {
            "message": "fix: resolve null pointer",
            "author": {"name": "alice", "date": "2026-05-20T10:00:00Z"},
        },
        "author": {"avatar_url": "https://example.com/alice.png"},
    }]

    with (
        patch("gitpulse_mcp.services.assessment_service.fetch_recent_commits",
              new_callable=AsyncMock, return_value=fake_commits),
        patch("gitpulse_mcp.services.assessment_service.fetch_recent_pr_events",
              new_callable=AsyncMock, return_value=[]),
        patch("gitpulse_mcp.services.assessment_service.fetch_recent_issue_events",
              new_callable=AsyncMock, return_value=[]),
        patch("gitpulse_mcp.services.assessment_service.fetch_latest_release",
              new_callable=AsyncMock, return_value=None),
    ):
        svc = AssessmentService()
        timeline = await svc._build_timeline("owner", "repo")

    assert len(timeline) >= 1
    types = {item.type.value for item in timeline}
    assert "commit" in types


@pytest.mark.asyncio
async def test_build_timeline_includes_release():
    fake_release = {
        "id": 99, "tag_name": "v1.2.0", "name": "Version 1.2.0",
        "published_at": "2026-05-15T12:00:00Z",
        "author": {"login": "maintainer", "avatar_url": ""},
    }

    with (
        patch("gitpulse_mcp.services.assessment_service.fetch_recent_commits",
              new_callable=AsyncMock, return_value=[]),
        patch("gitpulse_mcp.services.assessment_service.fetch_recent_pr_events",
              new_callable=AsyncMock, return_value=[]),
        patch("gitpulse_mcp.services.assessment_service.fetch_recent_issue_events",
              new_callable=AsyncMock, return_value=[]),
        patch("gitpulse_mcp.services.assessment_service.fetch_latest_release",
              new_callable=AsyncMock, return_value=fake_release),
    ):
        svc = AssessmentService()
        timeline = await svc._build_timeline("owner", "repo")

    types = {item.type.value for item in timeline}
    assert "release" in types


@pytest.mark.asyncio
async def test_build_timeline_capped_at_ten():
    """Timeline should never return more than 10 items."""
    fake_commits = [
        {
            "sha": f"sha{i}",
            "commit": {"message": f"commit {i}", "author": {"name": "a", "date": "2026-05-01T00:00:00Z"}},
            "author": {"avatar_url": ""},
        }
        for i in range(5)
    ]
    fake_prs = [
        {
            "number": i, "title": f"PR {i}", "state": "open", "merged_at": None,
            "user": {"login": "bob", "avatar_url": ""}, "updated_at": "2026-05-01T00:00:00Z",
        }
        for i in range(5)
    ]

    with (
        patch("gitpulse_mcp.services.assessment_service.fetch_recent_commits",
              new_callable=AsyncMock, return_value=fake_commits),
        patch("gitpulse_mcp.services.assessment_service.fetch_recent_pr_events",
              new_callable=AsyncMock, return_value=fake_prs),
        patch("gitpulse_mcp.services.assessment_service.fetch_recent_issue_events",
              new_callable=AsyncMock, return_value=[]),
        patch("gitpulse_mcp.services.assessment_service.fetch_latest_release",
              new_callable=AsyncMock, return_value=None),
    ):
        svc = AssessmentService()
        timeline = await svc._build_timeline("owner", "repo")

    assert len(timeline) <= 10


# ------------------------------------------------------------------
# Full assess() orchestration — uses real ScoredSection instances
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assess_returns_repo_details_shape():
    """assess() should return a RepoDetails with all required sections."""
    fake_health = _make_fake_health_result()
    real_quality = {
        "readme": _real_section(75),
        "security": _real_section(60),
        "ci_cd": _real_section(90),
        "contribution": _real_section(70),
    }

    with (
        patch("gitpulse_mcp.services.assessment_service.HealthService") as MockHealth,
        patch("gitpulse_mcp.services.assessment_service.TriageService") as MockTriage,
        patch.object(AssessmentService, "_run_quality_checks",
                     new_callable=AsyncMock, return_value=real_quality),
        patch.object(AssessmentService, "_review_recent_files",
                     new_callable=AsyncMock, return_value="No highlights"),
        patch.object(AssessmentService, "_build_timeline",
                     new_callable=AsyncMock, return_value=[]),
        patch.object(AssessmentService, "_synthesise_insights",
                     new_callable=AsyncMock,
                     return_value=RepoInsights(
                         summary="Good.", strengths=["Active"],
                         risks=[], recommendations=[],
                     )),
    ):
        MockHealth.return_value.analyse = AsyncMock(return_value=fake_health)
        MockTriage.return_value.triage = AsyncMock(return_value=FAKE_TRIAGE_RESULT)

        svc = AssessmentService()
        result = await svc.assess("owner", "repo")

    assert result.repository.name == "repo"
    assert result.repository.health_score == 82
    assert result.readme_quality.score == 75
    assert result.security.score == 60
    assert result.ci_cd.score == 90
    assert result.contribution_health.score == 70
    assert result.insights.summary == "Good."


@pytest.mark.asyncio
async def test_assess_serialises_to_camel_case():
    """model_dump(by_alias=True) must produce frontend-expected camelCase keys."""
    fake_health = _make_fake_health_result()
    real_quality = {
        "readme": _real_section(80),
        "security": _real_section(80),
        "ci_cd": _real_section(80),
        "contribution": _real_section(80),
    }

    with (
        patch("gitpulse_mcp.services.assessment_service.HealthService") as MockHealth,
        patch("gitpulse_mcp.services.assessment_service.TriageService") as MockTriage,
        patch.object(AssessmentService, "_run_quality_checks",
                     new_callable=AsyncMock, return_value=real_quality),
        patch.object(AssessmentService, "_review_recent_files",
                     new_callable=AsyncMock, return_value=""),
        patch.object(AssessmentService, "_build_timeline",
                     new_callable=AsyncMock, return_value=[]),
        patch.object(AssessmentService, "_synthesise_insights",
                     new_callable=AsyncMock,
                     return_value=RepoInsights(
                         summary="OK.", strengths=[], risks=[], recommendations=[]
                     )),
    ):
        MockHealth.return_value.analyse = AsyncMock(return_value=fake_health)
        MockTriage.return_value.triage = AsyncMock(return_value=FAKE_TRIAGE_RESULT)

        svc = AssessmentService()
        result = await svc.assess("owner", "repo")

    data = result.model_dump(by_alias=True)
    assert "readmeQuality" in data
    assert "ciCd" in data
    assert "contributionHealth" in data
    assert "healthScore" in data["repository"]


@pytest.mark.asyncio
async def test_assess_quality_check_scores_in_output():
    """All four quality scores should appear correctly in the serialised output."""
    fake_health = _make_fake_health_result()
    real_quality = {
        "readme": _real_section(55),
        "security": _real_section(40),
        "ci_cd": _real_section(100),
        "contribution": _real_section(85),
    }

    with (
        patch("gitpulse_mcp.services.assessment_service.HealthService") as MockHealth,
        patch("gitpulse_mcp.services.assessment_service.TriageService") as MockTriage,
        patch.object(AssessmentService, "_run_quality_checks",
                     new_callable=AsyncMock, return_value=real_quality),
        patch.object(AssessmentService, "_review_recent_files",
                     new_callable=AsyncMock, return_value=""),
        patch.object(AssessmentService, "_build_timeline",
                     new_callable=AsyncMock, return_value=[]),
        patch.object(AssessmentService, "_synthesise_insights",
                     new_callable=AsyncMock,
                     return_value=RepoInsights(
                         summary="Mixed.", strengths=[], risks=[], recommendations=[]
                     )),
    ):
        MockHealth.return_value.analyse = AsyncMock(return_value=fake_health)
        MockTriage.return_value.triage = AsyncMock(return_value=FAKE_TRIAGE_RESULT)

        svc = AssessmentService()
        result = await svc.assess("owner", "repo")

    data = result.model_dump(by_alias=True)
    assert data["readmeQuality"]["score"] == 55
    assert data["security"]["score"] == 40
    assert data["ciCd"]["score"] == 100
    assert data["contributionHealth"]["score"] == 85
