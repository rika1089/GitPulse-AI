# project-context.md
# GitHub Repo Health & Review MCP Assistant — Project Context

---

## Project Overview

The **GitHub Repo Health & Review MCP Assistant** is an intelligent, MCP-based developer tool that helps maintainers, contributors, and engineering teams understand the health, quality, and maintainability of GitHub repositories — through a single natural-language interface powered by AI.

The system is implemented as a Python **MCP (Model Context Protocol) server** that exposes a suite of structured, callable tools to AI assistants like Claude and ChatGPT. When a user asks "Is this repository healthy?" or "Review this pull request," the AI client automatically invokes the appropriate tool, which fetches live GitHub data, computes metrics, generates LLM-driven analysis, and returns a clear, actionable report.

The project's three functional pillars are:

1. **Repository Health Analysis** *(primary focus)* — quantitative and qualitative assessment of a repository's maintenance status, activity trends, and engineering health
2. **AI-Assisted Code Review** *(supporting feature)* — lightweight review of repository files and PR diffs for code quality, documentation, and potential bugs
3. **Issue Triage and Prioritization** *(supporting feature)* — automated classification and prioritization of open issues to help maintainers focus on what matters

The project was developed as part of a B.Tech Information Technology academic submission at SASTRA University, May 2026.

---

## Problem Statement

Software repositories often suffer from a silent but compounding problem: **gradual decay in maintainability and transparency**.

The challenges are familiar to anyone who works with open-source or collaborative codebases:

- **Repository health is invisible.** Developers evaluating whether to use or contribute to a project must manually inspect commit frequency, issue backlogs, PR activity, and contributor trends — often across dozens of tabs and tools.
- **Code reviews are inconsistent.** Without automated guidance, pull request reviews vary in depth and quality depending on who reviewed and when. Junior contributors receive little feedback; stale PRs accumulate unreviewed.
- **Issue management is manual.** Maintainers with hundreds of open issues have no automated way to identify which are urgent bugs, which are stale duplicates, and which are great for first-time contributors.
- **Existing tools are fragmented.** Tools like Shields.io and Repobeats offer raw metrics dashboards. Tools like CodeRabbit and GitHub Copilot offer code review. Issue trackers like Linear and Jira offer workflow management. But **no single tool combines all three** with natural-language AI reasoning that maintainers can query conversationally.

The result is that maintainers spend significant time on low-value manual assessment work, and contributors — especially new ones — lack the context they need to engage effectively with a project.

---

## Motivation

Two reference projects directly informed the motivation for this work:

**[openedx/edx-repo-health](https://github.com/openedx/edx-repo-health)** demonstrates the real need for structured repository health tooling at scale. The edX organization built a pytest-based check system to run health checks across their entire GitHub organization and aggregate results into a dashboard spreadsheet. The system works, but requires running CLI commands per repository, produces raw YAML output, and requires significant manual interpretation. There is no AI layer and no natural-language interface.

**[Orcus2021/code-review-mcp-server](https://github.com/Orcus2021/code-review-mcp-server)** demonstrates the power of MCP-native code review — the ability to fetch PR diffs, apply configurable review guidelines (from Notion, local files, or defaults), and post structured comments directly back to GitHub. However, it focuses entirely on code review and has no understanding of repository health, issue state, or maintenance trends.

The gap between these two projects is exactly what this project fills: **a unified AI-native assistant that reasons about repository health, code quality, and issue management together**, accessible conversationally through any MCP-compatible AI client.

---

## Goals

### Primary Goals

1. Develop a fully functional MCP server in Python that integrates with public GitHub repositories
2. Implement the `get_repo_health()` tool with quantitative metric computation and LLM-driven narrative generation
3. Implement `review_file()` and `review_pull_request()` tools for AI-assisted code review
4. Implement `triage_issues()` for automated issue classification and prioritization
5. Implement `full_repo_assessment()` as an orchestrating tool combining all three capabilities
6. Produce well-structured, beginner-friendly documentation across all four required documentation files

### Secondary Goals

1. Design the architecture to be modular and extensible for future features (CI/CD analysis, security scanning, web dashboard)
2. Demonstrate practical application of MCP architecture, GitHub REST APIs, and prompt engineering
3. Provide a reference implementation that other students and developers can learn from and extend

---

## Target Users

### Open-Source Maintainers

The primary beneficiary. Maintainers managing repositories with hundreds of issues and dozens of PR contributors need quick, reliable answers to: "Is my project in a healthy state? What should I focus on this week?" The assistant delivers this in seconds without manual dashboard review.

### New Contributors

Before submitting a first PR, contributors want to understand a project's activity level, code style expectations, and issue priorities. The assistant helps them quickly orient themselves and identify beginner-friendly issues.

### Students and Learners

Students learning software engineering workflows can use this project as:
- A working example of MCP server architecture
- A demonstration of GitHub API integration patterns
- A practical application of prompt engineering for structured LLM outputs

### Engineering Teams Evaluating Dependencies

Teams deciding whether to adopt an open-source library want to know: Is this actively maintained? How quickly are bugs fixed? Is the code quality acceptable? The assistant answers these questions programmatically.

---

## Key Features

### 1. Repository Health Analysis

The flagship feature. The system fetches the following data for any public GitHub repository and computes a normalized health score (0–100):

- Commit frequency over the last 30 and 90 days
- Pull request merge ratio (merged / total)
- Issue close rate (closed / total)
- Contributor count and activity trends
- Average issue resolution time

These metrics are fed to an LLM which classifies the repository as one of: **Healthy**, **Stagnant**, **At Risk**, or **Archived**, and generates a natural-language report with strengths, risks, and specific recommendations.

**Example output:**
> "This repository is **Actively Maintained** (Health Score: 82/100). Commit activity is strong with 47 commits in the last 30 days and an issue close rate of 91%. However, 3 critical bug reports have been open for more than 45 days without activity — addressing these should be the immediate priority."

---

### 2. AI-Assisted Code Review

The `review_file()` and `review_pull_request()` tools enable lightweight but structured code review. Inspired by the approach in [Orcus2021/code-review-mcp-server](https://github.com/Orcus2021/code-review-mcp-server), which fetches PR diffs and applies configurable review guidelines:

- **File review** — fetches raw file content and sends it to the LLM with a structured review prompt covering code quality, naming conventions, documentation, complexity, and potential bugs
- **PR review** — fetches the unified diff, reviews each changed file, and produces both a per-file review and an overall PR summary

Reviews are returned in a structured format:

```
Strengths:
- Clear function naming throughout the module
- Good use of type hints on all public methods

Issues Identified:
- [HIGH] Missing error handling in fetch_data() — network failure will raise an unhandled exception
- [MEDIUM] The process_response() function is 87 lines long — consider splitting at line 45

Suggestions:
- Add a try/except block around the requests.get() call in fetch_data()
- Extract the pagination logic from process_response() into a separate helper
```

---

### 3. Issue Triage and Prioritization

The `triage_issues()` tool analyzes all open issues in a repository and produces a prioritized triage report. Each issue is classified into one of five categories based on its labels, age, and engagement:

| Category | Identification Criteria |
|----------|------------------------|
| High Priority Bug | Labels: `bug`, `critical`, `urgent`; or high comment count with no resolution |
| Stale Issue | No activity in > 30 days; still open |
| Good First Issue | Labels: `good-first-issue`, `beginner`, `easy` |
| Documentation Request | Labels: `docs`, `documentation` |
| Feature Request | Labels: `enhancement`, `feature` |

The LLM synthesizes this classification into a prioritized summary report with maintainer-specific recommendations.

---

### 4. Combined Repository Assessment

The `full_repo_assessment()` tool orchestrates all three capabilities into a single comprehensive report — the project's most powerful feature. It runs health analysis and issue triage in parallel (using `asyncio.gather()`), optionally adds a review of recent commits, and synthesizes everything through the Report Generator.

The output includes:
- Overall health score and classification
- Top 3 engineering risks requiring immediate attention
- Critical issue summary (top 5 priority issues)
- Code quality indicators from recent commits
- Specific, actionable recommendations for the maintainer

---

## What Makes This Project Unique

| Capability | edx-repo-health | code-review-mcp-server | This Project |
|-----------|----------------|----------------------|-------------|
| Repository health metrics | ✅ | ❌ | ✅ |
| AI-generated health narrative | ❌ | ❌ | ✅ |
| Code review of files/PRs | ❌ | ✅ | ✅ |
| Issue triage and prioritization | ❌ | ❌ | ✅ |
| MCP-native (AI client compatible) | ❌ | ✅ | ✅ |
| Conversational interface | ❌ | ❌ | ✅ |
| Combined assessment report | ❌ | ❌ | ✅ |
| Python-based | ✅ | ❌ (TypeScript) | ✅ |

The key differentiator is **integration with reasoning**: while existing tools surface raw data or perform isolated reviews, this project feeds all three dimensions of repository intelligence (health, code quality, issue state) into a single LLM-synthesized assessment — accessible through natural language.

---

## Scope

The project scope includes:

- Integration with **public** GitHub repositories via GitHub REST API
- MCP server with five registered tools: `get_repo_health`, `review_file`, `review_pull_request`, `triage_issues`, `full_repo_assessment`
- Health metric computation covering: commit frequency, PR merge ratio, issue close rate, contributor activity
- AI-powered review for repository files and PR diffs
- Issue classification and prioritization based on metadata (labels, age, engagement)
- Natural-language report generation using LLMs (OpenAI API)
- Configurable health scoring weights and lookback windows
- Local development setup with stdio MCP transport
- Comprehensive documentation: architecture, tech stack, coding standards, project context

---

## Out of Scope

| Item | Reason Excluded |
|------|----------------|
| Private repository support | Requires per-user OAuth flow; adds significant auth complexity beyond project scope |
| Deep static analysis (AST-based) | Requires language-specific parsers (tree-sitter, pylint, eslint) — heavyweight and language-specific |
| Runtime vulnerability scanning | Requires integration with security databases (CVE, Dependabot) — a separate engineering effort |
| CI/CD pipeline analysis | GitHub Actions integration is architecturally planned but not implemented in this version |
| Enterprise GitHub (GitHub Enterprise Server) | Requires different API base URLs and auth; public GitHub is sufficient for scope |
| Automated PR commenting | Posting review comments back to GitHub PRs is a future enhancement (demonstrated in the reference project) |
| Web dashboard frontend | FastAPI extension is architecturally included but the frontend is not implemented |

---

## Design Decisions Log

### Why MCP?

MCP (Model Context Protocol) was chosen as the integration layer because it is purpose-built for exactly this use case: exposing external tool capabilities to AI assistant clients. The alternative — building a standalone web API and instructing users to send API requests manually — would eliminate the conversational interface that makes this project useful. With MCP, the AI client handles intent parsing, tool selection, and response rendering automatically.

### Why Python?

Python is the natural choice for this project because:
1. The MCP Python SDK is the most mature option
2. The OpenAI Python SDK is first-class
3. `httpx` and `requests` are well-documented for GitHub API work
4. Python is the primary language taught in the IT program at SASTRA, making the project more approachable for academic evaluation and future contributors

TypeScript (used by [code-review-mcp-server](https://github.com/Orcus2021/code-review-mcp-server)) is a valid alternative but adds compilation overhead for a student project.

### Why GitHub REST API over GraphQL?

The REST API was chosen because it is simpler to debug (curl-friendly), better documented for the specific endpoints needed, and more predictable in response structure for caching purposes. GraphQL would allow fetching deeply nested data (repo + issues + PRs + contributors) in a single query, which is a compelling future optimization, but the added complexity is not justified for the current scope.

### Why Modular Architecture?

The strict separation between `tools/`, `services/`, `github/`, and `models/` layers was chosen to ensure each component is testable in isolation and replaceable without affecting others. This decision was directly informed by the edX repo-health architecture, which uses a similar philosophy: each health check is an independent function that reads data and writes to a shared result dict.

### Why Prompt Templates as Plain Text Files?

Storing prompt templates as `.txt` files (rather than as Python string constants) allows prompt iteration without touching Python code. Prompts can be reviewed, versioned in git, and modified by non-engineers who understand natural language better than they understand Python. This is a standard practice in production LLM applications.

### Why Pydantic for All Data Models?

Pydantic enforces type safety at the boundaries of each module and generates accurate JSON schemas that the MCP SDK uses to describe tool inputs and outputs to AI clients. Without Pydantic, tool schemas would be undocumented or inaccurate, degrading the AI client's ability to use tools correctly.

---

## Assumptions

| Assumption | Rationale |
|-----------|----------|
| Target repositories are public on GitHub.com | Private repos require per-user OAuth, which significantly increases complexity |
| Users have a valid GitHub Personal Access Token | Required for the 5,000 requests/hour authenticated rate limit |
| Users have an OpenAI API key | The LLM layer defaults to OpenAI; the architecture supports swapping providers |
| Repositories have at least some activity data (commits, issues) | Health scoring degrades gracefully for empty repos but results are less meaningful |
| MCP client (Claude Desktop or compatible) is already installed and configured | Installation guidance is provided in README but client setup is out of scope |

---

## Constraints

| Constraint | Impact | Mitigation |
|-----------|--------|-----------|
| GitHub REST API rate limit: 5,000 requests/hour | Limits how many repositories can be analyzed in a session | Session-level caching; paginated fetching with configurable depth limits |
| OpenAI API cost | Each tool call incurs token costs (~$0.01–$0.05 per call with gpt-4o-mini) | Use `gpt-4o-mini` by default; allow users to configure model |
| Public repositories only | Cannot analyze private codebases | Architecturally extensible for OAuth-based private repo support |
| GitHub API response latency | Cold fetches for large repositories can take 2–5 seconds | Async concurrent fetching; session cache for repeated calls |
| LLM context window limits | Very large PR diffs or files may exceed token limits | Chunked processing with summarization for large diffs |

---

## Risks & Challenges

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| LLM generates inaccurate code review suggestions | Medium | Medium | Frame suggestions as "recommendations, not verdicts"; add disclaimer to output |
| GitHub API changes break endpoint compatibility | Low | High | Pin API version header (`X-GitHub-Api-Version: 2022-11-28`); monitor GitHub changelog |
| LLM response parsing fails (malformed JSON) | Medium | Medium | Retry with explicit JSON formatting instructions; fallback to text response |
| Large repository fetching timeouts | Medium | Medium | Configurable depth limits for commits/issues; async concurrent requests |
| Health metrics misleading for non-standard repo types | Medium | Low | Add repo type detection (library vs. archived vs. org-internal) for calibrated thresholds |

---

## Success Criteria

The project is considered successful when:

| Criterion | Measurement |
|-----------|------------|
| All five MCP tools are registered and callable | Verified via MCP Inspector with no schema errors |
| `get_repo_health()` produces accurate health scores | Validated against 5+ known repositories with manually verified health status |
| `review_pull_request()` returns structured, useful reviews | Manually evaluated for a set of sample PRs across different codebases |
| `triage_issues()` correctly classifies issue categories | Compared against manual classification of 20+ issues per test repo |
| `full_repo_assessment()` completes in < 30 seconds | Timed across 5 test repositories of varying size |
| All modules have ≥ 80% unit test coverage | Measured via `pytest-cov` report |
| Documentation is complete and peer-readable | Reviewed by one academic evaluator and one student peer |

---

## Future Enhancements

### Phase 2 (Near-Term)

- **Automated PR commenting** — post `review_pull_request()` results as GitHub PR comments (line-level and summary), similar to [code-review-mcp-server](https://github.com/Orcus2021/code-review-mcp-server)
- **CI/CD analysis tool** — parse GitHub Actions workflow files to evaluate testing, coverage, and deployment quality
- **Private repository support** — OAuth-based authentication flow for analyzing private codebases

### Phase 3 (Medium-Term)

- **Web dashboard** — FastAPI + React frontend that visualizes health scores, issue trends, and review history across multiple repositories
- **Historical trending** — SQLite/PostgreSQL storage of health snapshots to track repository health over time
- **Security scanning integration** — connect to GitHub's Dependabot API and OSSAR results for vulnerability-aware health scoring

### Phase 4 (Long-Term)

- **Contributor recommendation engine** — suggest relevant past contributors to assign to new issues based on file touch history
- **Vector database for review history** — semantic search over past reviews to surface similar code patterns and past recommendations
- **Multi-repository organization assessment** — run health analysis across all repositories in a GitHub organization and produce an aggregated org-level report (similar to what [edx-repo-health](https://github.com/openedx/edx-repo-health) achieves for edX, but with AI narrative generation)
- **LangChain agent integration** — replace sequential tool calls with an agentic workflow that autonomously decides which tools to invoke based on the repository's specific characteristics
