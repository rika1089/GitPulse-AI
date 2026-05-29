"""
models/review.py
----------------
Public-facing Pydantic models for the review_file and review_pull_request
tool outputs.

These are what the MCP tools return to the AI client (and eventually the
frontend if a /api/review endpoint is added). They are distinct from the
internal llm/schemas.py models which capture the raw LLM JSON shape.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PRVerdict(str, Enum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    COMMENT = "COMMENT"


class ReviewIssue(BaseModel):
    """A single code issue found during review."""
    severity: IssueSeverity
    title: str
    description: str
    suggestion: str


class FileReview(BaseModel):
    """
    Complete review of a single file.
    Returned by the review_file MCP tool and used per-file inside PRReview.
    """
    file: str = Field(description="File path from repo root")
    language: str
    size_bytes: int = Field(ge=0)
    truncated: bool = Field(default=False)
    summary: str
    strengths: list[str] = Field(default_factory=list)
    issues: list[ReviewIssue] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    overall_quality_score: int = Field(ge=0, le=100)

    @property
    def has_blockers(self) -> bool:
        return any(i.severity == IssueSeverity.HIGH for i in self.issues)


class PRStats(BaseModel):
    files_changed: int = Field(ge=0, serialization_alias="filesChanged")
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)

    model_config = {"populate_by_name": True}


class PRBlocker(BaseModel):
    file: str
    issue: str


class PRSuggestion(BaseModel):
    file: str
    suggestion: str


class PRReview(BaseModel):
    """
    Complete review of a pull request.
    Returned by the review_pull_request MCP tool.
    """
    pr_number: int = Field(ge=1, serialization_alias="prNumber")
    title: str
    author: str
    stats: PRStats
    verdict: PRVerdict
    summary: str
    highlights: list[str] = Field(default_factory=list)
    blockers: list[PRBlocker] = Field(default_factory=list)
    suggestions: list[PRSuggestion] = Field(default_factory=list)
    test_coverage_comment: str = Field(default="", serialization_alias="testCoverageComment")
    documentation_comment: str = Field(default="", serialization_alias="documentationComment")
    file_reviews: list[FileReview] = Field(default_factory=list, serialization_alias="fileReviews")

    model_config = {"populate_by_name": True}

    @property
    def blocker_count(self) -> int:
        return len(self.blockers)
