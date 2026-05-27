import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  AlertTriangle,
  Lightbulb,
  FileCode,
  ThumbsUp
} from 'lucide-react';
import { Repository, RepoDetails } from '../types/dashboard';
import { AIInsightCard } from '../components/AIInsightCard';
import { mockRepoDetailsMap } from '../data/mockData';

interface AIInsightsPanelProps {
  selectedRepo: Repository | null;
}

export const AIInsightsPanel: React.FC<AIInsightsPanelProps> = ({ selectedRepo }) => {
  // Safe fallback to React details if none is selected
  const repoDetails: RepoDetails = useMemo(() => {
    if (!selectedRepo) return mockRepoDetailsMap['react-health'];
    return mockRepoDetailsMap[selectedRepo.id] || mockRepoDetailsMap['react-health'];
  }, [selectedRepo]);

  const { repository, insights, readmeQuality, security, ciCd, contributionHealth } = repoDetails;

  // Calculate cumulative average documentation and pipeline score
  const docScore = readmeQuality.score;
  const pipelineScore = Math.round((security.score + ciCd.score + contributionHealth.score) / 3);

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
      className="space-y-8 p-4 md:p-6 lg:p-8 text-left"
    >
      {/* AI Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-900 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
              <Sparkles className="h-4.5 w-4.5 shrink-0" />
            </div>
            <h2 className="font-outfit text-2xl font-extrabold text-white md:text-3xl tracking-tight">
              AI Insight Analyst
            </h2>
          </div>
          <p className="text-sm text-zinc-500 mt-1">
            Automated recommendations, risk analyses, and suggested refactor diagnostics.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500 font-semibold uppercase">Selected:</span>
          <span className="font-mono text-xs font-bold text-white bg-zinc-900 px-2.5 py-1 rounded border border-zinc-800">
            {repository.owner}/{repository.name}
          </span>
        </div>
      </div>

      {/* Main Insights Panel Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Core Analysis Narrative Card */}
        <motion.div 
          variants={itemVariants}
          className="lg:col-span-2 glass-panel p-6 space-y-6"
        >
          <div className="flex items-center gap-2 border-b border-zinc-900 pb-4">
            <Sparkles className="h-4.5 w-4.5 text-indigo-400" />
            <h4 className="font-outfit text-sm font-bold text-white">
              Health Assessment Narrative
            </h4>
          </div>

          <p className="text-sm text-zinc-300 leading-relaxed bg-zinc-950/40 border border-zinc-900/60 p-4 rounded-lg">
            "{insights.summary}"
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
            {/* Strengths List */}
            <div className="space-y-3">
              <h5 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider flex items-center gap-1.5">
                <ThumbsUp className="h-3.5 w-3.5 text-emerald-400" /> Core Strengths
              </h5>
              <ul className="space-y-2">
                {insights.strengths.map((str, i) => (
                  <li key={i} className="flex gap-2 text-xs text-zinc-300">
                    <span className="text-emerald-400 font-semibold">•</span>
                    <span>{str}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Risks List */}
            <div className="space-y-3">
              <h5 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-500" /> Maintenance Risks
              </h5>
              <ul className="space-y-2">
                {insights.risks.map((risk, i) => (
                  <li key={i} className="flex gap-2 text-xs text-zinc-300">
                    <span className="text-amber-500 font-semibold">•</span>
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </motion.div>

        {/* Documentation ring card */}
        <motion.div 
          variants={itemVariants}
          className="glass-panel p-6 flex flex-col justify-between"
        >
          <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-6">
            Diagnostics Scores
          </h4>

          <div className="space-y-6 flex-1 flex flex-col justify-center">
            {/* Doc Score Gauge Ring */}
            <div className="flex items-center gap-4">
              <div className="relative w-16 h-16 flex items-center justify-center shrink-0">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="16" strokeWidth="3" stroke="#1f1f23" fill="none" />
                  <circle cx="18" cy="18" r="16" strokeWidth="3" strokeDasharray="100" strokeDashoffset={100 - docScore} strokeLinecap="round" stroke="#22d3ee" fill="none" />
                </svg>
                <span className="absolute text-[11px] font-bold font-mono text-cyan-400">{docScore}%</span>
              </div>
              <div>
                <h5 className="text-xs font-bold text-white">Documentation Score</h5>
                <p className="text-[11px] text-zinc-400 mt-0.5">README index completeness and API code guidelines.</p>
              </div>
            </div>

            {/* Pipeline Score Gauge Ring */}
            <div className="flex items-center gap-4">
              <div className="relative w-16 h-16 flex items-center justify-center shrink-0">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="16" strokeWidth="3" stroke="#1f1f23" fill="none" />
                  <circle cx="18" cy="18" r="16" strokeWidth="3" strokeDasharray="100" strokeDashoffset={100 - pipelineScore} strokeLinecap="round" stroke="#818cf8" fill="none" />
                </svg>
                <span className="absolute text-[11px] font-bold font-mono text-indigo-400">{pipelineScore}%</span>
              </div>
              <div>
                <h5 className="text-xs font-bold text-white">Pipeline Compliance</h5>
                <p className="text-[11px] text-zinc-400 mt-0.5">Branch protection mechanisms and CI/CD validation builds.</p>
              </div>
            </div>
          </div>

          <div className="border-t border-zinc-900 pt-4 mt-6 text-[10px] text-zinc-500 leading-relaxed">
            Diagnosed by MCP assistant parser on {new Date().toLocaleDateString()}.
          </div>
        </motion.div>
      </div>

      {/* AI Recommendations & Refactor Examples Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 text-left">
        {/* Recommendation card list */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4.5 w-4.5 text-indigo-400" />
            <h4 className="font-outfit text-sm font-bold text-white">
              Actionable Recommendations
            </h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insights.recommendations.map((rec, i) => (
              <AIInsightCard
                key={i}
                title={rec.title}
                description={rec.description}
                impact={rec.impact}
                category={rec.category}
                onActionClick={() => alert(`Reviewing automated patch files for: ${rec.title}`)}
              />
            ))}
          </div>
        </div>

        {/* Refactoring Alerts Panel */}
        <motion.div 
          variants={itemVariants}
          className="glass-panel p-5 space-y-4"
        >
          <div className="flex items-center gap-2 border-b border-zinc-900 pb-3">
            <FileCode className="h-4.5 w-4.5 text-indigo-400" />
            <h5 className="font-semibold text-white text-xs uppercase tracking-wider">
              Diagnostic Alerts
            </h5>
          </div>

          <div className="space-y-4 text-xs">
            {repository.healthScore < 80 ? (
              <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-900 space-y-2">
                <span className="inline-block px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-semibold font-mono text-[9px]">
                  CRITICAL CODE ALERT
                </span>
                <p className="text-zinc-300 font-semibold mt-1">
                  Single-Maintainer Bottleneck Detected
                </p>
                <p className="text-zinc-500 leading-relaxed text-[11px]">
                  Over 90% of commit distributions originate from a single system author. Promoting secondary reviewers is recommended to offset key-man exposure vectors.
                </p>
              </div>
            ) : (
              <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-900 space-y-2">
                <span className="inline-block px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold font-mono text-[9px]">
                  HEALTHY METRIC SIGN
                </span>
                <p className="text-zinc-300 font-semibold mt-1">
                  Optimum Code Flow Maintained
                </p>
                <p className="text-zinc-500 leading-relaxed text-[11px]">
                  Healthy community distributions and multiple active contributors offset operational bottlenecks. Main branch safeguards are optimal.
                </p>
              </div>
            )}

            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-900 space-y-2">
              <span className="inline-block px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold font-mono text-[9px]">
                BEST PRACTICE WARNING
              </span>
              <p className="text-zinc-300 font-semibold mt-1">
                Stale PR Lifecycle Exceeded
              </p>
              <p className="text-zinc-500 leading-relaxed text-[11px]">
                Review channels identify open PRs stale for over 30 days without maintainer actions. Trigger automated stale action scripts to prune.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};
export default AIInsightsPanel;
