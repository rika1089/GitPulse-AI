# coding-standards.md
# GitHub Repo Health & Review MCP Assistant — Coding Standards

---

## Code Style Philosophy

The goal of this project's coding standards is **readability over cleverness**. Every file in this codebase should be understandable by:

1. A student encountering Python MCP servers for the first time
2. A future contributor who has never read this code before
3. An automated linting tool that enforces consistency

The guiding principles are:

- **Explicit is better than implicit** — avoid magic; name things clearly
- **One responsibility per function/class** — keep units small and testable
- **Fail loudly** — raise typed exceptions with helpful messages rather than swallowing errors
- **Document intent, not mechanics** — docstrings explain *why*, not *what the code obviously does*

---

## Python Standards

### PEP 8 Compliance

All Python code must comply with [PEP 8](https://peps.python.org/pep-0008/). Key rules enforced:

- Maximum line length: **88 characters** (Black default)
- 2 blank lines between top-level functions/classes
- 1 blank line between methods within a class
- Imports grouped: stdlib → third-party → local, each group separated by a blank line

### Type Hints

Type hints are **mandatory** for all function signatures. Use `from __future__ import annotations` at the top of each file for deferred evaluation.

```python
# ✅ Correct
async def fetch_commits(owner: str, repo: str, since_days: int = 30) -> list[dict]:
    ...

# ❌ Wrong — no type hints
async def fetch_commits(owner, repo, since_days=30):
    ...
```

For complex types, use `typing` module or built-in generics (Python 3.10+):

```python
from typing import Optional

def compute_health_score(
    commits: list[dict],
    open_issues: int,
    closed_issues: int,
) -> tuple[float, str]:
    ...
```

### Docstrings

All public functions, classes, and modules must have docstrings using the **Google style**:

```python
def compute_health_score(commits: list[dict], open_issues: int, closed_issues: int) -> float:
    """Compute a normalized repository health score from 0 to 100.

    The score is weighted across commit activity, issue close rate, and
    PR merge ratio. Higher scores indicate more active maintenance.

    Args:
        commits: List of commit objects from the GitHub API.
        open_issues: Count of currently open issues.
        closed_issues: Count of historically closed issues.

    Returns:
        A float between 0.0 and 100.0 representing repository health.

    Raises:
        ValueError: If both open_issues and closed_issues are zero.
    """
```

### Modularity

- No file should exceed **300 lines**. If it does, split it by responsibility.
- Functions should do **one thing** and be no longer than **40 lines**.
- Avoid deeply nested logic (max 3 levels of indentation). Extract nested blocks into named helper functions.

---

## Naming Conventions

### Files

| Type | Convention | Example |
|------|-----------|---------|
| Module files | `snake_case.py` | `metrics_engine.py`, `prompt_builder.py` |
| Test files | `test_<module>.py` | `test_metrics_engine.py` |
| Prompt templates | `<purpose>.txt` | `code_review.txt`, `health_analysis.txt` |
| Configuration | `snake_case` | `.env.example`, `pyproject.toml` |

### Classes

Use `PascalCase`. Class names should be **nouns** describing what the class *is*:

```python
class RepoHealthReport:       # ✅ Noun, describes data structure
class GitHubAPIClient:        # ✅ Noun, describes service
class FetchCommits:           # ❌ Verb phrase — use a function instead
```

### Functions and Methods

Use `snake_case`. Function names should be **verb phrases** describing what the function *does*:

```python
def fetch_open_issues(owner: str, repo: str) -> list[dict]: ...      # ✅ Clear verb phrase
def compute_issue_close_rate(open: int, closed: int) -> float: ...   # ✅ Clear verb phrase
def issues(owner, repo): ...                                          # ❌ Ambiguous noun
def get(owner, repo): ...                                             # ❌ Too generic
```

### Variables

Use `snake_case`. Names should be **descriptive**, not abbreviated:

```python
# ✅ Correct
commit_count = len(commits)
issue_close_rate = closed_issues / total_issues
health_classification = "Healthy"

# ❌ Wrong
cc = len(commits)
icr = cl / tot
hc = "Healthy"
```

### Constants

Use `UPPER_SNAKE_CASE` and define in `utils/config.py` or at the module top level:

```python
DEFAULT_LOOKBACK_DAYS = 30
HEALTH_SCORE_WEIGHTS = {
    "activity": 0.30,
    "pr_resolution": 0.25,
    "issue_resolution": 0.25,
    "contributor_activity": 0.20,
}
MAX_RETRIES = 3
```

### MCP Tool Functions

Tool handler names use `snake_case` and must match their registered MCP tool name exactly:

```python
@mcp.tool()
async def get_repo_health(owner: str, repo: str) -> RepoHealthReport:
    ...

@mcp.tool()
async def triage_issues(owner: str, repo: str) -> TriageReport:
    ...
```

---

## Folder Organization Rules

Each folder in the project has a single, clearly defined responsibility:

- `tools/` — thin handlers only. A tool function should call service functions and return a result. **No business logic inside tool handlers.**
- `services/` — all computation, LLM calls, report generation. **No GitHub API calls from services directly.**
- `github/` — all GitHub API communication. **No LLM calls from this layer.**
- `prompts/` — plain-text templates only. **No Python logic inside prompt files.**
- `models/` — Pydantic data models only. **No methods that call external services.**
- `utils/` — stateless helper utilities. **No domain-specific logic.**

This separation means any component can be tested and replaced in isolation.

---

## MCP Tool Standards

### Tool Naming

Tool names must be:
- `snake_case`
- Verb-first (`get_`, `review_`, `triage_`, `analyze_`)
- Descriptive enough that an AI assistant can infer their purpose from the name alone

```python
# ✅ Good tool names
get_repo_health
review_pull_request
triage_issues
full_repo_assessment

# ❌ Bad tool names
health          # Too vague
repo            # Too vague
do_review       # Redundant "do"
```

### Structured Outputs

Every tool must return a **Pydantic model**, not a raw dict or string:

```python
# ✅ Correct — returns typed Pydantic model
@mcp.tool()
async def get_repo_health(owner: str, repo: str) -> RepoHealthReport:
    ...

# ❌ Wrong — returns untyped dict
@mcp.tool()
async def get_repo_health(owner: str, repo: str) -> dict:
    ...
```

Pydantic models ensure the MCP SDK can generate accurate JSON schemas for AI clients.

### Input Validation

Validate inputs before making any API calls:

```python
@mcp.tool()
async def get_repo_health(owner: str, repo: str) -> RepoHealthReport:
    if not owner or not owner.strip():
        raise ValueError("owner cannot be empty")
    if not repo or not repo.strip():
        raise ValueError("repo cannot be empty")
    ...
```

### Exception Handling in Tools

Tools must catch all expected exceptions and raise MCP-compatible errors. Never let a raw exception bubble to the MCP client:

```python
@mcp.tool()
async def get_repo_health(owner: str, repo: str) -> RepoHealthReport:
    try:
        ...
    except RepositoryNotFoundError:
        raise ValueError(f"Repository {owner}/{repo} not found or is private.")
    except RateLimitError as e:
        raise RuntimeError(f"GitHub API rate limit exceeded. Retry after {e.reset_time}.")
    except Exception as e:
        logger.error(f"Unexpected error in get_repo_health: {e}", exc_info=True)
        raise RuntimeError("An unexpected error occurred during health analysis.")
```

---

## Error Handling Standards

All service-layer functions must define and raise **typed custom exceptions** from `utils/exceptions.py`:

```python
# utils/exceptions.py

class GitHubRepoHealthError(Exception):
    """Base exception for all project errors."""

class RepositoryNotFoundError(GitHubRepoHealthError):
    """Raised when a repository does not exist or cannot be accessed."""

class RateLimitError(GitHubRepoHealthError):
    """Raised when GitHub API rate limit is hit."""
    def __init__(self, reset_time: int):
        self.reset_time = reset_time
        super().__init__(f"Rate limit exceeded. Resets at {reset_time}.")

class AuthenticationError(GitHubRepoHealthError):
    """Raised when GitHub token is missing or invalid."""

class LLMError(GitHubRepoHealthError):
    """Raised when LLM API call fails."""
```

Never catch broad `Exception` in service functions — only in tool handlers as a last resort.

---

## Logging Standards

Use Python's standard `logging` module, configured centrally in `utils/logger.py`. Never use `print()` in production code.

```python
# utils/logger.py
import logging
import os

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    level = logging.DEBUG if os.getenv("DEBUG") == "1" else logging.INFO
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    ))
    logger.addHandler(handler)
    return logger
```

### Log Level Usage

| Level | When to Use | Example |
|-------|------------|---------|
| `DEBUG` | Detailed tracing for development | `logger.debug(f"Fetched {len(commits)} commits for {owner}/{repo}")` |
| `INFO` | Normal operational events | `logger.info(f"Starting health analysis for {owner}/{repo}")` |
| `WARNING` | Unexpected but recoverable conditions | `logger.warning(f"Rate limit approaching: {remaining} requests left")` |
| `ERROR` | Failures that affect a tool call | `logger.error(f"GitHub API returned 404 for {owner}/{repo}")` |

**Never log:** API keys, tokens, or any secret values. Sanitize log messages that include headers or credentials.

---

## Prompt Engineering Standards

### Reusable Prompt Templates

All LLM prompts are stored as plain-text files in `prompts/`. They must use `{placeholder}` syntax for variable injection:

```
# prompts/health_analysis.txt

You are a senior software engineering analyst reviewing GitHub repository health data.

Repository: {owner}/{repo}
Stars: {stars}
Forks: {forks}
Commits (last 30 days): {recent_commits}
Open Issues: {open_issues}
Closed Issues: {closed_issues}
Open PRs: {open_prs}
Merged PRs: {merged_prs}
Health Score: {health_score}/100

Based on this data, provide a repository health assessment with the following JSON structure:
{
  "classification": "Healthy | Stagnant | At Risk | Archived",
  "summary": "2-3 sentence overview",
  "strengths": ["..."],
  "risks": ["..."],
  "recommendations": ["..."]
}

Respond with ONLY the JSON object. Do not include markdown code fences.
```

### Structured LLM Outputs

Always request structured JSON from the LLM:

1. Specify the exact JSON schema in the prompt
2. Instruct the model to return ONLY JSON with no preamble or fences
3. Parse with `json.loads()` and validate with Pydantic after receiving the response

```python
# In services/llm_client.py
import json
from models.repo_health import RepoHealthLLMOutput

response_text = call_llm(prompt)
try:
    data = json.loads(response_text)
    return RepoHealthLLMOutput(**data)
except (json.JSONDecodeError, ValidationError) as e:
    logger.error(f"Failed to parse LLM response: {e}\nRaw: {response_text}")
    raise LLMError("LLM returned an unparseable response.")
```

### Prompt Version Control

Prompts are plain text files committed alongside code. When updating a prompt, note the change in the commit message:

```
docs: update health_analysis prompt to request severity ratings in risks list
```

---

## Git & Commit Standards

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

**Types:**

| Type | When to Use |
|------|------------|
| `feat` | New feature or MCP tool |
| `fix` | Bug fix |
| `refactor` | Code restructuring with no behavior change |
| `docs` | Documentation changes (prompts, markdown, docstrings) |
| `test` | Adding or fixing tests |
| `chore` | Dependency updates, config changes |
| `perf` | Performance improvement |

**Examples:**

```
feat(tools): add full_repo_assessment() orchestrator tool
fix(github): handle 403 rate limit response with exponential backoff
refactor(metrics): extract issue_close_rate calculation to dedicated function
docs(prompts): update code_review.txt with SOLID principles checklist
test(services): add unit tests for compute_health_score edge cases
chore(deps): upgrade httpx to 0.27.0
```

---

## Branching Strategy

| Branch | Purpose | Merge Target |
|--------|---------|-------------|
| `main` | Production-ready code; always stable | — |
| `dev` | Integration branch for feature work | `main` (via PR) |
| `feature/<name>` | Individual feature development | `dev` (via PR) |
| `fix/<name>` | Bug fix branches | `dev` or `main` |
| `docs/<name>` | Documentation-only changes | `main` directly |

**Rules:**
- Never commit directly to `main`
- All `dev` → `main` merges require a pull request with at least one review
- Feature branches should be short-lived (1–5 days)
- Branch names use `kebab-case`: `feature/issue-triage-engine`, `fix/rate-limit-backoff`

---

## Testing Standards

### Unit Tests

Every service function must have a corresponding unit test. Tests should be **fast** (no real network calls) and **isolated** (mock all dependencies):

```python
# tests/unit/test_metrics_engine.py

from unittest.mock import patch
from services.metrics_engine import compute_issue_close_rate

def test_issue_close_rate_normal():
    rate = compute_issue_close_rate(open_issues=10, closed_issues=90)
    assert abs(rate - 0.90) < 0.001

def test_issue_close_rate_zero_total():
    with pytest.raises(ValueError, match="No issues found"):
        compute_issue_close_rate(open_issues=0, closed_issues=0)
```

### Mock Testing (GitHub API)

Use `unittest.mock.patch` to replace GitHub API calls with fixture data:

```python
@patch("github.client.GitHubAPIClient.fetch_commits")
def test_health_analyzer_active_repo(mock_fetch):
    mock_fetch.return_value = load_fixture("mock_commits_active.json")
    report = analyze_repo_health("owner", "repo")
    assert report.classification == "Healthy"
    assert report.health_score >= 70
```

### Coverage Target

Aim for **80%+ code coverage** across `services/` and `github/`. Use `pytest-cov`:

```bash
pytest --cov=services --cov=github --cov-report=term-missing
```

---

## Linting & Formatting

All three tools are configured in `pyproject.toml` and enforced via pre-commit hooks:

### Black (Formatter)

```toml
[tool.black]
line-length = 88
target-version = ["py310"]
```

Run: `black .`

### Ruff (Linter — replaces flake8 + isort)

```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]
```

Run: `ruff check .`

### isort (Import Sorting — handled by Ruff)

Imports must be sorted: stdlib → third-party → local, each group separated by one blank line.

### Pre-commit Hook Setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.0.0
    hooks: [{ id: black }]
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.4.0
    hooks: [{ id: ruff, args: [--fix] }]
```

---

## Security Coding Practices

| Practice | Implementation |
|---------|---------------|
| No hardcoded secrets | All tokens and API keys loaded from environment variables only |
| `.env` in `.gitignore` | The `.env` file is never committed; `.env.example` is committed with empty values |
| Token redaction in logs | Logger configured to never log `Authorization` headers or `GITHUB_TOKEN` values |
| Input sanitization | All `owner` and `repo` inputs stripped and validated; no shell injection via subprocess |
| Prompt injection prevention | Repository content passed as data fields in LLM prompts, not as part of the system instruction |
| Dependency pinning | `requirements.txt` pins exact versions to prevent supply-chain attacks |

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Harmful | Correct Approach |
|-------------|-----------------|-----------------|
| Giant functions (>40 lines) | Impossible to test or understand | Split by single responsibility |
| Duplicated prompt strings | Changes must be made in multiple places | Centralize in `prompts/` as template files |
| Hardcoded configuration values | Breaks portability; security risk | Use environment variables via `utils/config.py` |
| Tightly coupled modules | `github/` calling `services/llm_client.py` directly | Always pass data upward; keep layers strictly separated |
| Returning raw dicts from tools | Type-unsafe; breaks MCP schema generation | Return Pydantic models exclusively |
| `print()` for debugging | Not configurable; pollutes stdout (which MCP uses) | Always use `logger.debug()` |
| Catching bare `Exception` in services | Hides real errors | Define and raise typed custom exceptions |
| Inline SQL or API URLs | Hard to maintain and test | Centralize in constants and dedicated client files |
