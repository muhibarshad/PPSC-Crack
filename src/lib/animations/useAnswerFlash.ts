/**
 * useAnswerFlash — Green glow pulse for correct answers, red shake for wrong.
 */

'use client';

import { useRef, useCallback } from 'react';
import gsap from 'gsap';

export function useAnswerFlash() {
  const ref = useRef<HTMLDivElement>(null);

  const flashCorrect = useCallback(() => {
    const el = ref.current;
    if (!el) return;

    const tl = gsap.timeline();
    tl.to(el, {
      boxShadow: '0 0 0 4px rgba(52, 211, 153, 0.4), 0 0 30px rgba(52, 211, 153, 0.25)',
      borderColor: 'rgba(52, 211, 153, 0.6)',
      backgroundColor: 'rgba(52, 211, 153, 0.08)',
      duration: 0.3,
      ease: 'power2.out',
    })
      .to(el, {
        boxShadow: '0 0 0 2px rgba(52, 211, 153, 0.2), 0 0 15px rgba(52, 211, 153, 0.1)',
        duration: 0.5,
        ease: 'power2.inOut',
        repeat: 1,
        yoyo: true,
      })
      .to(el, {
        boxShadow: 'none',
        borderColor: '',
        backgroundColor: '',
        duration: 0.4,
        ease: 'power2.out',
      });
  }, []);

  const shakeWrong = useCallback(() => {
    const el = ref.current;
    if (!el) return;

    const tl = gsap.timeline();
    tl.to(el, {
      borderColor: 'rgba(248, 113, 113, 0.5)',
      backgroundColor: 'rgba(248, 113, 113, 0.08)',
      duration: 0.1,
    })
      .to(el, { x: -8, duration: 0.08 })
      .to(el, { x: 8, duration: 0.08 })
      .to(el, { x: -5, duration: 0.08 })
      .to(el, {
        x: 0,
        borderColor: '',
        backgroundColor: '',
        duration: 0.3,
        ease: 'power2.out',
      });
  }, []);

  return { ref, flashCorrect, shakeWrong };
}
