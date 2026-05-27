import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GitBranch, Shield, Terminal, ArrowRight, Cpu, Loader2 } from 'lucide-react';
import { Repository } from '../types/dashboard';

interface LandingPageProps {
  repositories: Repository[];
  setCurrentTab: (tab: string) => void;
  setSelectedRepo: (repo: Repository) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  repositories,
  setCurrentTab,
  setSelectedRepo,
}) => {
  const [repoInput, setRepoInput] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState(0);

  const steps = [
    'Connecting to GitHub REST API...',
    'Fetching repository branch structures...',
    'Computing code churn & commit frequency...',
    'Analyzing README file depth & license profiles...',
    'Querying MCP OpenAI analysis narrative engines...',
    'Generating health reports and recommendation cards...'
  ];

  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoInput.trim()) return;

    setIsAnalyzing(true);
    setAnalysisStep(0);

    // Simulate multi-step analysis sequence
    const interval = setInterval(() => {
      setAnalysisStep((prev) => {
        if (prev >= steps.length - 1) {
          clearInterval(interval);
          setTimeout(() => {
            // Find a repo that matches input, or fallback to React
            const inputClean = repoInput.toLowerCase();
            const foundRepo = repositories.find(
              (r) => 
                r.name.toLowerCase().includes(inputClean) || 
                r.owner.toLowerCase().includes(inputClean)
            ) || repositories[0]; // fallback to facebook/react

            setSelectedRepo(foundRepo);
            setIsAnalyzing(false);
            setCurrentTab('details');
          }, 800);
          return prev;
        }
        return prev + 1;
      });
    }, 900);
  };

  const featureCards = [
    {
      icon: GitBranch,
      title: 'Repo Health Scoring',
      desc: 'Normalized score from 0-100 built from time-series commit density, issue close rates, and PR merge cycles.',
      color: 'from-indigo-500/10 to-indigo-500/0 border-indigo-500/10'
    },
    {
      icon: Cpu,
      title: 'AI Diagnostic Reports',
      desc: 'LLM-synthesized narrative reports covering primary architectural strengths, stale risks, and next-step actions.',
      color: 'from-purple-500/10 to-purple-500/0 border-purple-500/10'
    },
    {
      icon: Shield,
      title: 'Compliance & Security Audits',
      desc: 'Lightweight automated audits verifying security disclosure pathways, branch lockouts, and dependency state.',
      color: 'from-emerald-500/10 to-emerald-500/0 border-emerald-500/10'
    },
    {
      icon: Terminal,
      title: 'Contributor Diagnostics',
      desc: 'Time-series contribution maps highlighting core maintainer dependencies and stale contributor risks.',
      color: 'from-cyan-500/10 to-cyan-500/0 border-cyan-500/10'
    }
  ];

  return (
    <div className="relative isolate min-h-[calc(100vh-4rem)] overflow-hidden bg-background">
      {/* Background Grids */}
      <div className="absolute inset-0 -z-10 grid-background opacity-20" />

      {/* Floating glowing orbs */}
      <div className="absolute top-1/4 left-1/4 -z-10 h-72 w-72 rounded-full bg-indigo-500/10 blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 -z-10 h-96 w-96 rounded-full bg-violet-600/10 blur-3xl" />

      <div className="mx-auto max-w-7xl px-6 py-20 lg:px-8 text-center">
        {/* Main Hero Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-6"
        >
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-semibold text-zinc-400">
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Academic B.Tech Submission (IT)</span>
          </div>

          <h1 className="font-outfit text-4xl font-extrabold tracking-tight text-white sm:text-6xl md:text-7xl leading-none">
            Diagnose Your Repository's <br />
            <span className="text-gradient-indigo">Health with AI.</span>
          </h1>

          <p className="mx-auto max-w-2xl text-base text-zinc-400 sm:text-lg">
            An intelligent Model Context Protocol (MCP) developer cockpit analyzing public repositories for activity profiles, PR merge metrics, and security compliance.
          </p>
        </motion.div>

        {/* Dynamic Interactive Input Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="mx-auto mt-10 max-w-2xl"
        >
          <div className="glass-panel p-6 glow-indigo relative">
            <AnimatePresence mode="wait">
              {!isAnalyzing ? (
                <motion.form 
                  key="input-form"
                  onSubmit={handleAnalyze} 
                  className="space-y-4"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <div className="flex flex-col sm:flex-row gap-2">
                    <input
                      type="text"
                      placeholder="Enter GitHub Repository (e.g. facebook/react)"
                      value={repoInput}
                      onChange={(e) => setRepoInput(e.target.value)}
                      className="flex-1 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none transition-colors"
                      required
                    />
                    <button
                      type="submit"
                      className="flex items-center justify-center gap-1.5 rounded-lg bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 transition-all hover:scale-[1.01] active:scale-[0.99] cursor-pointer"
                    >
                      <span>Analyze</span>
                      <ArrowRight className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-zinc-500">
                    <span>Try:</span>
                    <button type="button" onClick={() => setRepoInput('vercel/next.js')} className="hover:text-indigo-400 transition-colors">next.js</button>
                    <button type="button" onClick={() => setRepoInput('facebook/react')} className="hover:text-indigo-400 transition-colors">react</button>
                    <button type="button" onClick={() => setRepoInput('openedx/edx-repo-health')} className="hover:text-indigo-400 transition-colors">edx-repo-health</button>
                    <button type="button" onClick={() => setRepoInput('code-review-mcp-server')} className="hover:text-indigo-400 transition-colors">code-review-mcp</button>
                  </div>
                </motion.form>
              ) : (
                <motion.div
                  key="loader-form"
                  className="py-6 flex flex-col items-center justify-center"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <Loader2 className="h-10 w-10 animate-spin text-indigo-400 mb-4" />
                  <p className="font-semibold text-white text-sm">
                    {steps[analysisStep]}
                  </p>
                  <div className="mt-3 w-full bg-zinc-950 rounded-full h-1.5 max-w-[320px] overflow-hidden border border-zinc-800">
                    <motion.div 
                      className="h-full bg-indigo-500"
                      initial={{ width: '0%' }}
                      animate={{ width: `${((analysisStep + 1) / steps.length) * 100}%` }}
                      transition={{ duration: 0.8 }}
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Counter Stats Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="mx-auto mt-16 max-w-4xl grid grid-cols-2 md:grid-cols-4 gap-6"
        >
          {[
            { value: '220K+', label: 'React Stars Analyzed' },
            { value: '1.4 Days', label: 'Average Response Time' },
            { value: '6 Projects', label: 'Reference Codebases' },
            { value: '98%', label: 'README Analysis accuracy' },
          ].map((stat, index) => (
            <div key={index} className="rounded-lg border border-zinc-900 bg-zinc-950/40 p-4 backdrop-blur-sm">
              <span className="block font-outfit text-2xl font-extrabold text-white md:text-3xl">
                {stat.value}
              </span>
              <span className="text-xs text-zinc-500 font-semibold mt-1 block uppercase tracking-wider">
                {stat.label}
              </span>
            </div>
          ))}
        </motion.div>

        {/* Features Grid Section */}
        <div className="mt-28">
          <div className="mb-12">
            <h2 className="font-outfit text-2xl font-bold text-white md:text-3xl">
              Engineered for Open Source Developers
            </h2>
            <p className="text-sm text-zinc-500 mt-1.5">
              Everything you need to analyze repositories, prioritize issue workflows, and review pull requests.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {featureCards.map((feat, idx) => {
              const FeatIcon = feat.icon;
              return (
                <motion.div
                  key={idx}
                  whileHover={{ y: -4 }}
                  className={`rounded-xl border bg-gradient-to-b ${feat.color} p-6 text-left transition-all duration-300`}
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-950 border border-zinc-800 text-indigo-400 mb-4">
                    <FeatIcon className="h-5 w-5" />
                  </div>
                  <h4 className="font-outfit text-sm font-semibold text-white">
                    {feat.title}
                  </h4>
                  <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
                    {feat.desc}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Academic Details Footer Section */}
        <footer className="mt-32 pt-8 border-t border-zinc-900 text-center text-xs text-zinc-600">
          <p>B.Tech Information Technology Academic Submission • SASTRA University, May 2026</p>
          <p className="mt-1">Inspired by open-source systems: openedx/edx-repo-health & Orcus2021/code-review-mcp-server</p>
        </footer>
      </div>
    </div>
  );
};
export default LandingPage;
