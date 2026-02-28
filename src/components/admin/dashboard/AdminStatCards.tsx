/**
 * Admin Stat Cards — CountUp animated stats
 * =============================================
 * Four glass cards showing key metrics with smooth number animation.
 * Uses red accent for admin theming.
 */

'use client';

import CountUp from 'react-countup';
import type { AdminStats } from './types';

interface StatCardProps {
  label: string;
  value: number;
  suffix?: string;
  decimals?: number;
  icon: React.ReactNode;
  accent: string;      // color token like 'var(--clr-danger)' for red admin accent
  accentDim: string;
}

function StatCard({ label, value, suffix, decimals = 0, icon, accent, accentDim }: StatCardProps) {
  return (
    <div className="glass p-5 group hover:border-[var(--clr-glass-border-hover)] transition-all duration-300">
      <div className="flex items-center justify-between mb-4">
        <div
          className="w-11 h-11 rounded-xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110"
          style={{ background: accentDim }}
        >
          {icon}
        </div>
        <span
          className="text-3xl font-black font-display tracking-tight"
          style={{ color: accent }}
        >
          <CountUp end={value} duration={2} separator="," decimals={decimals} suffix={suffix || ''} />
        </span>
      </div>
      <p className="text-xs font-semibold uppercase tracking-[0.15em] text-[var(--clr-text-muted)]">
        {label}
      </p>
    </div>
  );
}

export default function AdminStatCards({ stats }: { stats: AdminStats }) {
  const cards: StatCardProps[] = [
    {
      label: 'Papers Ingested',
      value: stats.total_papers,
      accent: '#f87171',
      accentDim: 'rgba(248, 113, 113, 0.10)',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      label: 'Total Questions',
      value: stats.total_questions,
      accent: '#a78bfa',
      accentDim: 'rgba(139, 92, 246, 0.10)',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      label: 'Topics Discovered',
      value: stats.topics_discovered,
      accent: '#34d399',
      accentDim: 'rgba(52, 211, 153, 0.10)',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#34d399" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
        </svg>
      ),
    },
    {
      label: 'Prediction Confidence',
      value: stats.avg_confidence_score * 100,
      suffix: '%',
      decimals: 1,
      accent: '#fbbf24',
      accentDim: 'rgba(251, 191, 36, 0.10)',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {cards.map((c) => (
        <StatCard key={c.label} {...c} />
      ))}
    </div>
  );
}
