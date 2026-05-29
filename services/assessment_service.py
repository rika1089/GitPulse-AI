"""
services/assessment_service.py
-------------------------------
Phase 4 — Full Repository Assessment.

Orchestrates HealthService + quality checks + TriageService + ReviewService
concurrently, then synthesises via LLM into the complete RepoDetails model.

This is the most expensive operation: ~10-15 GitHub API calls + 3-5 LLM calls.
asyncio.gather() keeps wall-clock time to 8-15 seconds for most repos.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from gitpulse_mcp.github.commits import fetch_recent_commits
from gitpulse_mcp.github.files import check_file_exists, list_workflows
from gitpulse_mcp.github.issues import fetch_recent_issue_events
from gitpulse_mcp.github.pulls import fetch_recent_pr_events
from gitpulse_mcp.github.repo import fetch_latest_release
from gitpulse_mcp.llm.client import get_llm_client
from gitpulse_mcp.llm.schemas import AssessmentInsightsResponse
from gitpulse_mcp.models.repository import (
    ActivityLevel,
    ActivityTimelineItem,
    CheckItem,
    CheckStatus,
    Contributor,
    RecommendationCategory,
    RecommendationImpact,
    Recommendation,
    RepoDetails,
    RepoInsights,
    ScoredSection,
    TimelineEventType,
    TimelineUser,
)
from gitpulse_mcp.services.health_service import HealthService
from gitpulse_mcp.services.review_service import ReviewService
from gitpulse_mcp.services.triage_service import TriageService

logger = logging.getLogger(__name__)


class AssessmentService:
    """Phase 4 service: Full repository assessment producing a RepoDetails model."""

    async def assess(self, owner: str, repo: str) -> RepoDetails:
        logger.info("Starting full assessment for %s/%s", owner, repo)

        health_svc = HealthService()
        triage_svc = TriageService()

        # Run health analysis, triage, and quality file checks concurrently
        health_result, triage_result, quality_data = await asyncio.gather(
            health_svc.analyse(owner, repo),
            triage_svc.triage(owner, repo, max_issues=30),
            self._run_quality_checks(owner, repo),
        )

        # Run recent file review on top 3 recently modified files
        review_highlights = await self._review_recent_files(owner, repo)

        # Fetch timeline data
        timeline = await self._build_timeline(owner, repo)

        # Build the four scored sections
        readme_section = quality_data["readme"]
        security_section = quality_data["security"]
        cicd_section = quality_data["ci_cd"]
        contribution_section = quality_data["contribution"]

        # LLM final synthesis
        insights = await self._synthesise_insights(
            owner=owner,
            repo=repo,
            health_result=health_result,
            triage_result=triage_result,
            readme_score=readme_section.score,
            security_score=security_section.score,
            cicd_score=cicd_section.score,
            contribution_score=contribution_section.score,
            review_highlights=review_highlights,
        )

        # Build contributor models
        raw_contributors = health_result.raw_metrics.get("contributors", [])
        contributors = [Contributor(**c) if isinstance(c, dict) else c for c in raw_contributors]

        logger.info("Full assessment complete for %s/%s", owner, repo)

        return RepoDetails(
            repository=health_result.repository,
            readme_quality=readme_section,
            security=security_section,
            ci_cd=cicd_section,
            contribution_health=contribution_section,
            contributors=contributors,
            timeline=timeline,
            insights=insights,
        )

    # ------------------------------------------------------------------
    # Quality checks (rule-based, no LLM needed)
    # ------------------------------------------------------------------

    async def _run_quality_checks(self, owner: str, repo: str) -> dict[str, ScoredSection]:
        """Run all four quality check categories concurrently."""
        readme_checks, security_checks, cicd_checks, contrib_checks = await asyncio.gather(
            self._check_readme(owner, repo),
            self._check_security(owner, repo),
            self._check_cicd(owner, repo),
            self._check_contribution_health(owner, repo),
        )
        return {
            "readme": readme_checks,
            "security": security_checks,
            "ci_cd": cicd_checks,
            "contribution": contrib_checks,
        }

    async def _check_readme(self, owner: str, repo: str) -> ScoredSection:
        checks = []
        score = 0

        # Check README exists
        readme_exists = await check_file_exists(owner, repo, "README.md") or await check_file_exists(owner, repo, "readme.md")
        if readme_exists:
            checks.append(CheckItem(name="README Present", description="README.md file exists.", status=CheckStatus.PASSED, feedback="README found at root."))
            score += 30
        else:
            checks.append(CheckItem(name="README Present", description="No README.md found.", status=CheckStatus.FAILED, feedback="Add a README.md to describe the project."))

        # License
        license_exists = await check_file_exists(owner, repo, "LICENSE") or await check_file_exists(owner, repo, "LICENSE.md")
        if license_exists:
            checks.append(CheckItem(name="License File", description="License file present.", status=CheckStatus.PASSED, feedback="License clearly defined."))
            score += 25
        else:
            checks.append(CheckItem(name="License File", description="No LICENSE file found.", status=CheckStatus.WARNING, feedback="Add a LICENSE file to clarify usage terms."))

        # Contributing guidelines
        contrib_exists = await check_file_exists(owner, repo, "CONTRIBUTING.md")
        if contrib_exists:
            checks.append(CheckItem(name="Contributing Guidelines", description="CONTRIBUTING.md exists.", status=CheckStatus.PASSED, feedback="Contributors have a clear guide."))
            score += 25
        else:
            checks.append(CheckItem(name="Contributing Guidelines", description="No CONTRIBUTING.md found.", status=CheckStatus.WARNING, feedback="Add CONTRIBUTING.md to guide new contributors."))

        # Code of Conduct
        coc_exists = await check_file_exists(owner, repo, "CODE_OF_CONDUCT.md")
        if coc_exists:
            checks.append(CheckItem(name="Code of Conduct", description="CODE_OF_CONDUCT.md present.", status=CheckStatus.PASSED, feedback="Community standards defined."))
            score += 20
        else:
            checks.append(CheckItem(name="Code of Conduct", description="No Code of Conduct found.", status=CheckStatus.WARNING, feedback="Consider adding a CODE_OF_CONDUCT.md."))

        return ScoredSection(score=min(100, score), checks=checks)

    async def _check_security(self, owner: str, repo: str) -> ScoredSection:
        checks = []
        score = 0

        security_policy = await check_file_exists(owner, repo, "SECURITY.md")
        if security_policy:
            checks.append(CheckItem(name="Security Policy", description="SECURITY.md exists.", status=CheckStatus.PASSED, feedback="Vulnerability reporting procedure defined."))
            score += 40
        else:
            checks.append(CheckItem(name="Security Policy", description="No SECURITY.md found.", status=CheckStatus.WARNING, feedback="Add SECURITY.md to define how to report vulnerabilities."))

        dependabot = await check_file_exists(owner, repo, ".github/dependabot.yml")
        if dependabot:
            checks.append(CheckItem(name="Dependabot Configured", description="Automated dependency updates enabled.", status=CheckStatus.PASSED, feedback="Dependencies will be kept up-to-date automatically."))
            score += 35
        else:
            checks.append(CheckItem(name="Dependabot Configured", description="No dependabot.yml found.", status=CheckStatus.WARNING, feedback="Add .github/dependabot.yml to automate dependency updates."))

        codeowners = await check_file_exists(owner, repo, "CODEOWNERS") or await check_file_exists(owner, repo, ".github/CODEOWNERS")
        if codeowners:
            checks.append(CheckItem(name="CODEOWNERS Defined", description="CODEOWNERS file present.", status=CheckStatus.PASSED, feedback="Review ownership is clearly assigned."))
            score += 25
        else:
            checks.append(CheckItem(name="CODEOWNERS Defined", description="No CODEOWNERS file.", status=CheckStatus.WARNING, feedback="Add CODEOWNERS to enforce review assignments."))

        return ScoredSection(score=min(100, score), checks=checks)

    async def _check_cicd(self, owner: str, repo: str) -> ScoredSection:
        checks = []
        score = 0

        workflows = await list_workflows(owner, repo)
        if workflows:
            checks.append(CheckItem(name="GitHub Actions Configured", description=f"{len(workflows)} workflow(s) found.", status=CheckStatus.PASSED, feedback=f"Workflows: {', '.join(w['name'] for w in workflows[:3])}."))
            score += 50
        else:
            checks.append(CheckItem(name="GitHub Actions Configured", description="No workflows found in .github/workflows/.", status=CheckStatus.FAILED, feedback="Add GitHub Actions workflows for CI/CD automation."))

        # Check for common CI patterns in workflow names
        workflow_names = " ".join(w.get("name", "").lower() for w in workflows)
        has_test_workflow = any(kw in workflow_names for kw in ["test", "ci", "check", "lint", "build"])
        if has_test_workflow:
            checks.append(CheckItem(name="Test Workflow", description="CI workflow with test/lint/build detected.", status=CheckStatus.PASSED, feedback="Automated quality gates are in place."))
            score += 30
        elif workflows:
            checks.append(CheckItem(name="Test Workflow", description="Workflows exist but no test/CI workflow detected.", status=CheckStatus.WARNING, feedback="Add a workflow that runs tests on every pull request."))
            score += 10

        has_deploy = any(kw in workflow_names for kw in ["deploy", "release", "publish", "cd"])
        if has_deploy:
            checks.append(CheckItem(name="Deployment Workflow", description="Deployment/release workflow detected.", status=CheckStatus.PASSED, feedback="Automated deployments configured."))
            score += 20
        else:
            checks.append(CheckItem(name="Deployment Workflow", description="No deployment workflow found.", status=CheckStatus.WARNING, feedback="Consider automating releases with a deploy workflow."))

        return ScoredSection(score=min(100, score), checks=checks)

    async def _check_contribution_health(self, owner: str, repo: str) -> ScoredSection:
        checks = []
        score = 0

        pr_template = await check_file_exists(owner, repo, ".github/PULL_REQUEST_TEMPLATE.md")
        if pr_template:
            checks.append(CheckItem(name="PR Template", description="Pull request template exists.", status=CheckStatus.PASSED, feedback="Contributors get guidance when opening PRs."))
            score += 35
        else:
            checks.append(CheckItem(name="PR Template", description="No PR template found.", status=CheckStatus.WARNING, feedback="Add .github/PULL_REQUEST_TEMPLATE.md to standardise PR descriptions."))

        issue_templates = await check_file_exists(owner, repo, ".github/ISSUE_TEMPLATE")
        if issue_templates:
            checks.append(CheckItem(name="Issue Templates", description="Issue templates directory found.", status=CheckStatus.PASSED, feedback="Issues are submitted in a consistent format."))
            score += 35
        else:
            checks.append(CheckItem(name="Issue Templates", description="No issue templates found.", status=CheckStatus.WARNING, feedback="Add .github/ISSUE_TEMPLATE/ to guide bug reports and feature requests."))

        contributing = await check_file_exists(owner, repo, "CONTRIBUTING.md")
        if contributing:
            checks.append(CheckItem(name="Contribution Guide", description="CONTRIBUTING.md present.", status=CheckStatus.PASSED, feedback="New contributors have a clear onboarding path."))
            score += 30
        else:
            checks.append(CheckItem(name="Contribution Guide", description="No CONTRIBUTING.md.", status=CheckStatus.WARNING, feedback="Add CONTRIBUTING.md to reduce contributor friction."))

        return ScoredSection(score=min(100, score), checks=checks)

    # ------------------------------------------------------------------
    # Timeline builder
    # ------------------------------------------------------------------

    async def _build_timeline(self, owner: str, repo: str) -> list[ActivityTimelineItem]:
        """Build activity timeline from recent commits, PRs, issues, and releases."""
        commits, prs, issues, release = await asyncio.gather(
            fetch_recent_commits(owner, repo, limit=3),
            fetch_recent_pr_events(owner, repo, limit=3),
            fetch_recent_issue_events(owner, repo, limit=3),
            fetch_latest_release(owner, repo),
        )

        items: list[ActivityTimelineItem] = []

        for c in commits:
            author = c.get("commit", {}).get("author", {})
            user_data = c.get("author") or {}
            msg = (c.get("commit", {}).get("message") or "Commit")[:80]
            items.append(ActivityTimelineItem(
                id=c.get("sha", "")[:8],
                type=TimelineEventType.COMMIT,
                title=msg.split("\n")[0],
                description=msg,
                user=TimelineUser(name=author.get("name", "unknown"), avatar_url=user_data.get("avatar_url", "")),
                timestamp=self._human_ts(author.get("date")),
            ))

        for pr in prs:
            user = pr.get("user", {})
            is_merged = bool(pr.get("merged_at"))
            items.append(ActivityTimelineItem(
                id=str(pr.get("number", "")),
                type=TimelineEventType.PR_MERGE if is_merged else TimelineEventType.PR_OPEN,
                title=pr.get("title", "Pull request"),
                description=f"#{pr.get('number')} by {user.get('login', 'unknown')}",
                user=TimelineUser(name=user.get("login", "unknown"), avatar_url=user.get("avatar_url", "")),
                timestamp=self._human_ts(pr.get("updated_at")),
            ))

        for issue in issues:
            user = issue.get("user", {})
            is_closed = issue.get("state") == "closed"
            items.append(ActivityTimelineItem(
                id=str(issue.get("number", "")),
                type=TimelineEventType.ISSUE_CLOSE if is_closed else TimelineEventType.ISSUE_OPEN,
                title=issue.get("title", "Issue"),
                description=f"#{issue.get('number')} — {issue.get('title', '')}",
                user=TimelineUser(name=user.get("login", "unknown"), avatar_url=user.get("avatar_url", "")),
                timestamp=self._human_ts(issue.get("updated_at")),
            ))

        if release:
            author = release.get("author", {})
            items.append(ActivityTimelineItem(
                id=str(release.get("id", "release")),
                type=TimelineEventType.RELEASE,
                title=f"Release {release.get('tag_name', '')}",
                description=release.get("name") or release.get("tag_name", "New release"),
                user=TimelineUser(name=author.get("login", "unknown"), avatar_url=author.get("avatar_url", "")),
                timestamp=self._human_ts(release.get("published_at")),
            ))

        return items[:10]  # cap at 10 items for display

    # ------------------------------------------------------------------
    # LLM synthesis
    # ------------------------------------------------------------------

    async def _review_recent_files(self, owner: str, repo: str) -> str:
        """Get brief review highlights for the 3 most recently modified files."""
        review_svc = ReviewService()
        try:
            commits = await fetch_recent_commits(owner, repo, limit=5)
            # Extract unique file paths from recent commits
            seen: list[str] = []
            for commit in commits:
                for file_info in commit.get("files", [])[:2]:
                    path = file_info.get("filename", "")
                    if path and path not in seen and not path.endswith((".lock", ".sum", ".mod")):
                        seen.append(path)
                if len(seen) >= 2:
                    break

            if not seen:
                return "No recent file changes available for review."

            reviews = await asyncio.gather(
                *[review_svc.review_file(owner, repo, p) for p in seen[:2]],
                return_exceptions=True,
            )

            highlights = []
            for r in reviews:
                if not isinstance(r, Exception):
                    review_data = r.get("review", {})
                    highlights.append(f"{r['file']}: {review_data.get('summary', 'No summary')}")

            return "; ".join(highlights) if highlights else "Recent files reviewed without notable findings."
        except Exception as exc:
            logger.warning("Recent file review failed: %s", exc)
            return "Recent file review could not be completed."

    async def _synthesise_insights(
        self,
        owner: str, repo: str,
        health_result: Any,
        triage_result: dict[str, Any],
        readme_score: int, security_score: int,
        cicd_score: int, contribution_score: int,
        review_highlights: str,
    ) -> RepoInsights:
        llm = get_llm_client()
        metrics = health_result.raw_metrics

        try:
            result: AssessmentInsightsResponse = await llm.generate(
                prompt_name="full_assessment",
                variables={
                    "owner": owner,
                    "repo": repo,
                    "health_score": str(metrics.get("health_score", 0)),
                    "classification": health_result.repository.classification.value,
                    "readme_score": str(readme_score),
                    "security_score": str(security_score),
                    "cicd_score": str(cicd_score),
                    "contribution_score": str(contribution_score),
                    "health_metrics_json": json.dumps({k: v for k, v in metrics.items() if k != "contributors"}, indent=2),
                    "triage_summary": triage_result.get("summary", "No triage data"),
                    "file_review_highlights": review_highlights,
                },
                response_model=AssessmentInsightsResponse,
                temperature=0.3,
            )
        except Exception as exc:
            logger.warning("Assessment synthesis LLM failed: %s", exc)
            result = AssessmentInsightsResponse(
                summary=f"Repository assessed with health score {metrics.get('health_score', 0)}/100.",
                strengths=health_result.insights.strengths,
                risks=health_result.insights.risks,
                recommendations=[],
            )

        # Map to public model
        impact_map = {"High": RecommendationImpact.HIGH, "Medium": RecommendationImpact.MEDIUM, "Low": RecommendationImpact.LOW}
        cat_map = {"Security": RecommendationCategory.SECURITY, "Documentation": RecommendationCategory.DOCUMENTATION, "Activity": RecommendationCategory.ACTIVITY, "Code Quality": RecommendationCategory.CODE_QUALITY}
        recs = [Recommendation(title=r.title, description=r.description, impact=impact_map.get(r.impact, RecommendationImpact.MEDIUM), category=cat_map.get(r.category, RecommendationCategory.ACTIVITY)) for r in result.recommendations]

        return RepoInsights(summary=result.summary, strengths=result.strengths, risks=result.risks, recommendations=recs)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _human_ts(iso_string: str | None) -> str:
        if not iso_string:
            return "recently"
        try:
            dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
            days = (datetime.now(tz=timezone.utc) - dt).days
            if days == 0: return "today"
            if days == 1: return "1 day ago"
            if days < 7: return f"{days} days ago"
            if days < 30: return f"{days // 7} week(s) ago"
            return f"{days // 30} month(s) ago"
        except Exception:
            return "recently"
