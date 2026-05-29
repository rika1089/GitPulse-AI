"""
tests/test_tools.py
--------------------
Tests for the tools/ input validation layer.
Verifies invalid inputs are rejected before reaching the service layer,
and valid inputs dispatch correctly.
Services are fully mocked — no GitHub API or LLM calls.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gitpulse_mcp.models.repository import (
    ActivityStatus,
    HealthClassification,
    Repository,
    RepoInsights,
    ScoredSection,
    CheckItem,
    CheckStatus,
)


# ------------------------------------------------------------------
# Shared fixture helpers
# ------------------------------------------------------------------

def _mock_health_result():
    repo = Repository(
        id="a-b", name="b", owner="a", description="", stars=0, forks=0,
        watchers=0, license="MIT", open_issues_count=0, closed_issues_count=0,
        open_prs_count=0, merged_prs_count=0, avg_response_time_days=0.0,
        avg_close_time_days=0.0, last_push_date="today", health_score=80,
        classification=HealthClassification.HEALTHY,
        activity_status=ActivityStatus.HIGH,
        primary_language="Python", languages=[], topics=[],
    )
    insights = RepoInsights(summary="ok", strengths=[], risks=[], recommendations=[])
    result = MagicMock()
    result.model_dump = lambda by_alias=False: {
        "repository": repo.model_dump(by_alias=by_alias),
        "insights": insights.model_dump(),
    }
    return result


def _real_section(score: int = 80) -> ScoredSection:
    return ScoredSection(
        score=score,
        checks=[CheckItem(
            name="Test", description="desc",
            status=CheckStatus.PASSED, feedback="ok",
        )],
    )


def _mock_assessment_result():
    repo = Repository(
        id="a-b", name="b", owner="a", description="", stars=0, forks=0,
        watchers=0, license="MIT", open_issues_count=0, closed_issues_count=0,
        open_prs_count=0, merged_prs_count=0, avg_response_time_days=0.0,
        avg_close_time_days=0.0, last_push_date="today", health_score=80,
        classification=HealthClassification.HEALTHY,
        activity_status=ActivityStatus.HIGH,
        primary_language="Python", languages=[], topics=[],
    )
    insights = RepoInsights(summary="ok", strengths=[], risks=[], recommendations=[])
    from gitpulse_mcp.models.repository import RepoDetails
    return RepoDetails(
        repository=repo,
        readme_quality=_real_section(75),
        security=_real_section(60),
        ci_cd=_real_section(90),
        contribution_health=_real_section(70),
        contributors=[],
        timeline=[],
        insights=insights,
    )


# ------------------------------------------------------------------
# tools/health.py
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_tool_valid_input():
    with patch(
        "gitpulse_mcp.tools.health.HealthService"
    ) as MockSvc:
        MockSvc.return_value.analyse = AsyncMock(return_value=_mock_health_result())
        from gitpulse_mcp.tools.health import run_get_repo_health
        result = await run_get_repo_health({"owner": "facebook", "repo": "react"})
    assert "repository" in result


@pytest.mark.asyncio
@pytest.mark.parametrize("owner,repo", [
    ("", "react"),
    ("facebook", ""),
    ("bad owner!", "react"),
    ("facebook", "re/po"),
    ("../etc", "passwd"),
    ("a" * 101, "repo"),
])
async def test_health_tool_invalid_input(owner, repo):
    from gitpulse_mcp.tools.health import run_get_repo_health
    with pytest.raises(ValueError):
        await run_get_repo_health({"owner": owner, "repo": repo})


# ------------------------------------------------------------------
# tools/review.py — review_file
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_review_file_tool_valid_input():
    with patch(
        "gitpulse_mcp.tools.review.ReviewService"
    ) as MockSvc:
        MockSvc.return_value.review_file = AsyncMock(
            return_value={"file": "src/app.py", "review": {}}
        )
        from gitpulse_mcp.tools.review import run_review_file
        result = await run_review_file({
            "owner": "org", "repo": "proj", "path": "src/app.py"
        })
    assert result["file"] == "src/app.py"


@pytest.mark.asyncio
async def test_review_file_default_ref_is_head():
    """Omitting ref should default to HEAD without raising."""
    with patch(
        "gitpulse_mcp.tools.review.ReviewService"
    ) as MockSvc:
        MockSvc.return_value.review_file = AsyncMock(
            return_value={"file": "main.py", "review": {}}
        )
        from gitpulse_mcp.tools.review import run_review_file
        await run_review_file({"owner": "org", "repo": "proj", "path": "main.py"})

    call_kwargs = MockSvc.return_value.review_file.call_args
    # ref argument (4th positional or keyword) should be HEAD
    assert "HEAD" in call_kwargs[0] or call_kwargs[1].get("ref") == "HEAD"


@pytest.mark.asyncio
@pytest.mark.parametrize("args", [
    {"owner": "org", "repo": "proj", "path": ""},
    {"owner": "org", "repo": "proj", "path": "../../../etc/passwd"},
    {"owner": "org", "repo": "proj", "path": "../../secret"},
    {"owner": "", "repo": "proj", "path": "main.py"},
    {"owner": "org", "repo": "", "path": "main.py"},
])
async def test_review_file_tool_invalid_input(args):
    from gitpulse_mcp.tools.review import run_review_file
    with pytest.raises(ValueError):
        await run_review_file(args)


# ------------------------------------------------------------------
# tools/review.py — review_pull_request
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_review_pr_tool_valid_input():
    with patch(
        "gitpulse_mcp.tools.review.ReviewService"
    ) as MockSvc:
        MockSvc.return_value.review_pull_request = AsyncMock(
            return_value={"pr_number": 42, "verdict": "APPROVE"}
        )
        from gitpulse_mcp.tools.review import run_review_pull_request
        result = await run_review_pull_request({
            "owner": "org", "repo": "proj", "pr_number": 42
        })
    assert result["verdict"] == "APPROVE"


@pytest.mark.asyncio
@pytest.mark.parametrize("pr_number,exc_type", [
    (0,     ValueError),
    (-1,    ValueError),
    (-99,   ValueError),
    ("abc", ValueError),
    (None,  ValueError),
])
async def test_review_pr_tool_invalid_pr_number(pr_number, exc_type):
    from gitpulse_mcp.tools.review import run_review_pull_request
    with pytest.raises(exc_type):
        await run_review_pull_request({
            "owner": "org", "repo": "proj", "pr_number": pr_number
        })


@pytest.mark.asyncio
async def test_review_pr_tool_string_number_coerced():
    """String integers like '42' should be accepted and coerced."""
    with patch(
        "gitpulse_mcp.tools.review.ReviewService"
    ) as MockSvc:
        MockSvc.return_value.review_pull_request = AsyncMock(
            return_value={"pr_number": 42, "verdict": "COMMENT"}
        )
        from gitpulse_mcp.tools.review import run_review_pull_request
        result = await run_review_pull_request({
            "owner": "org", "repo": "proj", "pr_number": "42"
        })
    assert result["pr_number"] == 42


# ------------------------------------------------------------------
# tools/triage.py
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_triage_tool_valid_input():
    with patch(
        "gitpulse_mcp.tools.triage.TriageService"
    ) as MockSvc:
        MockSvc.return_value.triage = AsyncMock(
            return_value={"issue_count": 5, "summary": "ok"}
        )
        from gitpulse_mcp.tools.triage import run_triage_issues
        result = await run_triage_issues({"owner": "org", "repo": "proj"})
    assert result["issue_count"] == 5


@pytest.mark.asyncio
async def test_triage_tool_default_max_issues():
    """Omitting max_issues should default to 50."""
    with patch(
        "gitpulse_mcp.tools.triage.TriageService"
    ) as MockSvc:
        MockSvc.return_value.triage = AsyncMock(
            return_value={"issue_count": 0, "summary": "none"}
        )
        from gitpulse_mcp.tools.triage import run_triage_issues
        await run_triage_issues({"owner": "org", "repo": "proj"})

    call_args = MockSvc.return_value.triage.call_args[0]
    assert call_args[2] == 50  # third positional arg is max_issues


@pytest.mark.asyncio
async def test_triage_tool_caps_max_issues_at_100():
    """max_issues > 100 should be silently capped to 100."""
    with patch(
        "gitpulse_mcp.tools.triage.TriageService"
    ) as MockSvc:
        MockSvc.return_value.triage = AsyncMock(
            return_value={"issue_count": 0, "summary": "none"}
        )
        from gitpulse_mcp.tools.triage import run_triage_issues
        await run_triage_issues({"owner": "org", "repo": "proj", "max_issues": 999})

    call_args = MockSvc.return_value.triage.call_args[0]
    assert call_args[2] == 100


@pytest.mark.asyncio
@pytest.mark.parametrize("max_issues", [0, -1, -50])
async def test_triage_tool_invalid_max_issues(max_issues):
    from gitpulse_mcp.tools.triage import run_triage_issues
    with pytest.raises(ValueError):
        await run_triage_issues({
            "owner": "org", "repo": "proj", "max_issues": max_issues
        })


@pytest.mark.asyncio
@pytest.mark.parametrize("owner,repo", [
    ("", "proj"), ("org", ""), ("bad name!", "proj"), ("org", "bad/repo"),
])
async def test_triage_tool_invalid_slugs(owner, repo):
    from gitpulse_mcp.tools.triage import run_triage_issues
    with pytest.raises(ValueError):
        await run_triage_issues({"owner": owner, "repo": repo})


# ------------------------------------------------------------------
# tools/assessment.py
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_assessment_tool_valid_input():
    with patch(
        "gitpulse_mcp.tools.assessment.AssessmentService"
    ) as MockSvc:
        MockSvc.return_value.assess = AsyncMock(
            return_value=_mock_assessment_result()
        )
        from gitpulse_mcp.tools.assessment import run_full_repo_assessment
        result = await run_full_repo_assessment({"owner": "org", "repo": "proj"})
    assert "repository" in result


@pytest.mark.asyncio
@pytest.mark.parametrize("owner,repo", [
    ("", "repo"),
    ("owner", ""),
    ("owner with spaces", "repo"),
    ("owner", "repo/sub"),
    ("../evil", "repo"),
    ("owner", "../evil"),
    ("a" * 101, "repo"),
])
async def test_assessment_tool_invalid_input(owner, repo):
    from gitpulse_mcp.tools.assessment import run_full_repo_assessment
    with pytest.raises(ValueError):
        await run_full_repo_assessment({"owner": owner, "repo": repo})


@pytest.mark.asyncio
async def test_assessment_tool_result_has_all_sections():
    """Serialised result must include all 4 quality sections with camelCase keys."""
    with patch(
        "gitpulse_mcp.tools.assessment.AssessmentService"
    ) as MockSvc:
        MockSvc.return_value.assess = AsyncMock(
            return_value=_mock_assessment_result()
        )
        from gitpulse_mcp.tools.assessment import run_full_repo_assessment
        result = await run_full_repo_assessment({"owner": "org", "repo": "proj"})

    assert "readmeQuality" in result
    assert "security" in result
    assert "ciCd" in result
    assert "contributionHealth" in result
    assert "insights" in result
