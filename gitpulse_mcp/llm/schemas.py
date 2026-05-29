"""
llm/schemas.py
--------------
Pydantic models used to parse LLM JSON responses.

These are INTERNAL schemas — they capture the LLM output shape and get
mapped to the public-facing models in models/repository.py by the service layer.
Keeping them separate means the LLM prompt format can evolve without
breaking the frontend-facing API contract.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Health narrative response
# ---------------------------------------------------------------------------


class LLMRecommendation(BaseModel):
    title: str
    description: str
    impact: str = Field(description="High | Medium | Low")
    category: str = Field(description="Security | Documentation | Activity | Code Quality")


class HealthNarrativeResponse(BaseModel):
    classification: str
    summary: str
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendations: list[LLMRecommendation] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# File review response
# ---------------------------------------------------------------------------


class LLMIssue(BaseModel):
    severity: str = Field(description="HIGH | MEDIUM | LOW")
    title: str
    description: str
    suggestion: str


class FileReviewResponse(BaseModel):
    summary: str
    strengths: list[str] = Field(default_factory=list)
    issues: list[LLMIssue] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    overall_quality_score: int = Field(ge=0, le=100, default=50)


# ---------------------------------------------------------------------------
# PR review response
# ---------------------------------------------------------------------------


class PRBlocker(BaseModel):
    file: str
    issue: str


class PRSuggestion(BaseModel):
    file: str
    suggestion: str


class PRReviewResponse(BaseModel):
    verdict: str = Field(description="APPROVE | REQUEST_CHANGES | COMMENT")
    summary: str
    highlights: list[str] = Field(default_factory=list)
    blockers: list[PRBlocker] = Field(default_factory=list)
    suggestions: list[PRSuggestion] = Field(default_factory=list)
    test_coverage_comment: str = ""
    documentation_comment: str = ""


# ---------------------------------------------------------------------------
# Triage response
# ---------------------------------------------------------------------------


class TriagedBug(BaseModel):
    number: int
    title: str
    reason: str
    suggested_labels: list[str] = Field(default_factory=list)


class TriagedGoodFirst(BaseModel):
    number: int
    title: str
    reason: str


class TriagedStale(BaseModel):
    number: int
    title: str
    age_days: int
    action: str


class TriageCategories(BaseModel):
    high_priority_bugs: list[TriagedBug] = Field(default_factory=list)
    good_first_issues: list[TriagedGoodFirst] = Field(default_factory=list)
    stale_issues: list[TriagedStale] = Field(default_factory=list)
    documentation_requests: list[int] = Field(default_factory=list)
    feature_requests: list[int] = Field(default_factory=list)


class HealthSignals(BaseModel):
    has_stale_issues: bool = False
    has_unanswered_bugs: bool = False
    good_first_issue_count: int = 0
    estimated_backlog_health: str = "Fair"


class TriageResponse(BaseModel):
    summary: str
    categories: TriageCategories = Field(default_factory=TriageCategories)
    recommendations: list[str] = Field(default_factory=list)
    health_signals: HealthSignals = Field(default_factory=HealthSignals)


# ---------------------------------------------------------------------------
# Full assessment insights response
# ---------------------------------------------------------------------------


class AssessmentInsightsResponse(BaseModel):
    summary: str
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendations: list[LLMRecommendation] = Field(default_factory=list)
