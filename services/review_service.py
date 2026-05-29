"""
services/review_service.py
--------------------------
Phase 3 — File and Pull Request Code Review.

review_file():          Fetch raw content → LLM review → structured result
review_pull_request():  Fetch all changed files → per-file reviews (concurrent)
                        → LLM PR synthesis → final verdict
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from gitpulse_mcp.github.files import fetch_file_content
from gitpulse_mcp.github.pulls import estimate_diff_tokens, fetch_pr_detail, fetch_pr_files
from gitpulse_mcp.llm.client import get_llm_client
from gitpulse_mcp.llm.schemas import FileReviewResponse, PRReviewResponse

logger = logging.getLogger(__name__)

# Token budget per file before we truncate the diff sent to the LLM
_MAX_DIFF_TOKENS_PER_FILE = 3000
# Max files reviewed per PR (avoids runaway API cost on 100-file PRs)
_MAX_FILES_PER_PR = 15


def _detect_language(path: str) -> str:
    ext_map = {
        ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript",
        ".js": "JavaScript", ".jsx": "JavaScript", ".java": "Java",
        ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
        ".cs": "C#", ".cpp": "C++", ".c": "C", ".swift": "Swift",
        ".kt": "Kotlin", ".dart": "Dart", ".sh": "Shell",
        ".md": "Markdown", ".yml": "YAML", ".yaml": "YAML", ".json": "JSON",
    }
    for ext, lang in ext_map.items():
        if path.endswith(ext):
            return lang
    return "Unknown"


class ReviewService:
    """Phase 3 service: Code review for files and pull requests."""

    # ------------------------------------------------------------------
    # File review
    # ------------------------------------------------------------------

    async def review_file(self, owner: str, repo: str, path: str, ref: str = "HEAD") -> dict[str, Any]:
        logger.info("Reviewing file %s in %s/%s@%s", path, owner, repo, ref)
        file_data = await fetch_file_content(owner, repo, path, ref)
        language = _detect_language(path)
        truncated_notice = "\n[NOTE: File was truncated to 100KB for review]" if file_data["truncated"] else ""

        llm = get_llm_client()
        try:
            result: FileReviewResponse = await llm.generate(
                prompt_name="review_file",
                variables={
                    "file_path": path,
                    "language": language,
                    "size_bytes": str(file_data["size_bytes"]),
                    "truncated_notice": truncated_notice,
                    "file_content": file_data["content"],
                },
                response_model=FileReviewResponse,
                temperature=0.4,
            )
        except Exception as exc:
            logger.warning("LLM file review failed for %s: %s", path, exc)
            result = FileReviewResponse(
                summary=f"Review of {path} could not be completed: {exc}",
                strengths=[], issues=[], suggestions=[], overall_quality_score=50,
            )

        return {
            "file": path,
            "language": language,
            "size_bytes": file_data["size_bytes"],
            "truncated": file_data["truncated"],
            "review": result.model_dump(),
        }

    # ------------------------------------------------------------------
    # PR review
    # ------------------------------------------------------------------

    async def review_pull_request(self, owner: str, repo: str, pr_number: int) -> dict[str, Any]:
        logger.info("Reviewing PR #%d in %s/%s", pr_number, owner, repo)

        pr_detail, pr_files = await asyncio.gather(
            fetch_pr_detail(owner, repo, pr_number),
            fetch_pr_files(owner, repo, pr_number),
        )

        # Filter to reviewable files (skip deletes, binaries, large diffs)
        reviewable = [
            f for f in pr_files[:_MAX_FILES_PER_PR]
            if f.get("status") != "removed" and f.get("patch")
        ]

        if not reviewable:
            return {
                "pr_number": pr_number,
                "title": pr_detail.get("title", ""),
                "verdict": "COMMENT",
                "summary": "No reviewable file changes found (only deletions or binary files).",
                "file_reviews": [],
                "highlights": [],
                "blockers": [],
                "suggestions": [],
            }

        # Run per-file reviews concurrently (each is a lightweight diff review)
        file_reviews = await asyncio.gather(
            *[self._review_diff(f) for f in reviewable],
            return_exceptions=True,
        )

        # Filter out any exceptions (failed individual file reviews)
        clean_reviews = []
        for review, file_info in zip(file_reviews, reviewable):
            if isinstance(review, Exception):
                logger.warning("File review failed for %s: %s", file_info["filename"], review)
                clean_reviews.append({"file": file_info["filename"], "error": str(review)})
            else:
                clean_reviews.append(review)

        # PR-level synthesis
        pr_metadata = {
            "number": pr_number,
            "title": pr_detail.get("title", ""),
            "body": (pr_detail.get("body") or "")[:500],
            "author": pr_detail.get("user", {}).get("login", "unknown"),
            "files_changed": len(pr_files),
            "additions": sum(f.get("additions", 0) for f in pr_files),
            "deletions": sum(f.get("deletions", 0) for f in pr_files),
            "base_branch": pr_detail.get("base", {}).get("ref", "main"),
        }

        llm = get_llm_client()
        try:
            synthesis: PRReviewResponse = await llm.generate(
                prompt_name="review_pr",
                variables={
                    "pr_metadata_json": json.dumps(pr_metadata, indent=2),
                    "file_reviews_json": json.dumps(clean_reviews, indent=2),
                },
                response_model=PRReviewResponse,
                temperature=0.3,
            )
        except Exception as exc:
            logger.warning("PR synthesis failed: %s", exc)
            synthesis = PRReviewResponse(
                verdict="COMMENT",
                summary=f"Reviewed {len(clean_reviews)} files. Synthesis failed: {exc}",
                highlights=[], blockers=[], suggestions=[],
            )

        return {
            "pr_number": pr_number,
            "title": pr_detail.get("title", ""),
            "author": pr_metadata["author"],
            "stats": {"files": len(pr_files), "additions": pr_metadata["additions"], "deletions": pr_metadata["deletions"]},
            "verdict": synthesis.verdict,
            "summary": synthesis.summary,
            "highlights": synthesis.highlights,
            "blockers": [b.model_dump() for b in synthesis.blockers],
            "suggestions": [s.model_dump() for s in synthesis.suggestions],
            "test_coverage_comment": synthesis.test_coverage_comment,
            "documentation_comment": synthesis.documentation_comment,
            "file_reviews": clean_reviews,
        }

    async def _review_diff(self, file_info: dict[str, Any]) -> dict[str, Any]:
        """Review a single file's diff from a PR."""
        filename = file_info["filename"]
        patch = file_info.get("patch", "")
        language = _detect_language(filename)

        # Truncate very large diffs to stay within token budget
        if len(patch) // 4 > _MAX_DIFF_TOKENS_PER_FILE:
            patch = patch[:_MAX_DIFF_TOKENS_PER_FILE * 4] + "\n... [diff truncated]"

        llm = get_llm_client()
        try:
            result: FileReviewResponse = await llm.generate(
                prompt_name="review_file",
                variables={
                    "file_path": filename,
                    "language": language,
                    "size_bytes": str(file_info.get("changes", 0)) + " changed lines",
                    "truncated_notice": "",
                    "file_content": f"[DIFF]\n{patch}",
                },
                response_model=FileReviewResponse,
                temperature=0.4,
            )
        except Exception as exc:
            result = FileReviewResponse(
                summary=f"Could not review {filename}: {exc}",
                strengths=[], issues=[], suggestions=[], overall_quality_score=50,
            )

        return {
            "file": filename,
            "language": language,
            "status": file_info.get("status", "modified"),
            "additions": file_info.get("additions", 0),
            "deletions": file_info.get("deletions", 0),
            "review": result.model_dump(),
        }
