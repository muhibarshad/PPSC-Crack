'use client';

import { useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';
import Icon from '@/components/Icon';
import { PROBLEMS, SOLUTIONS } from '@/data/mock-data';

gsap.registerPlugin(ScrollTrigger);

export default function ProblemSolution() {
  const container = useRef<HTMLElement>(null);

  useGSAP(() => {
    // Problem block
    gsap.from('.problem-side', {
      scrollTrigger: {
        trigger: '.problem-side',
        start: 'top 85%',
      },
      x: -50,
      opacity: 0,
      duration: 1.2,
      ease: 'power3.out',
    });

    // Solution block
    gsap.from('.solution-side', {
      scrollTrigger: {
        trigger: '.solution-side',
        start: 'top 85%',
      },
      x: 50,
      opacity: 0,
      duration: 1.2,
      ease: 'power3.out',
    });

    // List items staggering
    gsap.from('.list-item-problem', {
      scrollTrigger: { trigger: '.problem-side', start: 'top 85%' },
      y: 20, opacity: 0, duration: 0.8, stagger: 0.1, delay: 0.5, ease: 'back.out'
    });
    
    gsap.from('.list-item-solution', {
      scrollTrigger: { trigger: '.solution-side', start: 'top 85%' },
      y: 20, opacity: 0, duration: 0.8, stagger: 0.1, delay: 0.5, ease: 'back.out'
    });

  }, { scope: container });

  return (
    <section ref={container} id="problem" className="py-24 relative overflow-hidden bg-black/40 border-y border-primary/5">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:64px_64px] opacity-30 pointer-events-none" />
      
      <div className="container max-w-6xl mx-auto px-6 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 lg:gap-24">

          {/* Problem */}
          <div className="problem-side flex flex-col items-start pt-10 border-t-2 border-red-500/20">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                <Icon name="x" size={24} className="text-red-400" />
              </div>
              <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">
                The <span className="text-red-400">Old</span> Way
              </h2>
            </div>
            <p className="text-lg text-muted-foreground mb-8 leading-relaxed max-w-sm">
              Studying randomly based on guesswork, wasting months on topics 
              that won't appear on the exam.
            </p>
            <div className="space-y-5 w-full">
              {PROBLEMS.map((text, i) => (
                <div className="list-item-problem flex items-start gap-4 p-4 rounded-2xl bg-white/[0.02] border border-white/5" key={i}>
                  <div className="w-6 h-6 shrink-0 rounded-full bg-red-500/20 flex items-center justify-center mt-1">
                    <Icon name="x" size={12} className="text-red-400" />
                  </div>
                  <span className="text-white/70 font-medium leading-normal">{text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Solution */}
          <div className="solution-side flex flex-col items-start pt-10 border-t-2 border-primary/40 relative">
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-[80px] pointer-events-none -translate-y-1/2 translate-x-1/2" />
            <div className="flex items-center gap-3 mb-8 relative z-10">
              <div className="w-12 h-12 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center shadow-[0_0_30px_rgba(139,92,246,0.3)]">
                <Icon name="check" size={24} className="text-primary-light" />
              </div>
              <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight drop-shadow-[0_0_15px_rgba(139,92,246,0.4)]">
                The <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-neon">New</span> Way
              </h2>
            </div>
            <p className="text-lg text-muted-foreground mb-8 leading-relaxed max-w-sm">
              Targeted, algorithm-backed preparation focused purely on the highest-probability questions.
            </p>
            <div className="space-y-5 w-full relative z-10">
              {SOLUTIONS.map((text, i) => (
                <div className="list-item-solution flex items-start gap-4 p-4 rounded-2xl bg-gradient-to-r from-primary/10 to-transparent border border-primary/20 shadow-[inset_0_1px_rgba(255,255,255,0.1)] backdrop-blur-sm" key={i}>
                  <div className="w-6 h-6 shrink-0 rounded-full bg-primary/30 flex items-center justify-center mt-1">
                    <Icon name="check" size={12} className="text-primary-light" />
                  </div>
                  <span className="text-white font-medium leading-normal">{text}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
