// src/App.tsx
import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { mockDashboardStats, mockRepositories } from './data/mockData';
import { Repository } from './types/dashboard';

// Import components
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
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
            selectedRepo={selectedRepo!}
            setCurrentTab={setCurrentTab}
          />
        );
      case 'ai-insights':
        return <AIInsightsPanel selectedRepo={selectedRepo!} />;
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

  // Page transition animations
  const pageTransitionVariants = {
    initial: { opacity: 0, y: 8 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.25, ease: 'easeOut' } },
    exit: { opacity: 0, y: -8, transition: { duration: 0.15, ease: 'easeIn' } },
  };

  return (
    <div className="relative min-h-screen bg-background flex flex-col font-sans text-foreground">
      {/* Top Navigation */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        onMenuClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
      />

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          currentTab={currentTab}
          setCurrentTab={setCurrentTab}
          repositories={mockRepositories}
          selectedRepo={selectedRepo}
          setSelectedRepo={setSelectedRepo}
          isCollapsed={isSidebarCollapsed}
          setIsCollapsed={setIsSidebarCollapsed}
        />
        {/* Content area */}
        <main
          className={`flex-1 min-w-0 transition-all duration-300 ${
            currentTab === 'landing' ? 'ml-0' : isSidebarCollapsed ? 'md:ml-16' : 'md:ml-64'
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
