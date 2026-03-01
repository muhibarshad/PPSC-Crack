/**
 * useProgressRing — Animate SVG stroke-dashoffset to completion percentage.
 * Duration 1.5s with power2.inOut easing.
 */

'use client';

import { useEffect, useRef } from 'react';
import gsap from 'gsap';

interface UseProgressRingOptions {
  percent: number;
  circumference: number;
  duration?: number;
  delay?: number;
}

export function useProgressRing({
  percent,
  circumference,
  duration = 1.5,
  delay = 0.3,
}: UseProgressRingOptions) {
  const circleRef = useRef<SVGCircleElement>(null);
  const numberRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const circle = circleRef.current;
    const num = numberRef.current;
    if (!circle) return;

    const target = circumference - (circumference * percent) / 100;

    gsap.set(circle, { strokeDashoffset: circumference });

    gsap.to(circle, {
      strokeDashoffset: target,
      duration,
      ease: 'power2.inOut',
      delay,
    });

    if (num) {
      const obj = { val: 0 };
      gsap.to(obj, {
        val: percent,
        duration,
        ease: 'power2.inOut',
        delay,
        onUpdate: () => {
          num.textContent = `${Math.round(obj.val)}%`;
        },
      });
    }
  }, [percent, circumference, duration, delay]);

  return { circleRef, numberRef };
}
