import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { ComparisonSummary } from '../types/comparison';

interface ChangeDistributionChartProps {
  summary: ComparisonSummary;
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: '#b91c1c',
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#64748b',
};

export const ChangeDistributionChart: React.FC<ChangeDistributionChartProps> = ({ summary }) => {
  const priorityData = [
    { name: 'Critical', count: summary.priority_breakdown['critical'] || 0, key: 'critical' },
    { name: 'High', count: summary.priority_breakdown['high'] || 0, key: 'high' },
    { name: 'Medium', count: summary.priority_breakdown['medium'] || 0, key: 'medium' },
    { name: 'Low', count: summary.priority_breakdown['low'] || 0, key: 'low' },
  ].filter(d => d.count > 0);

  const categoryEntries = Object.entries(summary.category_breakdown || {}).map(([name, count]) => ({
    name: name.length > 25 ? name.substring(0, 25) + '…' : name,
    fullName: name,
    count
  }));

  if (priorityData.length === 0 && categoryEntries.length === 0) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      {/* Priority Bar Chart */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">
          Review Priority Triage Breakdown
        </h3>
        <div className="h-44 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={priorityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                cursor={{ fill: 'rgba(241, 245, 249, 0.6)' }}
              />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {priorityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PRIORITY_COLORS[entry.key] || '#3b82f6'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
          Semantic Change Categories
        </h3>
        <div className="space-y-2 overflow-y-auto max-h-44 pr-1">
          {categoryEntries.map((cat, idx) => (
            <div key={idx} className="flex items-center justify-between text-xs py-1.5 px-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <span className="font-medium text-slate-700 truncate mr-2" title={cat.fullName}>
                {cat.name}
              </span>
              <span className="font-bold text-slate-900 bg-white px-2 py-0.5 rounded shadow-2xs border border-slate-200">
                {cat.count}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

