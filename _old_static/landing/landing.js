/**
 * PPSC CRACK — Landing Page
 * ============================================================
 * Renders all dynamic content from centralized mock data.
 * Replace mock data imports with API calls when backend is ready.
 * ============================================================
 */

import {
  HERO_STATS, FEATURES, PRICING_PLANS,
  TESTIMONIALS, APP_CONFIG
} from '../assets/js/data/mock-data.js';

import { icon } from '../assets/js/components/icons.js';

// ──────────────────────────────────────────────
// NAVBAR SCROLL BEHAVIOR
// ──────────────────────────────────────────────
function initNavbar() {
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 20);
  }, { passive: true });

  // Mobile toggle (placeholder for future mobile menu)
  const toggle = document.getElementById('mobileToggle');
  const menuIconEl = document.getElementById('menuIcon');
  if (menuIconEl) menuIconEl.innerHTML = icon('menu', { size: 22 });
}

// ──────────────────────────────────────────────
// HERO BADGE
// ──────────────────────────────────────────────
function renderHeroBadge() {
  const el = document.getElementById('heroBadge');
  if (!el) return;
  el.innerHTML = `${icon('zap', { size: 12 })} Pakistan's #1 AI Exam Platform`;
}

// ──────────────────────────────────────────────
// ZAP ICON IN HERO CTA
// ──────────────────────────────────────────────
function renderHeroCTAIcon() {
  const el = document.getElementById('zapIcon');
  if (el) el.outerHTML = icon('zap', { size: 16 });
}

// ──────────────────────────────────────────────
// HERO STATS
// ──────────────────────────────────────────────
function renderHeroStats() {
  const container = document.getElementById('heroStats');
  if (!container) return;

  container.innerHTML = HERO_STATS.map(stat => `
    <div class="glass glass-sm hero-stat">
      <div class="hero-stat-value">${stat.value}</div>
      <div class="hero-stat-label">${stat.label}</div>
    </div>
  `).join('');
}

// ──────────────────────────────────────────────
// PROBLEM / SOLUTION LISTS
// ──────────────────────────────────────────────
const PROBLEMS = [
  'Studying 10 subjects with no strategy',
  'Wasting months on never-tested topics',
  'Zero pattern intelligence from guide books',
  'No idea which topics repeat most',
];

const SOLUTIONS = [
  'Know exactly which topics appear most often',
  'AI-generated personalized study path',
  'Story documents that replace memorization',
  'Daily predictions updated with new papers',
];

function renderProblemSolution() {
  const problemList = document.getElementById('problemList');
  const solutionList = document.getElementById('solutionList');

  if (problemList) {
    problemList.innerHTML = PROBLEMS.map(text => `
      <div class="problem-item">
        <div class="problem-item-icon">
          ${icon('x', { size: 14, color: 'var(--clr-danger)' })}
        </div>
        <span class="list-item-text">${text}</span>
      </div>
    `).join('');
  }

  if (solutionList) {
    solutionList.innerHTML = SOLUTIONS.map(text => `
      <div class="solution-item">
        <div class="solution-item-icon">
          ${icon('check', { size: 14, color: 'var(--clr-success)' })}
        </div>
        <span class="list-item-text">${text}</span>
      </div>
    `).join('');
  }
}

// ──────────────────────────────────────────────
// FEATURES GRID
// ──────────────────────────────────────────────
function renderFeatures() {
  const container = document.getElementById('featuresGrid');
  if (!container) return;

  const colorMap = {
    primary: 'var(--clr-primary)',
    gold:    'var(--clr-gold)',
    success: 'var(--clr-success)',
    warning: 'var(--clr-warning)',
  };

  container.innerHTML = FEATURES.map((f, i) => `
    <div class="glass feature-card animate-fade-in-up" style="animation-delay:${i * 80}ms">
      <div class="feature-icon-wrap ${f.color}">
        ${icon(f.icon, { size: 22, color: colorMap[f.color] })}
      </div>
      <h3 class="feature-title">${f.title}</h3>
      <p class="feature-desc">${f.desc}</p>
    </div>
  `).join('');
}

// ──────────────────────────────────────────────
// HOW IT WORKS STEPS
// ──────────────────────────────────────────────
const STEPS = [
  { n: '01', title: 'Choose Your Job',    desc: 'Select your target position: Clerk, ASI, Tehsildar, Teacher, Inspector or more.' },
  { n: '02', title: 'AI Analyzes Papers', desc: 'Our engine processes 500+ past papers for your specific job to map every topic and frequency.' },
  { n: '03', title: 'Get Your Roadmap',   desc: 'Receive a personalized study path showing what to study, in what order, and what to skip.' },
  { n: '04', title: 'Ace the Exam',       desc: 'Study smarter with AI predictions, story documents, and daily current affairs updates.' },
];

function renderSteps() {
  const container = document.getElementById('stepsGrid');
  if (!container) return;

  container.innerHTML = STEPS.map((s, i) => `
    <div class="glass step-card animate-fade-in-up" style="animation-delay:${i * 100}ms">
      <div class="step-number">${s.n}</div>
      <h3 class="step-title">${s.title}</h3>
      <p class="step-desc">${s.desc}</p>
    </div>
  `).join('');
}

// ──────────────────────────────────────────────
// PRICING
// ──────────────────────────────────────────────
function renderPricing() {
  const container = document.getElementById('pricingGrid');
  if (!container) return;

  container.innerHTML = PRICING_PLANS.map(plan => {
    const isFeatured = plan.id === 'pro';
    const isGold     = plan.id === 'elite';
    const cardClass  = isFeatured ? 'featured' : isGold ? 'featured-gold' : '';
    const btnClass   = plan.variant === 'primary' ? 'btn-primary'
                      : plan.variant === 'gold'    ? 'btn-gold'
                      : 'btn-ghost';
    const priceHTML  = plan.price === 0
      ? `<span class="pricing-amount">Free</span>`
      : `<span class="pricing-currency">Rs</span><span class="pricing-amount">${plan.price}</span><span class="pricing-period">/${plan.period}</span>`;

    return `
      <div class="glass pricing-card ${cardClass}">
        ${plan.tag ? `<div class="pricing-tag badge ${isFeatured ? 'badge-primary' : 'badge-gold'}">${plan.tag}</div>` : ''}
        <div class="pricing-name">${plan.name}</div>
        <div class="pricing-price">${priceHTML}</div>
        <hr class="divider pricing-divider" />
        <div class="pricing-features">
          ${plan.features.map(f => `
            <div class="pricing-feature">
              ${icon('check', { size: 14, color: isFeatured ? 'var(--clr-primary)' : isGold ? 'var(--clr-gold)' : 'var(--clr-success)' })}
              ${f}
            </div>
          `).join('')}
        </div>
        <a href="#" class="btn ${btnClass}" style="width:100%;justify-content:center">${plan.cta}</a>
      </div>
    `;
  }).join('');
}

// ──────────────────────────────────────────────
// TESTIMONIALS
// ──────────────────────────────────────────────
function renderTestimonials() {
  const container = document.getElementById('testimonialsGrid');
  if (!container) return;

  container.innerHTML = TESTIMONIALS.map((t, i) => `
    <div class="glass testimonial-card animate-fade-in-up" style="animation-delay:${i * 100}ms">
      <p class="testimonial-quote">${t.text}</p>
      <div class="testimonial-author">
        <div class="avatar avatar-md"
          style="background: ${t.color}22; color: ${t.color}; border: 1px solid ${t.color}44;">
          ${t.initials}
        </div>
        <div>
          <div class="testimonial-name">${t.name}</div>
          <div class="testimonial-role">${icon('check', {size: 10, color: 'var(--clr-success)'})} ${t.role}</div>
        </div>
      </div>
    </div>
  `).join('');
}

// ──────────────────────────────────────────────
// INTERSECTION OBSERVER — animate on scroll
// ──────────────────────────────────────────────
function initScrollAnimations() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
  );

  // Observe all animate-fade-in-up elements that aren't in the hero
  document.querySelectorAll('.section .animate-fade-in-up').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = `opacity 400ms cubic-bezier(0.22,1,0.36,1), transform 400ms cubic-bezier(0.22,1,0.36,1)`;
    observer.observe(el);
  });
}

// ──────────────────────────────────────────────
// INIT
// ──────────────────────────────────────────────
function init() {
  initNavbar();
  renderHeroBadge();
  renderHeroStats();
  renderProblemSolution();
  renderFeatures();
  renderSteps();
  renderPricing();
  renderTestimonials();

  // Small delay to let DOM paint before setting up observers
  requestAnimationFrame(() => initScrollAnimations());

  document.title = `${APP_CONFIG.name} — ${APP_CONFIG.tagline}`;
}

document.addEventListener('DOMContentLoaded', init);
