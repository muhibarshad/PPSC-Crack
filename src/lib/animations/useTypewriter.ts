/**
 * useTypewriter — Typewriter effect using GSAP TextPlugin.
 * Reveals text character-by-character, then calls onComplete.
 */

'use client';

import { useRef, useCallback } from 'react';
import gsap from 'gsap';
import { TextPlugin } from 'gsap/TextPlugin';

gsap.registerPlugin(TextPlugin);

interface UseTypewriterOptions {
  /** Characters per second */
  speed?: number;
  /** Delay before starting (seconds) */
  delay?: number;
  /** Called when the typewriter finishes */
  onComplete?: () => void;
}

export function useTypewriter({
  speed = 30,
  delay = 0,
  onComplete,
}: UseTypewriterOptions = {}) {
  const ref = useRef<HTMLElement>(null);
  const tweenRef = useRef<gsap.core.Tween | null>(null);

  const start = useCallback(
    (text: string) => {
      const el = ref.current;
      if (!el) return;

      // Kill any running animation
      tweenRef.current?.kill();
      el.textContent = '';

      const duration = text.length / speed;

      tweenRef.current = gsap.to(el, {
        duration,
        delay,
        text: { value: text, delimiter: '' },
        ease: 'none',
        onComplete: () => {
          onComplete?.();
        },
      });
    },
    [speed, delay, onComplete],
  );

  const stop = useCallback(() => {
    tweenRef.current?.kill();
  }, []);

  return { ref, start, stop };
}
