/**
 * ReadinessComparison — Side-by-side comparison of user's readiness
 * vs average readiness of all users preparing for the same job type.
 * Uses Recharts BarChart for a clean visual comparison.
 */

'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
} from 'recharts';

interface Props {
  userReadiness: number;
  averageReadiness: number;
  totalPeers: number;
}

export default function ReadinessComparison({
  userReadiness,
  averageReadiness,
  totalPeers,
}: Props) {
  const chartData = [
    { name: 'You', value: Math.round(userReadiness * 10) / 10 },
    { name: `Avg (${totalPeers} peers)`, value: Math.round(averageReadiness * 10) / 10 },
  ];

  const colors = ['#a78bfa', '#818cf8'];
  const diff = userReadiness - averageReadiness;

  return (
    <div className="flex flex-col gap-4">
      {/* Insight badge */}
      <div className="flex items-center gap-3">
        {diff > 0 ? (
          <span
            className="badge text-[10px]"
            style={{
              background: 'rgba(52, 211, 153, 0.12)',
              color: '#34d399',
              border: '1px solid rgba(52, 211, 153, 0.25)',
            }}
          >
            ▲ {Math.abs(diff).toFixed(1)}% above average
          </span>
        ) : diff < 0 ? (
          <span
            className="badge text-[10px]"
            style={{
              background: 'rgba(251, 146, 60, 0.12)',
              color: '#fb923c',
              border: '1px solid rgba(251, 146, 60, 0.25)',
            }}
          >
            ▼ {Math.abs(diff).toFixed(1)}% below average
          </span>
        ) : (
          <span className="badge badge-primary text-[10px]">
            Right at average
          </span>
        )}
        {totalPeers === 0 && (
          <span className="text-[10px] text-[var(--clr-text-muted)]">
            No peer data yet
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 4 }}>
          <XAxis
            dataKey="name"
            tick={{ fill: '#9d95c7', fontSize: 12 }}
            axisLine={{ stroke: 'rgba(139,92,246,0.1)' }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: '#9d95c7', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => `${v}%`}
          />
          <Tooltip
            contentStyle={{
              background: 'rgba(12, 12, 29, 0.95)',
              border: '1px solid rgba(139,92,246,0.2)',
              borderRadius: 12,
              color: '#f1f0ff',
              fontSize: 12,
            }}
            formatter={(value: number) => [`${value}%`, 'Readiness']}
          />
          <Bar dataKey="value" radius={[8, 8, 0, 0]} barSize={56}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={colors[i]} />
            ))}
            <LabelList
              dataKey="value"
              position="top"
              formatter={(v: number) => `${v}%`}
              style={{ fill: '#f1f0ff', fontSize: 13, fontWeight: 600 }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
