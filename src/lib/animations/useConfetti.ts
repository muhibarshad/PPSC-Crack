/**
 * useConfetti — Canvas confetti burst for topic completion.
 * Fires when a topic is fully read and quiz passed.
 */

'use client';

import { useCallback } from 'react';
import confetti from 'canvas-confetti';

interface ConfettiOptions {
  /** Number of confetti particles */
  particleCount?: number;
  /** Spread angle */
  spread?: number;
  /** Origin on screen (0-1) */
  origin?: { x: number; y: number };
  /** Custom colors */
  colors?: string[];
}

export function useConfetti({
  particleCount = 100,
  spread = 80,
  origin = { x: 0.5, y: 0.4 },
  colors = ['#a78bfa', '#8b5cf6', '#e879f9', '#fbbf24', '#34d399', '#818cf8'],
}: ConfettiOptions = {}) {
  const fire = useCallback(() => {
    // First burst
    confetti({
      particleCount,
      spread,
      origin,
      colors,
      gravity: 0.8,
      scalar: 1.2,
      drift: 0,
      ticks: 200,
    });

    // Staggered side bursts for a fuller effect
    setTimeout(() => {
      confetti({
        particleCount: Math.floor(particleCount * 0.5),
        angle: 60,
        spread: spread * 0.7,
        origin: { x: 0.15, y: 0.5 },
        colors,
        gravity: 0.8,
        scalar: 1,
      });
      confetti({
        particleCount: Math.floor(particleCount * 0.5),
        angle: 120,
        spread: spread * 0.7,
        origin: { x: 0.85, y: 0.5 },
        colors,
        gravity: 0.8,
        scalar: 1,
      });
    }, 200);
  }, [particleCount, spread, origin, colors]);

  return fire;
}
