"""
llm/report_generator.py
-----------------------
High-level report generation helpers used by the service layer.

This module sits between the raw LLMClient and the service layer.
Each function takes structured data, builds the correct prompt variables,
calls the LLM, and returns a typed Pydantic result.

Why this exists:
  The service layer (health_service, assessment_service etc.) has a lot of
  domain logic for gathering and scoring data, but the LLM call pattern is
  always the same: build variables dict → call llm.generate() → return model.
  Centralising that here:
    1. Keeps services focused on data orchestration
    2. Makes it easy to unit-test prompt variable construction separately
    3. Gives one place to tune temperature, token budgets, or swap models
"""

from __future__ import annotations

import json
import logging
from typing import Any

from gitpulse_mcp.llm.client import LLMClient, get_llm_client
from gitpulse_mcp.llm.schemas import (
    AssessmentInsightsResponse,
    FileReviewResponse,
    HealthNarrativeResponse,
    PRReviewResponse,
    TriageResponse,
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Stateless helper that wraps LLMClient with domain-specific generate methods.
    Instantiate once per request or share as a singleton — it holds no state.
    """

    def __init__(self, client: LLMClient | None = None) -> None:
        self._llm = client or get_llm_client()

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health_narrative(
        self, metrics: dict[str, Any]
    ) -> HealthNarrativeResponse:
        """
        Generate a health classification + narrative from raw repo metrics.

        Args:
            metrics: Dict produced by HealthService (health_score, commits,
                     pr_merge_ratio, issue_close_rate, etc.)

        Returns:
            HealthNarrativeResponse with classification, summary, strengths,
            risks, and recommendations.
        """
        return await self._llm.generate(
            prompt_name="health_narrative",
            variables={"metrics_json": json.dumps(metrics, indent=2)},
            response_model=HealthNarrativeResponse,
            temperature=0.2,
        )

    # ------------------------------------------------------------------
    # File review
    # ------------------------------------------------------------------

    async def file_review(
        self,
        file_path: str,
        language: str,
        size_bytes: int | str,
        content: str,
        truncated: bool = False,
    ) -> FileReviewResponse:
        """
        Review a file (full content or diff patch).

        Args:
            file_path:  Path from repo root e.g. 'src/auth.py'
            language:   Detected language e.g. 'Python'
            size_bytes: File size or changed-lines description string
            content:    Raw file content or unified diff patch
            truncated:  Whether the content was truncated before being sent
        """
        truncated_notice = "\n[NOTE: File was truncated to 100KB for review]" if truncated else ""
        return await self._llm.generate(
            prompt_name="review_file",
            variables={
                "file_path": file_path,
                "language": language,
                "size_bytes": str(size_bytes),
                "truncated_notice": truncated_notice,
                "file_content": content,
            },
            response_model=FileReviewResponse,
            temperature=0.4,
        )

    # ------------------------------------------------------------------
    # PR review synthesis
    # ------------------------------------------------------------------

    async def pr_synthesis(
        self,
        pr_metadata: dict[str, Any],
        file_reviews: list[dict[str, Any]],
    ) -> PRReviewResponse:
        """
        Synthesise individual file reviews into a PR-level verdict.

        Args:
            pr_metadata:  Dict with number, title, body, author, stats
            file_reviews: List of per-file review dicts
        """
        return await self._llm.generate(
            prompt_name="review_pr",
            variables={
                "pr_metadata_json": json.dumps(pr_metadata, indent=2),
                "file_reviews_json": json.dumps(file_reviews, indent=2),
            },
            response_model=PRReviewResponse,
            temperature=0.3,
        )

    # ------------------------------------------------------------------
    # Issue triage
    # ------------------------------------------------------------------

    async def triage_issues(
        self,
        owner: str,
        repo: str,
        issue_summaries: list[dict[str, Any]],
    ) -> TriageResponse:
        """
        Classify and prioritise open issues.

        Args:
            owner:           Repo owner
            repo:            Repo name
            issue_summaries: List of compact issue dicts (number, title,
                             labels, comments, age, pre_classification)
        """
        return await self._llm.generate(
            prompt_name="triage_issues",
            variables={
                "owner": owner,
                "repo": repo,
                "issue_count": str(len(issue_summaries)),
                "issues_json": json.dumps(issue_summaries, indent=2),
            },
            response_model=TriageResponse,
            temperature=0.2,
        )

    # ------------------------------------------------------------------
    # Full assessment synthesis
    # ------------------------------------------------------------------

    async def assessment_insights(
        self,
        owner: str,
        repo: str,
        health_score: int,
        classification: str,
        quality_scores: dict[str, int],
        health_metrics: dict[str, Any],
        triage_summary: str,
        file_review_highlights: str,
    ) -> AssessmentInsightsResponse:
        """
        Synthesise all assessment data into a final insights block.

        Args:
            owner/repo:              Repo identity
            health_score:            Computed 0-100 score
            classification:          Healthy / Stagnant / At Risk / Archived
            quality_scores:          {readme, security, ci_cd, contribution} → int
            health_metrics:          Full raw metrics dict from HealthService
            triage_summary:          One-sentence triage summary from TriageService
            file_review_highlights:  Brief highlights string from recent file reviews
        """
        return await self._llm.generate(
            prompt_name="full_assessment",
            variables={
                "owner": owner,
                "repo": repo,
                "health_score": str(health_score),
                "classification": classification,
                "readme_score": str(quality_scores.get("readme", 0)),
                "security_score": str(quality_scores.get("security", 0)),
                "cicd_score": str(quality_scores.get("ci_cd", 0)),
                "contribution_score": str(quality_scores.get("contribution", 0)),
                "health_metrics_json": json.dumps(
                    {k: v for k, v in health_metrics.items() if k != "contributors"},
                    indent=2,
                ),
                "triage_summary": triage_summary,
                "file_review_highlights": file_review_highlights,
            },
            response_model=AssessmentInsightsResponse,
            temperature=0.3,
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_generator: ReportGenerator | None = None


def get_report_generator() -> ReportGenerator:
    """Return the shared ReportGenerator singleton."""
    global _generator
    if _generator is None:
        _generator = ReportGenerator()
    return _generator
