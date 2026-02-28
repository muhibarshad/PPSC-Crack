/**
 * TopicCompletionBars — Horizontal bar chart showing % completion per topic.
 * Uses Recharts BarChart with horizontal layout.
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
} from 'recharts';

interface TopicCompletion {
  topic_id: string;
  topic_name: string;
  display_name: string;
  completed: boolean;
  weight: number;
  completion_percent: number;
}

interface Props {
  data: TopicCompletion[];
}

export default function TopicCompletionBars({ data }: Props) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center py-8 text-[var(--clr-text-muted)] text-sm">
        No topic data available yet.
      </div>
    );
  }

  // Sort by weight descending, limit to top 15
  const sorted = [...data]
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 15);

  const chartData = sorted.map((t) => ({
    name: t.display_name.length > 22 ? t.display_name.slice(0, 20) + '…' : t.display_name,
    fullName: t.display_name,
    percent: t.completion_percent,
    weight: t.weight,
    completed: t.completed,
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(250, sorted.length * 36)}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 4, right: 30, left: 4, bottom: 4 }}
      >
        <XAxis
          type="number"
          domain={[0, 100]}
          tick={{ fill: '#9d95c7', fontSize: 11 }}
          axisLine={{ stroke: 'rgba(139,92,246,0.1)' }}
          tickLine={false}
          tickFormatter={(v: number) => `${v}%`}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={150}
          tick={{ fill: '#9d95c7', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background: 'rgba(12, 12, 29, 0.95)',
            border: '1px solid rgba(139,92,246,0.2)',
            borderRadius: 12,
            color: '#f1f0ff',
            fontSize: 12,
          }}
          formatter={(value: number, _name: string, props: any) => [
            `${value}% complete (weight: ${props?.payload?.weight ?? ''})`,
            props?.payload?.fullName ?? '',
          ]}
          cursor={{ fill: 'rgba(139,92,246,0.06)' }}
        />
        <Bar dataKey="percent" radius={[0, 6, 6, 0]} barSize={20}>
          {chartData.map((entry, i) => (
            <Cell
              key={i}
              fill={entry.completed ? '#34d399' : 'rgba(139, 92, 246, 0.35)'}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
