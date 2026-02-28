'use client';

/**
 * Step 2: AI Analysis — Radar chart + stats per selected job type.
 * Uses Recharts (already in dependencies).
 */

import { useState } from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import Icon from '@/components/Icon';

export interface TopicRatioEntry {
  topic_name: string;
  display_name: string;
  percentage: number;
  question_count: number;
}

export interface JobAnalysis {
  job_type_id: string;
  job_type_name: string;
  topic_ratios: TopicRatioEntry[];
  estimated_prep_hours: number;
  confidence_score: number;
  total_papers_analyzed: number;
  total_topics: number;
}

interface Props {
  analyses: JobAnalysis[];
  onNext: () => void;
  onBack: () => void;
}

/* Theme-matched colors for multiple jobs */
const RADAR_COLORS = [
  'rgba(167, 139, 250, 0.85)',  // primary
  'rgba(232, 121, 249, 0.85)',  // neon
  'rgba(56, 189, 248, 0.85)',   // info
  'rgba(52, 211, 153, 0.85)',   // success
  'rgba(251, 191, 36, 0.85)',   // gold
];
const RADAR_FILLS = [
  'rgba(167, 139, 250, 0.15)',
  'rgba(232, 121, 249, 0.15)',
  'rgba(56, 189, 248, 0.15)',
  'rgba(52, 211, 153, 0.15)',
  'rgba(251, 191, 36, 0.15)',
];

function ConfidenceMeter({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 70 ? 'var(--clr-success)' :
    pct >= 40 ? 'var(--clr-warning)' :
    'var(--clr-danger)';
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium" style={{ color: 'var(--clr-text-secondary)' }}>
          Prediction Confidence
        </span>
        <span className="text-sm font-bold" style={{ color }}>{pct}%</span>
      </div>
      <div className="h-2 rounded-full overflow-hidden" style={{ background: 'rgba(139,92,246,0.1)' }}>
        <div
          className="h-full rounded-full transition-all"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${color}, ${color}88)`,
            boxShadow: `0 0 12px ${color}44`,
            transition: 'width 1s var(--ease-out)',
          }}
        />
      </div>
    </div>
  );
}

export default function AIAnalysisStep({ analyses, onNext, onBack }: Props) {
  const [activeTab, setActiveTab] = useState(0);
  const active = analyses[activeTab];

  if (!active) return null;

  // Radar data: take top 8 topics for readability
  const radarData = active.topic_ratios.slice(0, 8).map((t) => ({
    subject: t.display_name.length > 14 ? t.display_name.slice(0, 12) + '…' : t.display_name,
    fullName: t.display_name,
    value: t.percentage,
    questions: t.question_count,
  }));

  return (
    <div className="animate-fade-in-up">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6"
          style={{ background: 'var(--clr-neon-dim)', border: '1px solid rgba(232,121,249,0.2)' }}>
          <Icon name="brain" size={14} color="var(--clr-neon)" />
          <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--clr-neon)' }}>
            Step 2 of 3
          </span>
        </div>
        <h1 className="font-display text-3xl md:text-4xl font-bold mb-3" style={{ color: 'var(--clr-text-primary)' }}>
          AI <span className="gradient-text">Analysis</span> Results
        </h1>
        <p className="max-w-xl mx-auto" style={{ color: 'var(--clr-text-secondary)' }}>
          Here&apos;s what our AI discovered from analyzing past papers for your selected jobs.
        </p>
      </div>

      {/* Job tabs */}
      {analyses.length > 1 && (
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          {analyses.map((a, i) => (
            <button
              key={a.job_type_id}
              onClick={() => setActiveTab(i)}
              className="px-4 py-2 rounded-xl text-sm font-medium transition-all"
              style={{
                background: i === activeTab ? 'var(--grad-primary)' : 'var(--clr-glass-bg)',
                color: i === activeTab ? 'white' : 'var(--clr-text-secondary)',
                border: i === activeTab ? 'none' : '1px solid var(--clr-glass-border)',
                boxShadow: i === activeTab ? '0 4px 20px rgba(139,92,246,0.3)' : 'none',
              }}
            >
              {a.job_type_name}
            </button>
          ))}
        </div>
      )}

      {/* Analysis content */}
      <div className="grid lg:grid-cols-2 gap-6 mb-10">
        {/* Radar Chart */}
        <div className="glass p-6">
          <h3 className="font-display text-lg font-semibold mb-4" style={{ color: 'var(--clr-text-primary)' }}>
            Topic Ratio Breakdown
          </h3>
          {radarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
                <PolarGrid
                  stroke="rgba(139,92,246,0.12)"
                  strokeDasharray="3 3"
                />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{
                    fill: 'var(--clr-text-secondary)',
                    fontSize: 11,
                    fontFamily: 'var(--font-body)',
                  }}
                />
                <PolarRadiusAxis
                  angle={30}
                  domain={[0, 'auto']}
                  tick={{ fill: 'var(--clr-text-muted)', fontSize: 10 }}
                  axisLine={false}
                />
                <Radar
                  name={active.job_type_name}
                  dataKey="value"
                  stroke={RADAR_COLORS[activeTab % RADAR_COLORS.length]}
                  fill={RADAR_FILLS[activeTab % RADAR_FILLS.length]}
                  strokeWidth={2}
                  dot={{ r: 3, fill: RADAR_COLORS[activeTab % RADAR_COLORS.length] }}
                />
                <Tooltip
                  contentStyle={{
                    background: 'var(--clr-bg-elevated)',
                    border: '1px solid var(--clr-glass-border)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--clr-text-primary)',
                    fontSize: '13px',
                  }}
                  formatter={(value: number, _name: string, props: { payload?: { fullName?: string; questions?: number } }) => [
                    `${value.toFixed(1)}% (${props.payload?.questions ?? 0} questions)`,
                    props.payload?.fullName ?? '',
                  ]}
                />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64">
              <p style={{ color: 'var(--clr-text-muted)' }}>No topic data available yet</p>
            </div>
          )}
        </div>

        {/* Stats panel */}
        <div className="flex flex-col gap-4">
          {/* Confidence */}
          <div className="glass p-6">
            <ConfidenceMeter score={active.confidence_score} />
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="glow-card p-5">
              <div className="flex items-center gap-2 mb-2">
                <Icon name="cpu" size={16} color="var(--clr-primary)" />
                <span className="text-xs uppercase tracking-widest" style={{ color: 'var(--clr-text-muted)' }}>
                  Papers
                </span>
              </div>
              <p className="font-display text-2xl font-bold" style={{ color: 'var(--clr-text-primary)' }}>
                {active.total_papers_analyzed}
              </p>
              <p className="text-xs" style={{ color: 'var(--clr-text-muted)' }}>analyzed</p>
            </div>

            <div className="glow-card p-5">
              <div className="flex items-center gap-2 mb-2">
                <Icon name="book-open" size={16} color="var(--clr-neon)" />
                <span className="text-xs uppercase tracking-widest" style={{ color: 'var(--clr-text-muted)' }}>
                  Topics
                </span>
              </div>
              <p className="font-display text-2xl font-bold" style={{ color: 'var(--clr-text-primary)' }}>
                {active.total_topics}
              </p>
              <p className="text-xs" style={{ color: 'var(--clr-text-muted)' }}>unique topics</p>
            </div>

            <div className="glow-card p-5 col-span-2">
              <div className="flex items-center gap-2 mb-2">
                <Icon name="zap" size={16} color="var(--clr-gold)" />
                <span className="text-xs uppercase tracking-widest" style={{ color: 'var(--clr-text-muted)' }}>
                  Est. Preparation Time
                </span>
              </div>
              <p className="font-display text-3xl font-bold" style={{ color: 'var(--clr-text-primary)' }}>
                {active.estimated_prep_hours}
                <span className="text-base font-normal ml-1" style={{ color: 'var(--clr-text-secondary)' }}>hours</span>
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--clr-text-muted)' }}>
                Based on {active.total_topics} topics &amp; story document lengths
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="btn btn-ghost">
          <Icon name="arrow-right" size={16} className="rotate-180" />
          Back
        </button>
        <button onClick={onNext} className="btn btn-primary btn-lg">
          View Learning Path
          <Icon name="arrow-right" size={18} />
        </button>
      </div>
    </div>
  );
}
