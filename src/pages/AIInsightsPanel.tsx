import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Sparkles, AlertTriangle, Lightbulb, FileCode, ThumbsUp,
  RefreshCw, AlertCircle,
} from 'lucide-react';
import { Repository, RepoDetails } from '../types/dashboard';
import { AIInsightCard }  from '../components/AIInsightCard';
import { useRepoDetails } from '../hooks/useRepoData';

interface AIInsightsPanelProps {
  selectedRepo: Repository | null;
}

export const AIInsightsPanel: React.FC<AIInsightsPanelProps> = ({ selectedRepo }) => {
  // ── Live data ─────────────────────────────────────────────────────────────
  const { data, loading, error, refetch } = useRepoDetails(
    selectedRepo?.owner,
    selectedRepo?.name,
  );

  const repoDetails = data;

  const containerVariants = {
    hidden: { opacity: 0 },
    show:   { opacity: 1, transition: { staggerChildren: 0.05 } },
  };
  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show:   { opacity: 1, y: 0 },
  };

  // ── Loading ───────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4 text-zinc-400">
        <RefreshCw className="h-8 w-8 animate-spin text-indigo-400" />
        <p className="text-sm">
          Running AI analysis on {selectedRepo?.owner}/{selectedRepo?.name}…
        </p>
        <p className="text-xs text-zinc-600">Analysing commits, PRs, issues, and code quality</p>
      </div>
    );
  }

  // ── Error ─────────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4 p-8">
        <AlertCircle className="h-10 w-10 text-red-400" />
        <p className="text-sm text-red-400 text-center max-w-sm">{error}</p>
        <button
          onClick={refetch}
          className="flex items-center gap-2 rounded-lg border border-zinc-800 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900"
        >
          <RefreshCw className="h-4 w-4" /> Retry
        </button>
      </div>
    );
  }

  // ── No repo or data yet ───────────────────────────────────────────────────
  if (!selectedRepo || !repoDetails) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3 text-zinc-400">
        <Sparkles className="h-8 w-8 text-zinc-600" />
        <p className="text-sm">Select a repository to view AI insights.</p>
      </div>
    );
  }

  const { repository, insights, readmeQuality, security, ciCd, contributionHealth } = repoDetails;
  const docScore      = readmeQuality.score;
  const pipelineScore = Math.round((security.score + ciCd.score + contributionHealth.score) / 3);

  // ── Main content (structure identical to original) ────────────────────────
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-8 p-4 md:p-6 lg:p-8 text-left"
    >
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-900 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
              <Sparkles className="h-4 w-4" />
            </div>
            <h2 className="font-outfit text-2xl font-extrabold text-white tracking-tight">
              AI Insight Analyst
            </h2>
          </div>
          <p className="text-sm text-zinc-500 mt-1">
            Automated recommendations, risk analyses, and suggested refactor diagnostics.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-zinc-500 font-semibold uppercase">Selected:</span>
          <span className="font-mono text-xs font-bold text-white bg-zinc-900 px-2.5 py-1 rounded border border-zinc-800">
            {repository.owner}/{repository.name}
          </span>
          <button
            onClick={refetch}
            className="flex items-center gap-1.5 rounded border border-zinc-800 px-2.5 py-1 text-xs text-zinc-400 hover:bg-zinc-900 hover:text-white transition-colors"
          >
            <RefreshCw className="h-3 w-3" /> Refresh
          </button>
        </div>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Narrative card */}
        <motion.div variants={itemVariants} className="lg:col-span-2 glass-panel p-6 space-y-6">
          <div className="flex items-center gap-2 border-b border-zinc-900 pb-4">
            <Sparkles className="h-4 w-4 text-indigo-400" />
            <h4 className="font-outfit text-sm font-bold text-white">Health Assessment Narrative</h4>
          </div>

          <p className="text-sm text-zinc-300 leading-relaxed bg-zinc-950/40 border border-zinc-900/60 p-4 rounded-lg">
            "{insights.summary}"
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
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

        {/* Diagnostic scores */}
        <motion.div variants={itemVariants} className="glass-panel p-6 flex flex-col justify-between">
          <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-6">
            Diagnostics Scores
          </h4>

          <div className="space-y-6 flex-1 flex flex-col justify-center">
            {[
              { score: docScore,      color: '#22d3ee', label: 'Documentation Score',   desc: 'README completeness and API guidelines.' },
              { score: pipelineScore, color: '#818cf8', label: 'Pipeline Compliance',    desc: 'Branch protection and CI/CD builds.' },
            ].map(({ score, color, label, desc }) => (
              <div key={label} className="flex items-center gap-4">
                <div className="relative w-16 h-16 flex items-center justify-center shrink-0">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                    <circle cx="18" cy="18" r="16" strokeWidth="3" stroke="#1f1f23" fill="none" />
                    <circle cx="18" cy="18" r="16" strokeWidth="3"
                      strokeDasharray="100"
                      strokeDashoffset={100 - score}
                      strokeLinecap="round"
                      stroke={color}
                      fill="none"
                    />
                  </svg>
                  <span className="absolute text-[11px] font-bold font-mono" style={{ color }}>
                    {score}%
                  </span>
                </div>
                <div>
                  <h5 className="text-xs font-bold text-white">{label}</h5>
                  <p className="text-[11px] text-zinc-400 mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-zinc-900 pt-4 mt-6 text-[10px] text-zinc-500 leading-relaxed">
            Diagnosed by GitPulse AI on {new Date().toLocaleDateString()}.
          </div>
        </motion.div>
      </div>

      {/* Recommendations + diagnostic alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 text-left">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-indigo-400" />
            <h4 className="font-outfit text-sm font-bold text-white">Actionable Recommendations</h4>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insights.recommendations.map((rec, i) => (
              <AIInsightCard
                key={i}
                title={rec.title}
                description={rec.description}
                impact={rec.impact}
                category={rec.category}
                onActionClick={() => alert(`Reviewing patch for: ${rec.title}`)}
              />
            ))}
          </div>
        </div>

        {/* Diagnostic alert panel */}
        <motion.div variants={itemVariants} className="glass-panel p-5 space-y-4">
          <div className="flex items-center gap-2 border-b border-zinc-900 pb-3">
            <FileCode className="h-4 w-4 text-indigo-400" />
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
                  Repository Health Below Threshold
                </p>
                <p className="text-zinc-500 leading-relaxed text-[11px]">
                  Health score of {repository.healthScore}/100 indicates issues with commit activity,
                  PR throughput, or issue resolution. Review the recommendations above.
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
                  Score of {repository.healthScore}/100. Healthy contributor distribution
                  and active maintenance detected.
                </p>
              </div>
            )}

            {insights.risks.length > 0 && (
              <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-900 space-y-2">
                <span className="inline-block px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold font-mono text-[9px]">
                  RISK DETECTED
                </span>
                <p className="text-zinc-300 font-semibold mt-1">
                  {insights.risks[0].split(':')[0] || 'Maintenance Risk'}
                </p>
                <p className="text-zinc-500 leading-relaxed text-[11px]">
                  {insights.risks[0]}
                </p>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default AIInsightsPanel;
