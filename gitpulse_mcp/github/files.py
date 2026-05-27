"""
github/files.py
---------------
Fetches raw file content and directory listings for code review.

Endpoints used:
  GET /repos/{owner}/{repo}/contents/{path}    — file content (base64 encoded)
  GET /repos/{owner}/{repo}/contents/          — root directory listing

The review_file() tool uses fetch_file_content() to get the source code
before sending it to the LLM for review.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

from gitpulse_mcp.github.client import get_client

logger = logging.getLogger(__name__)

# File size safety limit — we won't attempt to review files larger than this.
# Anything bigger needs chunking which is handled in the service layer.
MAX_FILE_BYTES = 100_000  # ~100 KB


async def fetch_file_content(
    owner: str,
    repo: str,
    path: str,
    ref: str = "HEAD",
) -> dict[str, Any]:
    """
    Fetch the content of a single file from the repository.

    Args:
        owner:  Repository owner login.
        repo:   Repository name.
        path:   File path relative to repo root e.g. "src/utils/auth.py"
        ref:    Branch, tag, or commit SHA (default: HEAD).

    Returns:
        {
            "path": str,
            "content": str,          # decoded UTF-8 text
            "size_bytes": int,
            "sha": str,              # blob SHA
            "encoding": str,         # always "base64" from GitHub
            "truncated": bool,       # True if content was truncated to MAX_FILE_BYTES
        }

    Raises:
        NotFoundError:  If the file path doesn't exist at the given ref.
        ValueError:     If the path points to a directory, not a file.
        UnicodeDecodeError: If the file is binary (non-UTF-8).
    """
    client = get_client()
    raw: dict[str, Any] = await client.get(
        f"/repos/{owner}/{repo}/contents/{path}",
        params={"ref": ref},
    )

    if raw.get("type") == "dir":
        raise ValueError(
            f"Path '{path}' is a directory. "
            "Use fetch_directory_listing() to list its contents."
        )

    # GitHub returns file content as base64-encoded string with newlines
    encoded_content = raw.get("content", "")
    raw_bytes = base64.b64decode(encoded_content.replace("\n", ""))

    truncated = False
    if len(raw_bytes) > MAX_FILE_BYTES:
        raw_bytes = raw_bytes[:MAX_FILE_BYTES]
        truncated = True
        logger.warning(
            "File %s/%s/%s truncated to %d bytes for review",
            owner, repo, path, MAX_FILE_BYTES,
        )

    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise UnicodeDecodeError(
            "utf-8", raw_bytes, 0, 1,
            f"File '{path}' appears to be binary and cannot be reviewed as text."
        )

    return {
        "path": path,
        "content": content,
        "size_bytes": raw.get("size", len(raw_bytes)),
        "sha": raw.get("sha", ""),
        "encoding": "base64",
        "truncated": truncated,
    }


async def fetch_directory_listing(
    owner: str,
    repo: str,
    path: str = "",
    ref: str = "HEAD",
) -> list[dict[str, Any]]:
    """
    List the contents of a directory in the repository.

    Each item in the returned list has:
      - name: filename
      - path: full path from repo root
      - type: 'file' | 'dir' | 'symlink'
      - size: file size in bytes (0 for dirs)
      - sha: blob/tree SHA

    Used to discover existing community health files (SECURITY.md,
    CONTRIBUTING.md, CODE_OF_CONDUCT.md) for the quality checks.
    """
    client = get_client()
    contents = await client.get(
        f"/repos/{owner}/{repo}/contents/{path}",
        params={"ref": ref},
    )
    if isinstance(contents, list):
        return contents
    # Single file returned (path pointed to a file, not a dir)
    return [contents]


async def check_file_exists(
    owner: str,
    repo: str,
    path: str,
    ref: str = "HEAD",
) -> bool:
    """
    Return True if the file at `path` exists in the repository.

    Used by the quality check rules to verify presence of README,
    SECURITY.md, CONTRIBUTING.md, etc.
    """
    try:
        client = get_client()
        await client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
        )
        return True
    except Exception:
        return False


async def list_workflows(owner: str, repo: str) -> list[dict[str, Any]]:
    """
    List GitHub Actions workflow files in .github/workflows/.

    Returns [] if the directory doesn't exist (no CI/CD configured).
    Used by the CI/CD quality checks.
    """
    try:
        entries = await fetch_directory_listing(owner, repo, ".github/workflows")
        return [e for e in entries if e.get("name", "").endswith(".yml") or e.get("name", "").endswith(".yaml")]
    except Exception:
        return []
