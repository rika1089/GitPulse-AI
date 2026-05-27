import React from 'react';
import { GitBranch, Cpu, Menu } from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  onMenuClick?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab, onMenuClick }) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md">
      <div className="flex h-16 items-center px-4 md:px-6">
        <button 
          onClick={onMenuClick}
          className="mr-3 md:hidden rounded-md p-2 text-zinc-400 hover:bg-zinc-900 hover:text-white"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2 font-semibold text-white mr-6 cursor-pointer" onClick={() => setCurrentTab('landing')}>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 shadow-md shadow-indigo-500/20">
            <GitBranch className="h-4.5 w-4.5 text-white" />
          </div>
          <span className="font-outfit text-lg font-bold tracking-tight bg-gradient-to-r from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent">
            GitPulse <span className="text-indigo-400">AI</span>
          </span>
        </div>

        <nav className="hidden md:flex items-center gap-5 text-sm font-medium">
          <button
            onClick={() => setCurrentTab('landing')}
            className={`transition-colors duration-200 ${
              currentTab === 'landing' ? 'text-white font-semibold' : 'text-zinc-400 hover:text-white'
            }`}
          >
            Home
          </button>
          <button
            onClick={() => setCurrentTab('dashboard')}
            className={`transition-colors duration-200 ${
              currentTab === 'dashboard' ? 'text-white font-semibold' : 'text-zinc-400 hover:text-white'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setCurrentTab('details')}
            className={`transition-colors duration-200 ${
              currentTab === 'details' ? 'text-white font-semibold' : 'text-zinc-400 hover:text-white'
            }`}
          >
            Repo Details
          </button>
          <button
            onClick={() => setCurrentTab('ai-insights')}
            className={`transition-colors duration-200 ${
              currentTab === 'ai-insights' ? 'text-white font-semibold' : 'text-zinc-400 hover:text-white'
            }`}
          >
            AI Insights
          </button>
        </nav>

        <div className="ml-auto flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-semibold glow-indigo animate-pulse-glow">
            <Cpu className="h-3 w-3 animate-spin-slow" />
            <span>MCP Server Connected</span>
          </div>

          <div className="h-8 w-8 rounded-full border border-zinc-800 bg-zinc-900 flex items-center justify-center font-bold text-xs text-indigo-400 cursor-pointer hover:bg-zinc-800 transition-colors">
            SU
          </div>
        </div>
      </div>
    </header>
  );
};
export default Navbar;
