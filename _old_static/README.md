# PPSC Crack — Frontend
**AI-Powered Exam Domination System**

---

## Project Structure

```
ppsc-crack/
│
├── index.html                      # Root → redirects to /landing/
│
├── assets/
│   ├── css/
│   │   ├── design-tokens.css       # ★ CSS variables (colors, fonts, spacing, radii)
│   │   └── base.css                # Reset, body, utilities, components (glass, btn, badge)
│   └── js/
│       ├── data/
│       │   └── mock-data.js        # ★ ALL mock data — replace with API calls here
│       ├── utils/
│       │   └── helpers.js          # Pure utility functions (format, sanitize, etc.)
│       └── components/
│           └── icons.js            # SVG icon renderer (add new icons here)
│
├── landing/
│   ├── index.html                  # Landing page markup
│   ├── landing.css                 # Landing-specific styles
│   └── landing.js                  # Landing page renderer (reads from mock-data.js)
│
└── admin/
    ├── index.html                  # Admin dashboard markup
    ├── admin.css                   # Admin-specific styles
    └── admin.js                    # Admin renderer (reads from mock-data.js)
```

---

## Design System

**Theme:** Liquid Glass Glassmorphism — Dark Mode  
**Fonts:** Syne (display) + Plus Jakarta Sans (body)  
**Colors:** Electric Cyan (`#00C2FF`) + Amber Gold (`#FFB800`)

All design decisions live in `assets/css/design-tokens.css`.  
Change a token once → updates everywhere.

---

## Integrating the Backend

### Step 1 — Open `assets/js/data/mock-data.js`

Every exported constant maps 1:1 to a backend endpoint. Replace each with an async fetch:

```js
// BEFORE (mock)
export const ADMIN_STATS = [ { id: 'total_users', value: 52840, ... } ];

// AFTER (real API)
export async function getAdminStats() {
  const res = await fetch('/api/admin/stats', {
    headers: { Authorization: `Bearer ${getToken()}` }
  });
  return res.json();
}
```

### Step 2 — Update the page renderers

In `admin/admin.js` and `landing/landing.js`, change:

```js
// BEFORE
import { ADMIN_STATS } from '../assets/js/data/mock-data.js';

// AFTER
import { getAdminStats } from '../assets/js/data/mock-data.js';
const ADMIN_STATS = await getAdminStats();
```

### Step 3 — Add auth layer

Add a `assets/js/utils/auth.js` module for token management,  
then protect the `/admin/` route with a guard check on load.

---

## Adding New Pages (Admin)

1. Create `/admin/pages/users.html` (or any name)
2. Create matching `/admin/pages/users.js`
3. Import shared CSS: `../assets/css/base.css` + `../admin.css`
4. Add the route to `ADMIN_NAV` in `mock-data.js`
5. The sidebar auto-renders — no other changes needed

---

## Tech Stack

| Layer       | Technology                    |
|-------------|-------------------------------|
| Markup      | Semantic HTML5                |
| Styling     | CSS3 + Custom Properties      |
| Scripting   | Vanilla ES Modules (no build) |
| Icons       | Inline SVG (Lucide-inspired)  |
| Fonts       | Google Fonts (Syne + Jakarta) |

No build tool required. Open `landing/index.html` directly in a browser  
or serve from any static host (Vercel, Netlify, S3, Nginx).
