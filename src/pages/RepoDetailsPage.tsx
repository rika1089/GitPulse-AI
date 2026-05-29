import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { 
  Star, 
  GitFork, 
  Eye, 
  FileCheck, 
  ShieldAlert, 
  PlayCircle, 
  Users2, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { Repository, RepoDetails } from '../types/dashboard';
import { HealthBadge } from '../components/HealthBadge';
import { ActivityTimeline } from '../components/ActivityTimeline';
import { mockRepoDetailsMap } from '../data/mockData';

interface RepoDetailsPageProps {
  selectedRepo: Repository | null;
  setCurrentTab: (tab: string) => void;
}

export const RepoDetailsPage: React.FC<RepoDetailsPageProps> = ({
  selectedRepo,
  setCurrentTab,
}) => {
  // Use selectedRepo directly — look up mock details only for supplementary data
  const repoDetails: RepoDetails | null = useMemo(() => {
    if (!selectedRepo) return mockRepoDetailsMap['react-health'];
    // Try to find mock details for the checklist sections
    return mockRepoDetailsMap[selectedRepo.id] || null;
  }, [selectedRepo]);

  // Always use the real selectedRepo for the header — never fall back to mock
  const repository = selectedRepo || mockRepoDetailsMap['react-health'].repository;

  // For checklist/timeline sections, use mock details if available, otherwise show placeholders
  const readmeQuality = repoDetails?.readmeQuality || { score: 0, checks: [] };
  const security = repoDetails?.security || { score: 0, checks: [] };
  const ciCd = repoDetails?.ciCd || { score: 0, checks: [] };
  const contributionHealth = repoDetails?.contributionHealth || { score: 0, checks: [] };
  const timeline = repoDetails?.timeline || [];

  const checkGroups = [
    { title: 'README & Documentation', score: readmeQuality.score, checks: readmeQuality.checks, icon: FileCheck, color: 'text-cyan-400' },
    { title: 'Security Safeguards', score: security.score, checks: security.checks, icon: ShieldAlert, color: 'text-rose-400' },
    { title: 'Automated CI/CD Pipelines', score: ciCd.score, checks: ciCd.checks, icon: PlayCircle, color: 'text-indigo-400' },
    { title: 'Contribution Vitality', score: contributionHealth.score, checks: contributionHealth.checks, icon: Users2, color: 'text-emerald-400' },
  ];

  const statusIcons = {
    passed: <CheckCircle2 className="h-4.5 w-4.5 text-emerald-400 shrink-0" />,
    warning: <AlertTriangle className="h-4.5 w-4.5 text-amber-400 shrink-0" />,
    failed: <XCircle className="h-4.5 w-4.5 text-rose-500 shrink-0" />,
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
      {/* Top Banner Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 border-b border-zinc-900 pb-6 text-left">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="h-8 w-8 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center font-bold text-sm text-indigo-400">
              {repository.owner[0].toUpperCase()}
            </span>
            <h2 className="font-outfit text-2xl font-extrabold text-white md:text-3xl tracking-tight">
              {repository.owner}/<span className="bg-gradient-to-r from-white via-zinc-100 to-indigo-200 bg-clip-text text-transparent">{repository.name}</span>
            </h2>
            <HealthBadge classification={repository.classification} />
          </div>
          <p className="text-sm text-zinc-400 mt-2.5 max-w-3xl leading-relaxed">
            {repository.description}
          </p>

          {/* Repository Meta Stats Badges */}
          <div className="flex flex-wrap items-center gap-4 mt-4 text-xs font-semibold text-zinc-500">
            <span className="flex items-center gap-1">
              <Star className="h-4 w-4" /> {repository.stars.toLocaleString()} Stars
            </span>
            <span className="flex items-center gap-1">
              <GitFork className="h-4 w-4" /> {repository.forks.toLocaleString()} Forks
            </span>
            <span className="flex items-center gap-1">
              <Eye className="h-4 w-4" /> {repository.watchers.toLocaleString()} Watching
            </span>
            <span className="rounded bg-zinc-900 border border-zinc-800/80 px-2 py-0.5 font-mono text-[10px] text-zinc-400">
              License: {repository.license || 'None'}
            </span>
          </div>
        </div>

        {/* Dynamic Navigation to AI View */}
        <div className="shrink-0">
          <button
            onClick={() => setCurrentTab('ai-insights')}
            className="flex items-center gap-2 rounded-lg bg-indigo-500/10 border border-indigo-500/30 hover:bg-indigo-500/20 text-indigo-400 hover:text-white px-5 py-2.5 text-sm font-bold shadow-lg shadow-indigo-500/5 glow-indigo transition-all hover:scale-[1.01] active:scale-[0.99] cursor-pointer"
          >
            <Sparkles className="h-4.5 w-4.5" />
            <span>Open AI Insights</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Main Analysis Summary Card */}
      <motion.div 
        variants={itemVariants}
        className="grid grid-cols-1 lg:grid-cols-3 gap-6"
      >
        {/* Large Health Score Radial Dial Gauge */}
        <div className="glass-panel p-6 flex flex-col items-center justify-center text-center">
          <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-6">
            Health Check Gauge
          </h4>
          <div className="relative w-44 h-44 flex items-center justify-center">
            {/* SVG Ring Gauge */}
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="42"
                strokeWidth="6"
                stroke="currentColor"
                fill="transparent"
                className="text-zinc-800"
              />
              <motion.circle
                cx="50"
                cy="50"
                r="42"
                strokeWidth="6"
                strokeDasharray="264"
                initial={{ strokeDashoffset: 264 }}
                animate={{ strokeDashoffset: 264 - (264 * repository.healthScore) / 100 }}
                transition={{ duration: 1.2, ease: 'easeOut' }}
                strokeLinecap="round"
                stroke="currentColor"
                fill="transparent"
                className={`${
                  repository.healthScore >= 80 ? 'text-emerald-500' :
                  repository.healthScore >= 60 ? 'text-amber-500' : 'text-red-500'
                }`}
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="font-outfit text-4xl font-extrabold text-white">
                {repository.healthScore}
              </span>
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide mt-0.5">
                Out of 100
              </span>
            </div>
          </div>
          <p className="text-xs text-zinc-400 mt-6 max-w-[240px]">
            Weighted index of commit frequencies, PR throughput speeds, and documentation depth.
          </p>
        </div>

        {/* Technical stack language bars */}
        <div className="glass-panel p-6 flex flex-col text-left lg:col-span-2">
          <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-6">
            Language & Stack Breakdown
          </h4>
          
          <div className="space-y-5 flex-1 flex flex-col justify-center">
            {/* Horizontal Percentage bar */}
            <div className="w-full h-3 bg-zinc-950 rounded-full overflow-hidden flex border border-zinc-900">
              {repository.languages.map((lang, index) => (
                <div 
                  key={lang.name}
                  style={{ 
                    width: `${lang.percentage}%`,
                    backgroundColor: lang.color
                  }}
                  className={`h-full ${index === 0 ? 'rounded-l-full' : ''} ${index === repository.languages.length - 1 ? 'rounded-r-full' : ''}`}
                />
              ))}
            </div>

            {/* Metrics List columns */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-2">
              {repository.languages.map((lang) => (
                <div key={lang.name} className="p-3 bg-zinc-950/40 rounded-lg border border-zinc-900/60">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: lang.color }} />
                    <span className="text-xs font-semibold text-white">{lang.name}</span>
                  </div>
                  <span className="block font-mono text-lg font-bold text-zinc-300 mt-1">
                    {lang.percentage}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          <p className="text-xs text-zinc-500 mt-4">
            * Generated from repository byte allocation indices on Github source commits.
          </p>
        </div>
      </motion.div>

      {/* Checklist Audit Sections & Activities Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 text-left">
        {/* Core Checklist audits (takes 2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {checkGroups.map((group) => (
            <motion.div 
              key={group.title}
              variants={itemVariants}
              className="glass-panel p-6"
            >
              <div className="flex items-center justify-between border-b border-zinc-900 pb-4 mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 bg-zinc-900 rounded-lg border border-zinc-800/80">
                    <group.icon className={`h-4.5 w-4.5 ${group.color}`} />
                  </div>
                  <h4 className="font-outfit text-sm font-bold text-white">
                    {group.title}
                  </h4>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-zinc-500 font-medium">Compliance:</span>
                  <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/5 px-2 py-0.5 rounded border border-indigo-500/10">
                    {group.score}%
                  </span>
                </div>
              </div>

              {/* Items checklist rows */}
              <div className="space-y-4">
                {group.checks.map((check, index) => (
                  <div key={index} className="flex gap-3 items-start text-xs p-2.5 rounded-lg bg-zinc-950/20 border border-zinc-900/50">
                    {statusIcons[check.status]}
                    <div>
                      <p className="font-semibold text-zinc-200">
                        {check.name}
                      </p>
                      <p className="text-zinc-400 mt-0.5">
                        {check.description}
                      </p>
                      {check.feedback && (
                        <p className="text-[11px] text-indigo-400/80 mt-1.5 font-medium italic">
                          Feedback: {check.feedback}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Sidebar activity stream (takes 1 col) */}
        <div className="space-y-6">
          <ActivityTimeline timeline={timeline} />
          
          {/* Average response card */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Clock className="h-4.5 w-4.5 text-zinc-400" />
              <h5 className="font-semibold text-white text-xs uppercase tracking-wider">
                Response Benchmarks
              </h5>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-[10px] text-zinc-500 block uppercase font-bold">First Reply</span>
                <span className="font-mono text-xl font-bold text-white mt-1 block">
                  {repository.avgResponseTimeDays > 0 ? `${repository.avgResponseTimeDays} Days` : 'n/a'}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-zinc-500 block uppercase font-bold">Issue Resolution</span>
                <span className="font-mono text-xl font-bold text-white mt-1 block">
                  {repository.avgCloseTimeDays > 0 ? `${repository.avgCloseTimeDays} Days` : 'n/a'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
export default RepoDetailsPage;
