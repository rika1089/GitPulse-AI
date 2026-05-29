# GitPulseAI — Fix & Setup Instructions

## What went wrong

Three issues in the current local setup:

1. **Missing `gitpulse_mcp/` sub-folder** — Python imports expect
   `from gitpulse_mcp.llm.schemas import ...` but your files sit flat
   inside `GitPulseAI/` with no `gitpulse_mcp/` wrapper directory.

2. **Old stub service files** — `services/triage_service.py` etc. still
   contained `raise NotImplementedError(...)` from Phase 1.

3. **pytest-asyncio not configured** — `asyncio_mode = "auto"` was missing
   from `pyproject.toml`, causing the `Unknown pytest.mark.asyncio` warnings.

---

## Fix: Step-by-step

### 1. Restructure your project folder

Open PowerShell in your `GitPulseAI/` root and run:

```powershell
# Create the package sub-folder
mkdir gitpulse_mcp

# Move all source code into it
Move-Item cache, github, llm, models, services, tools `
          config.py, main.py, __init__.py `
          gitpulse_mcp\
```

After this your folder should look like:
```
GitPulseAI/
├── gitpulse_mcp/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── cache/
│   ├── github/
│   ├── llm/
│   ├── models/
│   ├── services/
│   └── tools/
├── tests/
├── conftest.py          ← NEW (from this zip)
├── pyproject.toml       ← UPDATED (from this zip)
└── .env
```

### 2. Copy files from this zip

From the `gitpulse_mcp/` folder inside this zip, copy:

- `gitpulse_mcp/services/` → overwrite all 4 service files + `__init__.py`
- `gitpulse_mcp/llm/` → overwrite `client.py`, `schemas.py`, `__init__.py`
- `gitpulse_mcp/llm/prompts/` → copy all 5 `.txt` files
- `gitpulse_mcp/tests/` → overwrite all test files

From the zip root, copy:
- `conftest.py` → to your `GitPulseAI/` root
- `pyproject.toml` → to your `GitPulseAI/` root (overwrite existing)

### 3. Install dependencies

```powershell
cd GitPulseAI
pip install pytest pytest-asyncio respx httpx pydantic pydantic-settings openai python-dotenv anyio
```

Or if you have the project installed in editable mode:
```powershell
pip install -e ".[dev]"
```

### 4. Set up your .env file

Copy `.env.example` to `.env` and fill in your tokens:

```
GITHUB_TOKEN=ghp_your_token_here
OPENAI_API_KEY=sk-your_key_here
```

### 5. Run tests

```powershell
python -m pytest tests/ -v
```

Expected output: **64 passed**

---

## If you still get import errors

Run this to verify the package structure is correct:

```powershell
python -c "import gitpulse_mcp; print('OK')"
python -c "from gitpulse_mcp.llm.schemas import HealthNarrativeResponse; print('OK')"
python -c "from gitpulse_mcp.services.triage_service import TriageService; print('OK')"
```

All three should print `OK`. If the first fails, the `gitpulse_mcp/` folder
is either missing or not on your Python path — re-check Step 1.
