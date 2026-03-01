/**
 * TopicNode — A single node in the vertical learning-path roadmap.
 *
 * States:
 *  - completed   → green checkmark with scale+rotate animation
 *  - in-progress → animated gradient progress bar
 *  - not-started → muted default state
 *
 * High-frequency topics get a glowing orange HOT badge.
 */

'use client';

import { useRef, useEffect, useCallback } from 'react';
import gsap from 'gsap';
import Icon from '@/components/Icon';

export interface TopicNodeData {
  topic_id: string;
  topic_name: string;
  display_name: string;
  icon: string | null;
  color_hex: string | null;
  frequency_percentage: number;
  trend_direction: string | null;
  is_hot: boolean;
  story_word_count: number;
  estimated_read_minutes: number;
  has_story: boolean;
  status: 'completed' | 'in-progress' | 'not-started';
  progress_percent: number;
  rank: number;
}

interface TopicNodeProps {
  topic: TopicNodeData;
  isLast: boolean;
  onClick: (topicId: string) => void;
}

export default function TopicNode({ topic, isLast, onClick }: TopicNodeProps) {
  const checkRef = useRef<HTMLDivElement>(null);
  const barRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLButtonElement>(null);

  /* ── Magnetic hover: card subtly follows cursor (offset = cursor / 20) ── */
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    const el = cardRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left - rect.width / 2) / 20;
    const y = (e.clientY - rect.top - rect.height / 2) / 20;
    gsap.to(el, { x, y, duration: 0.3, ease: 'power2.out', overwrite: 'auto' });
  }, []);

  const handleMouseLeave = useCallback(() => {
    const el = cardRef.current;
    if (!el) return;
    gsap.to(el, { x: 0, y: 0, duration: 0.8, ease: 'elastic.out(1, 0.3)', overwrite: 'auto' });
  }, []);

  /* ── Completed checkmark pop-in ── */
  useEffect(() => {
    if (topic.status === 'completed' && checkRef.current) {
      gsap.fromTo(
        checkRef.current,
        { scale: 0, rotate: -90, opacity: 0 },
        {
          scale: 1,
          rotate: 0,
          opacity: 1,
          duration: 0.6,
          ease: 'back.out(2)',
          delay: 0.15,
        },
      );
    }
  }, [topic.status]);

  /* ── In-progress bar animation ── */
  useEffect(() => {
    if (topic.status === 'in-progress' && barRef.current) {
      gsap.fromTo(
        barRef.current,
        { width: '0%' },
        {
          width: `${topic.progress_percent}%`,
          duration: 1.2,
          ease: 'power3.out',
          delay: 0.2,
        },
      );
    }
  }, [topic.status, topic.progress_percent]);

  /* ── Status-dependent styles ── */
  const isCompleted = topic.status === 'completed';
  const isInProgress = topic.status === 'in-progress';

  const dotColor = isCompleted
    ? 'var(--clr-success)'
    : isInProgress
      ? 'var(--clr-primary)'
      : 'var(--clr-text-muted)';

  const dotBg = isCompleted
    ? 'var(--clr-success-dim)'
    : isInProgress
      ? 'var(--clr-primary-dim)'
      : 'rgba(82, 77, 115, 0.15)';

  const lineColor = isCompleted
    ? 'var(--clr-success)'
    : 'var(--clr-glass-border)';

  return (
    <div className="flex gap-5 group">
      {/* ── Timeline spine ── */}
      <div className="flex flex-col items-center shrink-0" style={{ width: 44 }}>
        {/* Dot / checkmark */}
        <div
          className="relative w-11 h-11 rounded-full flex items-center justify-center shrink-0 transition-all duration-300"
          style={{
            background: dotBg,
            border: `2px solid ${dotColor}`,
            boxShadow: isCompleted
              ? '0 0 16px rgba(52, 211, 153, 0.3)'
              : isInProgress
                ? '0 0 16px rgba(139, 92, 246, 0.2)'
                : 'none',
          }}
        >
          {isCompleted ? (
            <div ref={checkRef} style={{ opacity: 0 }}>
              <Icon name="check" size={20} color="var(--clr-success)" />
            </div>
          ) : (
            <span
              className="font-display text-sm font-bold"
              style={{ color: dotColor }}
            >
              {topic.rank}
            </span>
          )}
        </div>

        {/* Connecting line */}
        {!isLast && (
          <div
            className="flex-1 w-0.5 min-h-[24px] transition-colors duration-300"
            style={{ background: lineColor }}
          />
        )}
      </div>

      {/* ── Card ── */}
      <button
        ref={cardRef}
        onClick={() => onClick(topic.topic_id)}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className={`
          glow-card p-5 flex-1 mb-4 text-left cursor-pointer
          transition-all duration-300
          ${isCompleted ? 'opacity-80' : ''}
          group-hover:!opacity-100
        `}
        style={{
          borderLeft: isCompleted
            ? '3px solid var(--clr-success)'
            : isInProgress
              ? '3px solid var(--clr-primary)'
              : '3px solid transparent',
        }}
      >
        {/* Top row: icon + name + badges */}
        <div className="flex items-start gap-3">
          {/* Icon circle */}
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
            style={{
              background: topic.color_hex
                ? `${topic.color_hex}18`
                : 'var(--clr-primary-dim)',
            }}
          >
            <Icon
              name={topic.icon || 'book-open'}
              size={18}
              color={topic.color_hex || 'var(--clr-primary)'}
            />
          </div>

          {/* Title + meta */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-display text-base font-bold text-white leading-snug truncate">
                {topic.display_name}
              </h3>

              {/* HOT badge */}
              {topic.is_hot && (
                <span
                  className="badge text-[10px] font-bold shrink-0"
                  style={{
                    background: 'rgba(251, 146, 60, 0.15)',
                    color: '#fb923c',
                    border: '1px solid rgba(251, 146, 60, 0.3)',
                    boxShadow: '0 0 14px rgba(251, 146, 60, 0.2)',
                    animation: 'pulseGlow 2.5s ease-in-out infinite',
                  }}
                >
                  🔥 HOT
                </span>
              )}

              {/* Status badge */}
              {isCompleted && (
                <span className="badge badge-success text-[10px]">✓ Done</span>
              )}
              {isInProgress && (
                <span className="badge badge-primary text-[10px]">In Progress</span>
              )}
            </div>

            {/* Meta row */}
            <div className="flex items-center gap-4 mt-1.5 text-[12px] text-[var(--clr-text-muted)]">
              <span className="flex items-center gap-1">
                <Icon name="chart-line" size={12} />
                {topic.frequency_percentage}% exam weight
              </span>
              {topic.has_story && (
                <span className="flex items-center gap-1">
                  ⏱️ {topic.estimated_read_minutes} min read
                </span>
              )}
              {topic.trend_direction && (
                <span className="flex items-center gap-1">
                  {topic.trend_direction === 'up'
                    ? '📈'
                    : topic.trend_direction === 'down'
                      ? '📉'
                      : '➡️'}
                  {topic.trend_direction}
                </span>
              )}
            </div>
          </div>

          {/* Arrow */}
          <Icon
            name="chevron-right"
            size={18}
            color="var(--clr-text-muted)"
            className="shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
          />
        </div>

        {/* ── Progress bar (in-progress only) ── */}
        {isInProgress && (
          <div className="mt-3 w-full h-1.5 rounded-full overflow-hidden bg-[rgba(139,92,246,0.1)]">
            <div
              ref={barRef}
              className="h-full rounded-full"
              style={{
                background: 'var(--grad-vivid)',
                width: 0,
              }}
            />
          </div>
        )}
      </button>
    </div>
  );
}
