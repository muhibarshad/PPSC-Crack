'use client';

/**
 * Step 3: Learning Path Preview — First 5 priority topics + complete button.
 */

import Icon from '@/components/Icon';

export interface LearningPathTopic {
  rank: number;
  topic_id: string;
  topic_name: string;
  display_name: string;
  frequency_score: number;
  trend_direction: string | null;
  story_available: boolean;
  estimated_read_minutes: number;
}

export interface LearningPathPreview {
  topics: LearningPathTopic[];
  total_topics_in_path: number;
}

interface Props {
  learningPath: LearningPathPreview;
  onBack: () => void;
  onComplete: () => void;
  loading?: boolean;
}

const TREND_META: Record<string, { icon: string; color: string; label: string }> = {
  up:     { icon: 'trending-up', color: 'var(--clr-success)', label: 'Rising' },
  rising: { icon: 'trending-up', color: 'var(--clr-success)', label: 'Rising' },
  down:   { icon: 'trending-up', color: 'var(--clr-danger)',  label: 'Declining' },
  falling:{ icon: 'trending-up', color: 'var(--clr-danger)',  label: 'Declining' },
  stable: { icon: 'arrow-right', color: 'var(--clr-info)',    label: 'Stable' },
  new:    { icon: 'sparkles',    color: 'var(--clr-gold)',    label: 'New' },
};

const RANK_COLORS = [
  'var(--clr-gold)',
  'var(--clr-primary)',
  'var(--clr-neon)',
  'var(--clr-accent)',
  'var(--clr-info)',
];

export default function LearningPathStep({ learningPath, onBack, onComplete, loading }: Props) {
  return (
    <div className="animate-fade-in-up">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6"
          style={{ background: 'var(--clr-success-dim)', border: '1px solid rgba(52,211,153,0.2)' }}>
          <Icon name="route" size={14} color="var(--clr-success)" />
          <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--clr-success)' }}>
            Step 3 of 3
          </span>
        </div>
        <h1 className="font-display text-3xl md:text-4xl font-bold mb-3" style={{ color: 'var(--clr-text-primary)' }}>
          Your <span className="gradient-text-aurora">Learning Path</span>
        </h1>
        <p className="max-w-xl mx-auto" style={{ color: 'var(--clr-text-secondary)' }}>
          AI has prioritized the most important topics for you. Start with these for maximum impact.
        </p>
      </div>

      {/* Topic list */}
      <div className="max-w-2xl mx-auto space-y-4 mb-8">
        {learningPath.topics.map((topic, i) => {
          const trend = TREND_META[topic.trend_direction || 'stable'] || TREND_META.stable;
          const rankColor = RANK_COLORS[i % RANK_COLORS.length];

          return (
            <div
              key={topic.topic_id}
              className="glass flex items-center gap-5 p-5 transition-all"
              style={{
                animationDelay: `${i * 100}ms`,
                animation: 'fadeInUp 0.5s var(--ease-out) both',
              }}
            >
              {/* Rank badge */}
              <div
                className="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center font-display text-lg font-bold"
                style={{
                  background: `${rankColor}18`,
                  color: rankColor,
                  border: `1px solid ${rankColor}33`,
                }}
              >
                #{topic.rank}
              </div>

              {/* Topic info */}
              <div className="flex-1 min-w-0">
                <h3 className="font-display text-base font-semibold" style={{ color: 'var(--clr-text-primary)' }}>
                  {topic.display_name}
                </h3>
                <div className="flex items-center gap-3 mt-1 flex-wrap">
                  {/* Frequency score */}
                  <span className="text-xs" style={{ color: 'var(--clr-text-muted)' }}>
                    Score: <strong style={{ color: 'var(--clr-primary)' }}>{topic.frequency_score}</strong>
                  </span>

                  {/* Trend */}
                  <span className="inline-flex items-center gap-1 text-xs" style={{ color: trend.color }}>
                    <Icon
                      name={trend.icon}
                      size={12}
                      color={trend.color}
                      className={topic.trend_direction === 'down' || topic.trend_direction === 'falling' ? 'rotate-180' : ''}
                    />
                    {trend.label}
                  </span>

                  {/* Story available */}
                  {topic.story_available && (
                    <span className="badge badge-success text-xs" style={{ padding: '2px 8px', fontSize: '10px' }}>
                      Story Ready
                    </span>
                  )}
                </div>
              </div>

              {/* Est. reading time */}
              {topic.estimated_read_minutes > 0 && (
                <div className="flex-shrink-0 text-right">
                  <p className="font-display text-lg font-bold" style={{ color: 'var(--clr-text-primary)' }}>
                    {topic.estimated_read_minutes}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--clr-text-muted)' }}>min read</p>
                </div>
              )}
            </div>
          );
        })}

        {/* Empty state */}
        {learningPath.topics.length === 0 && (
          <div className="text-center py-16">
            <Icon name="route" size={48} color="var(--clr-text-muted)" className="mx-auto mb-4" />
            <p style={{ color: 'var(--clr-text-secondary)' }}>
              No topic data available yet. Don&apos;t worry — your path will populate as papers are analyzed.
            </p>
          </div>
        )}
      </div>

      {/* Summary */}
      {learningPath.total_topics_in_path > 5 && (
        <div className="text-center mb-8">
          <p className="text-sm" style={{ color: 'var(--clr-text-muted)' }}>
            + {learningPath.total_topics_in_path - 5} more topics in your full path available on the dashboard
          </p>
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between max-w-2xl mx-auto">
        <button onClick={onBack} className="btn btn-ghost">
          <Icon name="arrow-right" size={16} className="rotate-180" />
          Back
        </button>
        <button
          onClick={onComplete}
          disabled={loading}
          className="btn btn-gold btn-lg animate-pulse-glow"
        >
          {loading ? (
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <>
              <Icon name="sparkles" size={18} />
              Start Dominating
              <Icon name="arrow-right" size={18} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
