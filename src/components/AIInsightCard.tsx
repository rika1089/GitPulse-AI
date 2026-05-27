import React from 'react';
import { motion } from 'framer-motion';
import { Shield, FileText, Activity, AlertTriangle, ArrowRight } from 'lucide-react';

interface AIInsightCardProps {
  title: string;
  description: string;
  impact: 'High' | 'Medium' | 'Low';
  category: 'Security' | 'Documentation' | 'Activity' | 'Code Quality';
  onActionClick?: () => void;
}

export const AIInsightCard: React.FC<AIInsightCardProps> = ({
  title,
  description,
  impact,
  category,
  onActionClick,
}) => {
  const categoryIcons = {
    Security: Shield,
    Documentation: FileText,
    Activity: Activity,
    'Code Quality': AlertTriangle,
  };

  const Icon = categoryIcons[category] || AlertTriangle;

  const impactStyles = {
    High: 'bg-red-500/10 text-red-400 border-red-500/30',
    Medium: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    Low: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  };

  const categoryStyles = {
    Security: 'text-rose-400 bg-rose-500/5 border-rose-500/10',
    Documentation: 'text-cyan-400 bg-cyan-500/5 border-cyan-500/10',
    Activity: 'text-indigo-400 bg-indigo-500/5 border-indigo-500/10',
    'Code Quality': 'text-amber-400 bg-amber-500/5 border-amber-500/10',
  };

  return (
    <motion.div
      whileHover={{ scale: 1.01, y: -2 }}
      className="relative overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-900/30 p-5 backdrop-blur-sm transition-all duration-300 hover:border-indigo-500/30 hover:bg-zinc-900/50 glow-indigo"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${categoryStyles[category]}`}>
            <Icon className="h-3 w-3" />
            {category}
          </span>
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${impactStyles[impact]}`}>
            {impact} Impact
          </span>
        </div>
      </div>

      <h5 className="mt-3 font-outfit text-sm font-semibold text-white">
        {title}
      </h5>
      <p className="mt-1 text-xs text-zinc-400 leading-relaxed">
        {description}
      </p>

      {onActionClick && (
        <button
          onClick={onActionClick}
          className="mt-4 flex items-center gap-1 text-[11px] font-bold text-indigo-400 hover:text-white transition-colors cursor-pointer"
        >
          <span>Review proposed fix</span>
          <ArrowRight className="h-3 w-3" />
        </button>
      )}
    </motion.div>
  );
};
export default AIInsightCard;
