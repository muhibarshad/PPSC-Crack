/**
 * useMagneticHover — Magnetic card effect that subtly follows cursor.
 * Card offsets by cursor-position / 20, snaps back with elastic.out on leave.
 */

'use client';

import { useRef, useCallback } from 'react';
import gsap from 'gsap';

export function useMagneticHover(strength: number = 20) {
  const ref = useRef<HTMLDivElement>(null);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const el = ref.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const x = (e.clientX - rect.left - rect.width / 2) / strength;
      const y = (e.clientY - rect.top - rect.height / 2) / strength;

      gsap.to(el, {
        x,
        y,
        duration: 0.3,
        ease: 'power2.out',
        overwrite: 'auto',
      });
    },
    [strength],
  );

  const handleMouseLeave = useCallback(() => {
    const el = ref.current;
    if (!el) return;

    gsap.to(el, {
      x: 0,
      y: 0,
      duration: 0.8,
      ease: 'elastic.out(1, 0.3)',
      overwrite: 'auto',
    });
  }, []);

  return { ref, handleMouseMove, handleMouseLeave };
}
