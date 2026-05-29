"""
tests/test_assessment_service.py
--------------------------------
Tests for AssessmentService: full repository assessment, quality checks,
timeline generation, and final synthesis.
All GitHub API calls and external services are mocked.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from gitpulse_mcp.llm.schemas import AssessmentInsightsResponse
from gitpulse_mcp.models.repository import (
    CheckStatus,
    HealthClassification,
    RecommendationCategory,
    RecommendationImpact,
    TimelineEventType,
)
from gitpulse_mcp.services.assessment_service import AssessmentService

# Fake dependencies
class MockHealthResult:
    def __init__(self):
        from gitpulse_mcp.models.repository import Repository
        self.repository = Repository(
            id="testrepo",
            name="testrepo",
            owner="testowner",
            description="",
            stars=10,
            forks=5,
            watchers=5,
            open_issues_count=10,
            closed_issues_count=0,
            open_prs_count=0,
            merged_prs_count=50,
            avg_response_time_days=0.0,
            avg_close_time_days=0.0,
            last_push_date="today",
            health_score=85,
            classification=HealthClassification.HEALTHY,
            activity_status="High",
            primary_language="Python"
        )
        self.raw_metrics = {"health_score": 85, "contributors": []}

    @property
    def insights(self):
        class _Insights:
            strengths = ["Strong"]
            risks = ["None"]
        return _Insights()

def _patch_github_and_services(test_fn):
    return patch("gitpulse_mcp.services.assessment_service.check_file_exists", new_callable=AsyncMock, return_value=True)(
    patch("gitpulse_mcp.services.assessment_service.list_workflows", new_callable=AsyncMock, return_value=[{"name": "CI build and test"}])(
    patch("gitpulse_mcp.services.assessment_service.fetch_recent_commits", new_callable=AsyncMock, return_value=[{"sha": "abcdef12", "commit": {"message": "Fix bug", "author": {"name": "Alice"}}, "author": {"login": "alice"}}])(
    patch("gitpulse_mcp.services.assessment_service.fetch_recent_pr_events", new_callable=AsyncMock, return_value=[{"number": 42, "title": "Update docs", "user": {"login": "bob"}}])(
    patch("gitpulse_mcp.services.assessment_service.fetch_recent_issue_events", new_callable=AsyncMock, return_value=[{"number": 13, "title": "Crash", "user": {"login": "carol"}, "state": "closed"}])(
    patch("gitpulse_mcp.services.assessment_service.fetch_latest_release", new_callable=AsyncMock, return_value={"id": 1, "tag_name": "v1.0.0", "name": "First Release", "author": {"login": "alice"}})(
    patch("gitpulse_mcp.services.health_service.HealthService.analyse", new_callable=AsyncMock, return_value=MockHealthResult())(
    patch("gitpulse_mcp.services.triage_service.TriageService.triage", new_callable=AsyncMock, return_value={"summary": "Triage ok"})(
    patch("gitpulse_mcp.services.review_service.ReviewService.review_file", new_callable=AsyncMock, return_value={"file": "main.py", "review": {"summary": "Looks good"}})(
    patch("gitpulse_mcp.services.assessment_service.get_llm_client")(
        test_fn
    ))))))))))

@pytest.mark.asyncio
@_patch_github_and_services
async def test_assess_full_flow(
    mock_llm,
    mock_review_file,
    mock_triage,
    mock_health,
    mock_fetch_latest_release,
    mock_fetch_recent_issue_events,
    mock_fetch_recent_pr_events,
    mock_fetch_recent_commits,
    mock_list_workflows,
    mock_check_file_exists,
):
    # Mock LLM synthesis
    class MockLLMClient:
        async def generate(self, *args, **kwargs):
            from gitpulse_mcp.llm.schemas import LLMRecommendation
            return AssessmentInsightsResponse(
                summary="Overall great repo.",
                strengths=["Good docs"],
                risks=[],
                recommendations=[
                    LLMRecommendation(
                        title="Add tests",
                        description="More tests needed",
                        impact="High",
                        category="Code Quality"
                    )
                ]
            )
    mock_llm.return_value = MockLLMClient()

    svc = AssessmentService()
    result = await svc.assess("testowner", "testrepo")

    assert result.repository.name == "testrepo"
    
    # Quality sections
    assert result.readme_quality.score == 100
    assert result.security.score == 100
    assert result.ci_cd.score == 80  # 50 for present, 30 for 'test' in 'CI build and test'
    assert result.contribution_health.score == 100

    # Timeline
    assert len(result.timeline) == 4
    types = [t.type for t in result.timeline]
    assert TimelineEventType.COMMIT in types
    assert TimelineEventType.PR_OPEN in types
    assert TimelineEventType.ISSUE_CLOSE in types
    assert TimelineEventType.RELEASE in types

    # Insights
    assert result.insights.summary == "Overall great repo."
    assert len(result.insights.recommendations) == 1
    assert result.insights.recommendations[0].impact == RecommendationImpact.HIGH
    assert result.insights.recommendations[0].category == RecommendationCategory.CODE_QUALITY

@pytest.mark.asyncio
async def test_human_ts():
    svc = AssessmentService()
    assert svc._human_ts(None) == "recently"
    assert svc._human_ts("invalid date") == "recently"

@pytest.mark.asyncio
@patch("gitpulse_mcp.services.assessment_service.check_file_exists", new_callable=AsyncMock, return_value=False)
async def test_check_readme_missing(mock_check_file_exists):
    svc = AssessmentService()
    section = await svc._check_readme("owner", "repo")
    assert section.score == 0
    assert all(c.status in (CheckStatus.FAILED, CheckStatus.WARNING) for c in section.checks)

@pytest.mark.asyncio
@patch("gitpulse_mcp.services.assessment_service.check_file_exists", new_callable=AsyncMock, return_value=False)
async def test_check_security_missing(mock_check_file_exists):
    svc = AssessmentService()
    section = await svc._check_security("owner", "repo")
    assert section.score == 0
    assert all(c.status == CheckStatus.WARNING for c in section.checks)
