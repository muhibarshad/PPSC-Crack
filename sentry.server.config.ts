/**
 * Sentry Server-Side Configuration
 */

import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  enabled: process.env.NODE_ENV === 'production',
  tracesSampleRate: 0.2,
  environment: process.env.NODE_ENV,
  release: `ppsc-crack@${process.env.NEXT_PUBLIC_APP_VERSION || '0.1.0'}`,
});
