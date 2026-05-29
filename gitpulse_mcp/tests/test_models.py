"""
tests/test_models.py
---------------------
Validates that the Pydantic models accept valid data,
reject invalid data, and serialise to the camelCase field names
the frontend expects.
"""

import pytest
from pydantic import ValidationError

from gitpulse_mcp.models.repository import (
    ActivityStatus,
    CheckItem,
    CheckStatus,
    Contributor,
    ActivityLevel,
    HealthClassification,
    LanguageBreakdown,
    Recommendation,
    RecommendationCategory,
    RecommendationImpact,
    RepoDetails,
    RepoInsights,
    Repository,
    ScoredSection,
)


# ---------------------------------------------------------------------------
# Repository model
# ---------------------------------------------------------------------------


def _make_repo(**overrides) -> dict:
    base = {
        "id": "facebook-react",
        "name": "react",
        "owner": "facebook",
        "description": "The library for web and native user interfaces.",
        "stars": 220000,
        "forks": 44000,
        "watchers": 6800,
        "license": "MIT",
        "open_issues_count": 240,
        "closed_issues_count": 12400,
        "open_prs_count": 45,
        "merged_prs_count": 9800,
        "avg_response_time_days": 1.4,
        "avg_close_time_days": 3.2,
        "last_push_date": "2 hours ago",
        "health_score": 94,
        "classification": HealthClassification.HEALTHY,
        "activity_status": ActivityStatus.HIGH,
        "primary_language": "JavaScript",
        "languages": [{"name": "JavaScript", "percentage": 94.2, "color": "#f1e05a"}],
        "topics": ["react", "frontend"],
    }
    base.update(overrides)
    return base


def test_repository_valid():
    repo = Repository(**_make_repo())
    assert repo.name == "react"
    assert repo.health_score == 94
    assert repo.classification == HealthClassification.HEALTHY


def test_repository_serialises_camel_case():
    """Frontend expects camelCase field names — verify alias serialisation."""
    repo = Repository(**_make_repo())
    data = repo.model_dump(by_alias=True)

    assert "healthScore" in data
    assert "openIssuesCount" in data
    assert "mergedPRsCount" in data
    assert "activityStatus" in data
    assert "primaryLanguage" in data
    assert "lastPushDate" in data

    # Snake_case originals should NOT appear in alias serialisation
    assert "health_score" not in data
    assert "open_issues_count" not in data


def test_repository_health_score_bounds():
    with pytest.raises(ValidationError):
        Repository(**_make_repo(health_score=101))  # > 100

    with pytest.raises(ValidationError):
        Repository(**_make_repo(health_score=-1))   # < 0


def test_repository_language_percentage_bounds():
    with pytest.raises(ValidationError):
        LanguageBreakdown(name="Python", percentage=101.0, color="#3572A5")

    with pytest.raises(ValidationError):
        LanguageBreakdown(name="Python", percentage=-1.0, color="#3572A5")


# ---------------------------------------------------------------------------
# CheckItem model
# ---------------------------------------------------------------------------


def test_check_item_valid():
    item = CheckItem(
        name="License Present",
        description="MIT license is clearly listed.",
        status=CheckStatus.PASSED,
        feedback="Perfect placement in LICENSE.md.",
    )
    assert item.status == CheckStatus.PASSED


def test_check_item_invalid_status():
    with pytest.raises(ValidationError):
        CheckItem(
            name="X",
            description="Y",
            status="unknown_status",  # not in enum
            feedback="Z",
        )


# ---------------------------------------------------------------------------
# ScoredSection model
# ---------------------------------------------------------------------------


def test_scored_section_score_bounds():
    with pytest.raises(ValidationError):
        ScoredSection(score=150, checks=[])


# ---------------------------------------------------------------------------
# Recommendation model
# ---------------------------------------------------------------------------


def test_recommendation_valid():
    rec = Recommendation(
        title="Expand reviewer permissions",
        description="Promote active contributors to reviewers.",
        impact=RecommendationImpact.HIGH,
        category=RecommendationCategory.ACTIVITY,
    )
    assert rec.impact == RecommendationImpact.HIGH


# ---------------------------------------------------------------------------
# RepoDetails model (full shape)
# ---------------------------------------------------------------------------


def test_repo_details_full_shape():
    repo = Repository(**_make_repo())
    section = ScoredSection(
        score=95,
        checks=[
            CheckItem(
                name="License",
                description="MIT present",
                status=CheckStatus.PASSED,
                feedback="Good",
            )
        ],
    )
    insights = RepoInsights(
        summary="Healthy repo.",
        strengths=["Fast PR review"],
        risks=["Too few maintainers"],
        recommendations=[
            Recommendation(
                title="Expand reviewers",
                description="Promote contributors",
                impact=RecommendationImpact.HIGH,
                category=RecommendationCategory.ACTIVITY,
            )
        ],
    )
    details = RepoDetails(
        repository=repo,
        readme_quality=section,
        security=section,
        ci_cd=section,
        contribution_health=section,
        contributors=[],
        timeline=[],
        insights=insights,
    )

    # Verify alias serialisation for frontend consumption
    data = details.model_dump(by_alias=True)
    assert "readmeQuality" in data
    assert "ciCd" in data
    assert "contributionHealth" in data
    assert data["insights"]["summary"] == "Healthy repo."
