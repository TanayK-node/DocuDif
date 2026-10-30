import React from 'react';
import { ChangeRecord } from '../types/comparison';
import { X, ShieldAlert, AlertTriangle, CheckCircle, Info, ExternalLink } from 'lucide-react';
import { TokenDiffViewer } from './TokenDiffViewer';

interface ChangeDetailModalProps {
  change: ChangeRecord | null;
  onClose: () => void;
}

export const ChangeDetailModal: React.FC<ChangeDetailModalProps> = ({ change, onClose }) => {
  if (!change) return null;

  const priorityStyle = {
    critical: 'bg-red-600 text-white',
    high: 'bg-rose-100 text-rose-800 border-rose-200',
    medium: 'bg-amber-100 text-amber-800 border-amber-200',
    low: 'bg-slate-100 text-slate-700 border-slate-200',
  }[change.priority];

  const typeStyle = {
    modified: 'bg-blue-100 text-blue-800 border-blue-200',
    added: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    removed: 'bg-red-100 text-red-800 border-red-200',
    unchanged: 'bg-slate-100 text-slate-700 border-slate-200',
  }[change.change_type];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-3xl w-full border border-slate-200 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center space-x-2.5">
            <span className="font-mono text-xs font-bold text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200">
              {change.change_id}
            </span>
            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${typeStyle}`}>
              {change.change_type.toUpperCase()}
            </span>
            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${priorityStyle}`}>
              PRIORITY: {change.priority.toUpperCase()}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {/* Category & Sources */}
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
            <span className="font-semibold text-slate-800 bg-slate-100 px-3 py-1 rounded-lg">
              Category: {change.category}
            </span>
            <div className="text-slate-500">
              <span><strong>Baseline:</strong> {change.old_source || '—'}</span>
              <span className="mx-2">•</span>
              <span><strong>Revised:</strong> {change.new_source || '—'}</span>
            </div>
          </div>

          {/* Unified Diff View */}
          {change.change_type === 'modified' && (
            <div>
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                Unified Token-Level Difference
              </h4>
              <TokenDiffViewer tokens={change.diff_tokens} fallbackText={change.new_text} mode="unified" />
            </div>
          )}

          {/* Side by Side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 border-l-4 border-l-red-500">
              <span className="text-xs font-bold text-slate-500 uppercase block mb-1.5">Previous Text</span>
              <TokenDiffViewer tokens={change.diff_tokens} fallbackText={change.old_text} mode="old" />
            </div>

            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 border-l-4 border-l-emerald-500">
              <span className="text-xs font-bold text-slate-500 uppercase block mb-1.5">Revised Text</span>
              <TokenDiffViewer tokens={change.diff_tokens} fallbackText={change.new_text} mode="new" />
            </div>
          </div>

          {/* Explanations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-blue-50/50 rounded-xl p-4 border border-blue-100">
              <h4 className="text-xs font-bold text-blue-900 uppercase tracking-wider mb-1 flex items-center space-x-1">
                <Info className="w-3.5 h-3.5 text-blue-600" />
                <span>Change Explanation</span>
              </h4>
              <p className="text-xs text-blue-950 leading-relaxed">{change.explanation}</p>
            </div>

            <div className="bg-amber-50/50 rounded-xl p-4 border border-amber-100">
              <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider mb-1 flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>Operational Implication</span>
              </h4>
              <p className="text-xs text-amber-950 leading-relaxed">{change.implication}</p>
            </div>
          </div>

          {/* Rules and Rationale */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
              <h4 className="font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center space-x-1">
                <ShieldAlert className="w-3.5 h-3.5 text-slate-500" />
                <span>Deterministic Rule Signals</span>
              </h4>
              {change.rule_flags && change.rule_flags.length > 0 ? (
                <ul className="space-y-1.5">
                  {change.rule_flags.map((flag, idx) => (
                    <li key={idx} className="bg-white p-2 rounded border border-slate-200">
                      <span className="font-semibold text-slate-800">{flag.category}:</span>{' '}
                      <span className="text-slate-600">{flag.description}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-slate-400 italic">No material rule flags triggered for this clause.</p>
              )}
            </div>

            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
              <h4 className="font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center space-x-1">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                <span>Priority Rationale</span>
              </h4>
              <ul className="space-y-1.5">
                {change.priority_reasons.map((reason, idx) => (
                  <li key={idx} className="bg-white p-2 rounded border border-slate-200 text-slate-700">
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Warnings & Status */}
          {change.warnings && change.warnings.length > 0 && (
            <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-800">
              <strong>Warnings:</strong> {change.warnings.join('; ')}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold bg-white border border-slate-200 rounded-xl text-slate-700 hover:bg-slate-100 transition shadow-2xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

