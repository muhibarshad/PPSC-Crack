/**
 * TimeStudiedChart — Bar chart of daily study minutes for past 30 days.
 * Uses Recharts BarChart with gradient bars.
 */

'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

interface DailyStudyMinutes {
  date: string;
  minutes: number;
}

interface Props {
  data: DailyStudyMinutes[];
}

export default function TimeStudiedChart({ data }: Props) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center py-8 text-[var(--clr-text-muted)] text-sm">
        No study time data yet.
      </div>
    );
  }

  const chartData = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString('en', { day: 'numeric', month: 'short' }),
    rawDate: d.date,
    minutes: d.minutes,
  }));

  const totalMinutes = data.reduce((s, d) => s + d.minutes, 0);
  const avgMinutes = Math.round(totalMinutes / data.length);

  return (
    <div>
      {/* Summary stats */}
      <div className="flex gap-6 mb-4">
        <div>
          <p className="text-[10px] uppercase tracking-widest text-[var(--clr-text-muted)]">Total</p>
          <p className="font-display text-lg font-bold text-white">
            {Math.floor(totalMinutes / 60)}h {totalMinutes % 60}m
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-widest text-[var(--clr-text-muted)]">Daily Avg</p>
          <p className="font-display text-lg font-bold text-white">{avgMinutes} min</p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={chartData} margin={{ top: 4, right: 4, left: -16, bottom: 4 }}>
          <defs>
            <linearGradient id="studyBarGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#818cf8" stopOpacity={0.9} />
              <stop offset="100%" stopColor="#818cf8" stopOpacity={0.3} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(139,92,246,0.06)" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#9d95c7', fontSize: 9 }}
            axisLine={{ stroke: 'rgba(139,92,246,0.1)' }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: '#9d95c7', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => `${v}m`}
          />
          <Tooltip
            contentStyle={{
              background: 'rgba(12, 12, 29, 0.95)',
              border: '1px solid rgba(139,92,246,0.2)',
              borderRadius: 12,
              color: '#f1f0ff',
              fontSize: 12,
            }}
            formatter={(value: number) => [`${value} min`, 'Study Time']}
          />
          <Bar
            dataKey="minutes"
            fill="url(#studyBarGrad)"
            radius={[4, 4, 0, 0]}
            barSize={12}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
