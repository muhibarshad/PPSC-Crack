/**
 * PPSC CRACK — Mock Data Layer
 * ============================================================
 * Single source of truth for all mock/placeholder data.
 * When integrating a real backend, replace exports with API calls.
 * ============================================================
 */

export const APP_CONFIG = {
  name:         'PPSC Crack',
  tagline:      'AI-Powered Exam Domination System',
  version:      '1.0.0',
  currency:     'Rs',
  supportEmail: 'support@ppsccrack.pk',
};

export const HERO_STATS = [
  { value: '500+',   label: 'Past Papers Analyzed',  icon: 'file-text' },
  { value: '94%',    label: 'Prediction Accuracy',   icon: 'target'    },
  { value: '50,000', label: 'Students Enrolled',     icon: 'users'     },
  { value: '3x',     label: 'Faster Preparation',    icon: 'zap'       },
];

export const FEATURES = [
  {
    icon:  'brain',
    title: 'Pattern Intelligence Engine',
    desc:  'Analyzes 500+ past papers to detect exactly which topics repeat, how often, and what subtypes cluster together.',
    color: 'primary',
    tag:   'Core AI',
  },
  {
    icon:  'chart-line',
    title: 'Next-Paper Prediction',
    desc:  'Using RAG + GPT-4o, predict with high probability what topics will appear in your specific upcoming exam.',
    color: 'neon',
    tag:   'Prediction',
  },
  {
    icon:  'book-open',
    title: 'Story Document Engine',
    desc:  'Converts raw MCQs into flowing, narrative-style documents. Read like a story, retain like never before.',
    color: 'accent',
    tag:   'Learning',
  },
  {
    icon:  'newspaper',
    title: 'Daily Current Affairs',
    desc:  'Auto-updated pipeline that knows which type of news PPSC historically tests — you only read what matters.',
    color: 'warning',
    tag:   'Real-time',
  },
  {
    icon:  'target',
    title: 'Job-Specific Intelligence',
    desc:  'Separate AI models per job type: Clerk, ASI, Tehsildar, Teacher — your preparation is never generic again.',
    color: 'info',
    tag:   'Specialized',
  },
  {
    icon:  'route',
    title: 'Personalized Study Path',
    desc:  'See exactly what to study first, what to skip, and which topics give you the highest return on time.',
    color: 'gold',
    tag:   'Roadmap',
  },
];

export const STEPS = [
  {
    n:     '01',
    title: 'Choose Your Target Job',
    desc:  'Select your position: Clerk, ASI, Tehsildar, Teacher, Inspector or more. The AI customizes everything for you.',
    icon:  'target',
  },
  {
    n:     '02',
    title: 'AI Analyzes 500+ Papers',
    desc:  'Our engine processes hundreds of past papers for your specific job to map every topic, frequency, and pattern.',
    icon:  'cpu',
  },
  {
    n:     '03',
    title: 'Get Your Battle Plan',
    desc:  'Receive a personalized study roadmap showing what to study, in what order, and what to safely skip.',
    icon:  'route',
  },
  {
    n:     '04',
    title: 'Dominate the Exam',
    desc:  'Study smarter with AI predictions, story documents, and daily current affairs updates tailored to your exam.',
    icon:  'zap',
  },
];

export const PRICING_PLANS = [
  {
    id:       'free',
    name:     'Explorer',
    price:    0,
    period:   'forever',
    tag:      null,
    features: [
      '3 Past Papers / month',
      'Basic topic breakdown',
      'Limited AI predictions',
      'Community access',
    ],
    cta:      'Start Free',
    variant:  'ghost',
  },
  {
    id:       'pro',
    name:     'Pro',
    price:    499,
    period:   'month',
    tag:      'Most Popular',
    features: [
      'Unlimited Past Papers',
      'Full AI Pattern Analysis',
      'Story-style Learning Docs',
      'Next-Paper Predictions',
      'Daily Current Affairs',
      'Job-specific Intelligence',
    ],
    cta:      'Get Pro Access',
    variant:  'primary',
  },
  {
    id:       'elite',
    name:     'Elite',
    price:    999,
    period:   'month',
    tag:      'Best Results',
    features: [
      'Everything in Pro',
      'Priority AI Processing',
      'Personalized Study Roadmap',
      '1-on-1 Strategy Session',
      'Exam Day Prediction Bundle',
      'Early Access to New Features',
    ],
    cta:      'Go Elite',
    variant:  'gold',
  },
];

export const TESTIMONIALS = [
  {
    id:       1,
    name:     'Tariq Mehmood',
    role:     'Selected — ASI Punjab Police',
    initials: 'TM',
    color:    '#34d399',
    text:     'The prediction engine told me exactly which historical topics would appear. Three out of five predicted chapters came in the actual paper. I cleared in my first attempt.',
    rating:   5,
  },
  {
    id:       2,
    name:     'Aisha Butt',
    role:     'Selected — Tehsildar',
    initials: 'AB',
    color:    '#fbbf24',
    text:     'Story documents changed how I study. Instead of memorizing MCQs I actually understand the context. My retention went from 40% to nearly 90% in two weeks.',
    rating:   5,
  },
  {
    id:       3,
    name:     'Zain ul Abideen',
    role:     'Selected — PPSC Lecturer',
    initials: 'ZA',
    color:    '#22c55e',
    text:     'I had failed three times before PPSC Crack. The personalized study path showed me I was wasting time on topics with less than 2% frequency. Six weeks — done.',
    rating:   5,
  },
];

export const PROBLEMS = [
  'Studying 10 subjects with zero strategy',
  'Wasting 6-12 months on untested topics',
  'Zero pattern intelligence from guide books',
  'No idea which topics repeat every year',
];

export const SOLUTIONS = [
  'Know exactly which topics appear most often',
  'AI-generated personalized study path',
  'Story documents that replace memorization',
  'Daily predictions updated with new papers',
];

export const JOB_TYPES = [
  { id: 'clerk',       label: 'Clerk',          papersCount: 120 },
  { id: 'asi',         label: 'ASI',            papersCount: 85  },
  { id: 'tehsildar',   label: 'Tehsildar',      papersCount: 64  },
  { id: 'teacher',     label: 'Teacher',        papersCount: 97  },
  { id: 'inspector',   label: 'Inspector',      papersCount: 58  },
  { id: 'naib-tehsil', label: 'Naib Tehsildar', papersCount: 43  },
];

// ──────────────────────────────────────────────
// ADMIN DATA (for future admin pages)
// ──────────────────────────────────────────────
export const ADMIN_STATS = [
  { id: 'total_users',    label: 'Total Users',          value: 52840,    change: '+12.4%', trend: 'up',   period: 'vs last month', icon: 'users',       color: 'primary' },
  { id: 'active_subs',    label: 'Active Subscriptions', value: 8219,     change: '+8.1%',  trend: 'up',   period: 'vs last month', icon: 'credit-card', color: 'gold'    },
  { id: 'monthly_revenue',label: 'Monthly Revenue',      value: '₨ 5.2M', change: '+21.3%', trend: 'up',   period: 'vs last month', icon: 'trending-up', color: 'success' },
  { id: 'papers_uploaded', label: 'Papers Uploaded',      value: 512,      change: '+6',     trend: 'up',   period: 'this week',     icon: 'file-text',   color: 'warning' },
];

export const ADMIN_NAV = [
  { id: 'dashboard',   label: 'Dashboard',       icon: 'layout-dashboard', href: '/admin',            active: true  },
  { id: 'users',       label: 'Users',           icon: 'users',            href: '/admin/users',      active: false },
  { id: 'papers',      label: 'Papers',          icon: 'file-text',        href: '/admin/papers',     active: false },
  { id: 'predictions', label: 'Predictions',     icon: 'cpu',              href: '/admin/predictions',active: false },
  { id: 'current-aff', label: 'Current Affairs', icon: 'newspaper',        href: '/admin/affairs',    active: false },
  { id: 'payments',    label: 'Payments',        icon: 'credit-card',      href: '/admin/payments',   active: false },
  { id: 'settings',    label: 'Settings',        icon: 'settings',         href: '/admin/settings',   active: false },
];
