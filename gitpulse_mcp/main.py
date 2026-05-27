"""
main.py
-------
GitPulse AI MCP Server — entry point.

This file registers all five MCP tools and starts the server using stdio
transport (for local Claude Desktop / MCP Inspector usage).

All tool handlers are thin wrappers — they validate inputs, delegate to
the service layer, and return JSON-serialisable dicts. Error handling at
this layer converts domain exceptions into clean error messages that the
AI client can present to the user.

Transport:
  - Development: stdio (this file)
  - Production: SSE via FastAPI (future Phase 3 extension)

Setup:
  1. Copy .env.example to .env and fill in GITHUB_TOKEN + OPENAI_API_KEY
  2. pip install -e ".[dev]"
  3. python -m gitpulse_mcp.main
     OR add to Claude Desktop config (see README)
"""

from __future__ import annotations

import asyncio
import logging
import sys

import mcp.server.stdio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import ServerCapabilities, TextContent, Tool

from gitpulse_mcp.github.client import GitHubError, NotFoundError, RateLimitError

# ---------------------------------------------------------------------------
# Logging setup — writes to stderr so it doesn't pollute MCP stdio channel
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("gitpulse_mcp")

# ---------------------------------------------------------------------------
# MCP Server instance
# ---------------------------------------------------------------------------

server = Server("gitpulse-health-assistant")

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS: list[Tool] = [
    Tool(
        name="get_repo_health",
        description=(
            "Analyse the health of a public GitHub repository. "
            "Returns a health score (0-100), classification (Healthy/Stagnant/At Risk/Archived), "
            "and an AI-generated narrative with strengths, risks, and recommendations. "
            "Use this when the user asks about a repo's health, activity, or maintainability."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner login e.g. 'facebook'",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name e.g. 'react'",
                },
            },
            "required": ["owner", "repo"],
        },
    ),
    Tool(
        name="review_file",
        description=(
            "Review a specific file in a GitHub repository for code quality, "
            "naming conventions, documentation coverage, complexity, and potential bugs. "
            "Returns structured strengths, issues (with severity), and suggestions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner login"},
                "repo": {"type": "string", "description": "Repository name"},
                "path": {
                    "type": "string",
                    "description": "File path from repo root e.g. 'src/utils/auth.py'",
                },
                "ref": {
                    "type": "string",
                    "description": "Branch, tag, or commit SHA (default: HEAD)",
                    "default": "HEAD",
                },
            },
            "required": ["owner", "repo", "path"],
        },
    ),
    Tool(
        name="review_pull_request",
        description=(
            "Review all changed files in a pull request. "
            "Returns a per-file review and an overall PR summary covering "
            "code quality, test coverage, documentation, and potential issues."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner login"},
                "repo": {"type": "string", "description": "Repository name"},
                "pr_number": {
                    "type": "integer",
                    "description": "Pull request number",
                },
            },
            "required": ["owner", "repo", "pr_number"],
        },
    ),
    Tool(
        name="triage_issues",
        description=(
            "Triage and prioritise open issues in a repository. "
            "Classifies issues as: High Priority Bug, Stale, Good First Issue, "
            "Documentation Request, or Feature Request. "
            "Returns a prioritised summary with maintainer recommendations."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner login"},
                "repo": {"type": "string", "description": "Repository name"},
                "max_issues": {
                    "type": "integer",
                    "description": "Maximum issues to analyse (default: 50, max: 100)",
                    "default": 50,
                },
            },
            "required": ["owner", "repo"],
        },
    ),
    Tool(
        name="full_repo_assessment",
        description=(
            "Run a comprehensive assessment combining health analysis, issue triage, "
            "and code quality indicators. Produces the complete RepoDetails data structure "
            "including scored quality checks (README, security, CI/CD, contribution health), "
            "contributor profiles, activity timeline, and AI-generated insights. "
            "This is the most complete view of a repository — use it when the user wants "
            "a full picture or when they ask 'assess this repo'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner login"},
                "repo": {"type": "string", "description": "Repository name"},
            },
            "required": ["owner", "repo"],
        },
    ),
]


# ---------------------------------------------------------------------------
# Tool list handler
# ---------------------------------------------------------------------------


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return TOOLS


# ---------------------------------------------------------------------------
# Tool call handler — dispatches to service layer
# ---------------------------------------------------------------------------


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Central dispatcher for all tool calls.

    All errors are caught here and converted to user-readable TextContent
    so the AI client receives a useful error message rather than a crash.
    """
    import json

    try:
        result = await _dispatch(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except NotFoundError as exc:
        return [TextContent(
            type="text",
            text=f"Repository not found: {exc.url}. "
                 "Make sure the owner and repo name are correct and the repository is public.",
        )]

    except RateLimitError as exc:
        import time
        wait_mins = max(1, (exc.reset_at - int(time.time())) // 60)
        return [TextContent(
            type="text",
            text=f"GitHub API rate limit reached. Resets in approximately {wait_mins} minutes. "
                 "Try again shortly.",
        )]

    except GitHubError as exc:
        return [TextContent(
            type="text",
            text=f"GitHub API error ({exc.status_code}): {exc}",
        )]

    except ValueError as exc:
        return [TextContent(type="text", text=f"Invalid input: {exc}")]

    except Exception as exc:
        logger.exception("Unexpected error in tool '%s': %s", name, exc)
        return [TextContent(
            type="text",
            text=f"An unexpected error occurred: {exc}. "
                 "Please check the server logs for details.",
        )]


async def _dispatch(name: str, args: dict) -> dict:
    """Route tool calls to the appropriate service."""
    # Imports are deferred here so startup doesn't fail if .env is missing
    # (graceful error at call time rather than import time)

    if name == "get_repo_health":
        from gitpulse_mcp.services.health_service import HealthService
        svc = HealthService()
        result = await svc.analyse(args["owner"], args["repo"])
        return result.model_dump(by_alias=True)

    if name == "review_file":
        from gitpulse_mcp.services.review_service import ReviewService
        svc = ReviewService()
        result = await svc.review_file(
            owner=args["owner"],
            repo=args["repo"],
            path=args["path"],
            ref=args.get("ref", "HEAD"),
        )
        return result

    if name == "review_pull_request":
        from gitpulse_mcp.services.review_service import ReviewService
        svc = ReviewService()
        result = await svc.review_pull_request(
            owner=args["owner"],
            repo=args["repo"],
            pr_number=int(args["pr_number"]),
        )
        return result

    if name == "triage_issues":
        from gitpulse_mcp.services.triage_service import TriageService
        svc = TriageService()
        result = await svc.triage(
            owner=args["owner"],
            repo=args["repo"],
            max_issues=int(args.get("max_issues", 50)),
        )
        return result

    if name == "full_repo_assessment":
        from gitpulse_mcp.services.assessment_service import AssessmentService
        svc = AssessmentService()
        result = await svc.assess(args["owner"], args["repo"])
        return result.model_dump(by_alias=True)

    raise ValueError(f"Unknown tool: '{name}'")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def _run() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gitpulse-health-assistant",
                server_version="0.1.0",
                capabilities=ServerCapabilities(tools={}),
            ),
        )


def run() -> None:
    """Entry point called by the `gitpulse` CLI script."""
    asyncio.run(_run())


if __name__ == "__main__":
    run()
