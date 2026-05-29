"""
models/triage.py
----------------
Public-facing Pydantic models for the triage_issues tool output.

These match the shape the frontend's issue triage view would consume,
and what the MCP tool returns to the AI client.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class BacklogHealth(str, Enum):
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"


class StaleAction(str, Enum):
    CLOSE = "close"
    NEEDS_INFO = "needs-info"
    REASSIGN = "reassign"


class TriagedBug(BaseModel):
    number: int
    title: str
    reason: str
    suggested_labels: list[str] = Field(default_factory=list, serialization_alias="suggestedLabels")

    model_config = {"populate_by_name": True}


class TriagedGoodFirst(BaseModel):
    number: int
    title: str
    reason: str


class TriagedStaleIssue(BaseModel):
    number: int
    title: str
    age_days: int = Field(ge=0, serialization_alias="ageDays")
    action: StaleAction

    model_config = {"populate_by_name": True}


class TriageCategories(BaseModel):
    high_priority_bugs: list[TriagedBug] = Field(
        default_factory=list, serialization_alias="highPriorityBugs"
    )
    good_first_issues: list[TriagedGoodFirst] = Field(
        default_factory=list, serialization_alias="goodFirstIssues"
    )
    stale_issues: list[TriagedStaleIssue] = Field(
        default_factory=list, serialization_alias="staleIssues"
    )
    documentation_requests: list[int] = Field(
        default_factory=list, serialization_alias="documentationRequests"
    )
    feature_requests: list[int] = Field(
        default_factory=list, serialization_alias="featureRequests"
    )

    model_config = {"populate_by_name": True}

    @property
    def total_categorised(self) -> int:
        return (
            len(self.high_priority_bugs)
            + len(self.good_first_issues)
            + len(self.stale_issues)
            + len(self.documentation_requests)
            + len(self.feature_requests)
        )


class TriageHealthSignals(BaseModel):
    has_stale_issues: bool = Field(default=False, serialization_alias="hasStaleIssues")
    has_unanswered_bugs: bool = Field(default=False, serialization_alias="hasUnansweredBugs")
    good_first_issue_count: int = Field(default=0, ge=0, serialization_alias="goodFirstIssueCount")
    estimated_backlog_health: BacklogHealth = Field(
        default=BacklogHealth.FAIR, serialization_alias="estimatedBacklogHealth"
    )

    model_config = {"populate_by_name": True}


class TriageReport(BaseModel):
    """
    Complete triage report for a repository's open issues.
    Returned by the triage_issues MCP tool.
    """
    owner: str
    repo: str
    issue_count: int = Field(ge=0, serialization_alias="issueCount")
    summary: str
    categories: TriageCategories = Field(default_factory=TriageCategories)
    recommendations: list[str] = Field(default_factory=list)
    health_signals: TriageHealthSignals = Field(
        default_factory=TriageHealthSignals, serialization_alias="healthSignals"
    )

    model_config = {"populate_by_name": True}
