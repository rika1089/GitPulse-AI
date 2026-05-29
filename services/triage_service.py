"""
services/triage_service.py
--------------------------
Phase 3 — Issue Triage and Classification.

Two-pass approach:
  Pass 1 (rule-based, free):  Pre-classify using labels + age + keywords.
                               Avoids sending every issue to the LLM.
  Pass 2 (LLM):               Send the pre-classified set to the LLM for
                               richer reasoning and recommendations.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from gitpulse_mcp.github.issues import classify_issue_age, fetch_open_issues
from gitpulse_mcp.llm.client import get_llm_client
from gitpulse_mcp.llm.schemas import TriageResponse

logger = logging.getLogger(__name__)

# Keywords that signal a high-priority bug in the issue title/body
_BUG_KEYWORDS = {"crash", "error", "broken", "regression", "fail", "exception", "panic", "security", "vulnerability", "exploit", "overflow", "null", "undefined"}
_DOC_KEYWORDS = {"docs", "documentation", "readme", "guide", "typo", "spelling", "grammar", "example"}
_STALE_DAYS = 90


class TriageService:
    """Phase 3 service: Issue triage with rule-based pre-pass + LLM synthesis."""

    async def triage(self, owner: str, repo: str, max_issues: int = 50) -> dict[str, Any]:
        logger.info("Triaging issues for %s/%s (max=%d)", owner, repo, max_issues)
        issues = await fetch_open_issues(owner, repo, max_issues=max_issues)

        if not issues:
            return {
                "owner": owner, "repo": repo, "issue_count": 0,
                "summary": "No open issues found.", "categories": {},
                "recommendations": ["Great — no open issues to triage!"],
                "health_signals": {"estimated_backlog_health": "Good"},
            }

        # Rule-based pre-classification
        pre_classified = self._pre_classify(issues)

        # Build compact issue summaries for LLM (avoid sending full bodies)
        issue_summaries = [
            {
                "number": i["number"],
                "title": i["title"],
                "labels": [lbl["name"] for lbl in i.get("labels", [])],
                "comments": i.get("comments", 0),
                "age": classify_issue_age(i.get("created_at")),
                "pre_classification": pre_classified.get(i["number"], "unclassified"),
            }
            for i in issues
        ]

        llm = get_llm_client()
        try:
            result: TriageResponse = await llm.generate(
                prompt_name="triage_issues",
                variables={
                    "owner": owner,
                    "repo": repo,
                    "issue_count": str(len(issues)),
                    "issues_json": json.dumps(issue_summaries, indent=2),
                },
                response_model=TriageResponse,
                temperature=0.2,
            )
        except Exception as exc:
            logger.warning("LLM triage failed: %s. Using rule-based result.", exc)
            result = self._rule_based_triage(issues, pre_classified)

        return {
            "owner": owner,
            "repo": repo,
            "issue_count": len(issues),
            "summary": result.summary,
            "categories": result.categories.model_dump(),
            "recommendations": result.recommendations,
            "health_signals": result.health_signals.model_dump(),
        }

    def _pre_classify(self, issues: list[dict[str, Any]]) -> dict[int, str]:
        """
        Rule-based pre-classification. Returns {issue_number: category_label}.
        Used to seed the LLM prompt with our best guess.
        """
        result = {}
        now = datetime.now(tz=timezone.utc)

        for issue in issues:
            number = issue["number"]
            title_lower = issue.get("title", "").lower()
            body_lower = (issue.get("body") or "").lower()
            labels = {lbl["name"].lower() for lbl in issue.get("labels", [])}
            created = issue.get("created_at", "")

            # Parse age
            age_days = 0
            if created:
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    age_days = (now - dt).days
                except ValueError:
                    pass

            # Classification priority
            if any(kw in title_lower or kw in body_lower for kw in _BUG_KEYWORDS):
                result[number] = "high_priority_bug"
            elif age_days > _STALE_DAYS:
                result[number] = "stale"
            elif "good first issue" in labels or "good-first-issue" in labels:
                result[number] = "good_first_issue"
            elif any(kw in title_lower for kw in _DOC_KEYWORDS):
                result[number] = "documentation_request"
            else:
                result[number] = "feature_request"

        return result

    def _rule_based_triage(
        self, issues: list[dict[str, Any]], pre_classified: dict[int, str]
    ) -> TriageResponse:
        """Fallback triage result entirely from rules, no LLM required."""
        from gitpulse_mcp.llm.schemas import TriageCategories, HealthSignals, TriagedBug, TriagedStale
        bugs, good_first, stale_nums, docs, features = [], [], [], [], []

        for issue in issues:
            n = issue["number"]
            t = issue["title"]
            cls = pre_classified.get(n, "feature_request")
            if cls == "high_priority_bug":
                bugs.append(TriagedBug(number=n, title=t, reason="Contains bug keywords", suggested_labels=["bug"]))
            elif cls == "stale":
                stale_nums.append(TriagedStale(number=n, title=t, age_days=0, action="needs-info"))
            elif cls == "good_first_issue":
                good_first.append({"number": n, "title": t, "reason": "Labeled as good first issue"})
            elif cls == "documentation_request":
                docs.append(n)
            else:
                features.append(n)

        from gitpulse_mcp.llm.schemas import TriagedGoodFirst
        good_first_models = [TriagedGoodFirst(**g) for g in good_first]
        cats = TriageCategories(high_priority_bugs=bugs, good_first_issues=good_first_models, stale_issues=stale_nums, documentation_requests=docs, feature_requests=features)
        signals = HealthSignals(has_stale_issues=bool(stale_nums), has_unanswered_bugs=bool(bugs), good_first_issue_count=len(good_first_models), estimated_backlog_health="Fair")
        return TriageResponse(summary=f"Triaged {len(issues)} open issues. Found {len(bugs)} bugs, {len(stale_nums)} stale.", categories=cats, recommendations=["Review and close stale issues to keep the backlog clean."], health_signals=signals)
