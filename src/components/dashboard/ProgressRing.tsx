/**
 * ProgressRing — SVG animated circle showing overall exam readiness.
 * Uses GSAP to animate the stroke-dashoffset on mount.
 */

'use client';

import { useRef, useEffect } from 'react';
import gsap from 'gsap';

interface ProgressRingProps {
  /** 0–100 readiness percentage */
  percent: number;
  /** Completed topic count */
  completed: number;
  /** Total topic count */
  total: number;
  /** Ring diameter */
  size?: number;
  /** Ring stroke width */
  strokeWidth?: number;
}

export default function ProgressRing({
  percent,
  completed,
  total,
  size = 200,
  strokeWidth = 10,
}: ProgressRingProps) {
  const circleRef = useRef<SVGCircleElement>(null);
  const numberRef = useRef<HTMLSpanElement>(null);

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  useEffect(() => {
    const circle = circleRef.current;
    const num = numberRef.current;
    if (!circle || !num) return;

    // Start fully hidden
    gsap.set(circle, { strokeDashoffset: circumference });

    const target = circumference - (circumference * percent) / 100;

    // Animate ring stroke
    gsap.to(circle, {
      strokeDashoffset: target,
      duration: 1.8,
      ease: 'power3.out',
      delay: 0.3,
    });

    // Animate number counter
    const obj = { val: 0 };
    gsap.to(obj, {
      val: percent,
      duration: 1.8,
      ease: 'power3.out',
      delay: 0.3,
      onUpdate: () => {
        num.textContent = `${Math.round(obj.val)}%`;
      },
    });
  }, [percent, circumference]);

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative" style={{ width: size, height: size }}>
        {/* Outer glow */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: `radial-gradient(circle, rgba(139,92,246,${percent > 50 ? 0.15 : 0.06}) 0%, transparent 70%)`,
          }}
        />

        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background track */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="rgba(139, 92, 246, 0.08)"
            strokeWidth={strokeWidth}
          />
          {/* Animated progress arc */}
          <circle
            ref={circleRef}
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="url(#progressGradient)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference}
          />
          <defs>
            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#a78bfa" />
              <stop offset="50%" stopColor="#8b5cf6" />
              <stop offset="100%" stopColor="#e879f9" />
            </linearGradient>
          </defs>
        </svg>

        {/* Center number */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            ref={numberRef}
            className="font-display text-4xl font-bold text-white"
          >
            0%
          </span>
          <span className="text-xs text-[var(--clr-text-muted)] mt-1">Readiness</span>
        </div>
      </div>

      {/* Bottom label */}
      <p className="text-sm text-[var(--clr-text-secondary)]">
        <span className="text-white font-semibold">{completed}</span>
        <span className="mx-1">/</span>
        <span>{total} topics</span>
      </p>
    </div>
  );
}
