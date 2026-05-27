"""
models/repository.py
--------------------
Pydantic v2 models that mirror the TypeScript types in src/types/dashboard.ts
field-for-field. Any change to the frontend types must be reflected here.

These models serve two purposes:
1. Type-safe containers for GitHub API data within the Python backend.
2. JSON-serialisable responses the MCP tools return to the AI client.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class HealthClassification(str, Enum):
    """Maps to TypeScript: 'Healthy' | 'Stagnant' | 'At Risk' | 'Archived'"""
    HEALTHY = "Healthy"
    STAGNANT = "Stagnant"
    AT_RISK = "At Risk"
    ARCHIVED = "Archived"


class ActivityStatus(str, Enum):
    """Maps to TypeScript: 'High' | 'Moderate' | 'Low' | 'Inactive'"""
    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"
    INACTIVE = "Inactive"


class ActivityLevel(str, Enum):
    """Maps to TypeScript Contributor.activityLevel"""
    ACTIVE = "Active"
    VERY_ACTIVE = "Very Active"
    STALE = "Stale"


class TimelineEventType(str, Enum):
    """Maps to TypeScript ActivityTimelineItem.type"""
    COMMIT = "commit"
    PR_MERGE = "pr_merge"
    PR_OPEN = "pr_open"
    ISSUE_OPEN = "issue_open"
    ISSUE_CLOSE = "issue_close"
    RELEASE = "release"


class CheckStatus(str, Enum):
    """Maps to TypeScript CheckItem.status"""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class RecommendationImpact(str, Enum):
    """Maps to TypeScript recommendation.impact"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RecommendationCategory(str, Enum):
    """Maps to TypeScript recommendation.category"""
    SECURITY = "Security"
    DOCUMENTATION = "Documentation"
    ACTIVITY = "Activity"
    CODE_QUALITY = "Code Quality"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class LanguageBreakdown(BaseModel):
    """Maps to TypeScript: { name: string; percentage: number; color: string }"""
    name: str
    percentage: float = Field(ge=0.0, le=100.0)
    color: str = Field(description="Hex color string e.g. '#f1e05a'")


class Repository(BaseModel):
    """
    Maps to TypeScript interface Repository in dashboard.ts.
    This is the primary data model — all other tools reference it.
    """
    id: str = Field(description="Slug e.g. 'facebook-react'")
    name: str = Field(description="Repository name e.g. 'react'")
    owner: str = Field(description="Owner login e.g. 'facebook'")
    description: str = Field(default="", description="Repository description")
    stars: int = Field(ge=0)
    forks: int = Field(ge=0)
    watchers: int = Field(ge=0)
    license: str = Field(default="Unknown")
    open_issues_count: int = Field(ge=0, serialization_alias="openIssuesCount")
    closed_issues_count: int = Field(ge=0, serialization_alias="closedIssuesCount")
    open_prs_count: int = Field(ge=0, serialization_alias="openPRsCount")
    merged_prs_count: int = Field(ge=0, serialization_alias="mergedPRsCount")
    avg_response_time_days: float = Field(
        ge=0.0, serialization_alias="avgResponseTimeDays"
    )
    avg_close_time_days: float = Field(
        ge=0.0, serialization_alias="avgCloseTimeDays"
    )
    last_push_date: str = Field(
        serialization_alias="lastPushDate",
        description="ISO date string or human-readable e.g. '2 hours ago'",
    )
    health_score: int = Field(
        ge=0, le=100, serialization_alias="healthScore"
    )
    classification: HealthClassification
    activity_status: ActivityStatus = Field(serialization_alias="activityStatus")
    primary_language: str = Field(
        default="Unknown", serialization_alias="primaryLanguage"
    )
    languages: list[LanguageBreakdown] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class Contributor(BaseModel):
    """Maps to TypeScript interface Contributor in dashboard.ts."""
    name: str
    avatar_url: str = Field(serialization_alias="avatarUrl")
    commits: int = Field(ge=0)
    prs: int = Field(ge=0)
    role: str = Field(default="Contributor")
    activity_level: ActivityLevel = Field(serialization_alias="activityLevel")

    model_config = {"populate_by_name": True}


class TimelineUser(BaseModel):
    name: str
    avatar_url: str = Field(serialization_alias="avatarUrl")

    model_config = {"populate_by_name": True}


class ActivityTimelineItem(BaseModel):
    """Maps to TypeScript interface ActivityTimelineItem in dashboard.ts."""
    id: str
    type: TimelineEventType
    title: str
    description: str
    user: TimelineUser
    timestamp: str

    model_config = {"populate_by_name": True}


class CheckItem(BaseModel):
    """
    Maps to TypeScript interface CheckItem in dashboard.ts.
    Used inside readmeQuality, security, ciCd, contributionHealth sections.
    """
    name: str
    description: str
    status: CheckStatus
    feedback: str


class ScoredSection(BaseModel):
    """
    Common wrapper used for readmeQuality, security, ciCd, contributionHealth
    in RepoDetails — each has a numeric score and a list of checks.
    """
    score: int = Field(ge=0, le=100)
    checks: list[CheckItem] = Field(default_factory=list)


class Recommendation(BaseModel):
    """Maps to TypeScript recommendation object inside RepoDetails.insights."""
    title: str
    description: str
    impact: RecommendationImpact
    category: RecommendationCategory


class RepoInsights(BaseModel):
    """Maps to TypeScript RepoDetails.insights block."""
    summary: str
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)


class RepoDetails(BaseModel):
    """
    Maps to TypeScript interface RepoDetails in dashboard.ts.
    This is what full_repo_assessment() returns and what the
    AIInsightsPanel + RepoDetailsPage pages consume.
    """
    repository: Repository
    readme_quality: ScoredSection = Field(serialization_alias="readmeQuality")
    security: ScoredSection
    ci_cd: ScoredSection = Field(serialization_alias="ciCd")
    contribution_health: ScoredSection = Field(serialization_alias="contributionHealth")
    contributors: list[Contributor] = Field(default_factory=list)
    timeline: list[ActivityTimelineItem] = Field(default_factory=list)
    insights: RepoInsights

    model_config = {"populate_by_name": True}


class DashboardStats(BaseModel):
    """Maps to TypeScript interface DashboardStats in dashboard.ts."""
    total_repos: int = Field(ge=0, serialization_alias="totalRepos")
    open_issues: int = Field(ge=0, serialization_alias="openIssues")
    open_prs: int = Field(ge=0, serialization_alias="openPRs")
    avg_health_score: float = Field(ge=0.0, le=100.0, serialization_alias="avgHealthScore")
    avg_response_time_days: float = Field(ge=0.0, serialization_alias="avgResponseTimeDays")
    total_contributors: int = Field(ge=0, serialization_alias="totalContributors")

    model_config = {"populate_by_name": True}
