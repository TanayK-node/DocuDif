import React from 'react';
import { FileDiff, ShieldCheck, Sparkles, PlusCircle } from 'lucide-react';

interface HeaderProps {
  onNewComparison: () => void;
  hasActiveComparison: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onNewComparison, hasActiveComparison }) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={onNewComparison}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <FileDiff className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-slate-900 tracking-tight">DocuDiff<span className="text-blue-600">AI</span></span>
              <span className="text-xs bg-blue-50 text-blue-700 font-semibold px-2 py-0.5 rounded-full border border-blue-200">
                v1.0 MVP
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">Intelligent Document Comparison & Change Analyzer</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center space-x-2 text-xs text-slate-500 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Deterministic Rules Active</span>
          </div>

          {hasActiveComparison && (
            <button
              onClick={onNewComparison}
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700 transition shadow-sm"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>New Comparison</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

