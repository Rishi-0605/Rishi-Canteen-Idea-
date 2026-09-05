# IBS Cafeteria

A working front-end prototype of a queue-skipping cafeteria ordering system, built for **IBS Mumbai**.
Students browse the menu, pay online (simulated), get a token/QR code, and track their order in real time
while cafeteria staff manage orders from a live kanban dashboard and admins manage the menu and see analytics.

The pilot is branded **IBS Cafeteria**; the codebase is structured so it can grow into a multi-college
product called **Campus Bite** later (see [Future: Campus Bite](#future-campus-bite) below).

> All prices shown in the app are **demo prices** for prototype purposes only — they are not the cafeteria's
> real prices, and are fully editable from the Admin Dashboard.

## What's actually working

This is not a static mockup — every primary button is wired to real state:

- Add to cart, change quantity, remove items, empty-cart state
- Eat In / Parcel selection, ASAP or Schedule Pickup (with quick presets for ordering ahead of a break)
- Simulated payment (UPI / Google Pay / PhonePe / Card — no cash), including a **"simulate failed payment"**
  toggle so you can demo the failure state
- Auto-generated token (`#A127`, `#A128`, ...) with a real scannable-looking QR code
- Live order status timeline (Order Placed → Payment Confirmed → Accepted → Preparing → Ready → Collected)
- Staff dashboard: accept / start preparing / mark ready / complete — updates propagate to the student's
  tracking screen **live, with no page reload**, including across two separate browser tabs/windows
  (open Student in one tab and Staff in another to see it — the app uses `localStorage` + a `storage`
  event listener as its shared mock backend)
- Scheduled ("break-time") orders show up in their own section on the staff dashboard
- Admin dashboard: add / edit / delete menu items, edit prices inline, toggle Available/Sold Out, and view
  charts for popular items, orders-by-hour, revenue, AOV, and peak time
- Order history with one-tap Reorder
- A live "cafeteria queue" widget (current orders + estimated wait), and a cafeteria Open/Closed toggle that
  actually blocks checkout when closed
- Empty states, error states (sold out, closed, payment failed), and toast + bell notifications throughout

## Tech stack

- **React 19 + TypeScript + Vite**
- **React Router** for navigation
- **Zustand** for state, split into two stores (see [Architecture](#architecture))
- **Tailwind CSS v4** for styling
- **Recharts** for the admin analytics charts
- **qrcode.react** for the token QR codes
- **lucide-react** for icons

No backend — this is a front-end prototype. Data lives in the browser (see below).

## Getting started

```bash
npm install
npm run dev
```

Then open the printed local URL (typically `http://localhost:5173`).

To build a production bundle: `npm run build` (output in `dist/`). `npm run preview` serves that build locally.

## Demo login

On the Login screen, tap **DEMO LOGIN**, then pick a role:

| Role | What you get |
|---|---|
| **Enter Demo as Student** | Full ordering flow: browse → cart → pay → token → track → history |
| **Enter Demo as Canteen Staff** | `/staff` — the kanban order dashboard |
| **Enter Demo as Admin** | `/admin` — menu management + analytics |

You can also type anything into the College Email / Password fields and hit **LOGIN** — it accepts any
non-empty input and signs you in as the demo student (this is a prototype, not a real auth system).

**To see the "real-time" behaviour**, open the app in two tabs: log in as Student in one and Staff in the
other. Place an order in the Student tab, then Accept → Start Preparing → Mark Ready in the Staff tab — the
Student tab's tracking screen updates live.

## Where to customize things

| What | File |
|---|---|
| Food items, categories, demo prices, descriptions | `src/data/menu.ts` |
| Add/edit/delete food items, prices, availability at runtime | Admin Dashboard → **Menu Management** (no code needed) |
| Cafeteria / pilot name, tagline | `src/components/Logo.tsx`, `src/pages/Splash.tsx`, `src/pages/Login.tsx` |
| Colors / theme (brand blue, accent orange) | `src/index.css` → the `@theme` block (`--color-brand-*`, `--color-accent-*`) |
| College name shown in Profile | `DEMO_STUDENT` in `src/store/useSessionStore.ts` |
| Tax rate | `TAX_RATE` constant in `src/pages/student/Cart.tsx` and `Payment.tsx` |
| Food card images | Currently emoji + gradient (`emoji`/`gradient` fields in `src/data/menu.ts` and the Admin "Add Food" form) — swap `FoodCard.tsx`'s emoji block for an `<img>` once you have real photos |
| Campus Bite college list (teaser only) | `src/pages/CampusBiteTeaser.tsx` |

## Architecture

State is deliberately split into two Zustand stores:

- **`useSessionStore`** (`sessionStorage`, per browser tab) — who's logged in, their role, and their
  in-progress cart/checkout choices. Kept per-tab on purpose: logging into the Staff dashboard in a second
  tab must never log out or swap the cart of a Student tab already open elsewhere.
- **`useDataStore`** (`localStorage`, shared) — the menu, all orders, and notifications. This is the
  prototype's "shared backend." A `storage` event listener re-hydrates it in every open tab whenever
  another tab writes to it, which is what makes the Staff → Student live updates work without a real server.

Routes live in `src/App.tsx`. Student screens are under `src/pages/student/`, staff under `src/pages/staff/`,
admin under `src/pages/admin/`. The Admin and Staff dashboards are lazy-loaded to keep the initial student
bundle small.

## Future: Campus Bite

The pilot doesn't advertise this, but there's a low-key link at the bottom of the Login screen
("Built on the Campus Bite platform...") that leads to `/campus-bite` — a "Choose Your College" screen
listing IBS Mumbai plus several other Mumbai colleges as illustrative examples of where the product could
expand. Only IBS Mumbai is live; picking any other college shows a "coming soon" notice. **These colleges
are not actual partners** — they're placeholders to demonstrate the intended multi-college architecture to
college management. The menu/order data model (`FoodItem`, `Order`, etc. in `src/types.ts`) has no
IBS-specific fields, so scoping it per-college later mainly means adding a `collegeId` and filtering the
existing stores by it.

## Known prototype limits (by design)

- No real backend/database — state lives in the browser (`localStorage`/`sessionStorage`); clearing site
  data resets the demo.
- Payments are simulated — no real payment gateway is contacted.
- "Login" accepts any credentials for the student role; there's no real account system.
- The live queue numbers blend a slowly-changing baseline with real demo orders so the widget feels alive
  even with only one or two test orders placed.
