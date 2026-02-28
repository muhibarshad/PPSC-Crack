/**
 * PPSC CRACK — Mock Data
 * ============================================================
 * SINGLE SOURCE OF TRUTH for all mock/placeholder data.
 *
 * When integrating a real backend:
 *   1. Replace each exported object/array with an API call.
 *   2. Keep the same shape — components depend on these keys.
 *   3. e.g.  export const stats = await api.get('/admin/stats');
 * ============================================================
 */

// ──────────────────────────────────────────────
// APP CONFIG
// ──────────────────────────────────────────────
export const APP_CONFIG = {
  name:       'PPSC Crack',
  tagline:    'AI-Powered Exam Domination System',
  version:    '1.0.0',
  currency:   'Rs',
  supportEmail: 'support@ppsccrack.pk',
};

// ──────────────────────────────────────────────
// PRICING PLANS
// ──────────────────────────────────────────────
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

// ──────────────────────────────────────────────
// FEATURES (Landing Page)
// ──────────────────────────────────────────────
export const FEATURES = [
  {
    icon:  'brain',
    title: 'Pattern Intelligence Engine',
    desc:  'Analyzes 500+ past papers to detect exactly which topics repeat, how often, and what subtypes cluster together across job roles.',
    color: 'primary',
  },
  {
    icon:  'chart-line',
    title: 'Next-Paper Prediction',
    desc:  'Using RAG + GPT-4o, PPSC Crack predicts with high probability what topics will appear in your specific upcoming exam.',
    color: 'gold',
  },
  {
    icon:  'book-open',
    title: 'Story Document Engine',
    desc:  'Converts raw MCQs into flowing, narrative-style learning documents. Read like a story, retain like never before.',
    color: 'success',
  },
  {
    icon:  'newspaper',
    title: 'Daily Current Affairs',
    desc:  'Auto-updated pipeline that knows exactly which type of news PPSC historically tests — so you only read what matters.',
    color: 'warning',
  },
  {
    icon:  'target',
    title: 'Job-specific Intelligence',
    desc:  'Separate AI models trained per job type: Clerk, ASI, Tehsildar, Teacher — your preparation is never generic again.',
    color: 'primary',
  },
  {
    icon:  'route',
    title: 'Personalized Study Path',
    desc:  'See exactly what to study first, what to skip, and which topics give you the highest return on your time.',
    color: 'gold',
  },
];

// ──────────────────────────────────────────────
// STATS (Landing Hero)
// ──────────────────────────────────────────────
export const HERO_STATS = [
  { value: '500+',   label: 'Past Papers Analyzed' },
  { value: '94%',    label: 'Prediction Accuracy' },
  { value: '50,000', label: 'Students Enrolled' },
  { value: '3x',     label: 'Faster Preparation' },
];

// ──────────────────────────────────────────────
// TESTIMONIALS (Landing)
// ──────────────────────────────────────────────
export const TESTIMONIALS = [
  {
    id:     1,
    name:   'Tariq Mehmood',
    role:   'Selected — ASI Punjab Police',
    initials: 'TM',
    color:  '#00C2FF',
    text:   'The prediction engine told me exactly which historical topics would appear. Three out of five predicted chapters came in the actual paper. I cleared in my first attempt.',
  },
  {
    id:     2,
    name:   'Aisha Butt',
    role:   'Selected — Tehsildar',
    initials: 'AB',
    color:  '#FFB800',
    text:   'Story documents changed how I study. Instead of memorizing MCQs I actually understand the context. My retention went from 40% to nearly 90% in two weeks.',
  },
  {
    id:     3,
    name:   'Zain ul Abideen',
    role:   'Selected — PPSC Lecturer',
    initials: 'ZA',
    color:  '#00E5A0',
    text:   'I had failed three times before PPSC Crack. The personalized study path showed me I was wasting time on topics with less than 2% paper frequency. Six weeks of focused prep — done.',
  },
];

// ──────────────────────────────────────────────
// JOB TYPES
// ──────────────────────────────────────────────
export const JOB_TYPES = [
  { id: 'clerk',       label: 'Clerk',         papersCount: 120 },
  { id: 'asi',         label: 'ASI',           papersCount: 85  },
  { id: 'tehsildar',   label: 'Tehsildar',     papersCount: 64  },
  { id: 'teacher',     label: 'Teacher',       papersCount: 97  },
  { id: 'inspector',   label: 'Inspector',     papersCount: 58  },
  { id: 'naib-tehsil', label: 'Naib Tehsildar', papersCount: 43 },
];

// ──────────────────────────────────────────────
// ADMIN — OVERVIEW STATS
// ──────────────────────────────────────────────
export const ADMIN_STATS = [
  {
    id:      'total_users',
    label:   'Total Users',
    value:   52_840,
    change:  '+12.4%',
    trend:   'up',
    period:  'vs last month',
    icon:    'users',
    color:   'primary',
  },
  {
    id:      'active_subs',
    label:   'Active Subscriptions',
    value:   8_219,
    change:  '+8.1%',
    trend:   'up',
    period:  'vs last month',
    icon:    'credit-card',
    color:   'gold',
  },
  {
    id:      'monthly_revenue',
    label:   'Monthly Revenue',
    value:   '₨ 5.2M',
    change:  '+21.3%',
    trend:   'up',
    period:  'vs last month',
    icon:    'trending-up',
    color:   'success',
  },
  {
    id:      'papers_uploaded',
    label:   'Papers Uploaded',
    value:   512,
    change:  '+6',
    trend:   'up',
    period:  'this week',
    icon:    'file-text',
    color:   'warning',
  },
];

// ──────────────────────────────────────────────
// ADMIN — RECENT USERS TABLE
// ──────────────────────────────────────────────
export const RECENT_USERS = [
  { id: 'u001', name: 'Ali Hassan',      email: 'ali.hassan@gmail.com',    plan: 'pro',   status: 'active',    joined: '2025-01-28', initials: 'AH', color: '#00C2FF' },
  { id: 'u002', name: 'Sara Noor',       email: 'sara.noor@outlook.com',   plan: 'elite', status: 'active',    joined: '2025-01-27', initials: 'SN', color: '#FFB800' },
  { id: 'u003', name: 'Usman Khalid',    email: 'usman.k@yahoo.com',       plan: 'free',  status: 'active',    joined: '2025-01-27', initials: 'UK', color: '#00E5A0' },
  { id: 'u004', name: 'Fatima Zahra',    email: 'fatima.z@gmail.com',      plan: 'pro',   status: 'active',    joined: '2025-01-26', initials: 'FZ', color: '#FF8C42' },
  { id: 'u005', name: 'Bilal Ahmed',     email: 'bilal.ahmed@proton.me',   plan: 'pro',   status: 'suspended', joined: '2025-01-25', initials: 'BA', color: '#FF4D6D' },
  { id: 'u006', name: 'Hina Malik',      email: 'hina.m@gmail.com',        plan: 'elite', status: 'active',    joined: '2025-01-25', initials: 'HM', color: '#A78BFA' },
  { id: 'u007', name: 'Kashif Raza',     email: 'kashif.raza@live.com',    plan: 'free',  status: 'active',    joined: '2025-01-24', initials: 'KR', color: '#34D399' },
  { id: 'u008', name: 'Zara Siddiqui',   email: 'zara.s@gmail.com',        plan: 'pro',   status: 'active',    joined: '2025-01-23', initials: 'ZS', color: '#60A5FA' },
];

// ──────────────────────────────────────────────
// ADMIN — RECENT ACTIVITY LOG
// ──────────────────────────────────────────────
export const ACTIVITY_LOG = [
  { id: 1, type: 'upload',  icon: 'upload',      message: 'New paper uploaded: ASI Punjab 2024-B',          time: '2 min ago',    color: 'success'  },
  { id: 2, type: 'user',    icon: 'user-plus',   message: 'New user registered: Ali Hassan (Pro plan)',     time: '8 min ago',    color: 'primary'  },
  { id: 3, type: 'payment', icon: 'credit-card', message: 'Payment received: Rs 999 — Hina Malik (Elite)',  time: '15 min ago',   color: 'gold'     },
  { id: 4, type: 'ai',      icon: 'cpu',         message: 'Prediction engine updated — Tehsildar model',    time: '42 min ago',   color: 'warning'  },
  { id: 5, type: 'user',    icon: 'user-plus',   message: 'New user registered: Kashif Raza (Free plan)',   time: '1 hr ago',     color: 'primary'  },
  { id: 6, type: 'system',  icon: 'refresh-cw',  message: 'Daily current affairs pipeline completed',       time: '2 hr ago',     color: 'success'  },
  { id: 7, type: 'payment', icon: 'credit-card', message: 'Payment received: Rs 499 — Usman Khalid (Pro)', time: '3 hr ago',     color: 'gold'     },
  { id: 8, type: 'alert',   icon: 'alert-circle', message: 'User Bilal Ahmed account flagged for review',  time: '5 hr ago',     color: 'danger'   },
];

// ──────────────────────────────────────────────
// ADMIN — REVENUE CHART DATA (last 7 days)
// ──────────────────────────────────────────────
export const REVENUE_CHART = [
  { day: 'Mon', revenue: 320_000, users: 48  },
  { day: 'Tue', revenue: 410_000, users: 62  },
  { day: 'Wed', revenue: 375_000, users: 55  },
  { day: 'Thu', revenue: 490_000, users: 74  },
  { day: 'Fri', revenue: 620_000, users: 91  },
  { day: 'Sat', revenue: 580_000, users: 86  },
  { day: 'Sun', revenue: 520_000, users: 79  },
];

// ──────────────────────────────────────────────
// ADMIN — PLAN DISTRIBUTION
// ──────────────────────────────────────────────
export const PLAN_DISTRIBUTION = [
  { plan: 'Free',  users: 44_621, pct: 84.5, color: '#8896B0' },
  { plan: 'Pro',   users:  6_884, pct: 13.0, color: '#00C2FF' },
  { plan: 'Elite', users:  1_335, pct:  2.5, color: '#FFB800' },
];

// ──────────────────────────────────────────────
// ADMIN — TOP SUBJECTS BY FREQUENCY
// ──────────────────────────────────────────────
export const SUBJECT_FREQUENCY = [
  { subject: 'Pakistan Studies',   frequency: 28, change: '+2%'  },
  { subject: 'Islamic Studies',    frequency: 22, change: '+0%'  },
  { subject: 'English',            frequency: 18, change: '+3%'  },
  { subject: 'General Knowledge',  frequency: 15, change: '-1%'  },
  { subject: 'Urdu',               frequency: 10, change: '+1%'  },
  { subject: 'Mathematics',        frequency: 7,  change: '+0%'  },
];

// ──────────────────────────────────────────────
// ADMIN — NAV ITEMS
// ──────────────────────────────────────────────
export const ADMIN_NAV = [
  { id: 'dashboard',    label: 'Dashboard',       icon: 'layout-dashboard', href: '#dashboard',   active: true  },
  { id: 'users',        label: 'Users',           icon: 'users',            href: '#users',        active: false },
  { id: 'papers',       label: 'Papers',          icon: 'file-text',        href: '#papers',       active: false },
  { id: 'predictions',  label: 'Predictions',     icon: 'cpu',              href: '#predictions',  active: false },
  { id: 'current-aff', label: 'Current Affairs', icon: 'newspaper',        href: '#current-aff',  active: false },
  { id: 'payments',     label: 'Payments',        icon: 'credit-card',      href: '#payments',     active: false },
  { id: 'settings',     label: 'Settings',        icon: 'settings',         href: '#settings',     active: false },
];
