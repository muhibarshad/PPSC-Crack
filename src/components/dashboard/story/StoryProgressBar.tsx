/**
 * StoryProgressBar — Floating reading progress bar at top of viewport.
 * Uses GSAP ScrollTrigger with scrub for smooth scroll-linked animation.
 */

'use client';

import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

interface StoryProgressBarProps {
  contentRef: React.RefObject<HTMLDivElement | null>;
  onProgressUpdate: (progress: number) => void;
}

export default function StoryProgressBar({ contentRef, onProgressUpdate }: StoryProgressBarProps) {
  const barRef = useRef<HTMLDivElement>(null);
  const glowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!contentRef.current || !barRef.current) return;

    const ctx = gsap.context(() => {
      // Main progress bar — scrub-linked to scroll
      gsap.fromTo(
        barRef.current,
        { scaleX: 0 },
        {
          scaleX: 1,
          ease: 'none',
          scrollTrigger: {
            trigger: contentRef.current,
            start: 'top top',
            end: 'bottom bottom',
            scrub: 0.3,
            onUpdate: (self) => {
              onProgressUpdate(self.progress);

              // Intensify glow as progress increases
              if (glowRef.current) {
                const opacity = 0.3 + self.progress * 0.7;
                glowRef.current.style.opacity = String(opacity);
              }
            },
          },
        },
      );
    });

    return () => ctx.revert();
  }, [contentRef, onProgressUpdate]);

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: '3px',
        zIndex: 100,
        background: 'rgba(6, 6, 15, 0.6)',
        overflow: 'hidden',
      }}
    >
      {/* Progress fill */}
      <div
        ref={barRef}
        style={{
          height: '100%',
          width: '100%',
          transformOrigin: 'left center',
          transform: 'scaleX(0)',
          background: 'var(--grad-vivid)',
          borderRadius: '0 2px 2px 0',
        }}
      />

      {/* Glow effect */}
      <div
        ref={glowRef}
        style={{
          position: 'absolute',
          top: '-2px',
          left: 0,
          right: 0,
          height: '7px',
          background: 'var(--grad-vivid)',
          filter: 'blur(6px)',
          opacity: 0.3,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
}
