import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  glowColor?: 'indigo' | 'emerald' | 'amber' | 'red';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  description,
  icon: Icon,
  trend,
  glowColor = 'indigo',
}) => {
  const glowClasses = {
    indigo: 'hover:border-indigo-500/30 hover:shadow-indigo-500/5',
    emerald: 'hover:border-emerald-500/30 hover:shadow-emerald-500/5',
    amber: 'hover:border-amber-500/30 hover:shadow-amber-500/5',
    red: 'hover:border-red-500/30 hover:shadow-red-500/5',
  };

  return (
    <motion.div
      whileHover={{ y: -2 }}
      className={`relative overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-900/40 p-6 backdrop-blur-sm transition-all duration-300 ${glowClasses[glowColor]}`}
    >
      {/* Glow Effect */}
      <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-gradient-to-br from-indigo-500/5 to-transparent blur-2xl" />

      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
          {title}
        </span>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-900 border border-zinc-800/80 text-zinc-400">
          <Icon className="h-4.5 w-4.5" />
        </div>
      </div>

      <div className="mt-4 flex items-baseline gap-2">
        <h3 className="font-outfit text-2xl font-bold tracking-tight text-white md:text-3xl">
          {value}
        </h3>
        {trend && (
          <span className={`inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-xs font-medium ${
            trend.isPositive ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
          }`}>
            {trend.isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {trend.value}
          </span>
        )}
      </div>

      <p className="mt-1 text-xs text-zinc-400">
        {description}
      </p>
    </motion.div>
  );
};
export default MetricCard;
