/**
 * Year-by-Year Shift Chart — Multi-line chart showing topic % over years.
 */

'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { YearByYearResponse, TopicMeta } from './types';

const LINE_COLORS = [
  '#8b5cf6', '#06b6d4', '#f59e0b', '#ef4444',
  '#10b981', '#ec4899', '#6366f1', '#14b8a6',
  '#f97316', '#84cc16', '#a855f7', '#0ea5e9',
];

interface Props {
  data: YearByYearResponse | null;
  loading?: boolean;
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-sm px-4 py-3 rounded-xl border border-white/10 text-sm min-w-[180px]">
      <p className="font-semibold text-white mb-2">Year {label}</p>
      {payload.map((entry: any, idx: number) => (
        <div key={idx} className="flex items-center justify-between gap-4 text-[var(--clr-text-secondary)]">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: entry.color }} />
            {entry.name}
          </span>
          <span className="font-mono text-white">{entry.value?.toFixed(1)}%</span>
        </div>
      ))}
    </div>
  );
}

export default function YearByYearChart({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="glass rounded-2xl p-6">
        <div className="h-6 w-56 bg-white/5 rounded-lg animate-pulse mb-6" />
        <div className="h-[380px] flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-[var(--clr-primary)] border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (!data || !data.series.length) {
    return (
      <div className="glass rounded-2xl p-6">
        <h3 className="text-lg font-display font-bold text-white mb-4">Year-by-Year Shift</h3>
        <div className="h-[300px] flex items-center justify-center text-[var(--clr-text-muted)] text-sm">
          Not enough multi-year data yet. Upload papers from different years.
        </div>
      </div>
    );
  }

  const topics: TopicMeta[] = data.topics;

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-display font-bold text-white">Year-by-Year Shift</h3>
        <span className="text-xs text-[var(--clr-text-muted)] bg-white/5 px-3 py-1 rounded-full">
          {data.years.length} years · {topics.length} topics
        </span>
      </div>

      <ResponsiveContainer width="100%" height={380}>
        <LineChart data={data.series} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis
            dataKey="year"
            tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
            tickLine={false}
            tickFormatter={(v: number) => `${v}%`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '16px' }}
            formatter={(value: string) => (
              <span className="text-xs text-[var(--clr-text-secondary)]">{value}</span>
            )}
          />
          {topics.map((t, i) => (
            <Line
              key={t.name}
              type="monotone"
              dataKey={t.name}
              name={t.display_name}
              stroke={LINE_COLORS[i % LINE_COLORS.length]}
              strokeWidth={2}
              dot={{ r: 3, fill: LINE_COLORS[i % LINE_COLORS.length] }}
              activeDot={{ r: 5, stroke: '#fff', strokeWidth: 2 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
