import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle, FileText, Scissors, Binary, GitCompare, ShieldAlert, Cpu, FileCheck } from 'lucide-react';

export const STAGES = [
  { id: 'extract', label: 'Extracting document text & structural metadata', icon: FileText },
  { id: 'segment', label: 'Whitespace normalization & clause segmentation', icon: Scissors },
  { id: 'embed', label: 'Generating SentenceTransformer semantic vectors', icon: Binary },
  { id: 'align', label: 'Two-pass exact & semantic passage alignment', icon: GitCompare },
  { id: 'rules', label: 'Deterministic material change & rule detection', icon: ShieldAlert },
  { id: 'llm', label: 'AI reasoning, obligation analysis & priority triage', icon: Cpu },
  { id: 'report', label: 'Synthesizing report & validation checks', icon: FileCheck },
];

export const ProcessingState: React.FC = () => {
  const [currentStageIdx, setCurrentStageIdx] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStageIdx((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
    }, 900);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="max-w-xl mx-auto py-16 px-4">
      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm text-center">
        <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-4 border border-blue-100">
          <Loader2 className="w-7 h-7 animate-spin" />
        </div>
        <h3 className="text-xl font-bold text-slate-900 mb-1">Analyzing Document Revisions</h3>
        <p className="text-xs text-slate-500 mb-6">
          Executing pipeline stages with exact matching, embeddings, and deterministic rule verification.
        </p>

        <div className="space-y-3 text-left">
          {STAGES.map((stage, idx) => {
            const Icon = stage.icon;
            const isDone = idx < currentStageIdx;
            const isCurrent = idx === currentStageIdx;
            return (
              <div
                key={stage.id}
                className={`flex items-center space-x-3 p-2.5 rounded-xl text-xs transition ${
                  isCurrent
                    ? 'bg-blue-50/70 border border-blue-200 text-blue-900 font-semibold'
                    : isDone
                    ? 'text-slate-600 font-medium'
                    : 'text-slate-400 opacity-60'
                }`}
              >
                <div className="flex-shrink-0">
                  {isDone ? (
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                  ) : (
                    <Icon className="w-4 h-4 text-slate-400" />
                  )}
                </div>
                <span>{stage.label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

