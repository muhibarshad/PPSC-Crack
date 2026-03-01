/**
 * PostHog Product Analytics
 * ==========================
 * Event tracking for user behavior analytics.
 */

import posthog from 'posthog-js';

let initialized = false;

export function initPostHog() {
  if (typeof window === 'undefined') return;
  if (initialized) return;

  const apiKey = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  const host = process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://us.i.posthog.com';

  if (!apiKey) {
    console.warn('[PostHog] No API key found. Analytics disabled.');
    return;
  }

  posthog.init(apiKey, {
    api_host: host,
    person_profiles: 'identified_only',
    capture_pageview: true,
    capture_pageleave: true,
    autocapture: false, // We track events explicitly
    persistence: 'localStorage+cookie',
    loaded: () => { initialized = true; },
  });
}

/** Identify a user after login */
export function identifyUser(userId: string, properties?: Record<string, any>) {
  if (typeof window === 'undefined') return;
  posthog.identify(userId, properties);
}

/** Reset on logout */
export function resetAnalytics() {
  if (typeof window === 'undefined') return;
  posthog.reset();
}

// ── Typed Event Tracking ──

export function trackUserRegistered(method: 'email' | 'google' | 'magic_link') {
  posthog.capture('user_registered', { method });
}

export function trackJobSelected(jobTypeId: string, jobTypeName: string) {
  posthog.capture('job_selected', { job_type_id: jobTypeId, job_type_name: jobTypeName });
}

export function trackTopicStarted(topicId: string, topicName: string) {
  posthog.capture('topic_started', { topic_id: topicId, topic_name: topicName });
}

export function trackTopicCompleted(topicId: string, topicName: string, timeMinutes: number) {
  posthog.capture('topic_completed', { topic_id: topicId, topic_name: topicName, time_minutes: timeMinutes });
}

export function trackPracticeTestSubmitted(score: number, totalQuestions: number, timeTaken: number) {
  posthog.capture('practice_test_submitted', { score, total_questions: totalQuestions, time_taken: timeTaken });
}

export function trackPredictionViewed(predictionId: string) {
  posthog.capture('prediction_viewed', { prediction_id: predictionId });
}

export function trackSubscriptionStarted(plan: string, billing: 'monthly' | 'annual') {
  posthog.capture('subscription_started', { plan, billing });
}

export function trackSubscriptionCancelled(plan: string, reason?: string) {
  posthog.capture('subscription_cancelled', { plan, reason });
}

export function trackPageView(pageName: string, properties?: Record<string, any>) {
  posthog.capture('$pageview', { page_name: pageName, ...properties });
}

export default posthog;
