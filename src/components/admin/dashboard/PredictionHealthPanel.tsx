/**
 * Prediction Health Panel
 * =========================
 * Per-job-type health cards: paper count + color-coded status.
 * Green ≥ 50 papers · Orange 10–49 · Blue < 10.
 */

'use client';

import type { PredictionHealthItem } from './types';

const HEALTH_CONFIG: Record<string, { label: string; color: string; bg: string; glow: string }> = {
  green: {
    label: 'Strong Data',
    color: '#34d399',
    bg: 'rgba(52, 211, 153, 0.08)',
    glow: '0 0 20px rgba(52, 211, 153, 0.15)',
  },
  orange: {
    label: 'Building',
    color: '#fb923c',
    bg: 'rgba(251, 146, 60, 0.08)',
    glow: '0 0 20px rgba(251, 146, 60, 0.15)',
  },
  blue: {
    label: 'Early Stage',
    color: '#38bdf8',
    bg: 'rgba(56, 189, 248, 0.08)',
    glow: '0 0 20px rgba(56, 189, 248, 0.15)',
  },
};

function HealthBadge({ health }: { health: string }) {
  const cfg = HEALTH_CONFIG[health] || HEALTH_CONFIG.blue;
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider"
      style={{ color: cfg.color, background: cfg.bg }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: cfg.color, boxShadow: cfg.glow }} />
      {cfg.label}
    </span>
  );
}

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.min(score * 100, 100);
  const color = pct >= 70 ? '#34d399' : pct >= 40 ? '#fbbf24' : '#f87171';
  return (
    <div className="w-full h-1.5 rounded-full bg-white/[0.06] overflow-hidden mt-2">
      <div
        className="h-full rounded-full transition-all duration-700 ease-out"
        style={{ width: `${pct}%`, background: color }}
      />
    </div>
  );
}

export default function PredictionHealthPanel({ items }: { items: PredictionHealthItem[] }) {
  if (items.length === 0) {
    return (
      <div className="glass p-6 h-full flex items-center justify-center">
        <p className="text-sm text-[var(--clr-text-muted)]">No job types configured.</p>
      </div>
    );
  }

  return (
    <div className="glass p-5 h-full">
      <h2 className="text-sm font-bold text-white uppercase tracking-[0.1em] mb-4">
        Prediction Health
      </h2>

      <div className="space-y-3 overflow-y-auto max-h-[420px] pr-1 custom-scrollbar">
        {items.map((item) => {
          const cfg = HEALTH_CONFIG[item.health] || HEALTH_CONFIG.blue;
          return (
            <div
              key={item.job_type_id}
              className="glass-sm p-4 hover:border-[var(--clr-glass-border-hover)] transition-all duration-200"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white truncate">{item.job_type_name}</p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-xs text-[var(--clr-text-muted)]">
                      <span className="font-bold text-white">{item.paper_count}</span> papers
                    </span>
                    <span className="text-[var(--clr-text-muted)]">·</span>
                    <span className="text-xs text-[var(--clr-text-muted)]">
                      {(item.confidence_score * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                </div>
                <HealthBadge health={item.health} />
              </div>
              <ConfidenceBar score={item.confidence_score} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
