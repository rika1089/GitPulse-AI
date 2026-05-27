import React from 'react';
import { motion } from 'framer-motion';
import { 
  GitPullRequest, 
  AlertCircle, 
  Users, 
  Activity, 
  Hourglass, 
  FolderGit2
} from 'lucide-react';
import { Repository, DashboardStats } from '../types/dashboard';
import { MetricCard } from '../components/MetricCard';
import { ChartCard } from '../components/ChartCard';
import { RepoTable } from '../components/RepoTable';
import { 
  mockCommitActivity, 
  mockPRTrends, 
  mockIssueTrends, 
  mockContributorActivity 
} from '../data/mockData';

interface DashboardPageProps {
  stats: DashboardStats;
  repositories: Repository[];
  setSelectedRepo: (repo: Repository) => void;
  setCurrentTab: (tab: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  stats,
  repositories,
  setSelectedRepo,
  setCurrentTab,
}) => {
  const handleSelectRepo = (repo: Repository) => {
    setSelectedRepo(repo);
    setCurrentTab('details');
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-8 p-4 md:p-6 lg:p-8"
    >
      {/* Dashboard Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-900 pb-6 text-left">
        <div>
          <h2 className="font-outfit text-2xl font-extrabold text-white md:text-3xl tracking-tight">
            Repository Cockpit
          </h2>
          <p className="text-sm text-zinc-500 mt-1">
            Aggregated metric logs and active pipelines for your GitHub workspace.
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-400">
          <span>Synced: 1 min ago</span>
        </div>
      </div>

      {/* Metrics Row Grid */}
      <motion.div 
        variants={itemVariants} 
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4"
      >
        <MetricCard
          title="Total Repositories"
          value={stats.totalRepos}
          description="Monitored in project space"
          icon={FolderGit2}
          glowColor="indigo"
        />
        <MetricCard
          title="Open Issues"
          value={stats.openIssues}
          description="Across all repositories"
          icon={AlertCircle}
          trend={{ value: '+4.5%', isPositive: false }}
          glowColor="amber"
        />
        <MetricCard
          title="Open PRs"
          value={stats.openPRs}
          description="Pending review cycles"
          icon={GitPullRequest}
          trend={{ value: '-8.2%', isPositive: true }}
          glowColor="indigo"
        />
        <MetricCard
          title="Avg Health Score"
          value={`${stats.avgHealthScore}/100`}
          description="Overall organization health"
          icon={Activity}
          glowColor="emerald"
        />
        <MetricCard
          title="Avg Response Time"
          value={`${stats.avgResponseTimeDays}d`}
          description="First reply benchmark"
          icon={Hourglass}
          trend={{ value: '0.3d faster', isPositive: true }}
          glowColor="emerald"
        />
        <MetricCard
          title="Contributors"
          value={stats.totalContributors}
          description="Active code authors"
          icon={Users}
          glowColor="indigo"
        />
      </motion.div>

      {/* Charts Grid */}
      <motion.div 
        variants={itemVariants}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        <ChartCard
          title="Commit Activity Density"
          description="Volume of code additions per repository over the last 6 months"
          type="commit"
          data={mockCommitActivity}
        />
        <ChartCard
          title="Pull Request Throughput"
          description="Merged, pending, and closed review structures"
          type="pr"
          data={mockPRTrends}
        />
        <ChartCard
          title="Issue Pipeline Load"
          description="Active bugs opened versus items successfully resolved"
          type="issue"
          data={mockIssueTrends}
        />
        <ChartCard
          title="Contributor Velocity"
          description="Onboarding rate of new contributors versus active maintainers"
          type="contributor"
          data={mockContributorActivity}
        />
      </motion.div>

      {/* Repository Table Container */}
      <motion.div 
        variants={itemVariants}
        className="pt-4 text-left"
      >
        <div className="mb-4">
          <h3 className="font-outfit text-lg font-bold text-white">Monitored Codebases</h3>
          <p className="text-xs text-zinc-500 mt-0.5">Filter, sort, and select repository entries to deep dive into AI reviews</p>
        </div>

        <RepoTable 
          repositories={repositories} 
          onSelectRepo={handleSelectRepo} 
        />
      </motion.div>
    </motion.div>
  );
};
export default DashboardPage;
