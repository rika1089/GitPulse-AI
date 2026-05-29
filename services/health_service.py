"""
services/health_service.py
--------------------------
Phase 2 — Repository Health Analysis.

Health Score Formula (configurable weights in .env):
  score = (commit_freq_norm  * 0.30)
        + (pr_merge_ratio    * 0.25)
        + (issue_close_rate  * 0.25)
        + (contributor_norm  * 0.20)
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
from datetime import datetime, timezone
from typing import Any

from gitpulse_mcp.config import settings
from gitpulse_mcp.github.commits import get_commit_metrics
from gitpulse_mcp.github.issues import fetch_issue_metrics
from gitpulse_mcp.github.pulls import fetch_pr_metrics
from gitpulse_mcp.github.repo import (
    compute_language_percentages,
    fetch_contributors,
    fetch_languages,
    fetch_repo_metadata,
    parse_license,
)
from gitpulse_mcp.llm.client import get_llm_client
from gitpulse_mcp.llm.schemas import HealthNarrativeResponse
from gitpulse_mcp.models.repository import (
    ActivityLevel,
    ActivityStatus,
    Contributor,
    HealthClassification,
    LanguageBreakdown,
    Recommendation,
    RecommendationCategory,
    RecommendationImpact,
    RepoInsights,
    Repository,
)

logger = logging.getLogger(__name__)


class RepoHealthResult:
    def __init__(self, repository: Repository, insights: RepoInsights, raw_metrics: dict[str, Any]) -> None:
        self.repository = repository
        self.insights = insights
        self.raw_metrics = raw_metrics

    def model_dump(self, by_alias: bool = False) -> dict[str, Any]:
        return {
            "repository": self.repository.model_dump(by_alias=by_alias),
            "insights": self.insights.model_dump(),
            "raw_metrics": self.raw_metrics,
        }


class HealthService:
    async def analyse(self, owner: str, repo: str) -> RepoHealthResult:
        logger.info("Starting health analysis for %s/%s", owner, repo)

        metadata, commit_metrics, issue_metrics, pr_metrics, languages, contributors = (
            await asyncio.gather(
                fetch_repo_metadata(owner, repo),
                get_commit_metrics(owner, repo),
                fetch_issue_metrics(owner, repo),
                fetch_pr_metrics(owner, repo),
                fetch_languages(owner, repo),
                fetch_contributors(owner, repo, max_pages=1),
            )
        )

        score_components = self._compute_score_components(commit_metrics, issue_metrics, pr_metrics, contributors)
        health_score = self._weighted_score(score_components)

        last_push_days = self._days_since(metadata.get("pushed_at"))
        raw_metrics = {
            "owner": owner, "repo": repo, "health_score": health_score,
            "stars": metadata.get("stargazers_count", 0),
            "forks": metadata.get("forks_count", 0),
            "commits_last_30_days": commit_metrics["commits_last_30_days"],
            "commits_last_90_days": commit_metrics["commits_last_90_days"],
            "avg_commits_per_week": commit_metrics["avg_commits_per_week"],
            "open_issues": issue_metrics["open_count"],
            "closed_issues": issue_metrics["closed_count"],
            "issue_close_rate": issue_metrics["issue_close_rate"],
            "avg_resolution_time_days": issue_metrics["avg_resolution_time_days"],
            "avg_response_time_days": issue_metrics["avg_response_time_days"],
            "open_prs": pr_metrics["open_count"],
            "merged_prs": pr_metrics["merged_count"],
            "pr_merge_ratio": pr_metrics["pr_merge_ratio"],
            "contributor_count": len(contributors),
            "last_push_days_ago": last_push_days,
            "score_components": score_components,
        }

        narrative = await self._generate_narrative(raw_metrics)
        language_data = compute_language_percentages(languages)
        repository = self._build_repository_model(owner, repo, metadata, issue_metrics, pr_metrics, health_score, narrative.classification, language_data)
        insights = self._build_insights(narrative)

        logger.info("Health analysis complete: %s/%s score=%d", owner, repo, health_score)
        return RepoHealthResult(repository=repository, insights=insights, raw_metrics=raw_metrics)

    def _compute_score_components(self, commit_metrics, issue_metrics, pr_metrics, contributors) -> dict[str, float]:
        commits_30 = commit_metrics["commits_last_30_days"]
        commit_norm = min(1.0, math.log(commits_30 + 1) / math.log(31))
        pr_norm = pr_metrics["pr_merge_ratio"]
        issue_norm = issue_metrics["issue_close_rate"]
        contrib_count = len(contributors)
        contrib_norm = math.tanh(contrib_count / 5.0) if contrib_count > 0 else 0.0
        return {
            "commit_frequency": round(commit_norm, 3),
            "pr_merge_ratio": round(pr_norm, 3),
            "issue_close_rate": round(issue_norm, 3),
            "contributor_activity": round(contrib_norm, 3),
        }

    def _weighted_score(self, components: dict[str, float]) -> int:
        raw = (
            components["commit_frequency"]      * settings.weight_commit_freq
            + components["pr_merge_ratio"]      * settings.weight_pr_merge_ratio
            + components["issue_close_rate"]    * settings.weight_issue_close_rate
            + components["contributor_activity"]* settings.weight_contributor_activity
        )
        return max(0, min(100, round(raw * 100)))

    async def _generate_narrative(self, raw_metrics: dict[str, Any]) -> HealthNarrativeResponse:
        llm = get_llm_client()
        try:
            return await llm.generate(
                prompt_name="health_narrative",
                variables={"metrics_json": json.dumps(raw_metrics, indent=2)},
                response_model=HealthNarrativeResponse,
                temperature=0.2,
            )
        except Exception as exc:
            logger.warning("LLM failed: %s. Using rule-based fallback.", exc)
            return self._rule_based_narrative(raw_metrics)

    def _rule_based_narrative(self, metrics: dict[str, Any]) -> HealthNarrativeResponse:
        score = metrics["health_score"]
        commits = metrics["commits_last_30_days"]
        if score >= 70 and commits > 5:
            classification = "Healthy"
        elif commits == 0 and metrics.get("last_push_days_ago", 0) > 365:
            classification = "Archived"
        elif score >= 40:
            classification = "Stagnant"
        else:
            classification = "At Risk"
        return HealthNarrativeResponse(
            classification=classification,
            summary=f"Health score {score}/100, {commits} commits in last 30 days, PR merge ratio {metrics['pr_merge_ratio']:.0%}, issue close rate {metrics['issue_close_rate']:.0%}.",
            strengths=[f"PR merge ratio: {metrics['pr_merge_ratio']:.0%}", f"{metrics['contributor_count']} contributors"],
            risks=[f"Issue close rate: {metrics['issue_close_rate']:.0%}"],
            recommendations=[],
        )

    def _build_repository_model(self, owner, repo, metadata, issue_metrics, pr_metrics, health_score, classification, language_data) -> Repository:
        cls_map = {"Healthy": HealthClassification.HEALTHY, "Stagnant": HealthClassification.STAGNANT, "At Risk": HealthClassification.AT_RISK, "Archived": HealthClassification.ARCHIVED}
        health_cls = cls_map.get(classification, HealthClassification.AT_RISK)
        languages = [LanguageBreakdown(**lang) for lang in language_data]
        return Repository(
            id=f"{owner.lower()}-{repo.lower()}",
            name=metadata.get("name", repo),
            owner=owner,
            description=metadata.get("description") or "",
            stars=metadata.get("stargazers_count", 0),
            forks=metadata.get("forks_count", 0),
            watchers=metadata.get("watchers_count", 0),
            license=parse_license(metadata),
            open_issues_count=issue_metrics["open_count"],
            closed_issues_count=issue_metrics["closed_count"],
            open_prs_count=pr_metrics["open_count"],
            merged_prs_count=pr_metrics["merged_count"],
            avg_response_time_days=issue_metrics["avg_response_time_days"],
            avg_close_time_days=issue_metrics["avg_resolution_time_days"],
            last_push_date=self._human_readable_date(metadata.get("pushed_at")),
            health_score=health_score,
            classification=health_cls,
            activity_status=self._classify_activity(health_score),
            primary_language=metadata.get("language") or "Unknown",
            languages=languages,
            topics=metadata.get("topics") or [],
        )

    def _build_insights(self, narrative: HealthNarrativeResponse) -> RepoInsights:
        impact_map = {"High": RecommendationImpact.HIGH, "Medium": RecommendationImpact.MEDIUM, "Low": RecommendationImpact.LOW}
        cat_map = {"Security": RecommendationCategory.SECURITY, "Documentation": RecommendationCategory.DOCUMENTATION, "Activity": RecommendationCategory.ACTIVITY, "Code Quality": RecommendationCategory.CODE_QUALITY}
        recs = [Recommendation(title=r.title, description=r.description, impact=impact_map.get(r.impact, RecommendationImpact.MEDIUM), category=cat_map.get(r.category, RecommendationCategory.ACTIVITY)) for r in narrative.recommendations]
        return RepoInsights(summary=narrative.summary, strengths=narrative.strengths, risks=narrative.risks, recommendations=recs)

    @staticmethod
    def _classify_activity(score: int) -> ActivityStatus:
        if score >= 70: return ActivityStatus.HIGH
        if score >= 50: return ActivityStatus.MODERATE
        if score >= 25: return ActivityStatus.LOW
        return ActivityStatus.INACTIVE

    @staticmethod
    def _days_since(iso_string: str | None) -> int:
        if not iso_string: return 9999
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return (datetime.now(tz=timezone.utc) - dt).days

    @staticmethod
    def _human_readable_date(iso_string: str | None) -> str:
        if not iso_string: return "Unknown"
        days = HealthService._days_since(iso_string)
        if days == 0: return "today"
        if days == 1: return "1 day ago"
        if days < 7: return f"{days} days ago"
        if days < 30: return f"{days // 7} week(s) ago"
        if days < 365: return f"{days // 30} month(s) ago"
        return f"{days // 365} year(s) ago"
