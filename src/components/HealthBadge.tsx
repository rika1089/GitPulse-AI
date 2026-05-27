import React from 'react';
import { ShieldAlert, ShieldCheck, HelpCircle, Archive } from 'lucide-react';
import { HealthClassification } from '../types/dashboard';

interface HealthBadgeProps {
  classification: HealthClassification;
  showIcon?: boolean;
}

export const HealthBadge: React.FC<HealthBadgeProps> = ({ classification, showIcon = true }) => {
  const styles = {
    Healthy: {
      bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      icon: ShieldCheck,
      label: 'Healthy',
    },
    Stagnant: {
      bg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      icon: HelpCircle,
      label: 'Stagnant',
    },
    'At Risk': {
      bg: 'bg-red-500/10 text-red-400 border-red-500/20',
      icon: ShieldAlert,
      label: 'At Risk',
    },
    Archived: {
      bg: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
      icon: Archive,
      label: 'Archived',
    },
  };

  const current = styles[classification] || styles.Stagnant;
  const Icon = current.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${current.bg}`}>
      {showIcon && <Icon className="h-3.5 w-3.5 shrink-0" />}
      <span>{current.label}</span>
    </span>
  );
};
export default HealthBadge;
