'use client';

import { useRef } from 'react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import Icon from '@/components/Icon';
import { HERO_STATS } from '@/data/mock-data';

export default function HeroSection() {
  const container = useRef<HTMLElement>(null);

  useGSAP(() => {
    const tl = gsap.timeline();
    
    // Animate badge
    tl.from('.hero-badge', { y: 20, opacity: 0, duration: 1, ease: 'power4.out' })
      // Animate lines
      .from('.hero-line', {
        y: 60,
        opacity: 0,
        rotateZ: 2,
        duration: 1.2,
        stagger: 0.15,
        ease: 'power4.out',
      }, '-=0.8')
      // Subtitle
      .from('.hero-subtitle', { y: 20, opacity: 0, duration: 1, ease: 'power3.out' }, '-=0.8')
      // Buttons
      .from('.hero-btn', { scale: 0.9, opacity: 0, duration: 0.8, stagger: 0.1, ease: 'back.out(1.5)' }, '-=0.6')
      // Stats but differently! Fade them in from bottom gently without boxes
      .from('.hero-stat-item', { 
        y: 40,
        opacity: 0, 
        duration: 1, 
        stagger: 0.1, 
        ease: 'power3.out' 
      }, '-=0.4');

    // Subtle parallax on orbs
    gsap.to('.hero-orb', {
      y: 'random(-50, 50)',
      x: 'random(-50, 50)',
      duration: 5,
      repeat: -1,
      yoyo: true,
      ease: 'sine.inOut',
      stagger: 2,
    });
  }, { scope: container });

  return (
    <section ref={container} className="hero min-h-screen relative flex items-center justify-center pt-32 pb-20 overflow-hidden z-10">
      <div className="hero-orb absolute w-[600px] h-[600px] rounded-full top-[10%] -left-[10%] bg-primary/10 blur-[100px] -z-10" />
      <div className="hero-orb absolute w-[450px] h-[450px] rounded-full bottom-[5%] -right-[10%] bg-neon/5 blur-[100px] -z-10" />

      <div className="container max-w-5xl mx-auto px-6 z-10 relative">
        <div className="text-center">

          <div className="hero-badge inline-flex items-center gap-2 px-5 py-2 rounded-full border border-primary/20 bg-gradient-to-r from-primary/10 to-neon/5 text-xs font-semibold uppercase tracking-widest text-primary-light mb-8 overflow-hidden backdrop-blur-md">
            <Icon name="sparkles" size={14} className="text-neon animate-pulse" />
            <span>Pakistan's Next-Gen AI Platform</span>
          </div>

          <h1 className="hero-title text-[clamp(3rem,8vw,6.5rem)] font-black leading-[1.05] tracking-tight mb-8">
            <div className="overflow-hidden"><div className="hero-line">Crack the Exam.</div></div>
            <div className="overflow-hidden"><div className="hero-line text-transparent bg-clip-text bg-gradient-to-br from-primary-light via-primary to-neon pb-2">Read their Mind.</div></div>
          </h1>

          <p className="hero-subtitle text-[clamp(1.1rem,2vw,1.4rem)] text-muted-foreground leading-relaxed max-w-3xl mx-auto mb-12">
            The world's first predictive AI system built purely for PPSC. 
            Stop memorizing blindly. Know exactly what questions are coming next.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-5 mb-24">
            <a href="#pricing" className="hero-btn group relative inline-flex items-center justify-center gap-3 px-8 py-4 bg-primary text-white rounded-2xl font-semibold text-lg overflow-hidden transition-transform hover:scale-105 hover:shadow-[0_0_40px_rgba(139,92,246,0.6)]">
              <span className="absolute inset-0 bg-gradient-to-b from-white/20 to-transparent pointer-events-none" />
              <Icon name="zap" size={20} />
              Begin Your Journey
            </a>
            <a href="#how-it-works" className="hero-btn relative inline-flex items-center justify-center gap-3 px-8 py-4 bg-white/5 border border-white/10 text-white rounded-2xl font-semibold text-lg transition-all hover:bg-white/10 hover:border-white/20">
              <Icon name="play" size={18} />
              Watch Demo
            </a>
          </div>

          {/* Border-less floating stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-4 relative before:absolute before:inset-x-0 before:-top-10 before:h-px before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent">
            {HERO_STATS.map((stat, i) => (
              <div key={i} className="hero-stat-item flex flex-col items-center">
                <div className="text-4xl md:text-5xl font-black text-white mb-2 tracking-tighter mix-blend-screen">{stat.value}</div>
                <div className="text-sm font-medium text-white/50 tracking-wide uppercase">{stat.label}</div>
              </div>
            ))}
          </div>

        </div>
      </div>
    </section>
  );
}
