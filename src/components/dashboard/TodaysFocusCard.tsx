/**
 * TodaysFocusCard — Today's highest-predicted-weight topic.
 * Features a glowing HOT badge with CSS animation.
 */

'use client';

import Icon from '@/components/Icon';

interface TodaysFocusCardProps {
  topicName: string;
  displayName: string;
  percentage: number;
  trendDirection: string | null;
  icon: string | null;
}

export default function TodaysFocusCard({
  displayName,
  percentage,
  trendDirection,
  icon,
}: TodaysFocusCardProps) {
  const trendEmoji =
    trendDirection === 'up'
      ? '📈'
      : trendDirection === 'down'
        ? '📉'
        : '➡️';

  return (
    <div className="glow-card p-6 flex flex-col gap-4 flex-1 min-w-[260px] group">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'var(--clr-primary-dim)' }}
          >
            <Icon name={icon || 'target'} size={20} color="var(--clr-primary)" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-[var(--clr-text-muted)]">
              Today&apos;s Focus
            </p>
            <h3 className="font-display text-lg font-bold text-white leading-snug">
              {displayName}
            </h3>
          </div>
        </div>

        {/* HOT badge with glow */}
        <span
          className="badge text-[10px] font-bold relative"
          style={{
            background: 'rgba(248, 113, 113, 0.15)',
            color: '#f87171',
            border: '1px solid rgba(248, 113, 113, 0.3)',
            animation: 'pulseGlow 2.5s ease-in-out infinite',
            boxShadow: '0 0 20px rgba(248, 113, 113, 0.25)',
          }}
        >
          🔥 HOT
        </span>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 mt-auto">
        <div>
          <p className="text-2xl font-bold gradient-text">{percentage}%</p>
          <p className="text-[11px] text-[var(--clr-text-muted)]">Paper weight</p>
        </div>
        <div className="ml-auto flex items-center gap-1 text-sm text-[var(--clr-text-secondary)]">
          <span>{trendEmoji}</span>
          <span className="capitalize">{trendDirection || 'stable'}</span>
        </div>
      </div>

      {/* CTA */}
      <button className="btn btn-ghost btn-sm w-full mt-1 group-hover:border-[rgba(139,92,246,0.35)]">
        <Icon name="book-open" size={14} />
        Start Studying
        <Icon name="arrow-right" size={14} />
      </button>
    </div>
  );
}
