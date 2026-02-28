/**
 * Admin Dashboard — /admin
 * Protected route: requires role='admin'.
 */

'use client';

import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminLayout from '@/components/admin/AdminLayout';
import Link from 'next/link';

function AdminContent() {
  const cards = [
    {
      title: 'Job Types',
      desc: 'Manage PPSC job categories & topic ratios',
      href: '/admin/job-types',
      count: '8',
      icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
    },
    {
      title: 'Pattern Analytics',
      desc: 'Topic trends, repeat patterns & prediction accuracy',
      href: '/admin/pattern-analytics',
      count: '5',
      icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    },
    {
      title: 'Review Queue',
      desc: 'Questions needing manual correction',
      href: '/admin/review-queue',
      count: '—',
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
    },
    {
      title: 'Admin Notes',
      desc: 'Upload & process raw notes into story docs',
      href: '/admin/notes',
      count: '—',
      icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
    },
    {
      title: 'Papers',
      desc: 'Past papers & questions database',
      href: '/admin',
      count: '—',
      icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    },
    {
      title: 'Users',
      desc: 'Student & admin accounts',
      href: '/admin',
      count: '—',
      icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z',
    },
  ];

  return (
    <AdminLayout>
      <div className="max-w-5xl">
        <h1 className="font-display text-3xl font-bold text-white mb-1">Dashboard</h1>
        <p className="text-[var(--clr-text-secondary)] mb-8">Overview of the PPSC Crack admin panel.</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {cards.map((c) => (
            <Link key={c.title} href={c.href} className="group">
              <div className="glass p-6 hover:border-[var(--clr-glass-border-hover)] transition-all duration-200 group-hover:bg-[var(--clr-glass-bg-hover)]">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-[var(--clr-primary-dim)] flex items-center justify-center">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--clr-primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d={c.icon} />
                    </svg>
                  </div>
                  <span className="text-2xl font-bold text-white">{c.count}</span>
                </div>
                <h3 className="text-sm font-bold text-white mb-1">{c.title}</h3>
                <p className="text-xs text-[var(--clr-text-muted)]">{c.desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </AdminLayout>
  );
}

export default function AdminPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <AdminContent />
    </ProtectedRoute>
  );
}
