# GitPulse — FastAPI + React integration

## What this zip contains

Backend (copy into gitpulse_mcp/):
  gitpulse_mcp/api/__init__.py
  gitpulse_mcp/api/main.py          ← FastAPI server

Frontend (copy into your React src/):
  src/api/client.ts                  ← typed fetch wrapper  (NEW file)
  src/hooks/useRepoData.ts           ← React hooks          (NEW file)
  src/App.tsx                        ← replaces existing App.tsx
  src/pages/RepoDetailsPage.tsx      ← replaces existing RepoDetailsPage.tsx
  src/pages/AIInsightsPanel.tsx      ← replaces existing AIInsightsPanel.tsx

## Step 1 — Install backend deps

  cd GitPulseAI
  .venv\Scripts\activate
  pip install fastapi uvicorn

## Step 2 — Copy backend file

  copy "gitpulse_mcp\api\__init__.py"  GitPulseAI\gitpulse_mcp\api\__init__.py
  copy "gitpulse_mcp\api\main.py"      GitPulseAI\gitpulse_mcp\api\main.py

## Step 3 — Copy frontend files

  # Create new folders first
  mkdir GitHubReview\src\api
  mkdir GitHubReview\src\hooks

  copy "src\api\client.ts"               GitHubReview\src\api\client.ts
  copy "src\hooks\useRepoData.ts"        GitHubReview\src\hooks\useRepoData.ts
  copy "src\App.tsx"                     GitHubReview\src\App.tsx
  copy "src\pages\RepoDetailsPage.tsx"   GitHubReview\src\pages\RepoDetailsPage.tsx
  copy "src\pages\AIInsightsPanel.tsx"   GitHubReview\src\pages\AIInsightsPanel.tsx

## Step 4 — Start both servers (two terminals)

  Terminal 1 — Backend:
    cd GitPulseAI\gitpulse_mcp
    uvicorn gitpulse_mcp.api.main:app --reload --port 8000

  Terminal 2 — Frontend:
    cd GitHubReview
    npm run dev

## Step 5 — Open http://localhost:5173

  The dashboard now shows live data from GitHub.
  First load takes 10-15 seconds per repo (GitHub API + OpenAI).
  Subsequent loads within 5 minutes use the session cache.

## Customise which repos appear on the dashboard

  Edit src/hooks/useRepoData.ts → DEFAULT_REPOS array:

    export const DEFAULT_REPOS = [
      { owner: 'your-org', repo: 'your-repo' },
      { owner: 'facebook',  repo: 'react' },
    ];
