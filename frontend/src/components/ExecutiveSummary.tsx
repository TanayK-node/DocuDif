import React from 'react';
import { ComparisonSummary } from '../types/comparison';
import { Download, FileSpreadsheet, Globe, Clock, Layers, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';

interface ExecutiveSummaryProps {
  summary: ComparisonSummary;
}

export const ExecutiveSummary: React.FC<ExecutiveSummaryProps> = ({ summary }) => {
  const highCriticalCount = (summary.priority_breakdown['high'] || 0) + (summary.priority_breakdown['critical'] || 0);

  const handleExport = (format: 'csv' | 'html') => {
    const url = api.getExportUrl(summary.comparison_id, format);
    window.open(url, '_blank');
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Executive Comparison Summary</h2>
            <span className="font-mono text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-semibold">
              ID: {summary.comparison_id}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-xs text-slate-500">
            <span><strong>Baseline:</strong> {summary.old_filename}</span>
            <span>•</span>
            <span><strong>Revised:</strong> {summary.new_filename}</span>
            <span>•</span>
            <span className="flex items-center space-x-1">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>{summary.processing_duration_seconds}s</span>
            </span>
            <span>•</span>
            <span className="flex items-center space-x-1">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <span>{summary.langgraph_used ? 'LangGraph Workflow' : 'Sequential Pipeline'}</span>
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleExport('csv')}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition shadow-xs"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => handleExport('html')}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition shadow-xs shadow-blue-500/20"
          >
            <Globe className="w-4 h-4" />
            <span>Export HTML Report</span>
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5 mt-6">
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 text-center">
          <p className="text-2xl font-extrabold text-slate-900">{summary.total_changes}</p>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-0.5">Total Changes</p>
        </div>

        <div className="bg-emerald-50/60 border border-emerald-200/80 rounded-xl p-3.5 text-center">
          <p className="text-2xl font-extrabold text-emerald-700">{summary.added}</p>
          <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mt-0.5">Added Clauses</p>
        </div>

        <div className="bg-blue-50/60 border border-blue-200/80 rounded-xl p-3.5 text-center">
          <p className="text-2xl font-extrabold text-blue-700">{summary.modified}</p>
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider mt-0.5">Modified</p>
        </div>

        <div className="bg-red-50/60 border border-red-200/80 rounded-xl p-3.5 text-center">
          <p className="text-2xl font-extrabold text-red-700">{summary.removed}</p>
          <p className="text-xs font-semibold text-red-600 uppercase tracking-wider mt-0.5">Removed</p>
        </div>

        <div className="bg-rose-50/80 border border-rose-200 rounded-xl p-3.5 text-center col-span-2 sm:col-span-1">
          <p className="text-2xl font-extrabold text-rose-700">{highCriticalCount}</p>
          <p className="text-xs font-semibold text-rose-600 uppercase tracking-wider mt-0.5">High / Critical</p>
        </div>
      </div>
    </div>
  );
};

