/**
 * Topic Frequency Chart — Horizontal Bar Chart
 * Shows the latest-year topic distribution for a selected job type.
 */

'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { TopicTrend } from './types';

const BAR_COLORS = [
  '#8b5cf6', '#a78bfa', '#c084fc', '#7c3aed',
  '#6d28d9', '#5b21b6', '#4c1d95', '#ddd6fe',
  '#818cf8', '#6366f1', '#4f46e5', '#4338ca',
];

const TREND_ICONS: Record<string, string> = {
  rising: '↑',
  falling: '↓',
  stable: '→',
};

interface Props {
  data: TopicTrend[];
  loading?: boolean;
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as TopicTrend;
  return (
    <div className="glass-sm px-4 py-3 rounded-xl border border-white/10 text-sm">
      <p className="font-semibold text-white mb-1">{d.display_name}</p>
      <p className="text-[var(--clr-text-secondary)]">
        {d.percentage.toFixed(1)}% · {d.question_count} questions
      </p>
      {d.trend_direction && (
        <p className={`text-xs mt-1 ${
          d.trend_direction === 'rising' ? 'text-emerald-400' :
          d.trend_direction === 'falling' ? 'text-red-400' : 'text-[var(--clr-text-muted)]'
        }`}>
          Trend: {TREND_ICONS[d.trend_direction]} {d.trend_direction}
        </p>
      )}
    </div>
  );
}

export default function TopicFrequencyChart({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="glass rounded-2xl p-6">
        <div className="h-6 w-48 bg-white/5 rounded-lg animate-pulse mb-6" />
        <div className="h-[400px] flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-[var(--clr-primary)] border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="glass rounded-2xl p-6">
        <h3 className="text-lg font-display font-bold text-white mb-4">Topic Frequency</h3>
        <div className="h-[300px] flex items-center justify-center text-[var(--clr-text-muted)] text-sm">
          No topic data available. Ingest papers to see frequency analysis.
        </div>
      </div>
    );
  }

  const sorted = [...data].sort((a, b) => b.percentage - a.percentage);

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-display font-bold text-white">Topic Frequency</h3>
        <span className="text-xs text-[var(--clr-text-muted)] bg-white/5 px-3 py-1 rounded-full">
          {sorted.length} topics · Latest year
        </span>
      </div>

      <ResponsiveContainer width="100%" height={Math.max(300, sorted.length * 44)}>
        <BarChart data={sorted} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
            tickLine={false}
            domain={[0, 'dataMax']}
            tickFormatter={(v: number) => `${v}%`}
          />
          <YAxis
            type="category"
            dataKey="display_name"
            width={140}
            tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <Bar dataKey="percentage" radius={[0, 6, 6, 0]} barSize={24}>
            {sorted.map((_, i) => (
              <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Trend badges */}
      <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-white/[0.06]">
        {sorted.slice(0, 6).map((t) => (
          <span
            key={t.topic_id}
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium ${
              t.trend_direction === 'rising'
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : t.trend_direction === 'falling'
                ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                : 'bg-white/5 text-[var(--clr-text-muted)] border border-white/10'
            }`}
          >
            {TREND_ICONS[t.trend_direction || 'stable']} {t.display_name}
          </span>
        ))}
      </div>
    </div>
  );
}
