/**
 * Auth Layout — Shared wrapper for Login / Register / Forgot Password.
 * Glass-morphism card centred on the ultraviolet dark background.
 */

'use client';

import Link from 'next/link';
import Icon from '@/components/Icon';

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}

export default function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16 relative z-10">
      {/* Decorative orbs */}
      <div className="absolute w-[500px] h-[500px] rounded-full top-[5%] -left-[8%] bg-primary/10 blur-[120px] -z-10 pointer-events-none" />
      <div className="absolute w-[400px] h-[400px] rounded-full bottom-[5%] -right-[8%] bg-neon/5 blur-[120px] -z-10 pointer-events-none" />

      <div className="w-full max-w-[460px]">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 justify-center mb-10 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-vivid to-neon flex items-center justify-center font-black text-xl text-white shadow-[0_0_20px_rgba(139,92,246,0.5)] group-hover:scale-105 transition-transform duration-300">
            P
          </div>
          <span className="font-display font-black text-xl text-white tracking-tight">
            PPSC{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-neon">
              Crack
            </span>
          </span>
        </Link>

        {/* Glass card */}
        <div className="glass p-8 sm:p-10">
          <div className="text-center mb-8">
            <h1 className="font-display text-2xl sm:text-3xl font-bold text-white mb-2">
              {title}
            </h1>
            {subtitle && (
              <p className="text-sm text-[var(--clr-text-secondary)]">{subtitle}</p>
            )}
          </div>

          {children}
        </div>
      </div>
    </div>
  );
}
