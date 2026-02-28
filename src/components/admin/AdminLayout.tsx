/**
 * Admin Layout — Shared sidebar + content wrapper for admin pages.
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';

const NAV_ITEMS = [
  { label: 'Dashboard', href: '/admin', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { label: 'Job Types', href: '/admin/job-types', icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  return (
    <div className="min-h-screen flex z-10 relative">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 border-r border-white/[0.06] bg-[var(--clr-bg-surface)] flex flex-col">
        {/* Brand */}
        <div className="px-6 py-6 border-b border-white/[0.06]">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-vivid to-neon flex items-center justify-center font-black text-lg text-white shadow-[0_0_16px_rgba(139,92,246,0.5)] group-hover:scale-105 transition-transform duration-300">
              P
            </div>
            <span className="font-display font-black text-lg text-white tracking-tight">
              PPSC <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-neon">Crack</span>
            </span>
          </Link>
          <p className="text-[10px] uppercase tracking-[0.2em] text-[var(--clr-text-muted)] mt-2 font-semibold">
            Admin Panel
          </p>
        </div>

        {/* Nav Items */}
        <nav className="flex-1 px-3 py-4 space-y-1">
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

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-8">
        {children}
      </main>
    </div>
  );
}
