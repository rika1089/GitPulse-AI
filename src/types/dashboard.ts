export type HealthClassification = 'Healthy' | 'Stagnant' | 'At Risk' | 'Archived';

export interface Repository {
  id: string;
  name: string;
  owner: string;
  description: string;
  stars: number;
  forks: number;
  watchers: number;
  license: string;
  openIssuesCount: number;
  closedIssuesCount: number;
  openPRsCount: number;
  mergedPRsCount: number;
  avgResponseTimeDays: number;
  avgCloseTimeDays: number;
  lastPushDate: string; // ISO date or descriptive e.g. "2 days ago"
  healthScore: number;
  classification: HealthClassification;
  activityStatus: 'High' | 'Moderate' | 'Low' | 'Inactive';
  primaryLanguage: string;
  languages: { name: string; percentage: number; color: string }[];
  topics: string[];
}

export interface Contributor {
  name: string;
  avatarUrl: string;
  commits: number;
  prs: number;
  role: string;
  activityLevel: 'Active' | 'Very Active' | 'Stale';
}

export interface ActivityTimelineItem {
  id: string;
  type: 'commit' | 'pr_merge' | 'pr_open' | 'issue_open' | 'issue_close' | 'release';
  title: string;
  description: string;
  user: {
    name: string;
    avatarUrl: string;
  };
  timestamp: string;
}

export interface CheckItem {
  name: string;
  description: string;
  status: 'passed' | 'warning' | 'failed';
  feedback: string;
}

export interface RepoDetails {
  repository: Repository;
  readmeQuality: {
    score: number;
    checks: CheckItem[];
  };
  security: {
    score: number;
    checks: CheckItem[];
  };
  ciCd: {
    score: number;
    checks: CheckItem[];
  };
  contributionHealth: {
    score: number;
    checks: CheckItem[];
  };
  contributors: Contributor[];
  timeline: ActivityTimelineItem[];
  insights: {
    summary: string;
    strengths: string[];
    risks: string[];
    recommendations: {
      title: string;
      description: string;
      impact: 'High' | 'Medium' | 'Low';
      category: 'Security' | 'Documentation' | 'Activity' | 'Code Quality';
    }[];
  };
}

export interface DashboardStats {
  totalRepos: number;
  openIssues: number;
  openPRs: number;
  avgHealthScore: number;
  avgResponseTimeDays: number;
  totalContributors: number;
}
