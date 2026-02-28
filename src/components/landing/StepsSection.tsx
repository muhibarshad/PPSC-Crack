'use client';

import { useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';
import Icon from '@/components/Icon';
import { STEPS } from '@/data/mock-data';

gsap.registerPlugin(ScrollTrigger);

export default function StepsSection() {
  const container = useRef<HTMLElement>(null);

  useGSAP(() => {
    // Header animes
    gsap.from('.step-title-item', {
      scrollTrigger: {
        trigger: '.step-header',
        start: 'top 85%',
      },
      y: 40,
      opacity: 0,
      duration: 1,
      stagger: 0.1,
      ease: 'power3.out',
    });

    // Animate the line
    gsap.fromTo('.step-line-fill', 
      { height: '0%' }, 
      {
        scrollTrigger: {
          trigger: '.steps-track',
          start: 'top 70%',
          end: 'bottom 40%',
          scrub: 1,
        },
        height: '100%',
        ease: 'none',
      }
    );

    // Fade the blocks
    const blocks = gsap.utils.toArray('.step-block');
    blocks.forEach((block: any, i) => {
      gsap.from(block, {
        scrollTrigger: {
          trigger: block,
          start: 'top 85%',
        },
        y: 60,
        opacity: 0,
        duration: 1.2,
        ease: 'power4.out',
      });
      // Ping the dot
      gsap.from(block.querySelector('.step-dot'), {
        scrollTrigger: {
          trigger: block,
          start: 'top 65%',
        },
        scale: 0,
        backgroundColor: '#fff',
        duration: 0.8,
        ease: 'back.out(2)',
      });
    });

  }, { scope: container });

  return (
    <section ref={container} id="how-it-works" className="py-32 relative bg-surface border-y border-white/5">
      <div className="container max-w-4xl mx-auto px-6 relative z-10">
        
        <div className="step-header text-center mb-24">
          <div className="step-title-item text-xs font-semibold uppercase tracking-widest text-primary mb-6">
            <span className="inline-block border-b-2 border-primary pb-1">The Process</span>
          </div>
          <h2 className="step-title-item text-4xl md:text-5xl font-black mb-4">
            Zero to exam-ready<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-light to-primary-vivid">
              in four steps.
            </span>
          </h2>
        </div>

        <div className="steps-track relative pl-10 md:pl-24">
          {/* Vertical Track background */}
          <div className="absolute left-[29px] md:left-[85px] top-0 bottom-0 w-px bg-white/5" />
          
          {/* The active filling line */}
          <div className="step-line-fill absolute left-[29px] md:left-[85px] top-0 w-[2px] -ml-[0.5px] bg-gradient-to-b from-primary via-neon to-accent rounded-full shadow-[0_0_20px_rgba(139,92,246,0.8)]" />

          <div className="space-y-20">
            {STEPS.map((s, i) => (
              <div key={i} className="step-block relative">
                
                {/* The Dot */}
                <div className="step-dot absolute -left-[45px] md:-left-[64px] top-2 w-5 h-5 rounded-full bg-surface border-4 border-primary shadow-[0_0_15px_rgba(139,92,246,0.5)] z-20" />
                
                {/* Visual Number background faintly behind */}
                <div className="absolute -left-10 md:-left-20 -top-12 text-[7rem] md:text-[9rem] font-black text-white/[0.03] select-none leading-none -z-10 mix-blend-screen pointer-events-none">
                  {s.n}
                </div>

                <div className="flex flex-col md:flex-row gap-6 md:gap-8 items-start relative z-10 p-6 md:p-8 rounded-3xl bg-white/[0.015] border border-white/5 backdrop-blur-md shadow-2xl transition hover:bg-white/[0.03]">
                  <div className="w-14 h-14 shrink-0 rounded-2xl bg-gradient-to-br from-primary/20 to-neon/5 border border-primary/20 flex items-center justify-center">
                    <Icon name={s.icon} size={24} className="text-primary-light" />
                  </div>
                  
                  <div className="pt-2">
                    <h3 className="text-2xl font-bold mb-3 text-white tracking-tight">
                      {s.title}
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {s.desc}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </section>
  );
}
