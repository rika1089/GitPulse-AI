# techstack.md
# GitHub Repo Health & Review MCP Assistant — Technology Stack

---

## Overview

The technology stack for this project was selected around three core principles:

1. **API-centric by design** — the system integrates external APIs (GitHub, LLM providers) as its primary data and intelligence sources, so the stack must handle HTTP, async I/O, and JSON fluently
2. **MCP-compatible** — the entire server layer must conform to the Model Context Protocol specification, which mandates Python or TypeScript tooling and specific transport protocols
3. **Approachable and lightweight** — as a student project targeting open-source maintainers and contributors, the stack must be easy to set up locally, cost-efficient to run, and free from heavyweight enterprise dependencies

The result is a Python-first, API-driven stack that is minimal to get started with yet scales naturally toward production-grade deployment.

---

## Languages

### Python 3.10+

Python is the primary implementation language for the following reasons:

| Reason | Detail |
|--------|--------|
| MCP SDK availability | The official MCP Python SDK is the most mature and documented option for building MCP servers |
| GitHub API ecosystem | `PyGithub`, `httpx`, and `requests` are battle-tested Python libraries for GitHub REST API integration |
| LLM SDK support | OpenAI's and Anthropic's official Python SDKs are first-class and actively maintained |
| Rapid prototyping | Python's concise syntax accelerates iteration, which is critical in a research/student context |
| Data processing | `pandas` and `statistics` (stdlib) are ideal for computing repository metrics |
| Community and documentation | Python has the largest AI/ML tooling ecosystem, making it easy to find examples and support |

**Version requirement:** Python 3.10+ is required for `match/case` pattern matching, `typing` improvements, and compatibility with all listed libraries.

---

## Frameworks & Libraries

### MCP Python SDK

```bash
pip install mcp
```

**Why:** The [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk) is the official library for building MCP-compliant servers. It provides:

- The `@tool` decorator for registering tool handlers
- Automatic JSON schema generation from Python type hints
- Transport layer management (stdio and HTTP/SSE)
- Built-in request routing and error marshalling

Without this SDK, you would need to implement the entire MCP wire protocol manually. It is a non-negotiable dependency for this project.

---

### FastAPI (Optional Extension Layer)

```bash
pip install fastapi uvicorn
```

**Why:** While the core MCP server runs over stdio transport, FastAPI is included as an optional HTTP extension layer for two use cases:

1. Exposing tools as regular REST endpoints for testing via browser or Postman
2. Supporting a future web dashboard that queries the same business logic via HTTP

FastAPI was chosen over Flask because it has native `async/await` support, automatic OpenAPI documentation generation, and Pydantic integration — all of which align with the project's existing patterns.

---

### HTTPX

```bash
pip install httpx
```

**Why:** HTTPX is the preferred HTTP client over `requests` for this project because it supports both **synchronous and asynchronous** request modes. Since the GitHub API layer may need to fetch commits, issues, PRs, and file contents concurrently (e.g., inside `full_repo_assessment()`), async HTTP is essential for acceptable performance on larger repositories.

`httpx.AsyncClient` enables concurrent GitHub API calls with `asyncio.gather()`, which can reduce total fetch time by 60–70% compared to sequential `requests` calls.

---

### OpenAI Python SDK

```bash
pip install openai
```

**Why:** The OpenAI SDK is the standard client for interacting with GPT-4 and other OpenAI models. It handles:

- Authentication and API key management
- Request construction and response parsing
- Streaming support for long-form report generation
- Retry logic for transient API failures

The project is architected to be LLM-provider-agnostic (the `services/llm_client.py` module can be swapped), but OpenAI is the default provider due to its maturity and documentation quality.

---

### Pydantic v2

```bash
pip install pydantic
```

**Why:** Pydantic is used as the primary data validation and serialization library across the entire project. Every MCP tool input and output is defined as a Pydantic model, which provides:

- Automatic input validation with clear error messages
- JSON serialization and deserialization without boilerplate
- Type safety throughout the codebase
- Integration with FastAPI for automatic API schema generation

Pydantic v2 was chosen over v1 because of its significantly improved performance (Rust-based core) and stricter type handling.

---

### Pandas

```bash
pip install pandas
```

**Why:** Pandas is used in the Metrics Engine for computing repository health statistics from raw GitHub API responses. Specifically:

- Time-series analysis of commit frequency over configurable windows (7d, 30d, 90d)
- DataFrame-based aggregation of contributor activity
- Issue resolution time calculations using date arithmetic

For the current project scope, `pandas` can be partially replaced with pure Python for simpler operations, but it provides a clean foundation for future time-series dashboard features.

---

### Rich (Optional CLI)

```bash
pip install rich
```

**Why:** `rich` is used for local development and debugging to produce readable, color-formatted console output when running the MCP server directly. It improves developer experience by formatting tool call logs, error traces, and health report previews in the terminal.

---

### Typer (Optional CLI)

```bash
pip install typer
```

**Why:** `typer` provides a CLI wrapper for running individual tools from the command line during development and testing — for example:

```bash
python -m cli repo-health --owner microsoft --repo vscode
```

This makes it easy to test tool behavior without requiring an MCP client to be configured.

---

### python-dotenv

```bash
pip install python-dotenv
```

**Why:** Manages environment variable loading from `.env` files during local development. Ensures that GitHub tokens and API keys are never hardcoded and are consistent across environments.

---

## APIs & Services

### GitHub REST API

**URL:** `https://api.github.com`

**Why:** The GitHub REST API is the most comprehensive and well-documented interface for repository data. It provides all necessary endpoints for repository metadata, commit history, PR diffs, issues, and file content. The GraphQL API (v4) was considered but not adopted for this project because:

- REST is simpler to debug with Postman and curl
- REST responses are more predictable and cacheable
- The data access patterns in this project (resource-by-resource fetching) are better suited to REST than graph traversal

**Authentication:** GitHub Personal Access Tokens (PATs) with `repo` and `read:org` scopes are used. Fine-grained tokens are recommended for security.

---

### OpenAI API (Default LLM Provider)

**URL:** `https://api.openai.com/v1`

**Why:** OpenAI's API provides access to GPT-4o and GPT-4-turbo models, which are the most capable available for code review, health analysis narrative generation, and issue triage summarization. The structured output feature (JSON mode) is particularly important for enforcing consistent LLM response formats.

**Cost Management:** The project uses `gpt-4o-mini` as the default model for cost efficiency, with `gpt-4o` available for full assessments when higher reasoning quality is needed.

---

## Development Tools

### Visual Studio Code

**Why:** VS Code is the recommended IDE because of its excellent Python extension ecosystem (`Pylance`, `Ruff`, `Black Formatter`) and native support for `.env` files, `pyproject.toml`, and terminal-based MCP server testing.

---

### Git

**Why:** Git is used for version control with a three-branch strategy (see `coding-standards.md`). All contributors are expected to follow conventional commit standards.

---

### Postman

**Why:** Postman is used for testing GitHub REST API endpoints directly during development — validating response structures, authentication headers, and pagination behaviour before implementing them in code.

---

### MCP Inspector

**Why:** The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) is the official debugging tool for MCP servers. It provides a browser-based UI for:

- Sending tool calls to a running MCP server
- Inspecting request/response JSON
- Validating tool schemas

It is essential during development to confirm tools behave correctly before connecting them to Claude or ChatGPT.

---

### Docker (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "server.main"]
```

**Why:** Docker is included as an optional deployment target to ensure consistent environments across development and any potential cloud deployment. It is not required for local development.

---

## Testing Stack

### pytest

```bash
pip install pytest pytest-asyncio pytest-cov
```

**Why:** `pytest` is the standard Python testing framework, chosen for:
- Clean fixture management for mocking GitHub API responses
- `pytest-asyncio` plugin for testing async tool handlers
- `pytest-cov` for coverage reporting

The test structure in [openedx/edx-repo-health](https://github.com/openedx/edx-repo-health) demonstrates using a pytest-based plugin system for repo health checks — this project adopts a similar philosophy for test organization.

### unittest.mock

**Why:** Python's standard `unittest.mock` is used to mock GitHub API responses and LLM API calls in unit tests, preventing any real network calls during testing.

### Example Test Pattern

```python
from unittest.mock import patch, MagicMock
import pytest
from services.metrics_engine import compute_health_score

@pytest.fixture
def mock_commits():
    return [{"commit": {"author": {"date": "2025-05-01T00:00:00Z"}}} for _ in range(25)]

def test_health_score_active_repo(mock_commits):
    score = compute_health_score(commits=mock_commits, open_issues=10, closed_issues=90, open_prs=3, merged_prs=47)
    assert score >= 70
```

---

## Deployment Stack

### Local Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GITHUB_TOKEN and OPENAI_API_KEY
python -m server.main
```

The server starts over stdio transport and can be connected to Claude Desktop or the MCP Inspector.

### MCP Client Configuration (Claude Desktop)

```json
{
  "mcpServers": {
    "repo-health-assistant": {
      "command": "python",
      "args": ["-m", "server.main"],
      "cwd": "/path/to/github-repo-health-mcp",
      "env": {
        "GITHUB_TOKEN": "your_token_here",
        "OPENAI_API_KEY": "your_key_here"
      }
    }
  }
}
```

### Docker Deployment

```bash
docker build -t repo-health-mcp .
docker run -e GITHUB_TOKEN=... -e OPENAI_API_KEY=... repo-health-mcp
```

### Cloud Deployment (Future)

For cloud deployment, the FastAPI extension layer enables hosting on:
- **Railway** or **Render** for simple PaaS deployment
- **Google Cloud Run** or **AWS Lambda** for serverless HTTP endpoints

---

## Why This Stack Fits the Project

| Property | How the Stack Delivers It |
|----------|--------------------------|
| Student-friendly | Python is the most taught language in universities; all libraries have excellent documentation |
| Lightweight | No heavyweight framework like Django; FastAPI is optional; SQLite used over PostgreSQL |
| Low cost | OpenAI `gpt-4o-mini` is cost-effective; GitHub free tier provides 5,000 API requests/hour |
| API-centric | `httpx`, `openai`, and `mcp` are all purpose-built for API-first architectures |
| MCP-compatible | MCP Python SDK is the standard way to build MCP servers |
| Scalable | `asyncio` + `httpx.AsyncClient` provides a path to concurrent processing without architectural changes |

---

## Future Technology Improvements

| Technology | Purpose | When to Adopt |
|------------|---------|--------------|
| **LangChain / LangGraph** | Orchestrate multi-step LLM workflows with agents and tool chains | When assessment logic becomes too complex for single prompts |
| **Qdrant / Chroma (Vector DB)** | Semantic search across historical code reviews and issue archives | When review history storage is implemented |
| **GitHub GraphQL API (v4)** | More efficient nested data fetching (e.g., repo + issues + PRs in one query) | When GitHub REST rate limits become a bottleneck |
| **Redis** | Distributed session-level caching for multi-user deployments | When moving to a hosted/shared service model |
| **Kubernetes** | Container orchestration for high-availability deployments | If the project moves to enterprise-grade hosting |
| **Prometheus + Grafana** | Observability and metrics dashboards for production monitoring | After initial production deployment |
| **Anthropic Claude API** | Alternative or complementary LLM provider | For comparison benchmarking or cost optimization |
