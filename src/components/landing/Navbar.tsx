'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/Icon';
import gsap from 'gsap';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    
    // Initial drop down anime
    gsap.from('.nav', { y: -100, opacity: 0, duration: 1, ease: 'power3.out' });

    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav className={`nav fixed top-0 w-full z-50 transition-all duration-300 ${scrolled ? 'bg-background/80 backdrop-blur-xl border-b border-primary/10 py-3 shadow-2xl' : 'bg-transparent py-5'}`} id="navbar">
      <div className="container max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between">

          <a href="#" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-vivid to-neon flex items-center justify-center font-black text-xl text-white shadow-[0_0_20px_rgba(139,92,246,0.5)] group-hover:scale-105 transition-transform duration-300">
              P
            </div>
            <span className="font-display font-black text-xl text-white tracking-tight">
              PPSC <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-neon">Crack</span>
            </span>
          </a>

          <div className="hidden md:flex items-center gap-10">
            {['Features', 'How It Works', 'Pricing', 'Success Stories'].map((item) => (
              <a 
                key={item} 
                href={`#${item.toLowerCase().replace(/ /g, '-')}`} 
                className="text-sm font-medium text-white/60 hover:text-white transition-colors relative group"
              >
                {item}
                <span className="absolute -bottom-2 left-1/2 w-0 h-px bg-gradient-to-r from-primary to-neon rounded-full transition-all duration-300 group-hover:w-full group-hover:left-0" />
              </a>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-4">
            <a href="/auth/login" className="text-sm font-semibold text-white/50 hover:text-white transition-colors px-4 py-2">
              Login
            </a>
            <a href="/auth/register" className="inline-flex items-center justify-center bg-white/10 hover:bg-white/20 border border-white/20 text-white text-sm font-bold px-6 py-2.5 rounded-xl transition-all hover:scale-105 shadow-[0_0_15px_rgba(255,255,255,0.05)]">
              Get Started
            </a>
          </div>

          <button
            className="md:hidden flex items-center justify-center w-10 h-10 text-white/80 hover:text-white"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            <Icon name={mobileOpen ? 'x' : 'menu'} size={24} />
          </button>

        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden flex flex-col gap-4 pt-6 pb-2 border-t border-white/10 mt-4 animate-in fade-in slide-in-from-top-4">
            {['Features', 'How It Works', 'Pricing', 'Success Stories'].map((item) => (
              <a 
                key={item}
                href={`#${item.toLowerCase().replace(/ /g, '-')}`} 
                onClick={() => setMobileOpen(false)} 
                className="text-base font-semibold text-white/70 hover:text-white py-2"
              >
                {item}
              </a>
            ))}
            <div className="flex flex-col gap-3 mt-4 pt-4 border-t border-white/5">
              <a href="/auth/login" className="text-center text-sm font-semibold text-white/50 py-2">Login</a>
              <a href="/auth/register" className="bg-primary text-white text-center font-bold px-6 py-3 rounded-xl">Get Started</a>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
