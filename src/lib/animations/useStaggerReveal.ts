/**
 * useStaggerReveal — Fade+slide-up stat cards with stagger 0.1s on dashboard mount.
 * Uses GSAP to animate child elements with the given selector.
 */

'use client';

import { useEffect, useRef } from 'react';
import gsap from 'gsap';

interface UseStaggerRevealOptions {
  /** CSS selector for child elements to stagger */
  childSelector: string;
  /** Stagger delay between each child (seconds) */
  stagger?: number;
  /** Duration of each child animation */
  duration?: number;
  /** Initial Y offset */
  y?: number;
  /** Initial delay before the stagger begins */
  delay?: number;
}

export function useStaggerReveal({
  childSelector,
  stagger = 0.1,
  duration = 0.6,
  y = 30,
  delay = 0,
}: UseStaggerRevealOptions) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const children = container.querySelectorAll(childSelector);
    if (children.length === 0) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        children,
        { opacity: 0, y, scale: 0.97 },
        {
          opacity: 1,
          y: 0,
          scale: 1,
          duration,
          stagger,
          delay,
          ease: 'power3.out',
        },
      );
    }, container);

    return () => ctx.revert();
  }, [childSelector, stagger, duration, y, delay]);

  return containerRef;
}
