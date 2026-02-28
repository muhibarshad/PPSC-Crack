'use client';

import { useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';
import Icon from '@/components/Icon';
import { PRICING_PLANS } from '@/data/mock-data';

gsap.registerPlugin(ScrollTrigger);

export default function PricingSection() {
  const container = useRef<HTMLElement>(null);

  useGSAP(() => {
    gsap.from('.pricing-header', {
      scrollTrigger: {
        trigger: '.pricing-header',
        start: 'top 85%',
      },
      y: 40,
      opacity: 0,
      duration: 1,
      ease: 'power3.out',
    });

    const cards = gsap.utils.toArray('.pricing-card-item');
    cards.forEach((card: any, i) => {
      gsap.from(card, {
        scrollTrigger: {
          trigger: card,
          start: 'top 85%',
        },
        y: 100,
        opacity: 0,
        duration: 1.2,
        ease: 'power4.out',
      });
      // Stagger features
      gsap.from(card.querySelectorAll('.pricing-feat'), {
        scrollTrigger: {
          trigger: card,
          start: 'top 85%',
        },
        x: -20,
        opacity: 0,
        duration: 0.8,
        stagger: 0.1,
        ease: 'back.out(1.5)',
      });
    });

  }, { scope: container });

  return (
    <section ref={container} id="pricing" className="py-32 relative overflow-hidden bg-background">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-[600px] bg-gradient-to-r from-primary/10 via-neon/5 to-accent/10 blur-[150px] rounded-full pointer-events-none" />

      <div className="container max-w-6xl mx-auto px-6 relative z-10">
        
        <div className="pricing-header text-center mb-24">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-semibold uppercase tracking-widest text-primary mb-6 backdrop-blur-md">
            Pricing
          </div>
          <h2 className="text-[clamp(2rem,5vw,3.5rem)] font-black leading-[1.1] tracking-tight mb-4">
            Invest in your future.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-yellow-400 to-orange-500 pb-2">
              Starting at Rs 499.
            </span>
          </h2>
          <p className="text-lg text-muted-foreground w-full max-w-xl mx-auto">
            Less than one chai per day. More than a lifetime of random studying.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8 items-center max-w-5xl mx-auto">
          {PRICING_PLANS.map((plan, i) => {
            const isFeatured = plan.id === 'pro';
            const isGold = plan.id === 'elite';
            
            return (
              <div 
                key={plan.id} 
                className={`pricing-card-item group relative flex flex-col p-8 rounded-[2.5rem] bg-surface backdrop-blur-xl transition-[transform,shadow] duration-500 hover:-translate-y-2
                  ${isFeatured 
                    ? 'border-2 border-primary/50 shadow-[0_0_60px_rgba(139,92,246,0.15)] z-10 lg:-mx-2 scale-100 lg:scale-105' 
                    : isGold 
                      ? 'border border-amber-500/30' 
                      : 'border border-white/5 opacity-90 hover:opacity-100'}`}
              >
                {/* Glow behind featured cards */}
                {isFeatured && <div className="absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-primary to-transparent" />}
                {isGold && <div className="absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-amber-400 to-transparent" />}

                {plan.tag && (
                  <div className={`absolute top-6 right-8 text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full 
                    ${isFeatured ? 'bg-primary/20 text-primary-light border border-primary/30' : 'bg-amber-500/20 text-amber-500 border border-amber-500/30'}`}>
                    {plan.tag}
                  </div>
                )}

                <div className="mb-8">
                  <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mt-4">
                    {plan.price === 0 ? (
                      <span className="text-5xl font-black text-white">Free</span>
                    ) : (
                      <>
                        <span className="text-xl font-medium text-white/50">Rs</span>
                        <span className={`text-6xl font-black ${isFeatured ? 'text-transparent bg-clip-text bg-gradient-to-br from-white to-primary-light' : isGold ? 'text-transparent bg-clip-text bg-gradient-to-br from-white to-amber-200' : 'text-white'}`}>
                          {plan.price}
                        </span>
                        <span className="text-sm font-medium text-white/40">/{plan.period}</span>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex-1">
                  <div className="w-full h-px bg-white/5 mb-8" />
                  <ul className="space-y-4 mb-10">
                    {plan.features.map((feat, fi) => (
                      <li key={fi} className="pricing-feat flex items-center gap-3 text-sm text-white/70">
                        <div className={`shrink-0 w-5 h-5 rounded-full flex items-center justify-center 
                          ${isFeatured ? 'bg-primary/20' : isGold ? 'bg-amber-500/20' : 'bg-white/5'}`}>
                          <Icon name="check" size={10} className={`${isFeatured ? 'text-primary' : isGold ? 'text-amber-500' : 'text-white/50'}`} />
                        </div>
                        {feat}
                      </li>
                    ))}
                  </ul>
                </div>

                <a 
                  href="#" 
                  className={`relative flex items-center justify-center w-full py-4 rounded-2xl font-bold transition-all
                    ${isFeatured 
                      ? 'bg-primary text-white hover:bg-primary-vivid shadow-[0_4px_20px_rgba(139,92,246,0.4)] hover:shadow-[0_8px_30px_rgba(139,92,246,0.6)]' 
                      : isGold
                        ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:shadow-[0_8px_30px_rgba(245,158,11,0.4)]'
                        : 'bg-white/5 text-white hover:bg-white/10 border border-white/5'}`}
                >
                  {plan.cta}
                </a>

              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
}
