import React from 'react';
import { Home, LayoutDashboard, ShieldCheck, Cpu, ChevronLeft, ChevronRight } from 'lucide-react';
import { Repository } from '../types/dashboard';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  repositories: Repository[];
  selectedRepo: Repository | null;
  setSelectedRepo: (repo: Repository) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  repositories,
  selectedRepo,
  setSelectedRepo,
  isCollapsed,
  setIsCollapsed,
}) => {
  const menuItems = [
    { id: 'landing', label: 'Home', icon: Home },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'details', label: 'Repo Details', icon: ShieldCheck },
    { id: 'ai-insights', label: 'AI Insights', icon: Cpu },
  ];

  return (
    <aside 
      className={`fixed inset-y-16 left-0 z-30 flex flex-col border-r border-zinc-800/80 bg-zinc-950 transition-all duration-300 ${
        isCollapsed ? 'w-16' : 'w-64'
      } hidden md:flex`}
    >
      <div className="flex-1 overflow-y-auto py-4">
        {/* Navigation Section */}
        <div className="px-3 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                  isActive 
                    ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' 
                    : 'text-zinc-400 hover:bg-zinc-900/50 hover:text-white border border-transparent'
                }`}
              >
                <Icon className="h-4.5 w-4.5 shrink-0" />
                {!isCollapsed && <span>{item.label}</span>}
              </button>
            );
          })}
        </div>

        {/* Repositories Sub-list */}
        {!isCollapsed && (
          <div className="mt-8 px-4">
            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">
              Analyze Repositories
            </h3>
            <div className="space-y-1.5 max-h-[300px] overflow-y-auto pr-1">
              {repositories.map((repo) => {
                const isSelected = selectedRepo?.id === repo.id;
                return (
                  <button
                    key={repo.id}
                    onClick={() => {
                      setSelectedRepo(repo);
                      setCurrentTab('details');
                    }}
                    className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-left transition-colors truncate ${
                      isSelected 
                        ? 'bg-zinc-800/80 text-white font-medium border-l-2 border-indigo-500 pl-1.5' 
                        : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
                    }`}
                  >
                    <span className="truncate">{repo.owner}/{repo.name}</span>
                    <span className={`ml-auto w-2 h-2 rounded-full shrink-0 ${
                      repo.healthScore >= 80 ? 'bg-emerald-500' :
                      repo.healthScore >= 60 ? 'bg-amber-500' : 'bg-red-500'
                    }`} />
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Collapse/Expand Controls */}
      <div className="p-4 border-t border-zinc-900 flex justify-end">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-900 hover:text-white"
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
    </aside>
  );
};
export default Sidebar;
