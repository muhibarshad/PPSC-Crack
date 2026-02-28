'use client';

import { useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';
import Icon from '@/components/Icon';
import { FEATURES } from '@/data/mock-data';

// Register ScrollTrigger
gsap.registerPlugin(ScrollTrigger);

export default function FeaturesSection() {
  const container = useRef<HTMLElement>(null);

  useGSAP(() => {
    // Title animations
    gsap.from('.feature-title-item', {
      scrollTrigger: {
        trigger: '.features-header',
        start: 'top 80%',
      },
      y: 50,
      opacity: 0,
      duration: 1,
      stagger: 0.1,
      ease: 'power3.out',
    });

    // Feature items alternating from left/right
    const items = gsap.utils.toArray('.feature-row');
    items.forEach((item: any, i) => {
      const isEven = i % 2 === 0;
      
      gsap.from(item, {
        scrollTrigger: {
          trigger: item,
          start: 'top 85%',
        },
        x: isEven ? -100 : 100,
        opacity: 0,
        duration: 1.2,
        ease: 'power4.out',
      });
      
      gsap.from(item.querySelector('.feature-icon-blob'), {
        scrollTrigger: {
          trigger: item,
          start: 'top 85%',
        },
        scale: 0,
        opacity: 0,
        duration: 1.5,
        delay: 0.2,
        ease: 'elastic.out(1, 0.5)',
      });
    });

  }, { scope: container });

  return (
    <section ref={container} id="features" className="py-32 relative overflow-hidden bg-background">
      {/* Background gradients */}
      <div className="absolute top-1/2 left-0 w-full h-[500px] bg-primary/5 blur-[120px] rounded-full pointer-events-none -translate-y-1/2" />
      
      <div className="container max-w-6xl mx-auto px-6 relative z-10">
        <div className="features-header text-center mb-24">
          <div className="feature-title-item inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-primary/20 bg-primary/10 text-xs font-semibold uppercase tracking-widest text-primary mb-6">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            The Intelligence Engine
          </div>
          <h2 className="feature-title-item text-[clamp(2rem,5vw,3.5rem)] font-black leading-[1.1] tracking-tight mb-4">
            Six AI Engines.<br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-neon to-primary-vivid">
              One Unfair Advantage.
            </span>
          </h2>
          <p className="feature-title-item text-lg text-muted-foreground max-w-2xl mx-auto">
            Forget passive reading. Our systems deeply analyze PPSC's history to engineer the exact path you need to clear the cut-off.
          </p>
        </div>

        <div className="space-y-32">
          {FEATURES.map((f, i) => {
            const isEven = i % 2 === 0;
            return (
              <div 
                key={i} 
                className={`feature-row flex flex-col gap-12 lg:gap-24 items-center ${
                  isEven ? 'lg:flex-row' : 'lg:flex-row-reverse'
                }`}
              >
                {/* Visual Side */}
                <div className="w-full lg:w-1/2 relative group">
                  <div className="feature-icon-blob absolute inset-0 bg-gradient-to-tr from-primary/20 to-neon/5 blur-3xl rounded-full transition-all duration-700 group-hover:blur-[80px] group-hover:from-primary/30" />
                  <div className="relative aspect-square md:aspect-[4/3] w-full rounded-3xl border border-white/5 bg-white/[0.02] backdrop-blur-sm flex items-center justify-center overflow-hidden">
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:32px_32px] opacity-20" />
                    
                    {/* The core icon in a floating orb */}
                    <div className="relative z-10 w-24 h-24 sm:w-32 sm:h-32 rounded-full border border-white/10 bg-gradient-to-br from-white/10 to-transparent flex items-center justify-center shadow-2xl backdrop-blur-md">
                      <Icon name={f.icon} size={48} className={`text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.5)]`} />
                    </div>
                  </div>

                  {/* Number Indicator */}
                  <div className={`absolute top-4 ${isEven ? 'left-4' : 'right-4'} text-[8rem] font-black text-white/5 leading-none select-none z-0 mix-blend-screen`}>
                    0{i + 1}
                  </div>
                </div>

                {/* Text Side */}
                <div className="w-full lg:w-1/2 flex flex-col items-start text-left">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-bold uppercase tracking-widest text-primary-light mb-6">
                    {f.tag}
                  </div>
                  <h3 className="text-3xl md:text-4xl font-bold mb-6 tracking-tight text-white leading-tight">
                    {f.title}
                  </h3>
                  <p className="text-lg text-muted-foreground leading-relaxed">
                    {f.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
