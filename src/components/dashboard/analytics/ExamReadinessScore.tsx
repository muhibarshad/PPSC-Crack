/**
 * ExamReadinessScore — Large animated number (CountUp) showing predicted readiness %.
 * Uses GSAP for the count-up animation. Displays the formula explanation below.
 */

'use client';

import { useRef, useEffect } from 'react';
import gsap from 'gsap';

interface Props {
  readinessPercent: number;
  completedWeight: number;
  totalWeight: number;
  topicsCompleted: number;
  topicsTotal: number;
}

export default function ExamReadinessScore({
  readinessPercent,
  completedWeight,
  totalWeight,
  topicsCompleted,
  topicsTotal,
}: Props) {
  const numberRef = useRef<HTMLSpanElement>(null);
  const barRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const num = numberRef.current;
    const bar = barRef.current;
    if (!num) return;

    // Animate number counter
    const obj = { val: 0 };
    gsap.to(obj, {
      val: readinessPercent,
      duration: 2.2,
      ease: 'power3.out',
      delay: 0.2,
      onUpdate: () => {
        num.textContent = `${Math.round(obj.val)}`;
      },
    });

    // Animate progress bar
    if (bar) {
      gsap.fromTo(
        bar,
        { width: '0%' },
        { width: `${Math.min(readinessPercent, 100)}%`, duration: 2.2, ease: 'power3.out', delay: 0.2 },
      );
    }
  }, [readinessPercent]);

  const getColor = () => {
    if (readinessPercent >= 75) return 'var(--clr-success)';
    if (readinessPercent >= 40) return 'var(--clr-warning)';
    return 'var(--clr-primary)';
  };

  const getGlow = () => {
    if (readinessPercent >= 75) return 'rgba(52, 211, 153, 0.3)';
    if (readinessPercent >= 40) return 'rgba(251, 146, 60, 0.3)';
    return 'rgba(139, 92, 246, 0.3)';
  };

  return (
    <div className="flex flex-col items-center gap-5 py-4">
      {/* Big number */}
      <div className="relative">
        <div
          className="absolute inset-0 rounded-full blur-3xl opacity-40"
          style={{ background: getGlow() }}
        />
        <div className="relative flex items-baseline gap-1">
          <span
            ref={numberRef}
            className="font-display font-black tabular-nums"
            style={{
              fontSize: '5rem',
              lineHeight: 1,
              color: getColor(),
              textShadow: `0 0 40px ${getGlow()}`,
            }}
          >
            0
          </span>
          <span
            className="font-display font-bold text-3xl"
            style={{ color: getColor(), opacity: 0.7 }}
          >
            %
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full max-w-xs">
        <div
          className="h-2 rounded-full overflow-hidden"
          style={{ background: 'rgba(139, 92, 246, 0.08)' }}
        >
          <div
            ref={barRef}
            className="h-full rounded-full"
            style={{
              background: `linear-gradient(90deg, ${getColor()}, ${getColor()}dd)`,
              boxShadow: `0 0 12px ${getGlow()}`,
              width: 0,
            }}
          />
        </div>
        <div className="flex justify-between mt-2 text-[11px] text-[var(--clr-text-muted)]">
          <span>{topicsCompleted} / {topicsTotal} topics</span>
          <span>{completedWeight.toFixed(1)} / {totalWeight.toFixed(1)} weight</span>
        </div>
      </div>

      {/* Formula explanation */}
      <div
        className="glass-sm px-4 py-3 text-center max-w-sm"
        style={{ background: 'rgba(139, 92, 246, 0.04)' }}
      >
        <p className="text-[11px] text-[var(--clr-text-muted)] leading-relaxed">
          <span className="text-[var(--clr-primary)] font-semibold">Formula:</span>{' '}
          (completed_topic_weight / total_topic_weight) × 100
        </p>
        <p className="text-[10px] text-[var(--clr-text-muted)] mt-1 opacity-70">
          Weights are derived from topic frequency scores across your selected job types.
          Complete higher-weight topics to boost your readiness faster.
        </p>
      </div>
    </div>
  );
}
