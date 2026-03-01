/**
 * Subscription Management — /dashboard/subscription
 * ===================================================
 * Shows current plan, renewal date, upgrade/downgrade, cancel.
 * Uses Stripe Checkout hosted flow for payment.
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/store/auth-store';
import Icon from '@/components/Icon';
import PricingCards from '@/components/dashboard/PricingCards';

/* ── Types ── */

interface SubscriptionStatus {
  is_premium: boolean;
  subscription_tier: string;
  subscription_expires_at: string | null;
  stripe_subscription_id: string | null;
  cancel_at_period_end: boolean;
  current_period_end: string | null;
}

/* ── API helper ── */

const API = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

async function apiFetch<T>(path: string, token: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    credentials: 'include',
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Page ── */

function SubscriptionContent() {
  const { user, session, refreshUser } = useAuthStore();
  const searchParams = useSearchParams();

  const [subStatus, setSubStatus] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Check for success/cancelled URL params from Stripe redirect
  useEffect(() => {
    const status = searchParams.get('status');
    if (status === 'success') {
      setSuccessMsg('Payment successful! Your subscription is now active.');
      // Refresh the user data to reflect the new subscription
      refreshUser();
    }
  }, [searchParams, refreshUser]);

  // Fetch subscription status
  const loadStatus = useCallback(async () => {
    const token = session?.access_token;
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const data = await apiFetch<SubscriptionStatus>('/payments/subscription', token);
      setSubStatus(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load subscription');
    } finally {
      setLoading(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    if (session?.access_token) loadStatus();
  }, [session?.access_token, loadStatus]);

  // Cancel subscription handler
  const handleCancel = async () => {
    const token = session?.access_token;
    if (!token) return;
    if (!confirm('Are you sure you want to cancel? You\'ll keep access until the end of your billing period.')) return;

    try {
      setCancelling(true);
      await apiFetch('/payments/cancel', token, { method: 'POST' });
      setSuccessMsg('Subscription cancellation scheduled.');
      await loadStatus();
      await refreshUser();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to cancel subscription');
    } finally {
      setCancelling(false);
    }
  };

  // Format date
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-PK', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  /* ── Tier display helpers ── */
  const tierName = (tier: string) => {
    const names: Record<string, string> = { free: 'Free', basic: 'Basic', pro: 'Pro' };
    return names[tier] || tier;
  };

  const tierColor = (tier: string) => {
    const colors: Record<string, string> = {
      free: 'var(--clr-text-secondary)',
      basic: 'var(--clr-accent)',
      pro: 'var(--clr-gold)',
    };
    return colors[tier] || 'var(--clr-text-secondary)';
  };

  /* ── Loading ── */
  if (loading) {
    return (
      <div className="min-h-screen z-10 relative pt-24 px-6">
        <div className="max-w-5xl mx-auto flex flex-col items-center justify-center gap-6 py-32">
          <div className="w-16 h-16 rounded-full border-4 border-[var(--clr-primary-dim)] border-t-[var(--clr-primary)] animate-spin" />
          <p className="text-[var(--clr-text-secondary)] text-sm">Loading subscription…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen z-10 relative pt-24 pb-16 px-6">
      <div className="max-w-5xl mx-auto flex flex-col gap-8">
        {/* ═══ Header ═══ */}
        <div className="animate-fade-in-up">
          <h1 className="font-display text-3xl md:text-4xl font-bold text-white">
            Subscription <span className="gradient-text">Management</span>
          </h1>
          <p className="text-[var(--clr-text-secondary)] mt-1">
            Manage your plan, billing, and subscription preferences
          </p>
        </div>

        {/* ═══ Success / Error Messages ═══ */}
        {successMsg && (
          <div className="glass p-4 border border-[var(--clr-success)]/20 bg-[var(--clr-success-dim)] animate-fade-in-up">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[var(--clr-success-dim)] flex items-center justify-center">
                <Icon name="check" size={16} color="var(--clr-success)" />
              </div>
              <p className="text-[var(--clr-success)] text-sm font-medium">{successMsg}</p>
              <button
                onClick={() => setSuccessMsg(null)}
                className="ml-auto text-[var(--clr-text-muted)] hover:text-white transition-colors"
              >
                <Icon name="x" size={14} />
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="glass p-4 border border-[var(--clr-danger)]/20 bg-[var(--clr-danger-dim)] animate-fade-in-up">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[var(--clr-danger-dim)] flex items-center justify-center">
                <Icon name="x" size={16} color="var(--clr-danger)" />
              </div>
              <p className="text-[var(--clr-danger)] text-sm font-medium">{error}</p>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-[var(--clr-text-muted)] hover:text-white transition-colors"
              >
                <Icon name="x" size={14} />
              </button>
            </div>
          </div>
        )}

        {/* ═══ Current Plan Card ═══ */}
        {subStatus && (
          <div className="glass p-6 md:p-8 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              {/* Plan info */}
              <div className="flex items-start gap-4">
                <div
                  className="w-14 h-14 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: `${tierColor(subStatus.subscription_tier)}15` }}
                >
                  <Icon
                    name={subStatus.subscription_tier === 'pro' ? 'star' : subStatus.subscription_tier === 'basic' ? 'zap' : 'user'}
                    size={24}
                    color={tierColor(subStatus.subscription_tier)}
                  />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="font-display text-xl font-bold text-white">
                      {tierName(subStatus.subscription_tier)} Plan
                    </h2>
                    {subStatus.is_premium && (
                      <span className="badge badge-gold text-xs">Active</span>
                    )}
                    {subStatus.cancel_at_period_end && (
                      <span className="badge bg-[var(--clr-warning-dim)] text-[var(--clr-warning)] text-xs">
                        Cancelling
                      </span>
                    )}
                  </div>
                  <p className="text-[var(--clr-text-secondary)] text-sm mt-1">
                    {subStatus.is_premium
                      ? subStatus.cancel_at_period_end
                        ? `Access until ${formatDate(subStatus.current_period_end)}`
                        : `Renews on ${formatDate(subStatus.current_period_end || subStatus.subscription_expires_at)}`
                      : 'Upgrade to unlock premium features'}
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-3">
                {subStatus.is_premium && !subStatus.cancel_at_period_end && (
                  <button
                    onClick={handleCancel}
                    disabled={cancelling}
                    className="btn btn-ghost btn-sm text-[var(--clr-danger)] hover:bg-[var(--clr-danger-dim)]"
                  >
                    {cancelling ? (
                      <span className="flex items-center gap-2">
                        <span className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
                        Cancelling…
                      </span>
                    ) : (
                      'Cancel Plan'
                    )}
                  </button>
                )}
              </div>
            </div>

            {/* Subscription details grid */}
            {subStatus.is_premium && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-[var(--clr-glass-border)]">
                <div>
                  <p className="text-[var(--clr-text-muted)] text-xs uppercase tracking-wider">Status</p>
                  <p className="text-white font-medium mt-1">
                    {subStatus.cancel_at_period_end ? 'Cancelling' : 'Active'}
                  </p>
                </div>
                <div>
                  <p className="text-[var(--clr-text-muted)] text-xs uppercase tracking-wider">Tier</p>
                  <p className="font-medium mt-1" style={{ color: tierColor(subStatus.subscription_tier) }}>
                    {tierName(subStatus.subscription_tier)}
                  </p>
                </div>
                <div>
                  <p className="text-[var(--clr-text-muted)] text-xs uppercase tracking-wider">
                    {subStatus.cancel_at_period_end ? 'Access Until' : 'Next Renewal'}
                  </p>
                  <p className="text-white font-medium mt-1">
                    {formatDate(subStatus.current_period_end || subStatus.subscription_expires_at)}
                  </p>
                </div>
                <div>
                  <p className="text-[var(--clr-text-muted)] text-xs uppercase tracking-wider">Payment</p>
                  <p className="text-white font-medium mt-1">
                    <Icon name="credit-card" size={14} className="inline mr-1 opacity-60" />
                    Card via Stripe
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ═══ Pricing Cards ═══ */}
        <div className="animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          <h2 className="font-display text-2xl font-bold text-white mb-2">
            {subStatus?.is_premium ? 'Change Your Plan' : 'Choose Your Plan'}
          </h2>
          <p className="text-[var(--clr-text-secondary)] mb-6">
            International card payments powered by Stripe. All prices in PKR.
          </p>
          <PricingCards
            currentTier={subStatus?.subscription_tier || 'free'}
            onError={setError}
          />
        </div>
      </div>
    </div>
  );
}

export default function SubscriptionPage() {
  return (
    <ProtectedRoute>
      <SubscriptionContent />
    </ProtectedRoute>
  );
}
