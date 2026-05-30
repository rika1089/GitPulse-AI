/**
 * api/client.ts
 * -------------
 * Typed fetch wrapper for the GitPulse FastAPI backend.
 *
 * All components import from here — never call fetch() directly.
 * Change BASE_URL once and every endpoint updates automatically.
 *
 * Usage:
 *   import { api } from '../api/client';
 *   const health = await api.getRepoHealth('facebook', 'react');
 */

import { Repository, RepoDetails, DashboardStats } from '../types/dashboard';

const BASE_URL = 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Generic fetch helper — centralises error handling
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? 'Unknown error', path);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Custom error class — lets components distinguish API errors from crashes
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public path: string,
  ) {
    super(`API ${status} on ${path}: ${detail}`);
    this.name = 'ApiError';
  }

  get isNotFound()    { return this.status === 404; }
  get isRateLimit()   { return this.status === 429; }
  get isServerError() { return this.status >= 500; }

  /** Human-readable message suitable for showing in the UI */
  get userMessage(): string {
    if (this.isNotFound)  return 'Repository not found. Check the owner and repo name.';
    if (this.isRateLimit) return 'GitHub rate limit reached. Try again in a few minutes.';
    if (this.isServerError) return 'Server error. Check that the backend is running.';
    return this.detail;
  }
}

// ---------------------------------------------------------------------------
// Response shapes returned by the backend
// ---------------------------------------------------------------------------

export interface HealthResponse {
  repository: Repository;
  insights: RepoDetails['insights'];
  raw_metrics: Record<string, unknown>;
}

export interface ReposResponse {
  repositories: Repository[];
  stats: DashboardStats;
  errors: { repo: string; error: string }[];
}

export interface TriageResponse {
  owner: string;
  repo: string;
  issue_count: number;
  summary: string;
  categories: {
    high_priority_bugs: { number: number; title: string; reason: string }[];
    good_first_issues:  { number: number; title: string; reason: string }[];
    stale_issues:       { number: number; title: string; age_days: number; action: string }[];
    documentation_requests: number[];
    feature_requests:       number[];
  };
  recommendations: string[];
  health_signals: {
    has_stale_issues: boolean;
    has_unanswered_bugs: boolean;
    good_first_issue_count: number;
    estimated_backlog_health: 'Good' | 'Fair' | 'Poor';
  };
}

// ---------------------------------------------------------------------------
// API client object — one method per endpoint
// ---------------------------------------------------------------------------

export const api = {
  /**
   * Fetch health data for a single repository.
   * Used by: RepoDetailsPage, AIInsightsPanel (lightweight load)
   */
  getRepoHealth(owner: string, repo: string): Promise<HealthResponse> {
    return apiFetch(`/api/health/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}`);
  },

  /**
   * Full assessment — all 4 quality sections + timeline + insights.
   * Used by: RepoDetailsPage, AIInsightsPanel (full load)
   */
  getFullAssessment(owner: string, repo: string): Promise<RepoDetails> {
    return apiFetch(`/api/assess/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}`);
  },

  /**
   * Health data for multiple repos in one call — used by DashboardPage.
   * Returns repositories[] + aggregated DashboardStats.
   */
  getMultipleRepos(repos: { owner: string; repo: string }[]): Promise<ReposResponse> {
    return apiFetch('/api/repos', {
      method: 'POST',
      body: JSON.stringify({ repos }),
    });
  },

  /**
   * Issue triage for a repository.
   */
  triageIssues(owner: string, repo: string, maxIssues = 50): Promise<TriageResponse> {
    return apiFetch(
      `/api/triage/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}?max_issues=${maxIssues}`
    );
  },

  /**
   * Review a specific file.
   */
  reviewFile(owner: string, repo: string, path: string, ref = 'HEAD'): Promise<unknown> {
    return apiFetch('/api/review/file', {
      method: 'POST',
      body: JSON.stringify({ owner, repo, path, ref }),
    });
  },

  /**
   * Review a pull request.
   */
  reviewPR(owner: string, repo: string, prNumber: number): Promise<unknown> {
    return apiFetch('/api/review/pr', {
      method: 'POST',
      body: JSON.stringify({ owner, repo, pr_number: prNumber }),
    });
  },
};
