/**
 * useCountUp — Triggers a CountUp animation when the element enters the viewport.
 * Uses IntersectionObserver to detect entry and GSAP to tween the number.
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';

interface UseCountUpOptions {
  end: number;
  duration?: number;
  delay?: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
}

export function useCountUp({
  end,
  duration = 1.5,
  delay = 0,
  decimals = 0,
  suffix = '',
  prefix = '',
}: UseCountUpOptions) {
  const ref = useRef<HTMLSpanElement>(null);
  const [hasAnimated, setHasAnimated] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || hasAnimated) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry.isIntersecting) {
          observer.disconnect();
          setHasAnimated(true);

          const obj = { val: 0 };
          gsap.to(obj, {
            val: end,
            duration,
            delay,
            ease: 'power2.out',
            onUpdate: () => {
              el.textContent = `${prefix}${obj.val.toFixed(decimals)}${suffix}`;
            },
          });
        }
      },
      { threshold: 0.3 },
    );

    observer.observe(el);

    return () => observer.disconnect();
  }, [end, duration, delay, decimals, suffix, prefix, hasAnimated]);

  return ref;
}
