/**
 * hooks/useRepoData.ts
 * --------------------
 * React hooks that fetch live data from the FastAPI backend.
 * Drop-in replacements for the static mockData imports.
 *
 * useRepositories()    — replaces mockRepositories + mockDashboardStats
 * useRepoDetails()     — replaces mockRepoDetailsMap[repo.id]
 *
 * Both hooks follow the same pattern:
 *   { data, loading, error, refetch }
 *
 * The data shape matches the TypeScript interfaces in dashboard.ts exactly,
 * so no changes are needed in DashboardPage, RepoDetailsPage, or AIInsightsPanel.
 */

import { useState, useEffect, useCallback } from 'react';
import { Repository, RepoDetails, DashboardStats } from '../types/dashboard';
import { api, ApiError } from '../api/client';

// ---------------------------------------------------------------------------
// Default repos shown on first load — edit this list to change what appears
// on the Dashboard before the user searches for anything.
// ---------------------------------------------------------------------------

export const DEFAULT_REPOS: { owner: string; repo: string }[] = [
  { owner: 'your-org', repo: 'your-repo' },
  { owner: 'facebook',    repo: 'react' },
  { owner: 'vercel',      repo: 'next.js' },
  { owner: 'tailwindlabs', repo: 'tailwindcss' },
  { owner: 'vitejs',      repo: 'vite' },
  { owner: 'pallets',     repo: 'flask' },
  { owner: 'microsoft',   repo: 'vscode' },
];

// ---------------------------------------------------------------------------
// Shared hook state shape
// ---------------------------------------------------------------------------

interface HookState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

// ---------------------------------------------------------------------------
// useRepositories — populates DashboardPage
// ---------------------------------------------------------------------------

interface RepositoriesState {
  repositories: Repository[];
  stats: DashboardStats;
}

const DEFAULT_STATS: DashboardStats = {
  totalRepos: 0,
  openIssues: 0,
  openPRs: 0,
  avgHealthScore: 0,
  avgResponseTimeDays: 0,
  totalContributors: 0,
};

export function useRepositories(
  repos: { owner: string; repo: string }[] = DEFAULT_REPOS
): HookState<RepositoriesState> {
  const [data, setData]       = useState<RepositoriesState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);
  const [tick, setTick]       = useState(0);

  const refetch = useCallback(() => setTick(t => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    api.getMultipleRepos(repos)
      .then(res => {
        if (!cancelled) {
          setData({ repositories: res.repositories, stats: res.stats });
        }
      })
      .catch(err => {
        if (!cancelled) {
          const msg = err instanceof ApiError ? err.userMessage : String(err);
          setError(msg);
          // Fall back to empty state so the UI doesn't crash
          setData({ repositories: [], stats: DEFAULT_STATS });
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [repos, tick]); // eslint-disable-line react-hooks/exhaustive-deps

  return { data, loading, error, refetch };
}

// ---------------------------------------------------------------------------
// useRepoDetails — populates RepoDetailsPage and AIInsightsPanel
// ---------------------------------------------------------------------------

export function useRepoDetails(
  owner: string | undefined,
  repo:  string | undefined,
): HookState<RepoDetails> {
  const [data, setData]       = useState<RepoDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [tick, setTick]       = useState(0);

  const refetch = useCallback(() => setTick(t => t + 1), []);

  useEffect(() => {
    if (!owner || !repo) return;

    let cancelled = false;
    setLoading(true);
    setError(null);
    setData(null);

    api.getFullAssessment(owner, repo)
      .then(res => {
        if (!cancelled) setData(res);
      })
      .catch(err => {
        if (!cancelled) {
          const msg = err instanceof ApiError ? err.userMessage : String(err);
          setError(msg);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [owner, repo, tick]);

  return { data, loading, error, refetch };
}

// ---------------------------------------------------------------------------
// useRepoSearch — lets users add any GitHub repo on the fly
// ---------------------------------------------------------------------------

interface SearchState {
  result: Repository | null;
  loading: boolean;
  error: string | null;
}

export function useRepoSearch() {
  const [state, setState] = useState<SearchState>({
    result: null, loading: false, error: null,
  });

  const search = useCallback(async (owner: string, repo: string) => {
    setState({ result: null, loading: true, error: null });
    try {
      const res = await api.getRepoHealth(owner, repo);
      setState({ result: res.repository, loading: false, error: null });
      return res.repository;
    } catch (err) {
      const msg = err instanceof ApiError ? err.userMessage : String(err);
      setState({ result: null, loading: false, error: msg });
      return null;
    }
  }, []);

  return { ...state, search };
}
