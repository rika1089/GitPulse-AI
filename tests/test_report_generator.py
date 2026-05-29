"""
tests/test_report_generator.py
------------------------------
Tests for report_generator.py
"""

from gitpulse_mcp.llm.report_generator import generate_markdown_report, format_timeline_for_prompt, format_recommendations
from gitpulse_mcp.models.repository import (
    RepoDetails,
    Repository,
    HealthClassification,
    ActivityTimelineItem,
    TimelineEventType,
    TimelineUser,
    Recommendation,
    RecommendationCategory,
    RecommendationImpact,
    RepoInsights,
    ScoredSection,
)

def test_generate_markdown_report():
    repo = Repository(
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
        activity_status="High"
    )
    insights = RepoInsights(
        summary="A great repository.",
        strengths=["Good docs"],
        risks=[],
        recommendations=[
            Recommendation(title="Add tests", description="More tests", impact=RecommendationImpact.HIGH, category=RecommendationCategory.CODE_QUALITY)
        ]
    )
    repo_details = RepoDetails(
        repository=repo,
        readme_quality=ScoredSection(score=100, checks=[]),
        security=ScoredSection(score=90, checks=[]),
        ci_cd=ScoredSection(score=80, checks=[]),
        contribution_health=ScoredSection(score=100, checks=[]),
        contributors=[],
        timeline=[],
        insights=insights
    )
    
    report = generate_markdown_report(repo_details)
    assert "Repository Assessment: testowner/testrepo" in report
    assert "**Health Score:** 85/100 (Healthy)" in report
    assert "**Activity Level:** High" in report
    assert "A great repository." in report
    assert "Good docs" in report
    assert "[HIGH]" in report
    assert "**README Quality:** 100/100" in report

def test_format_timeline_for_prompt():
    timeline = [
        ActivityTimelineItem(
            id="1",
            type=TimelineEventType.COMMIT,
            title="Fix bug",
            description="Fix bug",
            user=TimelineUser(name="alice", avatar_url=""),
            timestamp="today"
        )
    ]
    formatted = format_timeline_for_prompt(timeline)
    assert "today" in formatted
    assert "commit" in formatted
    assert "Fix bug" in formatted
    assert "alice" in formatted

def test_format_timeline_empty():
    assert format_timeline_for_prompt([]) == "No recent activity found."

def test_format_recommendations():
    recs = [
        Recommendation(
            title="Rec 1",
            description="Desc 1",
            impact=RecommendationImpact.LOW,
            category=RecommendationCategory.DOCUMENTATION
        )
    ]
    formatted = format_recommendations(recs)
    assert "Documentation" in formatted
    assert "Low" in formatted
    assert "Rec 1: Desc 1" in formatted

def test_format_recommendations_empty():
    assert format_recommendations([]) == "No recommendations."
