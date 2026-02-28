/**
 * NextStoryCard — Next unread story topic the student should tackle.
 */

'use client';

import Icon from '@/components/Icon';

interface NextStoryCardProps {
  displayName: string;
  storyWordCount: number;
  estimatedReadMinutes: number;
  frequencyScore: number;
}

export default function NextStoryCard({
  displayName,
  storyWordCount,
  estimatedReadMinutes,
  frequencyScore,
}: NextStoryCardProps) {
  return (
    <div className="glow-card p-6 flex flex-col gap-4 flex-1 min-w-[260px] group">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'var(--clr-accent-dim)' }}
          >
            <Icon name="book-open" size={20} color="var(--clr-accent)" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-[var(--clr-text-muted)]">
              Next Story
            </p>
            <h3 className="font-display text-lg font-bold text-white leading-snug">
              {displayName}
            </h3>
          </div>
        </div>
      </div>

      {/* Meta info */}
      <div className="flex items-center gap-4 text-sm text-[var(--clr-text-secondary)] mt-auto">
        <div className="flex items-center gap-1.5">
          <Icon name="file-text" size={14} />
          <span>{storyWordCount.toLocaleString()} words</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span>⏱️</span>
          <span>{estimatedReadMinutes} min</span>
        </div>
        {frequencyScore > 0 && (
          <div className="flex items-center gap-1.5 ml-auto">
            <Icon name="trending-up" size={14} color="var(--clr-success)" />
            <span className="text-[var(--clr-success)]">{frequencyScore}%</span>
          </div>
        )}
      </div>

      {/* CTA */}
      <button className="btn btn-ghost btn-sm w-full mt-1 group-hover:border-[rgba(139,92,246,0.35)]">
        <Icon name="play" size={14} />
        Read Story
        <Icon name="arrow-right" size={14} />
      </button>
    </div>
  );
}
