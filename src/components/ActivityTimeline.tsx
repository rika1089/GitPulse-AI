import React from 'react';
import { motion } from 'framer-motion';
import { GitCommit, GitMerge, GitPullRequest, AlertCircle, CheckCircle2, Award } from 'lucide-react';
import { ActivityTimelineItem } from '../types/dashboard';

interface ActivityTimelineProps {
  timeline: ActivityTimelineItem[];
}

export const ActivityTimeline: React.FC<ActivityTimelineProps> = ({ timeline }) => {
  const icons = {
    commit: { icon: GitCommit, color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20' },
    pr_merge: { icon: GitMerge, color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
    pr_open: { icon: GitPullRequest, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
    issue_open: { icon: AlertCircle, color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' },
    issue_close: { icon: CheckCircle2, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
    release: { icon: Award, color: 'text-teal-400 bg-teal-500/10 border-teal-500/20' },
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -10 },
    show: { opacity: 1, x: 0 },
  };

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 backdrop-blur-sm shadow-md">
      <div className="mb-6">
        <h4 className="font-outfit text-sm font-semibold text-white">Repository Activity</h4>
        <p className="text-xs text-zinc-500 mt-0.5">Real-time commit, release, and community streams</p>
      </div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="relative border-l border-zinc-800 ml-3 pl-6 space-y-6 text-left"
      >
        {timeline.map((item) => {
          const config = icons[item.type] || icons.commit;
          const ActionIcon = config.icon;
          return (
            <motion.div 
              key={item.id} 
              variants={itemVariants}
              className="relative"
            >
              {/* Timeline marker icon */}
              <span className={`absolute -left-[35px] top-1 flex h-6.5 w-6.5 items-center justify-center rounded-full border ${config.color}`}>
                <ActionIcon className="h-3.5 w-3.5" />
              </span>

              <div className="flex items-start justify-between gap-4">
                <div>
                  <h5 className="text-sm font-semibold text-white">
                    {item.title}
                  </h5>
                  <p className="text-xs text-zinc-400 mt-0.5 leading-relaxed">
                    {item.description}
                  </p>
                  <div className="flex items-center gap-1.5 mt-2">
                    <img 
                      src={item.user.avatarUrl} 
                      alt={item.user.name} 
                      className="w-4 h-4 rounded-full border border-zinc-800"
                    />
                    <span className="text-[10px] font-medium text-zinc-400">
                      {item.user.name}
                    </span>
                    <span className="text-[10px] text-zinc-600 font-medium">•</span>
                    <span className="text-[10px] text-zinc-500">
                      {item.timestamp}
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
};
export default ActivityTimeline;
