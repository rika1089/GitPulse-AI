# architecture.md
# GitHub Repo Health & Review MCP Assistant — System Architecture

---

## System Overview

The **GitHub Repo Health & Review MCP Assistant** is built around the **Model Context Protocol (MCP)** architecture — a structured protocol that allows AI assistants such as Claude or ChatGPT to interact with external services through well-defined, typed tool calls.

Instead of building a monolithic backend, the system is decomposed into a collection of focused, independently callable **MCP tools**, each responsible for a specific domain of repository intelligence:

- Repository health analysis
- AI-powered code review
- Issue triage and prioritization
- Combined repository assessment reports

The MCP server acts as an intelligent middleware layer that bridges **GitHub's REST API**, **Large Language Models (LLMs)**, and the **end-user AI assistant interface**. All tool calls are stateless by design, making the system easy to test, extend, and deploy.

### Why Modular MCP Architecture?

| Reason | Explanation |
|--------|-------------|
| Composability | Each tool solves one problem well and can be combined by the AI client |
| Testability | Each module can be unit-tested in isolation |
| Extensibility | New tools can be added without touching existing ones |
| AI-Native | MCP is purpose-built for AI assistant integration |
| Scalability | Modules can be distributed or cached independently |

---

## High-Level Architecture

The full request-to-response flow:

```
┌─────────────────────────────────────────────────────┐
│                    End User                         │
│  "Is this repository healthy?"                      │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│           MCP Client (Claude / ChatGPT)             │
│  Parses user intent → selects MCP tool              │
└─────────────────┬───────────────────────────────────┘
                  │  Tool call (JSON-RPC over stdio/HTTP)
                  ▼
┌─────────────────────────────────────────────────────┐
│              MCP Server (Python)                    │
│  Tool Registry → routes to appropriate handler     │
└──────┬──────────────────────────────┬───────────────┘
       │                              │
       ▼                              ▼
┌──────────────────┐      ┌───────────────────────────┐
│  GitHub API      │      │   LLM Processing Layer    │
│  Layer           │      │   (OpenAI / Claude API)   │
│  (REST API)      │      │                           │
└──────┬───────────┘      └───────────┬───────────────┘
       │                              │
       ▼                              ▼
┌──────────────────────────────────────────────────────┐
│              Analysis & Report Engine                │
│  Health Analyzer │ Code Review │ Issue Triage        │
└──────────────────────────────┬───────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────┐
│         Structured JSON + Natural Language Report    │
│         returned to MCP Client → rendered to User    │
└──────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Repository Health Analyzer

**Purpose:** Evaluates the overall maintenance status and activity level of a GitHub repository.

**Responsibilities:**
- Fetches commit history, issue counts, PR statistics, and contributor data
- Computes weighted health metrics (activity score, PR merge ratio, issue close rate)
- Feeds computed metrics into the LLM for natural-language interpretation
- Returns a health classification: `Healthy`, `Stagnant`, `At Risk`, or `Archived`

**Key Metrics Computed:**

| Metric | Weight | Description |
|--------|--------|-------------|
| Commit frequency (30d) | 30% | Commits in the last 30 days |
| PR merge ratio | 25% | Merged PRs / Total PRs |
| Issue close rate | 25% | Closed issues / Total issues |
| Contributor activity | 20% | Unique contributors in last 90 days |

---

### 2. Code Review Engine

**Purpose:** Performs lightweight AI-assisted review on repository source files and pull request diffs.

**Responsibilities:**
- Fetches raw file content or PR diff from GitHub API
- Constructs structured review prompts using the Prompt Builder
- Sends content to LLM with role-specific instructions
- Returns structured review output: Strengths, Issues, Suggestions

**Inspired by:** The approach used in [Orcus2021/code-review-mcp-server](https://github.com/Orcus2021/code-review-mcp-server), which demonstrates fetching PR diffs from GitHub URLs and posting line-specific and summary review comments directly back to the PR.

---

### 3. Issue Triage Engine

**Purpose:** Analyzes open issues in a repository to identify priorities, stale tickets, and beginner-friendly tasks.

**Responsibilities:**
- Fetches all open issues with labels, timestamps, and comment counts
- Classifies issues by urgency, type, and staleness
- Produces a prioritized triage report with actionable maintainer recommendations

**Classification Categories:**

| Category | Detection Logic |
|----------|----------------|
| High Priority Bug | Label contains `bug`, `critical`, or `urgent` |
| Stale Issue | No activity in > 30 days |
| Good First Issue | Label contains `good-first-issue` or `beginner` |
| Documentation | Label contains `docs` or `documentation` |
| Feature Request | Label contains `enhancement` or `feature` |

---

### 4. GitHub API Layer

**Purpose:** Centralized service for all GitHub REST API interactions.

**Responsibilities:**
- Authenticates using GitHub Personal Access Tokens
- Exposes typed methods for each API resource (repos, commits, issues, PRs, files)
- Handles rate limiting with exponential backoff
- Caches responses for repeated calls within a session

**Inspired by:** The design in [openedx/edx-repo-health](https://github.com/openedx/edx-repo-health), which uses a pytest-based check system where each check independently queries GitHub and writes results to a shared dictionary — demonstrating clean separation of data collection from analysis.

---

### 5. LLM Processing Layer

**Purpose:** Wraps all LLM API interactions, providing consistent prompt submission and structured response parsing.

**Responsibilities:**
- Manages API calls to OpenAI or Anthropic
- Applies prompt templates from the Prompt Builder
- Parses and validates LLM responses into structured Python objects
- Handles token budget management for large diffs or repositories

---

### 6. MCP Tool Registry

**Purpose:** The entry point for all MCP tool calls. Maps tool names to handler functions and validates input/output schemas.

**Responsibilities:**
- Registers all tools using the MCP Python SDK `@tool` decorator
- Validates input parameters using Pydantic models
- Routes requests to the correct handler module
- Formats responses as MCP-compliant structured JSON

---

### 7. Metrics Engine

**Purpose:** Computes all quantitative repository health metrics from raw GitHub API data.

**Responsibilities:**
- Calculates commit frequency, PR ratios, issue resolution time
- Generates time-series data for trend analysis
- Produces a normalized health score (0–100)

---

### 8. Prompt Builder

**Purpose:** Constructs all prompts sent to the LLM with consistent structure and context injection.

**Responsibilities:**
- Provides reusable prompt templates for each analysis type
- Injects repository metadata, diffs, and metrics into templates
- Enforces structured output formatting instructions (JSON sections, headings)

---

### 9. Report Generator

**Purpose:** Assembles all module outputs into a unified, human-readable final report.

**Responsibilities:**
- Merges health scores, code review comments, and issue triage summaries
- Renders markdown-formatted reports for display in MCP clients
- Produces a JSON-structured assessment for programmatic consumption

---

## Folder Structure

```
github-repo-health-mcp/
│
├── server/
│   ├── __init__.py
│   └── main.py                  # MCP server entry point, tool registration
│
├── tools/
│   ├── __init__.py
│   ├── repo_health.py           # get_repo_health() tool handler
│   ├── code_review.py           # review_file(), review_pull_request() handlers
│   ├── issue_triage.py          # triage_issues() handler
│   └── full_assessment.py       # full_repo_assessment() orchestrator
│
├── services/
│   ├── __init__.py
│   ├── metrics_engine.py        # Health score computation
│   ├── report_generator.py      # Final report assembly
│   └── prompt_builder.py        # LLM prompt templates and constructors
│
├── github/
│   ├── __init__.py
│   ├── client.py                # GitHub REST API client (auth, rate limiting)
│   ├── repos.py                 # Repository metadata fetchers
│   ├── commits.py               # Commit history fetchers
│   ├── pull_requests.py         # PR diff and metadata fetchers
│   ├── issues.py                # Issue list and metadata fetchers
│   └── files.py                 # File content fetchers
│
├── prompts/
│   ├── health_analysis.txt      # Prompt template: repo health narrative
│   ├── code_review.txt          # Prompt template: code review instructions
│   ├── issue_triage.txt         # Prompt template: issue prioritization
│   └── full_assessment.txt      # Prompt template: combined assessment
│
├── models/
│   ├── __init__.py
│   ├── repo_health.py           # Pydantic models: RepoHealthReport
│   ├── code_review.py           # Pydantic models: CodeReviewResult
│   ├── issue.py                 # Pydantic models: IssueSummary, TriageReport
│   └── assessment.py            # Pydantic models: FullAssessmentReport
│
├── utils/
│   ├── __init__.py
│   ├── cache.py                 # In-memory and SQLite caching helpers
│   ├── rate_limiter.py          # GitHub API rate limit handler
│   ├── logger.py                # Centralized logging setup
│   └── config.py                # Environment variable loader
│
├── tests/
│   ├── unit/
│   │   ├── test_metrics_engine.py
│   │   ├── test_prompt_builder.py
│   │   └── test_report_generator.py
│   ├── integration/
│   │   ├── test_github_client.py
│   │   └── test_tools.py
│   └── fixtures/
│       ├── mock_repo_response.json
│       └── mock_issues_response.json
│
├── docs/
│   ├── architecture.md          # This file
│   ├── techstack.md
│   ├── coding-standards.md
│   └── project-context.md
│
├── .env.example                 # Template for environment variables
├── requirements.txt
├── pyproject.toml
└── README.md
```

**Folder Purpose Summary:**

| Folder | Purpose |
|--------|---------|
| `server/` | MCP server bootstrap and tool registration |
| `tools/` | One file per MCP tool — thin handlers that orchestrate services |
| `services/` | Business logic: metrics, prompts, report generation |
| `github/` | All GitHub API communication, cleanly separated by resource type |
| `prompts/` | Plain-text prompt templates versioned alongside code |
| `models/` | Pydantic data models for all inputs and outputs |
| `utils/` | Cross-cutting concerns: logging, caching, config |
| `tests/` | Unit and integration tests with mock fixtures |
| `docs/` | All project documentation |

---

## Data Flow

### Step-by-Step Request Lifecycle

```
1. User Query
   └── "Review the pull request at github.com/owner/repo/pull/42"

2. MCP Client (Claude/ChatGPT)
   └── Identifies intent → invokes review_pull_request(owner, repo, pr_number=42)

3. MCP Server Tool Registry
   └── Validates parameters via Pydantic
   └── Routes to tools/code_review.py → review_pull_request()

4. GitHub API Layer
   └── github/pull_requests.py → fetch_pr_diff(owner, repo, 42)
   └── GitHub REST API: GET /repos/{owner}/{repo}/pulls/42
   └── Returns: unified diff string

5. Prompt Builder
   └── prompts/code_review.txt → injected with diff content
   └── Structured prompt with output schema instructions

6. LLM Processing Layer
   └── POST to OpenAI/Anthropic API
   └── Returns: structured review JSON

7. Report Generator
   └── Parses LLM response into CodeReviewResult Pydantic model
   └── Formats as markdown sections: Strengths / Issues / Suggestions

8. MCP Server
   └── Returns structured JSON response to MCP Client

9. MCP Client (Claude/ChatGPT)
   └── Renders report to user in natural language
```

---

## MCP Tool Design

### `get_repo_health(owner, repo)`

| Field | Details |
|-------|---------|
| **Purpose** | Fetch repository metrics and generate a health summary report |
| **Input** | `owner: str` — GitHub username or org; `repo: str` — repository name |
| **Output** | `RepoHealthReport` — health score, classification, narrative, key metrics |
| **Internal Workflow** | Fetch commits/issues/PRs → compute metrics via MetricsEngine → send to LLM → return report |

---

### `review_file(owner, repo, path)`

| Field | Details |
|-------|---------|
| **Purpose** | Review a specific source file using AI for quality, readability, and bugs |
| **Input** | `owner`, `repo`, `path: str` — file path within the repository |
| **Output** | `CodeReviewResult` — strengths, issues, suggestions, severity tags |
| **Internal Workflow** | Fetch file content → build review prompt → send to LLM → parse structured response |

---

### `review_pull_request(owner, repo, pr_number)`

| Field | Details |
|-------|---------|
| **Purpose** | Review a PR diff and generate inline comments and a summary |
| **Input** | `owner`, `repo`, `pr_number: int` |
| **Output** | `PRReviewResult` — summary comment, line-level comments, overall verdict |
| **Internal Workflow** | Fetch PR diff → split by file → build review prompt per file → aggregate results |

---

### `triage_issues(owner, repo)`

| Field | Details |
|-------|---------|
| **Purpose** | Analyze all open issues and produce a prioritized triage report |
| **Input** | `owner`, `repo` |
| **Output** | `TriageReport` — categorized issues list, stale count, priority bugs, recommendations |
| **Internal Workflow** | Fetch issues → classify by label/age/engagement → build triage prompt → return prioritized list |

---

### `full_repo_assessment(owner, repo)`

| Field | Details |
|-------|---------|
| **Purpose** | Orchestrate all tools to produce a comprehensive repository assessment |
| **Input** | `owner`, `repo` |
| **Output** | `FullAssessmentReport` — health score, top risks, code review summary, issue priorities, recommendations |
| **Internal Workflow** | Run `get_repo_health` + `triage_issues` in parallel → optionally review recent commits → combine via ReportGenerator |

---

## API Design

### GitHub REST API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /repos/{owner}/{repo}` | Repository metadata (stars, forks, watchers) |
| `GET /repos/{owner}/{repo}/commits` | Commit history (paginated) |
| `GET /repos/{owner}/{repo}/pulls?state=all` | Pull request statistics |
| `GET /repos/{owner}/{repo}/pulls/{pr_number}` | PR metadata |
| `GET /repos/{owner}/{repo}/pulls/{pr_number}/files` | PR diff files |
| `GET /repos/{owner}/{repo}/issues?state=all` | All issues (paginated) |
| `GET /repos/{owner}/{repo}/contributors` | Contributor list |
| `GET /repos/{owner}/{repo}/contents/{path}` | File content (base64 encoded) |
| `GET /repos/{owner}/{repo}/stats/commit_activity` | Weekly commit activity |

### Authentication Flow

```python
# In github/client.py
headers = {
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}
```

GitHub tokens are loaded from environment variables — never hardcoded.

### Rate Limiting Strategy

The GitHub REST API allows **5,000 requests/hour** for authenticated users. The system handles this via:

1. **Response header inspection** — check `X-RateLimit-Remaining` and `X-RateLimit-Reset` on every response
2. **Exponential backoff** — on 403/429 responses, wait with increasing delay before retrying
3. **Session-level caching** — cache API responses in memory for the duration of a single tool call to avoid redundant fetches

### Error Handling

| HTTP Status | Handling |
|-------------|---------|
| 401 | Raise `AuthenticationError` — token missing or invalid |
| 403 | Check rate limit headers; if rate-limited, backoff and retry |
| 404 | Raise `RepositoryNotFoundError` — repository doesn't exist or is private |
| 422 | Raise `InvalidParameterError` — bad request parameters |
| 5xx | Retry up to 3 times with exponential backoff |

---

## Database / Storage Design

While the current version operates statelessly, a future-ready schema is provided for caching and history.

**Recommended lightweight options:** SQLite (local development), PostgreSQL (production deployment)

### Schema Design

```sql
-- Cached repository health snapshots
CREATE TABLE repo_health_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    owner           TEXT NOT NULL,
    repo            TEXT NOT NULL,
    health_score    REAL,
    classification  TEXT,
    metrics_json    TEXT,   -- JSON blob of computed metrics
    report_text     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Code review history
CREATE TABLE code_reviews (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    owner           TEXT NOT NULL,
    repo            TEXT NOT NULL,
    target_type     TEXT CHECK(target_type IN ('file', 'pr')),
    target_ref      TEXT,   -- file path or PR number
    review_json     TEXT,   -- structured review output
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Issue triage snapshots
CREATE TABLE issue_triage_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    owner           TEXT NOT NULL,
    repo            TEXT NOT NULL,
    triage_json     TEXT,
    stale_count     INTEGER,
    priority_count  INTEGER,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Session/request log
CREATE TABLE request_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name       TEXT,
    owner           TEXT,
    repo            TEXT,
    duration_ms     INTEGER,
    status          TEXT CHECK(status IN ('success', 'error')),
    error_msg       TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Scalability Considerations

| Concern | Strategy |
|---------|---------|
| Slow GitHub API calls | `asyncio` + `httpx.AsyncClient` for concurrent requests |
| Repeated repo fetches | In-memory cache with TTL; SQLite for cross-session persistence |
| Large PR diffs | Chunked diff processing — split by file, review in parallel |
| Large repositories | Paginated API consumption with configurable depth limits |
| Multiple concurrent users | Stateless tool design — each call is fully independent |
| New features | Add new files to `tools/` and `services/` without modifying existing code |

---

## Security Considerations

| Area | Practice |
|------|---------|
| GitHub Token | Loaded from environment variables via `python-dotenv`; never logged or returned |
| API Keys | Stored in `.env` file listed in `.gitignore`; `.env.example` provided with no real values |
| Input Validation | All tool inputs validated via Pydantic models before processing |
| LLM Prompt Injection | Repository content passed as data, not instruction — system/user role separation enforced |
| Rate Abuse Prevention | Backoff strategy prevents hammering the GitHub API |
| Secrets in Logs | Logger configured to redact Authorization header values |

---

## Future Architecture Extensions

| Extension | Description |
|-----------|-------------|
| **CI/CD Analysis Tool** | New MCP tool: `analyze_cicd(owner, repo)` — parses GitHub Actions workflows for quality signals |
| **Security Scanning** | Integrate with GitHub's Dependabot API or OSSAR results |
| **Contributor Recommender** | Match open issues to past contributors based on file touch history |
| **Web Dashboard** | FastAPI + React frontend consuming the same tool layer as an HTTP API |
| **Vector Database Integration** | Store code review embeddings in Qdrant or Chroma for semantic search across historical reviews |
| **Multi-Provider LLM** | Abstract LLM calls behind a provider interface — swap OpenAI for Anthropic, Gemini, or local models |
| **Webhook Integration** | GitHub webhooks trigger automatic PR review on push events |
| **Redis Caching** | Replace in-memory cache with Redis for multi-instance deployments |
