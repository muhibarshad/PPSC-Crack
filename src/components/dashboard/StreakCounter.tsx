/**
 * StreakCounter — Consecutive days studied with fire emoji animation.
 * The fire emoji scales up when streak > 0.
 */

'use client';

import { useRef, useEffect } from 'react';
import gsap from 'gsap';

interface StreakCounterProps {
  currentStreak: number;
  longestStreak: number;
  studiedToday: boolean;
}

export default function StreakCounter({
  currentStreak,
  longestStreak,
  studiedToday,
}: StreakCounterProps) {
  const fireRef = useRef<HTMLSpanElement>(null);
  const countRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const fire = fireRef.current;
    const count = countRef.current;
    if (!fire || !count) return;

    if (currentStreak > 0) {
      // Fire pop-in animation
      gsap.fromTo(
        fire,
        { scale: 0, rotate: -20, opacity: 0 },
        {
          scale: 1,
          rotate: 0,
          opacity: 1,
          duration: 0.7,
          ease: 'elastic.out(1, 0.4)',
          delay: 0.4,
        },
      );

      // Continuous subtle float
      gsap.to(fire, {
        y: -4,
        duration: 1.2,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
        delay: 1.1,
      });
    }

    // Count number animation
    const obj = { val: 0 };
    gsap.to(obj, {
      val: currentStreak,
      duration: 1.2,
      ease: 'power2.out',
      delay: 0.3,
      onUpdate: () => {
        count.textContent = String(Math.round(obj.val));
      },
    });
  }, [currentStreak]);

  return (
    <div className="glow-card p-6 flex flex-col items-center justify-center gap-3 min-w-[160px]">
      {/* Fire emoji */}
      <span
        ref={fireRef}
        className="text-4xl select-none"
        style={{ opacity: currentStreak > 0 ? undefined : 0.3 }}
      >
        🔥
      </span>

      {/* Streak count */}
      <div className="text-center">
        <span
          ref={countRef}
          className="font-display text-3xl font-bold text-white"
        >
          0
        </span>
        <p className="text-xs text-[var(--clr-text-muted)] mt-1 uppercase tracking-widest">
          Day Streak
        </p>
      </div>

      {/* Status badge */}
      {studiedToday ? (
        <span className="badge badge-success text-[10px]">✓ Today done</span>
      ) : (
        <span className="badge badge-warning text-[10px]">Study today!</span>
      )}

      {/* Longest streak */}
      <p className="text-[11px] text-[var(--clr-text-muted)]">
        Best: <span className="text-[var(--clr-gold)] font-semibold">{longestStreak}</span> days
      </p>
    </div>
  );
}
