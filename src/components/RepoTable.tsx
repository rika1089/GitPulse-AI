import React, { useState, useMemo } from 'react';
import { Search, Download, ArrowUpDown, ChevronRight, Filter } from 'lucide-react';
import { Repository } from '../types/dashboard';
import { HealthBadge } from './HealthBadge';

interface RepoTableProps {
  repositories: Repository[];
  onSelectRepo: (repo: Repository) => void;
}

type SortField = 'name' | 'license' | 'openIssuesCount' | 'openPRsCount' | 'lastPushDate' | 'healthScore';
type SortOrder = 'asc' | 'desc';

export const RepoTable: React.FC<RepoTableProps> = ({ repositories, onSelectRepo }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('healthScore');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // Collect all unique topics/tags for filtering
  const allTopics = useMemo(() => {
    const topicsSet = new Set<string>();
    repositories.forEach(repo => {
      repo.topics.forEach(topic => topicsSet.add(topic));
    });
    return Array.from(topicsSet).slice(0, 8); // Limit to top 8 for UI aesthetics
  }, [repositories]);

  // Handle CSV export
  const exportToCSV = () => {
    const headers = ['Repository Name', 'Owner', 'License', 'Open Issues', 'Open PRs', 'Last Push', 'Health Score', 'Classification', 'Primary Language'];
    const rows = filteredAndSortedRepos.map(repo => [
      repo.name,
      repo.owner,
      repo.license,
      repo.openIssuesCount,
      repo.openPRsCount,
      repo.lastPushDate,
      repo.healthScore,
      repo.classification,
      repo.primaryLanguage
    ]);

    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `gitpulse_health_report_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Toggle sorting
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc'); // Default to high-to-low on first click
    }
  };

  // Filter & Sort logic
  const filteredAndSortedRepos = useMemo(() => {
    return repositories
      .filter(repo => {
        const matchesSearch = 
          repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          repo.owner.toLowerCase().includes(searchQuery.toLowerCase()) ||
          repo.description.toLowerCase().includes(searchQuery.toLowerCase());
        
        const matchesTopic = selectedTopic ? repo.topics.includes(selectedTopic) : true;
        
        return matchesSearch && matchesTopic;
      })
      .sort((a, b) => {
        let valA = a[sortField];
        let valB = b[sortField];

        // Format names to lowercase for string sorting
        if (typeof valA === 'string' && typeof valB === 'string') {
          valA = valA.toLowerCase();
          valB = valB.toLowerCase();
        }

        if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
        if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
  }, [repositories, searchQuery, selectedTopic, sortField, sortOrder]);

  return (
    <div className="space-y-4">
      {/* Search & Action Controls */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search repositories by name, owner, or tech..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-zinc-800 bg-zinc-900/50 py-2 pl-10 pr-4 text-sm text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none transition-colors"
          />
        </div>

        <div className="flex items-center gap-2">
          {selectedTopic && (
            <button
              onClick={() => setSelectedTopic(null)}
              className="text-xs text-zinc-400 hover:text-white underline underline-offset-4 px-2 py-1.5"
            >
              Clear filters
            </button>
          )}
          <button
            onClick={exportToCSV}
            className="flex items-center gap-1.5 rounded-lg bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 hover:text-white px-3.5 py-2 text-xs font-semibold text-zinc-300 transition-all cursor-pointer"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Download CSV</span>
          </button>
        </div>
      </div>

      {/* Filter Topics Grid */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-zinc-500 flex items-center gap-1">
          <Filter className="h-3 w-3" /> Filter Topics:
        </span>
        {allTopics.map((topic) => {
          const isSelected = selectedTopic === topic;
          return (
            <button
              key={topic}
              onClick={() => setSelectedTopic(isSelected ? null : topic)}
              className={`rounded-full px-3 py-1 text-xs font-medium border transition-all ${
                isSelected
                  ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40 glow-indigo'
                  : 'bg-zinc-900/50 text-zinc-400 border-zinc-800 hover:text-white hover:border-zinc-700'
              }`}
            >
              #{topic}
            </button>
          );
        })}
      </div>

      {/* Repository Table Container */}
      <div className="overflow-x-auto rounded-xl border border-zinc-800/80 bg-zinc-900/20 backdrop-blur-sm">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-zinc-800 text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-900/40">
              <th className="py-3.5 px-4 cursor-pointer hover:text-white select-none" onClick={() => handleSort('name')}>
                <div className="flex items-center gap-1">
                  Repository Name
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="py-3.5 px-4 cursor-pointer hover:text-white select-none" onClick={() => handleSort('license')}>
                <div className="flex items-center gap-1">
                  License
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="py-3.5 px-4 cursor-pointer hover:text-white select-none text-center" onClick={() => handleSort('openIssuesCount')}>
                <div className="flex items-center gap-1 justify-center">
                  Issues
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="py-3.5 px-4 cursor-pointer hover:text-white select-none text-center" onClick={() => handleSort('openPRsCount')}>
                <div className="flex items-center gap-1 justify-center">
                  PRs
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="py-3.5 px-4 cursor-pointer hover:text-white select-none" onClick={() => handleSort('lastPushDate')}>
                <div className="flex items-center gap-1">
                  Last Push
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="py-3.5 px-4 cursor-pointer hover:text-white select-none" onClick={() => handleSort('healthScore')}>
                <div className="flex items-center gap-1">
                  Health Score
                  <ArrowUpDown className="h-3 w-3" />
                </div>
              </th>
              <th className="py-3.5 px-4">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-900/80 text-sm">
            {filteredAndSortedRepos.length > 0 ? (
              filteredAndSortedRepos.map((repo) => (
                <tr 
                  key={repo.id}
                  onClick={() => onSelectRepo(repo)}
                  className="group hover:bg-zinc-900/40 cursor-pointer transition-colors"
                >
                  <td className="py-4 px-4">
                    <div className="flex flex-col">
                      <span className="font-semibold text-white group-hover:text-indigo-400 transition-colors">
                        {repo.owner}/<span className="text-zinc-100">{repo.name}</span>
                      </span>
                      <span className="text-xs text-zinc-400 mt-1 max-w-[320px] truncate">
                        {repo.description}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <span className="inline-block rounded bg-zinc-900 border border-zinc-800/80 px-2 py-0.5 text-xs text-zinc-300 font-medium font-mono">
                      {repo.license || 'Proprietary'}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center font-mono text-zinc-300">
                    {repo.openIssuesCount}
                  </td>
                  <td className="py-4 px-4 text-center font-mono text-zinc-300">
                    {repo.openPRsCount}
                  </td>
                  <td className="py-4 px-4 text-xs text-zinc-400">
                    {repo.lastPushDate}
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-3">
                      <div className="relative flex items-center justify-center">
                        {/* Circular Progress Gauge */}
                        <svg className="w-9 h-9" viewBox="0 0 36 36">
                          <path
                            className="text-zinc-800"
                            strokeWidth="2.5"
                            stroke="currentColor"
                            fill="none"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          />
                          <path
                            className={`${
                              repo.healthScore >= 80 ? 'text-emerald-500' :
                              repo.healthScore >= 60 ? 'text-amber-500' : 'bg-red-500'
                            }`}
                            strokeWidth="2.5"
                            strokeDasharray={`${repo.healthScore}, 100`}
                            strokeLinecap="round"
                            stroke="currentColor"
                            fill="none"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          />
                        </svg>
                        <span className="absolute text-[10px] font-bold font-mono text-zinc-300">
                          {repo.healthScore}
                        </span>
                      </div>
                      <HealthBadge classification={repo.classification} showIcon={false} />
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <button className="rounded-lg p-1.5 text-zinc-500 group-hover:text-white group-hover:bg-zinc-800 transition-all">
                      <ChevronRight className="h-4.5 w-4.5" />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} className="py-12 text-center text-zinc-500 text-sm">
                  No repositories found matching your current query. Try adjusting your filter tags.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
export default RepoTable;
