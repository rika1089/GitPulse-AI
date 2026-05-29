# GitPulse AI — MCP Backend

A Python MCP server that exposes GitHub repository health analysis, AI-assisted
code review, and issue triage as callable tools to Claude and other MCP-compatible
AI clients.

---

## Table of Contents

- [What it does](#what-it-does)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the server](#running-the-server)
- [Connecting to Claude Desktop](#connecting-to-claude-desktop)
- [Testing with MCP Inspector](#testing-with-mcp-inspector)
- [Available tools](#available-tools)
- [Architecture overview](#architecture-overview)
- [Running tests](#running-tests)
- [Troubleshooting](#troubleshooting)

---

## What it does

GitPulse AI analyses public GitHub repositories and surfaces actionable insights:

| Tool | What it produces |
|---|---|
| `get_repo_health` | Health score 0–100, classification, AI narrative |
| `review_file` | Per-file code review with severity-ranked issues |
| `review_pull_request` | PR verdict (APPROVE / REQUEST_CHANGES / COMMENT) + per-file breakdown |
| `triage_issues` | Prioritised issue backlog: bug / stale / good-first-issue classification |
| `full_repo_assessment` | Complete RepoDetails — all four quality sections + timeline + insights |

---

## Project structure

```
GitPulseAI/
├── gitpulse_mcp/
│   ├── __init__.py
│   ├── config.py              # Centralised settings via pydantic-settings
│   ├── main.py                # MCP server entry point
│   │
│   ├── tools/                 # Input validation + dispatch
│   │   ├── health.py
│   │   ├── review.py
│   │   ├── triage.py
│   │   └── assessment.py
│   │
│   ├── services/              # Business logic
│   │   ├── health_service.py
│   │   ├── review_service.py
│   │   ├── triage_service.py
│   │   └── assessment_service.py
│   │
│   ├── github/                # GitHub REST API layer
│   │   ├── client.py          # Async httpx, rate-limit, retry, cache
│   │   ├── repo.py
│   │   ├── commits.py
│   │   ├── issues.py
│   │   ├── pulls.py
│   │   └── files.py
│   │
│   ├── llm/                   # LLM layer
│   │   ├── client.py          # OpenAI wrapper with JSON retry
│   │   ├── schemas.py         # Internal Pydantic models for LLM responses
│   │   ├── report_generator.py
│   │   └── prompts/
│   │       ├── health_narrative.txt
│   │       ├── review_file.txt
│   │       ├── review_pr.txt
│   │       ├── triage_issues.txt
│   │       └── full_assessment.txt
│   │
│   ├── models/                # Public-facing Pydantic models
│   │   ├── repository.py      # Repository, RepoDetails, Contributor …
│   │   ├── review.py          # FileReview, PRReview
│   │   └── triage.py          # TriageReport, TriageCategories
│   │
│   └── cache/
│       └── session_cache.py   # Async in-memory TTL cache
│
├── tests/                     # 121 tests, all passing
├── conftest.py
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Prerequisites

- Python 3.11 or higher
- A GitHub Personal Access Token (classic, `public_repo` scope)
- An OpenAI API key (`gpt-4o-mini` is the default)

---

## Installation

```powershell
# 1. Open a terminal inside GitPulseAI/
cd "C:\Users\Srikar\Desktop\Git Hub\GitPulseAI"

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install the package with dev dependencies
pip install -e ".[dev]"
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```powershell
copy .env.example .env
```

Open `.env` in any editor:

```dotenv
# Required
GITHUB_TOKEN=ghp_your_token_here
OPENAI_API_KEY=sk-your_key_here

# Optional — defaults shown
OPENAI_MODEL=gpt-4o-mini
ACTIVITY_LOOKBACK_DAYS=30
CACHE_TTL_SECONDS=300

# Health score weights — must sum to 1.0
WEIGHT_COMMIT_FREQ=0.30
WEIGHT_PR_MERGE_RATIO=0.25
WEIGHT_ISSUE_CLOSE_RATE=0.25
WEIGHT_CONTRIBUTOR_ACTIVITY=0.20
```

**Getting a GitHub token:**
1. Go to https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. Tick the `public_repo` scope, generate, and paste the token into `.env`

**Getting an OpenAI key:**
1. Go to https://platform.openai.com/api-keys
2. Create a new secret key and paste it into `.env`

---

## Running the server

```powershell
# With .venv active, from GitPulseAI/ root
python -m gitpulse_mcp.main
```

The server listens on **stdio** — it will appear to hang; that is correct.
MCP clients communicate over stdin/stdout.

Verify config loads without errors first:
```powershell
python -c "from gitpulse_mcp.config import settings; print('OK:', settings.openai_model)"
```

---

## Connecting to Claude Desktop

**Step 1 — Find the config file:**

| OS | Path |
|---|---|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |

**Step 2 — Add the GitPulse server entry:**

```json
{
  "mcpServers": {
    "gitpulse": {
      "command": "C:\\Users\\Srikar\\Desktop\\Git Hub\\GitPulseAI\\.venv\\Scripts\\python.exe",
      "args": ["-m", "gitpulse_mcp.main"],
      "cwd": "C:\\Users\\Srikar\\Desktop\\Git Hub\\GitPulseAI"
    }
  }
}
```

> Use the full absolute path. Point `command` at the `.venv` Python so your
> installed packages are found. Use double backslashes on Windows.

**Step 3 — Restart Claude Desktop completely.**

The tools panel should list all 5 GitPulse tools. Try asking Claude:
> *"Analyse the health of the facebook/react repository"*
> *"Review PR #1234 in microsoft/vscode"*
> *"Triage the open issues in pallets/flask"*

---

## Testing with MCP Inspector

MCP Inspector lets you test the server interactively in a browser without
needing Claude Desktop.

```powershell
# Node.js must be installed (https://nodejs.org)
npx @modelcontextprotocol/inspector python -m gitpulse_mcp.main
```

Open http://localhost:5173. All 5 tools appear in the sidebar. Fill in
arguments and click **Run** to call them against real repositories.

**Recommended test sequence to verify everything works end-to-end:**

1. `get_repo_health` → `owner: torvalds` / `repo: linux`
2. `triage_issues` → `owner: microsoft` / `repo: vscode` / `max_issues: 20`
3. `review_file` → `owner: pallets` / `repo: flask` / `path: src/flask/app.py`
4. `full_repo_assessment` → `owner: pallets` / `repo: flask`

---

## Available tools

### `get_repo_health`

| Argument | Type | Required | Description |
|---|---|---|---|
| `owner` | string | yes | GitHub owner login e.g. `facebook` |
| `repo` | string | yes | Repository name e.g. `react` |

Returns `repository` (with `healthScore`, `classification`, `activityStatus`)
and `insights` (with `summary`, `strengths`, `risks`, `recommendations`).

---

### `review_file`

| Argument | Type | Required | Default | Description |
|---|---|---|---|---|
| `owner` | string | yes | — | GitHub owner login |
| `repo` | string | yes | — | Repository name |
| `path` | string | yes | — | File path from repo root |
| `ref` | string | no | `HEAD` | Branch, tag, or commit SHA |

Returns `review` with `summary`, `strengths`, `issues` (each with `severity`
HIGH / MEDIUM / LOW), `suggestions`, and `overall_quality_score`.

---

### `review_pull_request`

| Argument | Type | Required | Description |
|---|---|---|---|
| `owner` | string | yes | GitHub owner login |
| `repo` | string | yes | Repository name |
| `pr_number` | integer | yes | Pull request number |

Returns `verdict` (APPROVE / REQUEST_CHANGES / COMMENT), `summary`,
`highlights`, `blockers`, `suggestions`, and per-file `file_reviews`.

---

### `triage_issues`

| Argument | Type | Required | Default | Description |
|---|---|---|---|---|
| `owner` | string | yes | — | GitHub owner login |
| `repo` | string | yes | — | Repository name |
| `max_issues` | integer | no | `50` | Issues to analyse (capped at 100) |

Returns `categories` (high_priority_bugs, good_first_issues, stale_issues,
documentation_requests, feature_requests), `recommendations`, and
`health_signals`.

---

### `full_repo_assessment`

| Argument | Type | Required | Description |
|---|---|---|---|
| `owner` | string | yes | GitHub owner login |
| `repo` | string | yes | Repository name |

Returns the complete `RepoDetails` shape used by the frontend:
`readmeQuality`, `security`, `ciCd`, `contributionHealth` (each with a score
and `checks[]`), `contributors[]`, `timeline[]`, and `insights`.

---

## Architecture overview

```
Claude Desktop / MCP Inspector
          │  stdio
          ▼
      main.py
          │
          ▼
       tools/          ← input validation, slug rules, path traversal checks
          │
          ▼
      services/        ← business logic, asyncio.gather() concurrency
       │       │
       ▼       ▼
   github/   llm/      ← httpx client + OpenAI wrapper
       │       │
       ▼       ▼
   cache/   models/    ← async TTL cache + Pydantic v2
```

**Key design decisions:**

**Concurrent fetching** — `asyncio.gather()` in `HealthService.analyse()` fires
6 GitHub API calls in parallel (metadata, commits, issues, PRs, languages,
contributors). Wall-clock latency is typically 2-4 seconds.

**LLM fallback** — every `llm.generate()` call is wrapped in try/except.
If OpenAI is unavailable the tool returns a rule-based result — it never
raises an error to the user.

**Session cache** — GitHub responses are cached for 5 minutes. A repeated
`full_repo_assessment` call within 5 minutes returns in under 1 second.

**Rate limit awareness** — the GitHub client reads `X-RateLimit-Remaining`
and sleeps proactively when the budget drops below 10 requests.

**Prompt-as-config** — all LLM prompts are `.txt` files in `llm/prompts/`.
Tune the narrative style without touching Python code.

**Health score formula:**

```
score = commit_frequency_norm   × 0.30   (log scale, 30-day window)
      + pr_merge_ratio          × 0.25   (merged / total resolved PRs)
      + issue_close_rate        × 0.25   (closed / total sampled issues)
      + contributor_activity    × 0.20   (tanh normalisation)
```

All weights are configurable via `WEIGHT_*` environment variables.

---

## Running tests

```powershell
# All 121 tests
python -m pytest tests/ -v

# Single file
python -m pytest tests/test_health_service.py -v

# With coverage
python -m pytest tests/ --cov=gitpulse_mcp --cov-report=term-missing
```

| Test file | Coverage area | Tests |
|---|---|---|
| `test_cache.py` | TTL cache, concurrency, per-entry TTL | 9 |
| `test_github_client.py` | HTTP errors, retry, pagination, cache hits | 8 |
| `test_models.py` | Pydantic validation, camelCase serialisation | 9 |
| `test_health_service.py` | Scoring formula, classification, fallback | 13 |
| `test_review_service.py` | Language detection, file review, PR synthesis | 14 |
| `test_triage_service.py` | Pre-classification rules, LLM fallback | 10 |
| `test_assessment_service.py` | Quality checks, timeline, orchestration | 17 |
| `test_tools.py` | Input validation across all 5 tools | 41 |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'gitpulse_mcp'`**

Your source files are not inside a `gitpulse_mcp/` sub-folder. Fix:
```powershell
mkdir gitpulse_mcp
Move-Item cache, github, llm, models, services, tools, config.py, main.py, __init__.py gitpulse_mcp\
```

**`ValidationError: weights must sum to 1.0`**

The `WEIGHT_*` values in `.env` don't add up to 1.0. Verify:
```powershell
python -c "from gitpulse_mcp.config import settings; print('OK')"
```

**`NotFoundError` when running a tool**

The repository is private or the owner/repo names are incorrect.
GitPulse only works with public repositories.

**`RateLimitError`**

The unauthenticated GitHub rate limit is 60 req/hour. Ensure `GITHUB_TOKEN`
is set in `.env`. With a valid token the limit is 5000 req/hour.

**`LLMError` or OpenAI connection error**

Check that `OPENAI_API_KEY` is valid. Every tool has a rule-based fallback —
results will be less detailed but the tool will not crash.

**Claude Desktop shows no tools**

1. Confirm the `cwd` path in `claude_desktop_config.json` points to your
   `GitPulseAI/` folder.
2. Point `command` at the `.venv` Python, not the system Python.
3. Fully quit and relaunch Claude Desktop after any config change.
4. Check Claude Desktop logs:
   `%APPDATA%\Claude\logs\` (Windows) or `~/Library/Logs/Claude/` (macOS).
