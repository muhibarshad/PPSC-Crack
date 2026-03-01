/**
 * PricingCards — Stripe + JazzCash/Easypaisa subscription pricing component
 * ============================================================================
 * Displays Basic & Pro tiers with monthly/annual toggle.
 * Supports Stripe (card) or JazzCash/Easypaisa mobile wallet checkout.
 */

'use client';

import { useEffect, useState, useRef } from 'react';
import { useAuthStore } from '@/store/auth-store';
import Icon from '@/components/Icon';

/* ── Types ── */

interface PricingPlan {
  tier: string;
  name: string;
  monthly_price: number;
  annual_price: number;
  monthly_price_id: string;
  annual_price_id: string;
  features: string[];
}

type PaymentProvider = 'stripe' | 'jazzcash';

interface PricingCardsProps {
  currentTier?: string;
  onError?: (msg: string) => void;
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

/* ── Component ── */

export default function PricingCards({ currentTier = 'free', onError }: PricingCardsProps) {
  const { session } = useAuthStore();
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [isAnnual, setIsAnnual] = useState(false);
  const [loadingTier, setLoadingTier] = useState<string | null>(null);
  const [plansLoading, setPlansLoading] = useState(true);
  const [provider, setProvider] = useState<PaymentProvider>('stripe');
  const jazzcashFormRef = useRef<HTMLFormElement>(null);

  // Fetch plans
  useEffect(() => {
    async function load() {
      try {
        const data = await fetch(`${API}/payments/plans`).then((r) => r.json());
        setPlans(data.plans || []);
      } catch {
        // fallback hardcoded plans
        setPlans([
          {
            tier: 'basic',
            name: 'Basic',
            monthly_price: 499,
            annual_price: 4190,
            monthly_price_id: '',
            annual_price_id: '',
            features: [
              'Access to all past papers',
              'Basic AI predictions',
              'Topic-wise study material',
              'Daily current affairs',
              'Practice tests',
            ],
          },
          {
            tier: 'pro',
            name: 'Pro',
            monthly_price: 999,
            annual_price: 8390,
            monthly_price_id: '',
            annual_price_id: '',
            features: [
              'Everything in Basic',
              'Advanced AI predictions',
              'Priority pattern analytics',
              'Personalized learning path',
              'Predicted paper generation',
              'Premium story-based learning',
              'Priority support',
            ],
          },
        ]);
      } finally {
        setPlansLoading(false);
      }
    }
    load();
  }, []);

  // Handle checkout
  const handleCheckout = async (plan: PricingPlan) => {
    const token = session?.access_token;
    if (!token) {
      onError?.('Please log in to subscribe.');
      return;
    }

    const priceId = isAnnual ? plan.annual_price_id : plan.monthly_price_id;
    if (!priceId) {
      onError?.('This plan is not available yet. Please contact support.');
      return;
    }

    try {
      setLoadingTier(plan.tier);
      const data = await apiFetch<{
        checkout_url: string;
        provider: string;
        form_data?: { action_url: string; fields: Record<string, string> };
      }>(
        '/payments/create-session',
        token,
        {
          method: 'POST',
          body: JSON.stringify({ price_id: priceId, provider }),
        },
      );

      if (provider === 'jazzcash' && data.form_data) {
        // JazzCash: submit hidden form
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = data.form_data.action_url;
        for (const [key, value] of Object.entries(data.form_data.fields)) {
          const input = document.createElement('input');
          input.type = 'hidden';
          input.name = key;
          input.value = value;
          form.appendChild(input);
        }
        document.body.appendChild(form);
        form.submit();
      } else {
        // Stripe: redirect to hosted checkout
        window.location.href = data.checkout_url;
      }
    } catch (err: unknown) {
      onError?.(err instanceof Error ? err.message : 'Failed to start checkout');
      setLoadingTier(null);
    }
  };

  const formatPrice = (amount: number) => {
    return new Intl.NumberFormat('en-PK').format(amount);
  };

  if (plansLoading) {
    return (
      <div className="grid md:grid-cols-2 gap-6">
        {[1, 2].map((i) => (
          <div key={i} className="glass p-6 animate-pulse">
            <div className="h-6 bg-white/5 rounded w-24 mb-4" />
            <div className="h-10 bg-white/5 rounded w-32 mb-6" />
            <div className="space-y-3">
              {[1, 2, 3, 4].map((j) => (
                <div key={j} className="h-4 bg-white/5 rounded w-full" />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* ═══ Monthly / Annual Toggle ═══ */}
      <div className="flex items-center justify-center gap-3">
        <span
          className={`text-sm font-medium transition-colors ${
            !isAnnual ? 'text-white' : 'text-[var(--clr-text-muted)]'
          }`}
        >
          Monthly
        </span>
        <button
          onClick={() => setIsAnnual(!isAnnual)}
          className={`relative w-14 h-7 rounded-full transition-colors ${
            isAnnual
              ? 'bg-[var(--clr-primary-vivid)]'
              : 'bg-[var(--clr-bg-elevated)]'
          }`}
        >
          <div
            className={`absolute top-0.5 w-6 h-6 rounded-full bg-white shadow transition-transform ${
              isAnnual ? 'translate-x-7' : 'translate-x-0.5'
            }`}
          />
        </button>
        <span
          className={`text-sm font-medium transition-colors ${
            isAnnual ? 'text-white' : 'text-[var(--clr-text-muted)]'
          }`}
        >
          Annual
        </span>
        {isAnnual && (
          <span className="badge bg-[var(--clr-success-dim)] text-[var(--clr-success)] text-xs ml-1">
            Save 30%
          </span>
        )}
      </div>

      {/* ═══ Payment Method Selector ═══ */}
      <div className="flex items-center justify-center gap-2 p-1 rounded-2xl bg-[var(--clr-bg-elevated)] border border-[var(--clr-glass-border)] w-fit mx-auto">
        <button
          onClick={() => setProvider('stripe')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
            provider === 'stripe'
              ? 'bg-[var(--clr-primary-vivid)]/20 text-white border border-[var(--clr-primary-vivid)]/40'
              : 'text-[var(--clr-text-muted)] hover:text-white'
          }`}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
            <line x1="1" y1="10" x2="23" y2="10" />
          </svg>
          Card (Stripe)
        </button>
        <button
          onClick={() => setProvider('jazzcash')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
            provider === 'jazzcash'
              ? 'bg-[#e2136e]/20 text-[#e2136e] border border-[#e2136e]/40'
              : 'text-[var(--clr-text-muted)] hover:text-white'
          }`}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
            <line x1="12" y1="18" x2="12.01" y2="18" />
          </svg>
          JazzCash / Easypaisa
        </button>
      </div>

      {/* ═══ Plan Cards ═══ */}
      <div className="grid md:grid-cols-2 gap-6">
        {plans.map((plan) => {
          const isCurrentPlan = currentTier === plan.tier;
          const isPro = plan.tier === 'pro';
          const price = isAnnual ? plan.annual_price : plan.monthly_price;
          const period = isAnnual ? '/year' : '/month';

          return (
            <div
              key={plan.tier}
              className={`glass relative overflow-hidden p-6 md:p-8 transition-all duration-300 hover:border-[var(--clr-glass-border-hover)] ${
                isPro ? 'border border-[var(--clr-gold)]/20' : ''
              }`}
            >
              {/* Popular badge */}
              {isPro && (
                <div className="absolute top-0 right-0">
                  <div
                    className="px-4 py-1 text-xs font-bold uppercase tracking-wider"
                    style={{
                      background: 'var(--grad-gold)',
                      color: 'var(--clr-text-inverse)',
                      borderRadius: '0 var(--radius-md) 0 var(--radius-md)',
                    }}
                  >
                    Most Popular
                  </div>
                </div>
              )}

              {/* Plan header */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                  <Icon
                    name={isPro ? 'star' : 'zap'}
                    size={20}
                    color={isPro ? 'var(--clr-gold)' : 'var(--clr-accent)'}
                  />
                  <h3 className="font-display text-xl font-bold text-white">{plan.name}</h3>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-[var(--clr-text-muted)] text-sm">Rs</span>
                  <span
                    className="font-display text-4xl font-bold"
                    style={{ color: isPro ? 'var(--clr-gold)' : 'var(--clr-accent)' }}
                  >
                    {formatPrice(price)}
                  </span>
                  <span className="text-[var(--clr-text-muted)] text-sm">{period}</span>
                </div>
                {isAnnual && (
                  <p className="text-[var(--clr-success)] text-xs mt-1">
                    Save Rs {formatPrice(plan.monthly_price * 12 - plan.annual_price)} vs monthly
                  </p>
                )}
              </div>

              {/* Features list */}
              <ul className="flex flex-col gap-3 mb-8">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-sm">
                    <Icon
                      name="check"
                      size={16}
                      color={isPro ? 'var(--clr-gold)' : 'var(--clr-success)'}
                      className="shrink-0 mt-0.5"
                    />
                    <span className="text-[var(--clr-text-secondary)]">{feature}</span>
                  </li>
                ))}
              </ul>

              {/* CTA button */}
              {isCurrentPlan ? (
                <button
                  disabled
                  className="w-full py-3 rounded-xl font-semibold text-sm bg-[var(--clr-bg-elevated)] text-[var(--clr-text-muted)] cursor-not-allowed"
                >
                  Current Plan
                </button>
              ) : (
                <button
                  onClick={() => handleCheckout(plan)}
                  disabled={loadingTier === plan.tier}
                  className={`w-full py-3 rounded-xl font-semibold text-sm transition-all duration-200 ${
                    isPro
                      ? 'text-[var(--clr-text-inverse)] hover:opacity-90'
                      : 'btn btn-primary'
                  }`}
                  style={
                    isPro
                      ? { background: 'var(--grad-gold)' }
                      : undefined
                  }
                >
                  {loadingTier === plan.tier ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
                      {provider === 'jazzcash' ? 'Redirecting to JazzCash…' : 'Redirecting to Stripe…'}
                    </span>
                  ) : currentTier !== 'free' ? (
                    `Switch to ${plan.name}`
                  ) : (
                    `Get ${plan.name}`
                  )}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* ═══ Footer note ═══ */}
      <p className="text-center text-[var(--clr-text-muted)] text-xs">
        <Icon name="lock" size={12} className="inline mr-1" />
        {provider === 'jazzcash'
          ? 'Secure payments via JazzCash / Easypaisa. Cancel anytime. Prices in Pakistani Rupees (PKR).'
          : 'Secure payments via Stripe. Cancel anytime. Prices in Pakistani Rupees (PKR).'}
      </p>
    </div>
  );
}
