/**
 * QuickStatsBar — Three stat boxes: Topics Completed, Questions Practiced, Days Active.
 * Numbers animate in on mount using GSAP.
 */

'use client';

import { useRef, useEffect } from 'react';
import gsap from 'gsap';
import Icon from '@/components/Icon';

interface QuickStatsBarProps {
  topicsCompleted: number;
  questionsPracticed: number;
  daysActive: number;
}

interface StatBoxProps {
  icon: string;
  iconColor: string;
  iconBg: string;
  label: string;
  value: number;
  delay: number;
}

function StatBox({ icon, iconColor, iconBg, label, value, delay }: StatBoxProps) {
  const numRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = numRef.current;
    if (!el) return;

    const obj = { val: 0 };
    gsap.to(obj, {
      val: value,
      duration: 1.4,
      ease: 'power2.out',
      delay,
      onUpdate: () => {
        el.textContent = String(Math.round(obj.val));
      },
    });
  }, [value, delay]);

  return (
    <div className="glass-sm p-4 flex items-center gap-4 flex-1 min-w-[180px]">
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
        style={{ background: iconBg }}
      >
        <Icon name={icon} size={18} color={iconColor} />
      </div>
      <div>
        <span
          ref={numRef}
          className="font-display text-2xl font-bold text-white block leading-none"
        >
          0
        </span>
        <span className="text-[11px] text-[var(--clr-text-muted)] uppercase tracking-widest">
          {label}
        </span>
      </div>
    </div>
  );
}

export default function QuickStatsBar({
  topicsCompleted,
  questionsPracticed,
  daysActive,
}: QuickStatsBarProps) {
  return (
    <div className="flex flex-wrap gap-4">
      <StatBox
        icon="check"
        iconColor="var(--clr-success)"
        iconBg="var(--clr-success-dim)"
        label="Topics Done"
        value={topicsCompleted}
        delay={0.2}
      />
      <StatBox
        icon="target"
        iconColor="var(--clr-primary)"
        iconBg="var(--clr-primary-dim)"
        label="Questions"
        value={questionsPracticed}
        delay={0.35}
      />
      <StatBox
        icon="zap"
        iconColor="var(--clr-gold)"
        iconBg="var(--clr-gold-dim)"
        label="Days Active"
        value={daysActive}
        delay={0.5}
      />
    </div>
  );
}
