/**
 * ParticlesBackground — Animated particle field with mouse repulsion.
 * Uses @tsparticles/slim for lightweight particle rendering.
 *
 * Props:
 *  - density: 'normal' (60 particles, dashboard) | 'dense' (100 particles, landing hero)
 *
 * Performance: disabled on mobile, replaced with static gradient.
 */

'use client';

import { useEffect, useMemo, useState } from 'react';
import Particles, { initParticlesEngine } from '@tsparticles/react';
import { loadSlim } from '@tsparticles/slim';
import type { ISourceOptions } from '@tsparticles/engine';

interface ParticlesBackgroundProps {
  density?: 'normal' | 'dense';
  className?: string;
}

export default function ParticlesBackground({
  density = 'normal',
  className = '',
}: ParticlesBackgroundProps) {
  const [isMobile, setIsMobile] = useState(false);
  const [ready, setReady] = useState(false);

  // Detect mobile on mount
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768 || 'ontouchstart' in window);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Initialise slim engine once
  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    }).then(() => setReady(true));
  }, []);

  const particleCount = density === 'dense' ? 100 : 60;

  const options: ISourceOptions = useMemo(
    () => ({
      fullScreen: false,
      fpsLimit: 60,
      particles: {
        number: {
          value: particleCount,
          density: {
            enable: true,
            width: 1920,
            height: 1080,
          },
        },
        color: {
          value: ['#4F8EF7', '#7C3AED'],
        },
        shape: {
          type: 'circle',
        },
        opacity: {
          value: { min: 0.15, max: 0.4 },
          animation: {
            enable: true,
            speed: 0.5,
            sync: false,
          },
        },
        size: {
          value: { min: 2, max: 3 },
        },
        links: {
          enable: true,
          distance: 120,
          color: '#4F8EF7',
          opacity: 0.15,
          width: 1,
        },
        move: {
          enable: true,
          speed: 0.6,
          direction: 'none' as const,
          random: true,
          straight: false,
          outModes: {
            default: 'bounce' as const,
          },
        },
      },
      interactivity: {
        detectsOn: 'window' as const,
        events: {
          onHover: {
            enable: true,
            mode: 'repulse',
          },
          onClick: {
            enable: false,
          },
        },
        modes: {
          repulse: {
            distance: 100,
            duration: 0.4,
            speed: 0.5,
          },
        },
      },
      detectRetina: true,
    }),
    [particleCount],
  );

  // On mobile: static gradient fallback
  if (isMobile) {
    return (
      <div
        className={`absolute inset-0 pointer-events-none ${className}`}
        style={{
          background:
            'radial-gradient(ellipse 80% 50% at 50% 50%, rgba(79,142,247,0.06) 0%, rgba(124,58,237,0.04) 50%, transparent 100%)',
        }}
      />
    );
  }

  return (
    <div className={`absolute inset-0 pointer-events-none ${className}`}>
      <Particles
        id={`tsparticles-${density}`}
        options={options}
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'auto',
        }}
      />
    </div>
  );
}
