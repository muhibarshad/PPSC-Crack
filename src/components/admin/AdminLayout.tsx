/**
 * Admin Layout — Shared sidebar + content wrapper for admin pages.
 * Mobile: sidebar collapses to hamburger menu overlay.
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';

const NAV_ITEMS = [
  { label: 'Dashboard', href: '/admin', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { label: 'Papers Library', href: '/admin/papers', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  { label: 'Prediction Studio', href: '/admin/prediction-studio', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
  { label: 'Job Types', href: '/admin/job-types', icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' },
  { label: 'Pattern Analytics', href: '/admin/pattern-analytics', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
  { label: 'Review Queue', href: '/admin/review-queue', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' },
  { label: 'Admin Notes', href: '/admin/notes', icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z' },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Close sidebar on route change
  useEffect(() => { setSidebarOpen(false); }, [pathname]);

  // Close on escape key
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setSidebarOpen(false); };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, []);

  return (
    <div className="min-h-screen flex z-10 relative">
      {/* Mobile hamburger button */}
      <button
        onClick={() => setSidebarOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50 w-10 h-10 rounded-xl bg-[var(--clr-bg-surface)] border border-white/[0.06] flex items-center justify-center text-white hover:bg-white/[0.08] transition-colors"
        aria-label="Open menu"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 12h18M3 6h18M3 18h18" />
        </svg>
      </button>

      {/* Mobile overlay backdrop */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar — hidden on mobile, slides in as overlay when open */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-64 shrink-0 border-r border-white/[0.06] bg-[var(--clr-bg-surface)] flex flex-col
        transition-transform duration-300 ease-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Brand + close button on mobile */}
        <div className="px-6 py-6 border-b border-white/[0.06] flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-vivid to-neon flex items-center justify-center font-black text-lg text-white shadow-[0_0_16px_rgba(139,92,246,0.5)] group-hover:scale-105 transition-transform duration-300">
              P
            </div>
            <span className="font-display font-black text-lg text-white tracking-tight">
              PPSC <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-neon">Crack</span>
            </span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden w-8 h-8 rounded-lg flex items-center justify-center text-[var(--clr-text-muted)] hover:text-white hover:bg-white/[0.06] transition-colors"
            aria-label="Close menu"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
          </button>
        </div>
        <p className="px-6 pt-2 text-[10px] uppercase tracking-[0.2em] text-[var(--clr-text-muted)] font-semibold">
          Admin Panel
        </p>

        {/* Nav Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || (item.href !== '/admin' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  active
                    ? 'bg-[var(--clr-primary-dim)] text-[var(--clr-primary)] border border-[var(--clr-glass-border-hover)]'
                    : 'text-[var(--clr-text-secondary)] hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d={item.icon} />
                </svg>
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* User footer */}
        <div className="px-4 py-4 border-t border-white/[0.06]">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-neon flex items-center justify-center text-xs font-bold text-white">
              {user?.name?.charAt(0)?.toUpperCase() ?? 'A'}
            </div>
            <div className="truncate">
              <p className="text-sm font-semibold text-white truncate">{user?.name}</p>
              <p className="text-[10px] text-[var(--clr-text-muted)] uppercase tracking-wider">{user?.role}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full text-xs font-medium text-[var(--clr-text-muted)] hover:text-[var(--clr-danger)] transition-colors text-left"
          >
            Sign Out →
          </button>
        </div>
      </aside>

      {/* Main content — add left padding on mobile for hamburger */}
      <main className="flex-1 overflow-y-auto p-4 pt-16 sm:p-6 sm:pt-16 lg:p-8 lg:pt-8">
        {children}
      </main>
    </div>
  );
}
