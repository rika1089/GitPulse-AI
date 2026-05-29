"""
github/
-------
GitHub REST API integration layer.

All GitHub API calls go through this package.
No service or tool module should import httpx directly.

Usage:
    from gitpulse_mcp.github.repo import fetch_repo_metadata
    from gitpulse_mcp.github.commits import get_commit_metrics
    from gitpulse_mcp.github.client import get_client, GitHubError
"""
