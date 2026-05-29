"""
main.py
-------
GitPulse AI MCP Server — entry point.

All tool dispatch now goes through the tools/ layer which handles input
validation. Services handle business logic. This file only wires the MCP
protocol plumbing.

Transport:
  - Development / Claude Desktop: stdio (this file)
  - Remote / Production: SSE via a FastAPI wrapper (future extension)

Setup:
  1. Copy .env.example to .env and fill in GITHUB_TOKEN + OPENAI_API_KEY
  2. pip install -e ".[dev]"
  3. python -m gitpulse_mcp.main
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("gitpulse_mcp")

server = Server("gitpulse-health-assistant")

# ---------------------------------------------------------------------------
# Tool definitions (schema shown to AI clients)
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
                "owner": {"type": "string", "description": "Repository owner login e.g. 'facebook'"},
                "repo":  {"type": "string", "description": "Repository name e.g. 'react'"},
            },
            "required": ["owner", "repo"],
        },
    ),
    Tool(
        name="review_file",
        description=(
            "Review a specific file in a GitHub repository for code quality, "
            "naming conventions, documentation, complexity, and potential bugs. "
            "Returns structured strengths, issues (with severity), and suggestions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner login"},
                "repo":  {"type": "string", "description": "Repository name"},
                "path":  {"type": "string", "description": "File path from repo root e.g. 'src/utils/auth.py'"},
                "ref":   {"type": "string", "description": "Branch, tag, or commit SHA (default: HEAD)", "default": "HEAD"},
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
                "owner":     {"type": "string", "description": "Repository owner login"},
                "repo":      {"type": "string", "description": "Repository name"},
                "pr_number": {"type": "integer", "description": "Pull request number"},
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
                "owner":      {"type": "string", "description": "Repository owner login"},
                "repo":       {"type": "string", "description": "Repository name"},
                "max_issues": {"type": "integer", "description": "Maximum issues to analyse (default: 50, max: 100)", "default": 50},
            },
            "required": ["owner", "repo"],
        },
    ),
    Tool(
        name="full_repo_assessment",
        description=(
            "Run a comprehensive assessment combining health analysis, issue triage, "
            "and code quality indicators. Produces the complete RepoDetails structure "
            "including scored quality checks (README, security, CI/CD, contribution health), "
            "contributor profiles, activity timeline, and AI-generated insights. "
            "Use this when the user wants a full picture or asks to 'assess this repo'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner login"},
                "repo":  {"type": "string", "description": "Repository name"},
            },
            "required": ["owner", "repo"],
        },
    ),
]


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    import json

    try:
        result = await _dispatch(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except NotFoundError as exc:
        return [TextContent(
            type="text",
            text=f"Repository not found: {exc.url}. "
                 "Verify the owner and repo name are correct and the repository is public.",
        )]
    except RateLimitError as exc:
        import time
        wait_mins = max(1, (exc.reset_at - int(time.time())) // 60)
        return [TextContent(
            type="text",
            text=f"GitHub API rate limit reached. Resets in ~{wait_mins} minute(s). Please retry shortly.",
        )]
    except GitHubError as exc:
        return [TextContent(type="text", text=f"GitHub API error ({exc.status_code}): {exc}")]
    except ValueError as exc:
        return [TextContent(type="text", text=f"Invalid input: {exc}")]
    except Exception as exc:
        logger.exception("Unexpected error in tool '%s'", name)
        return [TextContent(type="text", text=f"Unexpected error: {exc}. Check server logs for details.")]


async def _dispatch(name: str, args: dict) -> dict:
    """Route to the tools/ layer — each tool module owns its own validation."""
    if name == "get_repo_health":
        from gitpulse_mcp.tools.health import run_get_repo_health
        return await run_get_repo_health(args)

    if name == "review_file":
        from gitpulse_mcp.tools.review import run_review_file
        return await run_review_file(args)

    if name == "review_pull_request":
        from gitpulse_mcp.tools.review import run_review_pull_request
        return await run_review_pull_request(args)

    if name == "triage_issues":
        from gitpulse_mcp.tools.triage import run_triage_issues
        return await run_triage_issues(args)

    if name == "full_repo_assessment":
        from gitpulse_mcp.tools.assessment import run_full_repo_assessment
        return await run_full_repo_assessment(args)

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
    asyncio.run(_run())


if __name__ == "__main__":
    run()
