import { withSentryConfig } from '@sentry/nextjs';

/** @type {import('next').NextConfig} */
const nextConfig = {
  /* ── Proxy API requests to FastAPI backend ── */
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },

  /* ── Image optimization with Sharp ── */
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      { protocol: 'https', hostname: '**.supabase.co' },
      { protocol: 'https', hostname: '**.ppsc-crack.pk' },
    ],
  },
};

// Wrap with Sentry only when DSN is set
const sentryConfig = {
  org: process.env.SENTRY_ORG || '',
  project: process.env.SENTRY_PROJECT || '',
  silent: !process.env.CI,
  widenClientFileUpload: true,
  hideSourceMaps: true,
  disableLogger: true,
  automaticVercelMonitors: true,
  tunnelRoute: '/monitoring',
};

export default process.env.NEXT_PUBLIC_SENTRY_DSN
  ? withSentryConfig(nextConfig, sentryConfig)
  : nextConfig;
