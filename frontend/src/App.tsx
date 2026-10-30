import React, { useState, useEffect, useMemo } from 'react';
import { Header } from './components/Header';
import { UploadWorkspace } from './components/UploadWorkspace';
import { ProcessingState } from './components/ProcessingState';
import { ExecutiveSummary } from './components/ExecutiveSummary';
import { ChangeDistributionChart } from './components/ChangeDistributionChart';
import { ChangeFilters } from './components/ChangeFilters';
import { ChangeCard } from './components/ChangeCard';
import { ChangeDetailModal } from './components/ChangeDetailModal';
import { ComparisonResult, ChangeRecord, RecentComparisonItem } from './types/comparison';
import { api } from './services/api';
import { Clock, ArrowRight, History, Sparkles } from 'lucide-react';

export function App() {
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedChange, setSelectedChange] = useState<ChangeRecord | null>(null);
  const [recentComparisons, setRecentComparisons] = useState<RecentComparisonItem[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [includeUnchanged, setIncludeUnchanged] = useState<boolean>(false);

  useEffect(() => {
    // Fetch recent comparisons on load
    loadRecentComparisons();
  }, []);

  const loadRecentComparisons = async () => {
    try {
      const items = await api.listRecentComparisons();
      setRecentComparisons(items);
    } catch (err) {
      // Backend may be starting up
    }
  };

  const handleStartComparison = async (oldFile: File, newFile: File, provider: string, geminiApiKey?: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const result = await api.compareDocuments(oldFile, newFile, provider, 0.65, true, geminiApiKey);
      setComparisonResult(result);
      loadRecentComparisons();
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Comparison failed.';
      setErrorMessage(`Error: ${detail}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectRecent = async (id: string) => {
    setIsLoading(true);
    try {
      const res = await api.getComparison(id);
      setComparisonResult(res);
    } catch (err: any) {
      setErrorMessage(`Failed to load comparison ${id}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Filtered changes
  const filteredChanges = useMemo(() => {
    if (!comparisonResult) return [];

    return comparisonResult.changes.filter((c) => {
      if (!includeUnchanged && c.change_type === 'unchanged') {
        return false;
      }
      if (selectedType !== 'all' && c.change_type !== selectedType) {
        return false;
      }
      if (selectedPriority !== 'all' && c.priority !== selectedPriority) {
        return false;
      }
      if (selectedCategory !== 'all' && c.category !== selectedCategory) {
        return false;
      }
      if (searchQuery.trim() !== '') {
        const q = searchQuery.toLowerCase();
        const inOld = c.old_text.toLowerCase().includes(q);
        const inNew = c.new_text.toLowerCase().includes(q);
        const inExpl = c.explanation.toLowerCase().includes(q);
        const inImp = c.implication.toLowerCase().includes(q);
        const inCat = c.category.toLowerCase().includes(q);
        if (!inOld && !inNew && !inExpl && !inImp && !inCat) {
          return false;
        }
      }
      return true;
    });
  }, [comparisonResult, searchQuery, selectedType, selectedPriority, selectedCategory, includeUnchanged]);

  const availableCategories = useMemo(() => {
    if (!comparisonResult) return [];
    const set = new Set<string>();
    comparisonResult.changes.forEach((c) => {
      if (c.change_type !== 'unchanged') {
        set.add(c.category);
      }
    });
    return Array.from(set);
  }, [comparisonResult]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header
        onNewComparison={() => setComparisonResult(null)}
        hasActiveComparison={comparisonResult !== null}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {errorMessage && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            {errorMessage}
          </div>
        )}

        {isLoading ? (
          <ProcessingState />
        ) : !comparisonResult ? (
          <div>
            <UploadWorkspace
              onStartComparison={handleStartComparison}
              isLoading={isLoading}
            />

            {recentComparisons.length > 0 && (
              <div className="max-w-4xl mx-auto mt-12">
                <div className="flex items-center space-x-2 text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">
                  <History className="w-4 h-4" />
                  <span>Recent Comparison History</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {recentComparisons.map((item) => (
                    <div
                      key={item.comparison_id}
                      onClick={() => handleSelectRecent(item.comparison_id)}
                      className="bg-white p-4 rounded-xl border border-slate-200 hover:border-blue-400 hover:shadow-xs transition cursor-pointer"
                    >
                      <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                        <span className="font-mono font-semibold text-slate-700">{item.comparison_id}</span>
                        <span>{item.duration}s</span>
                      </div>
                      <p className="text-xs font-bold text-slate-800 truncate">{item.old_filename} vs {item.new_filename}</p>
                      <div className="flex items-center justify-between mt-3 text-2xs text-slate-500">
                        <span className="bg-slate-100 px-2 py-0.5 rounded font-semibold text-slate-700">
                          {item.total_changes} changes
                        </span>
                        <span className="text-blue-600 font-medium flex items-center space-x-0.5">
                          <span>View</span>
                          <ArrowRight className="w-3 h-3" />
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div>
            <ExecutiveSummary summary={comparisonResult.summary} />
            <ChangeDistributionChart summary={comparisonResult.summary} />

            <div className="mt-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-slate-900 tracking-tight">Clause-Level Change Explorer</h3>
              </div>

              <ChangeFilters
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                selectedType={selectedType}
                onTypeChange={setSelectedType}
                selectedPriority={selectedPriority}
                onPriorityChange={setSelectedPriority}
                selectedCategory={selectedCategory}
                onCategoryChange={setSelectedCategory}
                includeUnchanged={includeUnchanged}
                onToggleUnchanged={setIncludeUnchanged}
                availableCategories={availableCategories}
                totalMatches={filteredChanges.length}
              />

              <div className="space-y-3">
                {filteredChanges.length === 0 ? (
                  <div className="text-center py-12 bg-white rounded-2xl border border-slate-200 p-8">
                    <p className="text-sm font-semibold text-slate-700">No changes match the selected filter criteria.</p>
                    <p className="text-xs text-slate-400 mt-1">Try resetting the search or filter options above.</p>
                  </div>
                ) : (
                  filteredChanges.map((change) => (
                    <ChangeCard
                      key={change.change_id}
                      change={change}
                      onSelect={(c) => setSelectedChange(c)}
                    />
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <ChangeDetailModal
        change={selectedChange}
        onClose={() => setSelectedChange(null)}
      />

      <footer className="border-t border-slate-200 py-6 bg-white text-center text-xs text-slate-500">
        <p>DocuDiff AI — Document Intelligence & Difference Triage Platform</p>
      </footer>
    </div>
  );
}

export default App;

