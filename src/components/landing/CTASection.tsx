'use client';

import { useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';
import Icon from '@/components/Icon';

gsap.registerPlugin(ScrollTrigger);

export default function CTASection() {
  const container = useRef<HTMLElement>(null);

  useGSAP(() => {
    gsap.from('.cta-content-item', {
      scrollTrigger: {
        trigger: container.current,
        start: 'top 80%',
      },
      y: 60,
      opacity: 0,
      duration: 1.5,
      stagger: 0.15,
      ease: 'power3.out',
    });
  }, { scope: container });

  return (
    <section ref={container} className="py-40 relative overflow-hidden bg-background">
      {/* Background massive glow effect */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.15)_0%,transparent_60%)] pointer-events-none mix-blend-screen" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full max-w-4xl max-h-[400px] bg-gradient-to-r from-primary via-neon to-accent rounded-full blur-[180px] opacity-20 pointer-events-none" />

      <div className="container max-w-5xl mx-auto px-6 relative z-10">
        
        <div className="text-center bg-white/[0.02] border border-white/5 backdrop-blur-3xl rounded-[3rem] p-12 md:p-24 shadow-[0_0_80px_rgba(0,0,0,0.8)] relative overflow-hidden">
          {/* Internal diagonal slash */}
          <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent skew-x-12 translate-x-1/2 scale-150 pointer-events-none" />
          
          <h2 className="cta-content-item text-[clamp(2.5rem,6vw,4.5rem)] font-black text-white leading-none tracking-tight mb-8">
            Stop guessing.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-neon via-primary to-primary-light pb-2 drop-shadow-[0_0_20px_rgba(232,121,249,0.5)]">
              Start dominating.
            </span>
          </h2>
          
          <p className="cta-content-item text-[clamp(1.1rem,2vw,1.4rem)] text-white/70 max-w-2xl mx-auto leading-relaxed mb-12">
            Join 50,000+ aspirants already using AI to crack their PPSC exams. 
            The system is proven. The choice is yours.
          </p>
          
          <div className="cta-content-item flex flex-col sm:flex-row items-center justify-center gap-6">
            <a href="/auth/register" className="group relative inline-flex items-center justify-center gap-3 px-10 py-5 bg-white text-black rounded-2xl font-bold text-lg overflow-hidden transition-transform hover:scale-105 hover:shadow-[0_0_40px_rgba(255,255,255,0.4)] w-full sm:w-auto">
              <span className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-primary via-neon to-accent" />
              <Icon name="zap" size={20} className="text-primary-vivid animate-pulse" />
              Get Free Access
            </a>
            <a href="#features" className="inline-flex items-center justify-center gap-3 px-10 py-5 bg-white/5 border border-white/10 text-white rounded-2xl font-bold text-lg transition-colors hover:bg-white/10 hover:border-white/20 w-full sm:w-auto">
              Explore Features
            </a>
          </div>

          {/* Sparkles decorative */}
          <Icon name="sparkles" size={40} className="absolute top-10 left-10 text-white/10" />
          <Icon name="sparkles" size={60} className="absolute bottom-10 right-10 text-white/10" />
        </div>

      </div>
    </section>
  );
}
