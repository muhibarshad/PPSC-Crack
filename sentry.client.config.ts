/**
 * Sentry Client-Side Configuration
 * ==================================
 * Captures: unhandled exceptions, API errors, failed AI calls, payment failures.
 */

import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  enabled: process.env.NODE_ENV === 'production',

  // Performance
  tracesSampleRate: 0.2,
  profilesSampleRate: 0.1,

  // Replay (session recording for error context)
  replaysSessionSampleRate: 0.05,
  replaysOnErrorSampleRate: 1.0,

  // Environment
  environment: process.env.NODE_ENV,
  release: `ppsc-crack@${process.env.NEXT_PUBLIC_APP_VERSION || '0.1.0'}`,

  // Filter noise
  ignoreErrors: [
    'ResizeObserver loop',
    'Non-Error promise rejection captured',
    /Loading chunk \d+ failed/,
  ],

  integrations: [
    Sentry.replayIntegration(),
    Sentry.browserTracingIntegration(),
  ],

  beforeSend(event) {
    // Tag payment and AI errors for alerting
    if (event.exception?.values?.some(v => v.value?.includes('stripe') || v.value?.includes('payment'))) {
      event.tags = { ...event.tags, category: 'payment_failure' };
      event.level = 'fatal';
    }
    if (event.exception?.values?.some(v => v.value?.includes('openai') || v.value?.includes('AI'))) {
      event.tags = { ...event.tags, category: 'ai_failure' };
    }
    return event;
  },
});
