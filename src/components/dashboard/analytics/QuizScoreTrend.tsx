/**
 * QuizScoreTrend — Line chart of quiz scores over time.
 * Uses Recharts LineChart with gradient fill.
 */

'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Area,
  AreaChart,
} from 'recharts';

interface QuizScorePoint {
  date: string;
  score_percent: number;
  total_questions: number;
}

interface Props {
  data: QuizScorePoint[];
}

export default function QuizScoreTrend({ data }: Props) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center py-8 text-[var(--clr-text-muted)] text-sm">
        Complete a quiz to see your score trend.
      </div>
    );
  }

  const chartData = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString('en', { month: 'short', day: 'numeric' }),
    rawDate: d.date,
    score: Math.round(d.score_percent),
    questions: d.total_questions,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={chartData} margin={{ top: 8, right: 12, left: -8, bottom: 4 }}>
        <defs>
          <linearGradient id="quizGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#a78bfa" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#a78bfa" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(139,92,246,0.06)" />
        <XAxis
          dataKey="date"
          tick={{ fill: '#9d95c7', fontSize: 11 }}
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
          formatter={(value: number, _name: string, props: any) => [
            `${value}% (${props?.payload?.questions ?? 0} Qs)`,
            'Score',
          ]}
        />
        <Area
          type="monotone"
          dataKey="score"
          stroke="#a78bfa"
          strokeWidth={2.5}
          fill="url(#quizGrad)"
          dot={{ r: 4, fill: '#a78bfa', stroke: '#0c0c1d', strokeWidth: 2 }}
          activeDot={{ r: 6, fill: '#c4b5fd', stroke: '#a78bfa', strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
