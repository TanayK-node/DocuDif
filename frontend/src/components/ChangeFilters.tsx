import React from 'react';
import { Search, Filter, RotateCcw } from 'lucide-react';

interface ChangeFiltersProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selectedType: string;
  onTypeChange: (t: string) => void;
  selectedPriority: string;
  onPriorityChange: (p: string) => void;
  selectedCategory: string;
  onCategoryChange: (c: string) => void;
  includeUnchanged: boolean;
  onToggleUnchanged: (v: boolean) => void;
  availableCategories: string[];
  totalMatches: number;
}

export const ChangeFilters: React.FC<ChangeFiltersProps> = ({
  searchQuery,
  onSearchChange,
  selectedType,
  onTypeChange,
  selectedPriority,
  onPriorityChange,
  selectedCategory,
  onCategoryChange,
  includeUnchanged,
  onToggleUnchanged,
  availableCategories,
  totalMatches,
}) => {
  const handleReset = () => {
    onSearchChange('');
    onTypeChange('all');
    onPriorityChange('all');
    onCategoryChange('all');
    onToggleUnchanged(false);
  };

  const hasActiveFilters =
    searchQuery !== '' ||
    selectedType !== 'all' ||
    selectedPriority !== 'all' ||
    selectedCategory !== 'all' ||
    includeUnchanged;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs mb-6">
      <div className="flex flex-col md:flex-row items-center gap-3">
        {/* Search */}
        <div className="relative w-full md:flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search keywords, clauses, explanations..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />
        </div>

        {/* Change Type */}
        <div className="w-full md:w-auto">
          <select
            value={selectedType}
            onChange={(e) => onTypeChange(e.target.value)}
            className="w-full md:w-auto text-xs py-1.5 px-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            <option value="all">All Change Types</option>
            <option value="modified">Modified Only</option>
            <option value="added">Added Only</option>
            <option value="removed">Removed Only</option>
          </select>
        </div>

        {/* Priority */}
        <div className="w-full md:w-auto">
          <select
            value={selectedPriority}
            onChange={(e) => onPriorityChange(e.target.value)}
            className="w-full md:w-auto text-xs py-1.5 px-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            <option value="all">All Priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        {/* Category */}
        <div className="w-full md:w-auto">
          <select
            value={selectedCategory}
            onChange={(e) => onCategoryChange(e.target.value)}
            className="w-full md:w-auto text-xs py-1.5 px-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 max-w-[200px] truncate"
          >
            <option value="all">All Categories</option>
            {availableCategories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        {/* Include unchanged checkbox */}
        <label className="flex items-center space-x-2 text-xs font-medium text-slate-600 whitespace-nowrap cursor-pointer">
          <input
            type="checkbox"
            checked={includeUnchanged}
            onChange={(e) => onToggleUnchanged(e.target.checked)}
            className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
          />
          <span>Show Unchanged</span>
        </label>

        {hasActiveFilters && (
          <button
            onClick={handleReset}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg transition"
            title="Reset Filters"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <span>Showing <strong>{totalMatches}</strong> matching records</span>
      </div>
    </div>
  );
};

