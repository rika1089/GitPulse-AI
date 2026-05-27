import { Repository, RepoDetails, DashboardStats } from '../types/dashboard';

export const mockDashboardStats: DashboardStats = {
  totalRepos: 6,
  openIssues: 382,
  openPRs: 94,
  avgHealthScore: 78.5,
  avgResponseTimeDays: 2.1,
  totalContributors: 154,
};

export const mockRepositories: Repository[] = [
  {
    id: 'react-health',
    name: 'react',
    owner: 'facebook',
    description: 'The library for web and native user interfaces.',
    stars: 221000,
    forks: 44200,
    watchers: 6800,
    license: 'MIT',
    openIssuesCount: 240,
    closedIssuesCount: 12400,
    openPRsCount: 45,
    mergedPRsCount: 9800,
    avgResponseTimeDays: 1.4,
    avgCloseTimeDays: 3.2,
    lastPushDate: '2 hours ago',
    healthScore: 94,
    classification: 'Healthy',
    activityStatus: 'High',
    primaryLanguage: 'JavaScript',
    languages: [
      { name: 'JavaScript', percentage: 94.2, color: '#f1e05a' },
      { name: 'HTML', percentage: 2.8, color: '#e34c26' },
      { name: 'TypeScript', percentage: 1.9, color: '#3178c6' },
      { name: 'CSS', percentage: 1.1, color: '#563d7c' },
    ],
    topics: ['react', 'frontend', 'declarative', 'ui', 'library', 'javascript'],
  },
  {
    id: 'nextjs-health',
    name: 'next.js',
    owner: 'vercel',
    description: 'The React Framework for the Web.',
    stars: 120500,
    forks: 25400,
    watchers: 1700,
    license: 'MIT',
    openIssuesCount: 110,
    closedIssuesCount: 18700,
    openPRsCount: 32,
    mergedPRsCount: 14500,
    avgResponseTimeDays: 0.8,
    avgCloseTimeDays: 1.9,
    lastPushDate: '45 mins ago',
    healthScore: 97,
    classification: 'Healthy',
    activityStatus: 'High',
    primaryLanguage: 'TypeScript',
    languages: [
      { name: 'TypeScript', percentage: 89.4, color: '#3178c6' },
      { name: 'JavaScript', percentage: 9.8, color: '#f1e05a' },
      { name: 'CSS', percentage: 0.8, color: '#563d7c' },
    ],
    topics: ['nextjs', 'react', 'vercel', 'framework', 'ssr', 'typescript', 'server-components'],
  },
  {
    id: 'tailwind-health',
    name: 'tailwindcss',
    owner: 'tailwindlabs',
    description: 'A utility-first CSS framework for rapid UI development.',
    stars: 79200,
    forks: 4100,
    watchers: 950,
    license: 'MIT',
    openIssuesCount: 15,
    closedIssuesCount: 3400,
    openPRsCount: 8,
    mergedPRsCount: 2200,
    avgResponseTimeDays: 2.2,
    avgCloseTimeDays: 4.5,
    lastPushDate: '1 day ago',
    healthScore: 88,
    classification: 'Healthy',
    activityStatus: 'Moderate',
    primaryLanguage: 'TypeScript',
    languages: [
      { name: 'TypeScript', percentage: 76.5, color: '#3178c6' },
      { name: 'CSS', percentage: 12.3, color: '#563d7c' },
      { name: 'JavaScript', percentage: 11.2, color: '#f1e05a' },
    ],
    topics: ['tailwindcss', 'css', 'utility-first', 'design-system', 'postcss'],
  },
  {
    id: 'edx-health',
    name: 'edx-repo-health',
    owner: 'openedx',
    description: 'pytest-style checks that gather health information about repositories in the Open edX org.',
    stars: 12,
    forks: 18,
    watchers: 8,
    license: 'Apache-2.0',
    openIssuesCount: 8,
    closedIssuesCount: 24,
    openPRsCount: 4,
    mergedPRsCount: 85,
    avgResponseTimeDays: 5.6,
    avgCloseTimeDays: 14.2,
    lastPushDate: '2 months ago',
    healthScore: 62,
    classification: 'Stagnant',
    activityStatus: 'Low',
    primaryLanguage: 'Python',
    languages: [
      { name: 'Python', percentage: 89.3, color: '#3572A5' },
      { name: 'Shell', percentage: 6.7, color: '#89e051' },
      { name: 'Makefile', percentage: 3.7, color: '#427819' },
      { name: 'Dockerfile', percentage: 0.3, color: '#384d54' },
    ],
    topics: ['pytest', 'repo-health', 'open-edx', 'python', 'analytics'],
  },
  {
    id: 'code-review-mcp',
    name: 'code-review-mcp-server',
    owner: 'Orcus2021',
    description: 'MCP server for automated code reviews on GitHub Pull Requests.',
    stars: 8,
    forks: 3,
    watchers: 2,
    license: 'MIT',
    openIssuesCount: 9,
    closedIssuesCount: 4,
    openPRsCount: 5,
    mergedPRsCount: 6,
    avgResponseTimeDays: 12.4,
    avgCloseTimeDays: 24.8,
    lastPushDate: '5 months ago',
    healthScore: 45,
    classification: 'At Risk',
    activityStatus: 'Low',
    primaryLanguage: 'TypeScript',
    languages: [
      { name: 'TypeScript', percentage: 95.1, color: '#3178c6' },
      { name: 'JavaScript', percentage: 4.9, color: '#f1e05a' },
    ],
    topics: ['mcp-server', 'code-review', 'github-api', 'openai', 'typescript'],
  },
  {
    id: 'sastra-legacy',
    name: 'legacy-student-portal',
    owner: 'sastra-university',
    description: 'B.Tech IT program academic legacy student portal archives.',
    stars: 3,
    forks: 1,
    watchers: 2,
    license: 'None',
    openIssuesCount: 0,
    closedIssuesCount: 12,
    openPRsCount: 0,
    mergedPRsCount: 14,
    avgResponseTimeDays: 0,
    avgCloseTimeDays: 0,
    lastPushDate: '2 years ago',
    healthScore: 28,
    classification: 'Archived',
    activityStatus: 'Inactive',
    primaryLanguage: 'Java',
    languages: [
      { name: 'Java', percentage: 74.2, color: '#b07219' },
      { name: 'HTML', percentage: 18.5, color: '#e34c26' },
      { name: 'CSS', percentage: 7.3, color: '#563d7c' },
    ],
    topics: ['academic', 'legacy', 'java-ee', 'student-portal', 'sastra'],
  },
];

export const mockRepoDetailsMap: Record<string, RepoDetails> = {
  'react-health': {
    repository: mockRepositories[0],
    readmeQuality: {
      score: 95,
      checks: [
        { name: 'License Present', description: 'MIT license is clearly listed.', status: 'passed', feedback: 'Perfect placement in LICENSE.md.' },
        { name: 'Quick Start Guide', description: 'Steps to install and run React are clear.', status: 'passed', feedback: 'Includes npm instructions and basic template code.' },
        { name: 'Contributing Guidelines', description: 'CONTRIBUTING.md exists with clear rules.', status: 'passed', feedback: 'Excellent contributor flow setup.' },
        { name: 'Documentation Links', description: 'Links to official documentation are included.', status: 'passed', feedback: 'Points to react.dev with active routes.' },
      ]
    },
    security: {
      score: 90,
      checks: [
        { name: 'Dependency Vulnerabilities', description: 'Scanned third-party packages.', status: 'passed', feedback: '0 critical, 2 low vulnerabilities found.' },
        { name: 'Security Policy', description: 'SECURITY.md details disclosure channels.', status: 'passed', feedback: 'Clearly defined vulnerability reporting procedure.' },
        { name: 'Branch Protections', description: 'Main branch rules enforced.', status: 'passed', feedback: 'Requires 2 reviews and passing tests prior to merge.' },
      ]
    },
    ciCd: {
      score: 98,
      checks: [
        { name: 'GitHub Actions Configured', description: 'Workflows run automatically.', status: 'passed', feedback: 'Linting, testing, and size-limit checks active.' },
        { name: 'Unit Test Coverage', description: 'Coverage exceeds benchmark.', status: 'passed', feedback: 'Maintained at ~84.2% test coverage.' },
      ]
    },
    contributionHealth: {
      score: 92,
      checks: [
        { name: 'First Issue Friendly', description: 'Labels exist to guide beginners.', status: 'passed', feedback: '24 active issues labeled "good first issue".' },
        { name: 'Maintainer Responsiveness', description: 'Average response times are prompt.', status: 'passed', feedback: 'First response typically under 1.4 days.' },
      ]
    },
    contributors: [
      { name: 'gaearon', avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=80&fit=crop&q=80', commits: 1450, prs: 310, role: 'Lead Maintainer', activityLevel: 'Active' },
      { name: 'acdlite', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80', commits: 980, prs: 185, role: 'Core Reviewer', activityLevel: 'Active' },
      { name: 'sebmarkbage', avatarUrl: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&fit=crop&q=80', commits: 890, prs: 142, role: 'Core Architect', activityLevel: 'Stale' },
      { name: 'sophiebits', avatarUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=80&fit=crop&q=80', commits: 640, prs: 98, role: 'Contributor', activityLevel: 'Stale' },
    ],
    timeline: [
      { id: '1', type: 'commit', title: 'Refactor Suspense Boundaries', description: 'Optimize suspense resolution timing and context propagation.', user: { name: 'acdlite', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80' }, timestamp: '2 hours ago' },
      { id: '2', type: 'pr_merge', title: 'Merge PR #28410: Fix hydration mismatches in production', description: 'Resolves server-client HTML delta errors for dynamic dates.', user: { name: 'gaearon', avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=80&fit=crop&q=80' }, timestamp: '5 hours ago' },
      { id: '3', type: 'issue_close', title: 'Close #27998: Suspense triggers infinite loops inside portals', description: 'Fixed by patch in suspender engine.', user: { name: 'gaearon', avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=80&fit=crop&q=80' }, timestamp: '1 day ago' },
      { id: '4', type: 'release', title: 'Release v19.0.0-rc.0', description: 'First release candidate for React 19 featuring Server Components.', user: { name: 'acdlite', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80' }, timestamp: '3 days ago' },
    ],
    insights: {
      summary: 'facebook/react maintains exemplary open-source health. The project exhibits outstanding issue resolution times, robust automated CI/CD systems, and high documentation standards. Contributor growth remains stable.',
      strengths: [
        'Rapid PR response times (average under 1.4 days).',
        'Comprehensive GitHub Actions test coverage (~84%).',
        'Healthy documentation quality score of 95% with clear contribution guidelines.'
      ],
      risks: [
        'High dependency on 3 central maintainers for code reviews.',
        'Minor stale issues in complex SSR hydrate segments that require expert sorting.'
      ],
      recommendations: [
        { title: 'Expand reviewer permissions', description: 'Promote active non-employee contributors to review-only maintainers to mitigate bottlenecks.', impact: 'High', category: 'Activity' },
        { title: 'Resolve low dependency vulns', description: 'Upgrade development bundler packages flagged by Dependabot audits.', impact: 'Medium', category: 'Security' },
      ]
    }
  },
  'nextjs-health': {
    repository: mockRepositories[1],
    readmeQuality: {
      score: 98,
      checks: [
        { name: 'License Present', description: 'MIT license is clearly listed.', status: 'passed', feedback: 'Perfect placement in LICENSE.' },
        { name: 'Quick Start Guide', description: 'Steps to install and run Next.js are clear.', status: 'passed', feedback: 'Vite/Create-Next-App command provided.' },
        { name: 'Contributing Guidelines', description: 'CONTRIBUTING.md exists with clear rules.', status: 'passed', feedback: 'Includes detailed monorepo development setup.' },
        { name: 'Documentation Links', description: 'Links to official documentation are included.', status: 'passed', feedback: 'Direct links to nextjs.org/docs.' },
      ]
    },
    security: {
      score: 95,
      checks: [
        { name: 'Dependency Vulnerabilities', description: 'Scanned third-party packages.', status: 'passed', feedback: '0 critical vulnerabilities, package lockdown active.' },
        { name: 'Security Policy', description: 'SECURITY.md details disclosure channels.', status: 'passed', feedback: 'Vercel security email listed for reporting.' },
        { name: 'Branch Protections', description: 'Main branch rules enforced.', status: 'passed', feedback: 'Strict CI passing required prior to trunk merge.' },
      ]
    },
    ciCd: {
      score: 95,
      checks: [
        { name: 'GitHub Actions Configured', description: 'Workflows run automatically.', status: 'passed', feedback: 'Turborepo caching active, speeding up PR checks.' },
        { name: 'Unit Test Coverage', description: 'Coverage exceeds benchmark.', status: 'passed', feedback: 'High coverage on core runtime compiler modules.' },
      ]
    },
    contributionHealth: {
      score: 94,
      checks: [
        { name: 'First Issue Friendly', description: 'Labels exist to guide beginners.', status: 'passed', feedback: '18 issues marked "good first issue".' },
        { name: 'Maintainer Responsiveness', description: 'Average response times are prompt.', status: 'passed', feedback: 'First response routinely under 1 day.' },
      ]
    },
    contributors: [
      { name: 'timneutkens', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80', commits: 2100, prs: 410, role: 'Framework Lead', activityLevel: 'Active' },
      { name: 'huozhi', avatarUrl: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&fit=crop&q=80', commits: 1200, prs: 230, role: 'Core Engineer', activityLevel: 'Active' },
      { name: 'shuding', avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=80&fit=crop&q=80', commits: 980, prs: 180, role: 'Reviewer', activityLevel: 'Active' },
    ],
    timeline: [
      { id: '1', type: 'commit', title: 'Upgrade swc compiler engine', description: 'Optimizes server component compilation speed.', user: { name: 'huozhi', avatarUrl: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&fit=crop&q=80' }, timestamp: '45 mins ago' },
      { id: '2', type: 'pr_merge', title: 'Merge PR #62810: Fix fetch cache tagging error', description: 'Resolves SSR page caching inconsistencies during parallel revalidation.', user: { name: 'timneutkens', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80' }, timestamp: '3 hours ago' },
      { id: '3', type: 'release', title: 'Release v15.2.0', description: 'Introduces partial prerendering stabilization.', user: { name: 'timneutkens', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80' }, timestamp: '1 day ago' },
    ],
    insights: {
      summary: 'vercel/next.js has elite performance indicators. Excellent release rhythms, Turborepo optimizations, and a rapid, automated PR merging workflow represent top-tier open-source engineering standards.',
      strengths: [
        'Average issue closing time is under 2 days.',
        'Extremely active maintainer involvement with regular minor releases.',
        'High TypeScript typing coverage on public frameworks APIs.'
      ],
      risks: [
        'Monorepo complexity causes high CI/CD build queue costs.',
        'Heavy dependence on Vercel proprietary infrastructure for testing certain routing elements.'
      ],
      recommendations: [
        { title: 'Isolate local testing environments', description: 'Develop mock routing middleware so external contributors do not require Vercel test deployments.', impact: 'Medium', category: 'Code Quality' },
      ]
    }
  },
  'tailwind-health': {
    repository: mockRepositories[2],
    readmeQuality: {
      score: 92,
      checks: [
        { name: 'License Present', description: 'MIT license is clearly listed.', status: 'passed', feedback: 'Listed in README and LICENSE.' },
        { name: 'Quick Start Guide', description: 'Steps to install are clear.', status: 'passed', feedback: 'Covers CLI and postcss methods.' },
        { name: 'Contributing Guidelines', description: 'CONTRIBUTING.md exists with clear rules.', status: 'passed', feedback: 'Rules are straightforward but simple.' },
        { name: 'Documentation Links', description: 'Links to official documentation are included.', status: 'passed', feedback: 'Points to tailwindcss.com.' },
      ]
    },
    security: {
      score: 85,
      checks: [
        { name: 'Dependency Vulnerabilities', description: 'Scanned third-party packages.', status: 'passed', feedback: '0 vulns detected.' },
        { name: 'Security Policy', description: 'SECURITY.md details disclosure channels.', status: 'warning', feedback: 'SECURITY.md is missing; utilizes standard GitHub fallback policy.' },
        { name: 'Branch Protections', description: 'Main branch rules enforced.', status: 'passed', feedback: 'Protected branch setup.' },
      ]
    },
    ciCd: {
      score: 90,
      checks: [
        { name: 'GitHub Actions Configured', description: 'Workflows run automatically.', status: 'passed', feedback: 'Runs tests on multiple Node versions.' },
        { name: 'Unit Test Coverage', description: 'Coverage exceeds benchmark.', status: 'passed', feedback: 'Good compiler parsing tests.' },
      ]
    },
    contributionHealth: {
      score: 80,
      checks: [
        { name: 'First Issue Friendly', description: 'Labels exist to guide beginners.', status: 'warning', feedback: 'Few issues labeled "good first issue"; maintainers prefer fixing bugs quickly themselves.' },
        { name: 'Maintainer Responsiveness', description: 'Average response times are prompt.', status: 'passed', feedback: 'First response usually in 2.2 days.' },
      ]
    },
    contributors: [
      { name: 'adamwathan', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80', commits: 3400, prs: 520, role: 'Creator & Lead', activityLevel: 'Active' },
      { name: 'reinink', avatarUrl: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&fit=crop&q=80', commits: 540, prs: 45, role: 'Core Dev', activityLevel: 'Stale' },
    ],
    timeline: [
      { id: '1', type: 'commit', title: 'Add utility for scroll-bar-gutter', description: 'Supports standard scroll-bar-gutter layouts in custom theme.', user: { name: 'adamwathan', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80' }, timestamp: '1 day ago' },
      { id: '2', type: 'pr_merge', title: 'Merge PR #14201: Fix parsing of negative grid spans', description: 'Resolves issue with layout overlap in responsive grids.', user: { name: 'adamwathan', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80' }, timestamp: '3 days ago' },
    ],
    insights: {
      summary: 'tailwindlabs/tailwindcss is very stable. Standard development is driven primarily by core maintainer commits, resulting in super clean releases, though external contributor onboarding is moderate.',
      strengths: [
        'Extremely high code stability with zero current vulnerabilities.',
        'Clear, concise documentation.'
      ],
      risks: [
        'Single maintainer dependency (Adam Wathan).',
        'Lack of formal SECURITY.md vulnerability guide.'
      ],
      recommendations: [
        { title: 'Create SECURITY.md file', description: 'Establish a secure pathway for researchers to report compiler security vectors.', impact: 'High', category: 'Security' },
        { title: 'Label starter issues', description: 'Designate lightweight utility class requests as "good first issues" to encourage community contribution.', impact: 'Low', category: 'Documentation' },
      ]
    }
  },
  'edx-health': {
    repository: mockRepositories[3],
    readmeQuality: {
      score: 75,
      checks: [
        { name: 'License Present', description: 'Apache 2.0 license present.', status: 'passed', feedback: 'Listed in LICENSE.txt.' },
        { name: 'Quick Start Guide', description: 'Steps are outlined but outdated.', status: 'warning', feedback: 'Python virtualenv setup refers to Python 3.6.' },
        { name: 'Contributing Guidelines', description: 'CONTRIBUTING.md is absent.', status: 'failed', feedback: 'No contributing guild was found at root.' },
        { name: 'Documentation Links', description: 'Documentation is sparse.', status: 'warning', feedback: 'Refers to internal wiki links that are now broken.' },
      ]
    },
    security: {
      score: 60,
      checks: [
        { name: 'Dependency Vulnerabilities', description: 'Scanned third-party packages.', status: 'warning', feedback: '3 high-severity dependencies found in requirements.txt (old pytest versions).' },
        { name: 'Security Policy', description: 'SECURITY.md is missing.', status: 'failed', feedback: 'No security policy established.' },
        { name: 'Branch Protections', description: 'Enforcement state is weak.', status: 'warning', feedback: 'Branch is not locked down; push permissions are wide.' },
      ]
    },
    ciCd: {
      score: 70,
      checks: [
        { name: 'GitHub Actions Configured', description: 'Workflows exist.', status: 'passed', feedback: 'Standard make test active.' },
        { name: 'Unit Test Coverage', description: 'Coverage metrics.', status: 'warning', feedback: 'Coverage stands at ~52.1%; missing test cases for core metric modules.' },
      ]
    },
    contributionHealth: {
      score: 50,
      checks: [
        { name: 'First Issue Friendly', description: 'No beginner guidance.', status: 'failed', feedback: '0 open issues labeled for first-timers.' },
        { name: 'Maintainer Responsiveness', description: 'Response is slow.', status: 'failed', feedback: 'First response takes average 5.6 days.' },
      ]
    },
    contributors: [
      { name: 'feanil', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80', commits: 52, prs: 11, role: 'Maintainer', activityLevel: 'Stale' },
      { name: 'nedbat', avatarUrl: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&fit=crop&q=80', commits: 15, prs: 4, role: 'Reviewer', activityLevel: 'Stale' },
    ],
    timeline: [
      { id: '1', type: 'commit', title: 'Fix python 3.9 deprecation warnings', description: 'Resolve parser exceptions in old setup files.', user: { name: 'feanil', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80' }, timestamp: '2 months ago' },
      { id: '2', type: 'pr_open', title: 'Open PR #89: Add dependency scanning action', description: 'Proposed integration for vulnerability analysis.', user: { name: 'nedbat', avatarUrl: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&fit=crop&q=80' }, timestamp: '3 months ago' },
    ],
    insights: {
      summary: 'openedx/edx-repo-health exhibits high signs of stagnant activity. Main maintenance drives have halted. Issues have aged and documentation needs substantial modernization.',
      strengths: [
        'Clear tool foundation based on the edX pytest specifications.'
      ],
      risks: [
        'Outdated Python virtualenv settings and broken links.',
        'High dependency vulnerabilities in core package declarations.',
        'Extremely slow response times (average 5.6 days).'
      ],
      recommendations: [
        { title: 'Modernize developer setup', description: 'Update readme virtualenv rules to reference Python 3.10+ and prune broken links.', impact: 'High', category: 'Documentation' },
        { title: 'Patch requirements files', description: 'Upgrade older packages to secure pytest versions.', impact: 'High', category: 'Security' },
      ]
    }
  },
  'code-review-mcp': {
    repository: mockRepositories[4],
    readmeQuality: {
      score: 55,
      checks: [
        { name: 'License Present', description: 'License is found.', status: 'passed', feedback: 'MIT license active.' },
        { name: 'Quick Start Guide', description: 'Installation is vague.', status: 'warning', feedback: 'Lacks guidance on setting environment variables like GITHUB_TOKEN.' },
        { name: 'Contributing Guidelines', description: 'No CONTRIBUTING.md exists.', status: 'failed', feedback: 'No onboarding guide.' },
        { name: 'Documentation Links', description: 'Missing index links.', status: 'failed', feedback: 'Documentation is completely inline inside a single README page.' },
      ]
    },
    security: {
      score: 40,
      checks: [
        { name: 'Dependency Vulnerabilities', description: 'Package checks.', status: 'failed', feedback: '2 critical vulnerabilities located in dev packages.' },
        { name: 'Security Policy', description: 'No security policy exists.', status: 'failed', feedback: 'No security contacts.' },
        { name: 'Branch Protections', description: 'No protections active.', status: 'failed', feedback: 'Commits can be pushed directly to main branch without checks.' },
      ]
    },
    ciCd: {
      score: 45,
      checks: [
        { name: 'GitHub Actions Configured', description: 'Build system.', status: 'failed', feedback: 'No CI workflows configured. Builds are manually verified.' },
        { name: 'Unit Test Coverage', description: 'Tests are absent.', status: 'failed', feedback: 'No test suite was found.' },
      ]
    },
    contributionHealth: {
      score: 35,
      checks: [
        { name: 'First Issue Friendly', description: 'No issues listed.', status: 'failed', feedback: 'No issues labeled for beginners.' },
        { name: 'Maintainer Responsiveness', description: 'Extremely slow response.', status: 'failed', feedback: 'First response average takes 12.4 days.' },
      ]
    },
    contributors: [
      { name: 'Orcus2021', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80', commits: 24, prs: 3, role: 'Author & Dev', activityLevel: 'Stale' },
    ],
    timeline: [
      { id: '1', type: 'pr_open', title: 'Open PR #12: Fix OpenAI API schema error', description: 'Attempts to resolve JSON validation issues inside reviews.', user: { name: 'Orcus2021', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80' }, timestamp: '5 months ago' },
    ],
    insights: {
      summary: 'orcus2021/code-review-mcp-server is currently at high risk. There are critical vulnerabilities, a lack of CI testing pipelines, and no active branch protections.',
      strengths: [
        'Great conceptual implementation of a typescript-based MCP server.'
      ],
      risks: [
        'Complete absence of test suites and CI checks.',
        'Direct push rules allow unreviewed code into main branch.',
        'Average maintainer response time exceeds 12 days.'
      ],
      recommendations: [
        { title: 'Establish CI check system', description: 'Incorporate GitHub Actions with compile and typescript checks.', impact: 'High', category: 'Activity' },
        { title: 'Introduce unit tests', description: 'Add Jest or Vitest structure and test parsing engines.', impact: 'High', category: 'Code Quality' },
      ]
    }
  },
  'sastra-legacy': {
    repository: mockRepositories[5],
    readmeQuality: {
      score: 30,
      checks: [
        { name: 'License Present', description: 'No license.', status: 'failed', feedback: 'Proprietary or undefined license structure.' },
        { name: 'Quick Start Guide', description: 'No install details.', status: 'failed', feedback: 'Mentions local intranet server setups only.' },
        { name: 'Contributing Guidelines', description: 'No guidance.', status: 'failed', feedback: 'Closed source repository.' },
        { name: 'Documentation Links', description: 'None.', status: 'failed', feedback: 'All links points to old university intranet hosts.' },
      ]
    },
    security: {
      score: 20,
      checks: [
        { name: 'Dependency Vulnerabilities', description: 'Very old dependencies.', status: 'failed', feedback: 'Multiple critical security holes in old Java packages.' },
        { name: 'Security Policy', description: 'None.', status: 'failed', feedback: 'No security disclosures.' },
        { name: 'Branch Protections', description: 'None.', status: 'failed', feedback: 'No active safeguards.' },
      ]
    },
    ciCd: {
      score: 10,
      checks: [
        { name: 'GitHub Actions Configured', description: 'None.', status: 'failed', feedback: 'No automated actions.' },
        { name: 'Unit Test Coverage', description: 'No tests.', status: 'failed', feedback: '0% coverage.' },
      ]
    },
    contributionHealth: {
      score: 10,
      checks: [
        { name: 'First Issue Friendly', description: 'Closed development.', status: 'failed', feedback: 'No external issues permitted.' },
        { name: 'Maintainer Responsiveness', description: 'Dead project.', status: 'failed', feedback: '0 replies in years.' },
      ]
    },
    contributors: [
      { name: 'sastra-it-dev', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80', commits: 64, prs: 14, role: 'System Admin', activityLevel: 'Stale' },
    ],
    timeline: [
      { id: '1', type: 'release', title: 'Release v1.2-archive', description: 'Final legacy build snapshot.', user: { name: 'sastra-it-dev', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&fit=crop&q=80' }, timestamp: '2 years ago' },
    ],
    insights: {
      summary: 'This repository is fully archived and obsolete. It contains legacy systems for the B.Tech IT student portal and is kept for historic/academic reference. Active engineering checks are unnecessary.',
      strengths: [
        'Historical archival record.'
      ],
      risks: [
        'Outdated, vulnerable Java dependencies.'
      ],
      recommendations: [
        { title: 'Mark repo as archived', description: 'Click Archive in GitHub settings to explicitly label it read-only.', impact: 'Medium', category: 'Security' },
      ]
    }
  }
};

// Activity Charts mock data
export const mockCommitActivity = [
  { name: 'Jan', 'facebook/react': 180, 'vercel/next.js': 240, 'tailwindlabs/tailwindcss': 90, 'openedx/edx-repo-health': 5 },
  { name: 'Feb', 'facebook/react': 195, 'vercel/next.js': 280, 'tailwindlabs/tailwindcss': 75, 'openedx/edx-repo-health': 2 },
  { name: 'Mar', 'facebook/react': 160, 'vercel/next.js': 310, 'tailwindlabs/tailwindcss': 110, 'openedx/edx-repo-health': 0 },
  { name: 'Apr', 'facebook/react': 210, 'vercel/next.js': 270, 'tailwindlabs/tailwindcss': 85, 'openedx/edx-repo-health': 8 },
  { name: 'May', 'facebook/react': 185, 'vercel/next.js': 295, 'tailwindlabs/tailwindcss': 95, 'openedx/edx-repo-health': 12 },
  { name: 'Jun', 'facebook/react': 220, 'vercel/next.js': 320, 'tailwindlabs/tailwindcss': 105, 'openedx/edx-repo-health': 1 },
];

export const mockPRTrends = [
  { name: 'Jan', open: 45, merged: 110, closed: 12 },
  { name: 'Feb', open: 52, merged: 134, closed: 18 },
  { name: 'Mar', open: 41, merged: 156, closed: 9 },
  { name: 'Apr', open: 60, merged: 122, closed: 22 },
  { name: 'May', open: 49, merged: 147, closed: 15 },
  { name: 'Jun', open: 54, merged: 165, closed: 14 },
];

export const mockIssueTrends = [
  { name: 'Jan', active: 180, resolved: 145 },
  { name: 'Feb', active: 204, resolved: 162 },
  { name: 'Mar', active: 190, resolved: 178 },
  { name: 'Apr', active: 225, resolved: 152 },
  { name: 'May', active: 210, resolved: 194 },
  { name: 'Jun', active: 198, resolved: 212 },
];

export const mockContributorActivity = [
  { name: 'Jan', active: 85, new: 12 },
  { name: 'Feb', active: 94, new: 18 },
  { name: 'Mar', active: 102, new: 8 },
  { name: 'Apr', active: 98, new: 14 },
  { name: 'May', active: 115, new: 22 },
  { name: 'Jun', active: 124, new: 19 },
];
