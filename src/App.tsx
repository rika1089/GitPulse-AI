import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Home, LayoutDashboard, ShieldCheck, Cpu } from 'lucide-react';
import { mockDashboardStats, mockRepositories } from './data/mockData';
import { Repository } from './types/dashboard';

// Import components
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';

// Import pages
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { RepoDetailsPage } from './pages/RepoDetailsPage';
import { AIInsightsPanel } from './pages/AIInsightsPanel';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('landing');
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(mockRepositories[0]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);

  const renderActivePage = () => {
    switch (currentTab) {
      case 'landing':
        return (
          <LandingPage
            repositories={mockRepositories}
            setCurrentTab={setCurrentTab}
            setSelectedRepo={setSelectedRepo}
          />
        );
      case 'dashboard':
        return (
          <DashboardPage
            stats={mockDashboardStats}
            repositories={mockRepositories}
            setSelectedRepo={setSelectedRepo}
            setCurrentTab={setCurrentTab}
          />
        );
      case 'details':
        return (
          <RepoDetailsPage
            selectedRepo={selectedRepo}
            setCurrentTab={setCurrentTab}
          />
        );
      case 'ai-insights':
        return (
          <AIInsightsPanel selectedRepo={selectedRepo} />
        );
      default:
        return (
          <LandingPage
            repositories={mockRepositories}
            setCurrentTab={setCurrentTab}
            setSelectedRepo={setSelectedRepo}
          />
        );
    }
  };

  const pageTransitionVariants = {
    initial: { opacity: 0, y: 8 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.25, ease: 'easeOut' } },
    exit: { opacity: 0, y: -8, transition: { duration: 0.15, ease: 'easeIn' } },
  };

  return (
    <div className="relative min-h-screen bg-background flex flex-col font-sans text-foreground">
      {/* Top Glassmorphic Navigation */}
      <Navbar 
        currentTab={currentTab} 
        setCurrentTab={setCurrentTab} 
        onMenuClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
      />

      {/* Mobile Drawer Overlay */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsMobileMenuOpen(false)}
            className="fixed inset-0 top-16 z-30 bg-black/60 backdrop-blur-sm md:hidden"
          >
            <motion.div
              initial={{ x: -240 }}
              animate={{ x: 0 }}
              exit={{ x: -240 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              onClick={(e) => e.stopPropagation()}
              className="h-full w-60 bg-zinc-950 border-r border-zinc-900 p-4 space-y-4"
            >
              <div className="space-y-1.5">
                {[
                  { id: 'landing', label: 'Home', icon: Home },
                  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
                  { id: 'details', label: 'Repo Details', icon: ShieldCheck },
                  { id: 'ai-insights', label: 'AI Insights', icon: Cpu },
                ].map((item) => {
                  const Icon = item.icon;
                  const isActive = currentTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        setCurrentTab(item.id);
                        setIsMobileMenuOpen(false);
                      }}
                      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                        isActive 
                          ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' 
                          : 'text-zinc-400 hover:bg-zinc-900/50 hover:text-white border border-transparent'
                      }`}
                    >
                      <Icon className="h-4.5 w-4.5" />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* Repositories Sublist for Mobile */}
              <div className="pt-4 border-t border-zinc-900 text-left">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-2 px-2">
                  Repositories
                </h4>
                <div className="space-y-1 max-h-[250px] overflow-y-auto">
                  {mockRepositories.map((repo) => {
                    const isSelected = selectedRepo?.id === repo.id;
                    return (
                      <button
                        key={repo.id}
                        onClick={() => {
                          setSelectedRepo(repo);
                          setCurrentTab('details');
                          setIsMobileMenuOpen(false);
                        }}
                        className={`flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs text-left truncate ${
                          isSelected 
                            ? 'bg-zinc-800/80 text-white font-medium pl-2.5' 
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
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex-1 flex relative">
        {/* Collapsible Left Sidebar */}
        <Sidebar
          currentTab={currentTab}
          setCurrentTab={setCurrentTab}
          repositories={mockRepositories}
          selectedRepo={selectedRepo}
          setSelectedRepo={setSelectedRepo}
          isCollapsed={isSidebarCollapsed}
          setIsCollapsed={setIsSidebarCollapsed}
        />

        {/* Content Panel Area */}
        <main
          className={`flex-1 min-w-0 transition-all duration-300 ${
            currentTab === 'landing' ? 'ml-0' : (isSidebarCollapsed ? 'md:ml-16' : 'md:ml-64')
          }`}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={currentTab}
              variants={pageTransitionVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="h-full"
            >
              {renderActivePage()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};
export default App;
