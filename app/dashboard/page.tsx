/**
 * Student Dashboard — /dashboard
 * Protected route: requires authenticated user.
 */

'use client';

import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/store/auth-store';

function DashboardContent() {
  const { user, logout } = useAuthStore();

  return (
    <div className="min-h-screen z-10 relative pt-24 px-6">
      <div className="max-w-4xl mx-auto">
        <div className="glass p-8">
          <h1 className="font-display text-3xl font-bold text-white mb-2">
            Welcome back, {user?.name || 'Student'}! 👋
          </h1>
          <p className="text-[var(--clr-text-secondary)] mb-6">
            Your PPSC preparation dashboard is loading soon.
          </p>

          <div className="flex flex-wrap gap-4">
            <div className="glow-card p-6 flex-1 min-w-[200px]">
              <p className="text-xs uppercase tracking-widest text-[var(--clr-text-muted)] mb-1">Role</p>
              <p className="text-lg font-bold text-white capitalize">{user?.role}</p>
            </div>
            <div className="glow-card p-6 flex-1 min-w-[200px]">
              <p className="text-xs uppercase tracking-widest text-[var(--clr-text-muted)] mb-1">Plan</p>
              <p className="text-lg font-bold text-white capitalize">{user?.subscription_tier}</p>
            </div>
            <div className="glow-card p-6 flex-1 min-w-[200px]">
              <p className="text-xs uppercase tracking-widest text-[var(--clr-text-muted)] mb-1">Provider</p>
              <p className="text-lg font-bold text-white capitalize">{user?.auth_provider}</p>
            </div>
          </div>

          <button
            onClick={logout}
            className="btn btn-ghost mt-8"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
