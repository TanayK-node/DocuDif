import React from 'react';
import { TokenDiff } from '../types/comparison';

interface TokenDiffViewerProps {
  tokens?: TokenDiff[];
  fallbackText?: string;
  mode?: 'unified' | 'old' | 'new';
}

export const TokenDiffViewer: React.FC<TokenDiffViewerProps> = ({
  tokens = [],
  fallbackText = '',
  mode = 'unified'
}) => {
  if (!tokens || tokens.length === 0) {
    return <span className="text-slate-700 whitespace-pre-wrap">{fallbackText || '—'}</span>;
  }

  if (mode === 'old') {
    // Show only equal and delete tokens
    const oldParts = tokens.filter(t => t.operation !== 'insert');
    return (
      <div className="font-mono text-sm leading-relaxed whitespace-pre-wrap">
        {oldParts.map((t, idx) => {
          if (t.operation === 'delete') {
            return (
              <mark key={idx} className="bg-red-100 text-red-800 line-through rounded px-0.5 font-semibold">
                {t.text}
              </mark>
            );
          }
          return <span key={idx} className="text-slate-700">{t.text}</span>;
        })}
      </div>
    );
  }

  if (mode === 'new') {
    // Show only equal and insert tokens
    const newParts = tokens.filter(t => t.operation !== 'delete');
    return (
      <div className="font-mono text-sm leading-relaxed whitespace-pre-wrap">
        {newParts.map((t, idx) => {
          if (t.operation === 'insert') {
            return (
              <mark key={idx} className="bg-emerald-100 text-emerald-800 rounded px-0.5 font-semibold">
                {t.text}
              </mark>
            );
          }
          return <span key={idx} className="text-slate-700">{t.text}</span>;
        })}
      </div>
    );
  }

  // Unified mode
  return (
    <div className="font-mono text-sm leading-relaxed whitespace-pre-wrap bg-slate-50 p-3 rounded-lg border border-slate-200">
      {tokens.map((t, idx) => {
        if (t.operation === 'delete') {
          return (
            <mark key={idx} className="bg-red-100 text-red-800 line-through rounded px-0.5 font-medium">
              {t.text}
            </mark>
          );
        }
        if (t.operation === 'insert') {
          return (
            <mark key={idx} className="bg-emerald-100 text-emerald-800 rounded px-0.5 font-medium">
              {t.text}
            </mark>
          );
        }
        return <span key={idx} className="text-slate-800">{t.text}</span>;
      })}
    </div>
  );
};

