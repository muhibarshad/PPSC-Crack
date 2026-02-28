/**
 * Job Type Comparison — Radar Chart comparing topic ratios across job types.
 */

'use client';

import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { CompareJobTypesResponse, JobTypeMeta } from './types';

const RADAR_COLORS = [
  { stroke: '#8b5cf6', fill: 'rgba(139,92,246,0.15)' },
  { stroke: '#06b6d4', fill: 'rgba(6,182,212,0.15)' },
  { stroke: '#f59e0b', fill: 'rgba(245,158,11,0.15)' },
  { stroke: '#ef4444', fill: 'rgba(239,68,68,0.15)' },
  { stroke: '#10b981', fill: 'rgba(16,185,129,0.15)' },
];

interface Props {
  data: CompareJobTypesResponse | null;
  loading?: boolean;
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-sm px-4 py-3 rounded-xl border border-white/10 text-sm min-w-[160px]">
      <p className="font-semibold text-white mb-2">{label}</p>
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

export default function JobTypeComparisonChart({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="glass rounded-2xl p-6">
        <div className="h-6 w-52 bg-white/5 rounded-lg animate-pulse mb-6" />
        <div className="h-[420px] flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-[var(--clr-primary)] border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (!data || !data.series.length) {
    return (
      <div className="glass rounded-2xl p-6">
        <h3 className="text-lg font-display font-bold text-white mb-4">Job Type Comparison</h3>
        <div className="h-[300px] flex items-center justify-center text-[var(--clr-text-muted)] text-sm">
          Select at least 2 job types above to compare topic distributions.
        </div>
      </div>
    );
  }

  const jobTypes: JobTypeMeta[] = data.job_types;

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-display font-bold text-white">Job Type Comparison</h3>
        <span className="text-xs text-[var(--clr-text-muted)] bg-white/5 px-3 py-1 rounded-full">
          {jobTypes.length} job types · {data.topics.length} topics
        </span>
      </div>

      <ResponsiveContainer width="100%" height={420}>
        <RadarChart data={data.series} cx="50%" cy="50%" outerRadius="75%">
          <PolarGrid stroke="rgba(255,255,255,0.08)" />
          <PolarAngleAxis
            dataKey="topic"
            tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
          />
          <PolarRadiusAxis
            tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }}
            axisLine={false}
            tickFormatter={(v: number) => `${v}%`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '16px' }}
            formatter={(value: string) => (
              <span className="text-xs text-[var(--clr-text-secondary)]">{value}</span>
            )}
          />
          {jobTypes.map((jt, i) => (
            <Radar
              key={jt.id}
              name={jt.name}
              dataKey={jt.name}
              stroke={RADAR_COLORS[i % RADAR_COLORS.length].stroke}
              fill={RADAR_COLORS[i % RADAR_COLORS.length].fill}
              fillOpacity={1}
              strokeWidth={2}
            />
          ))}
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
