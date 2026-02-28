'use client';

import { useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';
import Icon from '@/components/Icon';
import { TESTIMONIALS } from '@/data/mock-data';

gsap.registerPlugin(ScrollTrigger);

export default function TestimonialsSection() {
  const container = useRef<HTMLElement>(null);

  useGSAP(() => {
    // Header
    gsap.from('.test-header', {
      scrollTrigger: {
        trigger: '.test-header',
        start: 'top 85%',
      },
      y: 40,
      opacity: 0,
      duration: 1,
      ease: 'power3.out',
    });

    // Staggered testimonials
    const cards = gsap.utils.toArray('.test-card-item');
    gsap.from(cards, {
      scrollTrigger: {
        trigger: '.testimonials-grid',
        start: 'top 80%',
      },
      y: 50,
      opacity: 0,
      duration: 1,
      stagger: 0.15,
      ease: 'back.out(1.2)',
    });
  }, { scope: container });

  return (
    <section ref={container} id="testimonials" className="py-32 relative overflow-hidden bg-background border-t border-white/5">
      <div className="absolute top-0 right-0 w-[800px] h-[500px] bg-gradient-to-l from-primary/10 to-transparent blur-[120px] rounded-full pointer-events-none -translate-y-1/2" />

      <div className="container max-w-6xl mx-auto px-6 relative z-10">
        
        <div className="test-header text-center mb-24">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-primary/20 bg-primary/10 text-xs font-semibold uppercase tracking-widest text-primary mb-6">
            Success Stories
          </div>
          <h2 className="text-[clamp(2rem,5vw,3.5rem)] font-black leading-[1.1] tracking-tight mb-4 text-white">
            Real aspirants.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-neon">
              Real results.
            </span>
          </h2>
        </div>

        <div className="testimonials-grid grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {TESTIMONIALS.map((t, i) => (
            <div key={t.id} className="test-card-item relative group flex flex-col p-8 rounded-3xl bg-white/[0.02] border border-white/5 backdrop-blur-md transition-all duration-500 hover:bg-white/[0.04] hover:-translate-y-2 hover:shadow-[0_20px_40px_rgba(0,0,0,0.5)]">
              {/* Subtle top border color matching avatar */}
              <div 
                className="absolute inset-x-0 top-0 h-1 rounded-t-3xl opacity-50"
                style={{ background: `linear-gradient(90deg, transparent, ${t.color}, transparent)` }} 
              />
              
              <div className="flex gap-1 mb-6">
                {[...Array(t.rating)].map((_, si) => (
                  <Icon key={si} name="star" size={16} className="text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.6)]" />
                ))}
              </div>

              <blockquote className="flex-1 text-lg text-white/80 leading-relaxed mb-8 relative">
                <span className="absolute -left-3 -top-3 text-4xl text-primary/20 font-serif leading-none">"</span>
                {t.text}
                <span className="absolute -bottom-4 text-4xl text-primary/20 font-serif leading-none ml-1">"</span>
              </blockquote>

              <div className="flex items-center gap-4 mt-auto pt-4 border-t border-white/5">
                <div 
                  className="w-12 h-12 flex items-center justify-center rounded-full font-black text-white text-lg shrink-0 shadow-[0_0_20px_rgba(0,0,0,0.5)]"
                  style={{ 
                    background: `linear-gradient(135deg, ${t.color}33 0%, ${t.color}11 100%)`,
                    border: `1px solid ${t.color}44`
                  }}
                >
                  {t.initials}
                </div>
                <div>
                  <div className="text-white font-bold">{t.name}</div>
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1">
                    <Icon name="check" size={12} className="text-emerald-400" />
                    <span>{t.role}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
