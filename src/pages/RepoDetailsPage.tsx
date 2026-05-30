import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Star, GitFork, Eye, FileCheck, ShieldAlert, PlayCircle, Users2,
  Clock, CheckCircle2, AlertTriangle, XCircle, Sparkles, ArrowRight,
  RefreshCw, AlertCircle,
} from 'lucide-react';
import { Repository, RepoDetails } from '../types/dashboard';
import { HealthBadge }       from '../components/HealthBadge';
import { ActivityTimeline }  from '../components/ActivityTimeline';
import { useRepoDetails }    from '../hooks/useRepoData';

interface RepoDetailsPageProps {
  selectedRepo: Repository | null;
  setCurrentTab: (tab: string) => void;
}

// Fallback empty RepoDetails shown while loading or on error
const EMPTY_DETAILS: RepoDetails = {
  repository: {} as Repository,
  readmeQuality:      { score: 0, checks: [] },
  security:           { score: 0, checks: [] },
  ciCd:               { score: 0, checks: [] },
  contributionHealth: { score: 0, checks: [] },
  contributors: [],
  timeline: [],
  insights: { summary: '', strengths: [], risks: [], recommendations: [] },
};

export const RepoDetailsPage: React.FC<RepoDetailsPageProps> = ({
  selectedRepo,
  setCurrentTab,
}) => {
  // ── Live data ─────────────────────────────────────────────────────────────
  const { data, loading, error, refetch } = useRepoDetails(
    selectedRepo?.owner,
    selectedRepo?.name,
  );

  const repoDetails: RepoDetails = data ?? EMPTY_DETAILS;
  const { repository, readmeQuality, security, ciCd, contributionHealth, timeline } = repoDetails;

  const checkGroups = useMemo(() => [
    { title: 'README & Documentation', score: readmeQuality.score,      checks: readmeQuality.checks,      icon: FileCheck,  color: 'text-cyan-400'    },
    { title: 'Security Safeguards',    score: security.score,           checks: security.checks,           icon: ShieldAlert,color: 'text-rose-400'    },
    { title: 'Automated CI/CD',        score: ciCd.score,               checks: ciCd.checks,               icon: PlayCircle, color: 'text-indigo-400'  },
    { title: 'Contribution Vitality',  score: contributionHealth.score, checks: contributionHealth.checks, icon: Users2,     color: 'text-emerald-400' },
  ], [readmeQuality, security, ciCd, contributionHealth]);

  const statusIcons = {
    passed:  <CheckCircle2  className="h-4 w-4 text-emerald-400 shrink-0" />,
    warning: <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0"   />,
    failed:  <XCircle       className="h-4 w-4 text-rose-500 shrink-0"    />,
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show:   { opacity: 1, transition: { staggerChildren: 0.05 } },
  };
  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show:   { opacity: 1, y: 0 },
  };

  // ── Loading state ─────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4 text-zinc-400">
        <RefreshCw className="h-8 w-8 animate-spin text-indigo-400" />
        <p className="text-sm">
          Analysing {selectedRepo?.owner}/{selectedRepo?.name}…
        </p>
        <p className="text-xs text-zinc-600">This takes 10-15 seconds for the first load</p>
      </div>
    );
  }

  // ── Error state ───────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4 p-8">
        <AlertCircle className="h-10 w-10 text-red-400" />
        <p className="text-sm text-red-400 text-center max-w-sm">{error}</p>
        <button
          onClick={refetch}
          className="flex items-center gap-2 rounded-lg border border-zinc-800 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900 transition-colors"
        >
          <RefreshCw className="h-4 w-4" /> Try again
        </button>
      </div>
    );
  }

  // ── No repo selected ──────────────────────────────────────────────────────
  if (!selectedRepo) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4 text-zinc-400">
        <p className="text-sm">Select a repository from the sidebar to view details.</p>
      </div>
    );
  }

  // ── Main content (identical to original) ─────────────────────────────────
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-8 p-4 md:p-6 lg:p-8"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex flex-col gap-4 border-b border-zinc-900 pb-6 text-left">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="font-outfit text-2xl font-extrabold text-white tracking-tight">
                {repository.owner}/{repository.name}
              </h2>
              {repository.classification && (
                <HealthBadge classification={repository.classification} />
              )}
            </div>
            <p className="text-sm text-zinc-500 mt-1">{repository.description}</p>
          </div>
          <div className="flex items-center gap-4 text-zinc-400 text-sm flex-wrap">
            {repository.stars !== undefined && (
              <span className="flex items-center gap-1.5">
                <Star className="h-4 w-4 text-amber-400" />
                {repository.stars.toLocaleString()}
              </span>
            )}
            {repository.forks !== undefined && (
              <span className="flex items-center gap-1.5">
                <GitFork className="h-4 w-4" />
                {repository.forks.toLocaleString()}
              </span>
            )}
            {repository.watchers !== undefined && (
              <span className="flex items-center gap-1.5">
                <Eye className="h-4 w-4" />
                {repository.watchers.toLocaleString()}
              </span>
            )}
            {repository.lastPushDate && (
              <span className="flex items-center gap-1.5">
                <Clock className="h-4 w-4" />
                {repository.lastPushDate}
              </span>
            )}
          </div>
        </div>

        {/* Refresh button */}
        <div className="flex items-center gap-2">
          <button
            onClick={refetch}
            className="flex items-center gap-1.5 rounded border border-zinc-800 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-900 hover:text-white transition-colors"
          >
            <RefreshCw className="h-3 w-3" /> Refresh
          </button>
          <button
            onClick={() => setCurrentTab('ai-insights')}
            className="flex items-center gap-1.5 rounded border border-indigo-500/30 bg-indigo-500/10 px-3 py-1.5 text-xs text-indigo-400 hover:bg-indigo-500/20 transition-colors"
          >
            <Sparkles className="h-3 w-3" /> AI Insights
            <ArrowRight className="h-3 w-3" />
          </button>
        </div>
      </motion.div>

      {/* Quality check sections */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
        {checkGroups.map(({ title, score, checks, icon: Icon, color }) => (
          <div key={title} className="glass-panel p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Icon className={`h-4.5 w-4.5 ${color}`} />
                <h4 className="font-outfit text-sm font-bold text-white">{title}</h4>
              </div>
              <span className={`font-mono text-sm font-bold ${
                score >= 80 ? 'text-emerald-400' :
                score >= 50 ? 'text-amber-400'   : 'text-rose-400'
              }`}>
                {score}/100
              </span>
            </div>
            {/* Score bar */}
            <div className="h-1.5 w-full rounded-full bg-zinc-900">
              <div
                className={`h-1.5 rounded-full transition-all duration-700 ${
                  score >= 80 ? 'bg-emerald-500' :
                  score >= 50 ? 'bg-amber-500'   : 'bg-rose-500'
                }`}
                style={{ width: `${score}%` }}
              />
            </div>
            <ul className="space-y-2">
              {checks.map((check, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  {statusIcons[check.status]}
                  <div>
                    <p className="text-xs font-semibold text-zinc-300">{check.name}</p>
                    <p className="text-[11px] text-zinc-500 mt-0.5">{check.feedback}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </motion.div>

      {/* Activity timeline */}
      {timeline.length > 0 && (
        <motion.div variants={itemVariants} className="text-left">
          <h3 className="font-outfit text-base font-bold text-white mb-4">Activity Timeline</h3>
          <ActivityTimeline items={timeline} />
        </motion.div>
      )}
    </motion.div>
  );
};

export default RepoDetailsPage;
