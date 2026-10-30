import React from 'react';
import { ChangeRecord } from '../types/comparison';
import { ChevronRight, ShieldAlert, Sparkles, CheckCircle2 } from 'lucide-react';
import { TokenDiffViewer } from './TokenDiffViewer';

interface ChangeCardProps {
  change: ChangeRecord;
  onSelect: (change: ChangeRecord) => void;
}

export const ChangeCard: React.FC<ChangeCardProps> = ({ change, onSelect }) => {
  const priorityStyle = {
    critical: 'bg-red-600 text-white',
    high: 'bg-rose-100 text-rose-800 border-rose-200',
    medium: 'bg-amber-100 text-amber-800 border-amber-200',
    low: 'bg-slate-100 text-slate-700 border-slate-200',
  }[change.priority];

  const typeStyle = {
    modified: 'bg-blue-50 text-blue-700 border-blue-200',
    added: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    removed: 'bg-red-50 text-red-700 border-red-200',
    unchanged: 'bg-slate-50 text-slate-600 border-slate-200',
  }[change.change_type];

  return (
    <div
      onClick={() => onSelect(change)}
      className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs hover:shadow-md hover:border-blue-300 transition cursor-pointer mb-3.5 group"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
            {change.change_id}
          </span>
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${typeStyle}`}>
            {change.change_type.toUpperCase()}
          </span>
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${priorityStyle}`}>
            {change.priority.toUpperCase()}
          </span>
          <span className="text-xs font-semibold text-slate-700 bg-slate-100/70 px-2.5 py-0.5 rounded-full border border-slate-200">
            {change.category}
          </span>
        </div>

        <div className="text-xs text-slate-400 font-medium flex items-center space-x-1 group-hover:text-blue-600 transition">
          <span>Inspect details</span>
          <ChevronRight className="w-4 h-4" />
        </div>
      </div>

      {/* Side by Side Diff Preview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
        <div className="bg-slate-50/70 rounded-xl p-3 border border-slate-100 border-l-4 border-l-red-400">
          <div className="flex items-center justify-between text-2xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
            <span>Previous</span>
            <span className="text-slate-400">{change.old_source || '—'}</span>
          </div>
          <div className="text-xs text-slate-800 line-clamp-3">
            <TokenDiffViewer tokens={change.diff_tokens} fallbackText={change.old_text} mode="old" />
          </div>
        </div>

        <div className="bg-slate-50/70 rounded-xl p-3 border border-slate-100 border-l-4 border-l-emerald-400">
          <div className="flex items-center justify-between text-2xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
            <span>Revised</span>
            <span className="text-slate-400">{change.new_source || '—'}</span>
          </div>
          <div className="text-xs text-slate-800 line-clamp-3">
            <TokenDiffViewer tokens={change.diff_tokens} fallbackText={change.new_text} mode="new" />
          </div>
        </div>
      </div>

      {/* Explanation & Rules */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs pt-2 border-t border-slate-100">
        <p className="text-slate-700 font-medium flex-1">
          <span className="font-semibold text-slate-900">Analysis:</span> {change.explanation}
        </p>

        {change.rule_flags && change.rule_flags.length > 0 && (
          <div className="flex items-center space-x-1 text-slate-500 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200/60 flex-shrink-0">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
            <span className="font-semibold text-amber-800">{change.rule_flags.length} Rule Trigger{change.rule_flags.length > 1 ? 's' : ''}</span>
          </div>
        )}
      </div>
    </div>
  );
};

