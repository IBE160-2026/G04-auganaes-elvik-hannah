# Epic 1 Context: Foundation — Accounts, Homes & Roles

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Lay the foundation every later epic builds on. Users can register and log in, create a Home (Household or Landlord), invite others via a scoped link, and have their Role (Household Member, Landlord, Tenant) enforced server-side. Underneath that sits a responsive, installable app shell with the design tokens wired in, the backend layering (routes, then permissions, then domain, then persistence) and a local Docker-based setup. A course reviewer must be able to run and test the app without the team's accounts or keys. The whole epic is Trinn 1, the minimal core flow that has to be finished and stable before any Trinn 2 work starts.

## Stories

- Story 1.1: Project Scaffold, Design Tokens & Responsive App Shell
- Story 1.2: Account Registration & Login
- Story 1.3: Create a Home (Household or Landlord)
- Story 1.4: Invite Members via Scoped Link & Accept Invite
- Story 1.5: View Home Members List & Enforce Role-Based Permissions
- Story 1.6: Run Locally with Docker, Seed Data and Mock Modes

## Requirements & Constraints

- **Homes:** A user can create a Home without belonging to any other Home. The creator of a Household Home is a Household Member with no creator privilege. The creator of a Landlord Home is its only Landlord, and the Home must be fully configurable with zero Tenants. A Home holds either only Household Members, or one Landlord plus Tenants. The two are never mixed.
- **Invites:** Any Household Member can invite to a Household Home (Role: Household Member). Only the Landlord can invite to a Landlord Home (Role: Tenant). A Tenant calling the invite endpoint is rejected server-side. A link resolves to registration for a new user and to a "join Home" action for a logged-in user. A used or expired link shows a clear message, never a 404. The default link policy (single-use, 7-day expiry, regenerable by whoever can invite) is an unconfirmed assumption and must be confirmed in the Story 1.4 PR.
- **Isolation:** A user with a Membership in Home A cannot read or change Home B, whatever their Role in A. Role restrictions are enforced on the server, never only hidden in the UI.
- **Multi-Home scope:** v1 has no Home-switcher UI. A Household Member or Tenant gets one self-service "create a Home" entry point. Landlords are never blocked from creating more Homes, because the Epic 6 portfolio depends on it.
- **Responsive:** Usable on phone, tablet and desktop. At 320 CSS px width / 400% zoom every surface reflows to one column with no horizontal scroll.
- **Local runnability:** `docker compose up` plus one documented command (migrations + seed) gives a working app with at least two example users, whose credentials are listed in the README. The seed is idempotent. The test suite passes offline with no keys. `.env.example` lists every variable with no secrets, and `.env` is gitignored. The README must work on both macOS and Windows (Git Bash), and it must say how mock mode shows in the UI.
- **Testable success criteria this epic must satisfy with automated tests:** Home creation and invite rules, including Tenant rejection and the expired-link message. Cross-Home isolation. Local run from the README with passing tests.
- **Copy is Norwegian only.** No i18n library.

## Technical Decisions

- **Stack:** Python 3.12+, FastAPI (pin the exact 0.14x patch at setup), SQLModel, Alembic and PostgreSQL in Docker. Frontend: React 19 (pin the exact minor), TypeScript (not plain JS), Vite, TanStack Query v5 and Node LTS. Tests: pytest (backend) and Vitest (frontend). Pin the PostgreSQL major version in `docker-compose.yml`, and keep the same major as the optional hosted Supabase demo. Do not use a project generator. Scaffold the committed tree directly.
- **Source tree:** At the repo root: `docker-compose.yml`, `.env.example`, `README.md`. Under `frontend/`: `public/manifest.json` and `src/{api,components,routes,styles}` plus `src/service-worker.ts`. Under `backend/app/`: `{routes,domain,permissions,models}`, with `ai/`, `seed/` and `notifications/` added by the stories that need them.
- **Layering:** Dependencies point downward only (UI, then routes, then permissions, then domain, then persistence/adapters). Routes are thin. Every mutation and external call goes through a domain service.
- **Role model:** Role lives on `Membership` (the User↔Home join), never on `User`. The JWT carries only `user_id`. Every Home-scoped route takes `home_id` as a path parameter and uses a `require_role(home_id, allowed_roles)` dependency. That dependency loads the caller's Membership row from the DB, never from a token claim, body or query. (Early architecture notes that read Role from the JWT are superseded.)
- **Auth:** A short-lived access token is returned in the response body and held only in React memory, never in `localStorage`. A long-lived refresh token goes in an `httpOnly`/`Secure`/`SameSite=None` cookie and is exchanged only at `/refresh`. CORS uses the exact origins from `CORS_ORIGINS` (the local frontend by default) with `allow_credentials=True`, never a wildcard. The API client sends `credentials: "include"`.
- **Frontend data:** No direct `fetch`/`axios` in components and no server data in `useState`. All server reads and writes go through TanStack Query hooks on one API client generated with `openapi-typescript` from FastAPI's OpenAPI schema. There is no real-time layer: data refetches on mount and on window focus.
- **Entities in this epic:** `User`, `Home` (type Household or Landlord), `Membership` (one Role per Home), `InviteLink` (token, target Role, used/expired/revoked state, kept separate from Membership).
- **Conventions:** Entity names follow the glossary (`Member` is the Home-scoped actor, `User` is the account row). IDs are UUIDv4. Datetimes are ISO 8601 UTC on the wire. Errors use FastAPI's `{"detail": ...}` and the standard 422 body. Every schema change is a committed Alembic migration, against each developer's own local database. Secrets (DB URL, JWT signing key, later Gemini/VAPID) come only from environment variables.
- **Mock adapters:** Each external service has an adapter with a mock that is picked automatically when its key is missing (AI when `GEMINI_API_KEY` is unset). Tests always use the mocks. The hosted Vercel/Render/Supabase setup is an optional demo, not a requirement.

## UX & Interaction Patterns

- **Design tokens:** Generate or copy CSS custom properties once from DESIGN.md's frontmatter into `frontend/src/styles/`. Components must not contain literal hex, px or radius values, only `var(--...)`. Token groups:
  - Colors: primary `#6E62CC`, secondary, accent, surface-base, surface-raised, ink-primary/secondary, success, warning, danger, must-/should-badge (with ink), focus-ring.
  - Typography: display, title, body, meta, badge, all in `rem`.
  - Spacing: 4–48px across seven steps.
  - Rounded: sm 8, md 14, lg 20, full pill.
- **Type:** System font stack (`-apple-system`, `BlinkMacSystemFont`, Segoe UI, Roboto…), `rem` against a 16px root, weights 500/700 only, no webfont.
- **Shapes:** The pill shape (`rounded.full`) is reserved for badges, status tags and primary buttons.
- **Surface:** Light mode only. Cards lift from surface-base to surface-raised with one soft shadow.
- **Breakpoints (mobile-first):** phone ≤599px, tablet 600–1023px, desktop ≥1024px. Task surfaces stay single-column at every width.
- **Accessibility floor in the shell:**
  - A 2px focus-ring outline with 2px offset on every interactive element, never suppressed.
  - Tap targets of at least 44×44px.
  - `prefers-reduced-motion: reduce` sets transitions and animations to zero.
  - Focus order follows reading order.
  - Accessible labels describe both the action and the current state.
- **Primary button:** One dominant action per screen. States: default; pressed (8% darker overlay); disabled (`ink-secondary` background, with the reason in `aria-describedby` when it isn't obvious); in-flight (text swaps to "Sender…", never a spinner alone).
- **PWA:** `manifest.json` and a service worker registered from day one. One shared "Add to Home Screen" prompt is shown once per device, tracked client-side. Web Push itself comes in Trinn 2, but iOS needs the installed PWA for it.
- **Auth states:**
  - Failed login shows an inline field-level error, with no page reload and no hint about whether the email exists.
  - An invited email that already has an account is offered "Logg inn i stedet".
  - An invalid or expired invite shows "Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra [utleier/husstandsmedlem]."
- **Members & Invite:** Reachable by Household Members and Landlords, and shows every Member with their Role. For a Tenant, the invite control is absent from the layout, not disabled. A failed invite generation shows an inline error with retry.
- **Tone:** Household copy is warm and slightly playful. Landlord copy is neutral. No gamification anywhere.

## Cross-Story Dependencies

- Order: 1.1, then 1.2 and 1.6, then 1.3, 1.4 and 1.5.
- **1.1 provides** the scaffold, `docker-compose.yml`, Alembic wiring, a health check, pytest and Vitest each with one passing offline test, and the first README and `.env.example`. Every later story that changes setup must update the README and `.env.example` in the same PR.
- **1.6 builds on** 1.1 and 1.2 (users). It owns the seed command, which 1.3 (example Household Home) and 2.1 (example tasks) extend rather than replace. The AI mock provider arrives with Story 5.1.
- **1.5's `require_role` dependency** is the permission path that every Home-scoped route in Epics 2–6 uses. The Epic 2 Tenant locks (classification/Frequency) depend on it.
- The shell's tokens, button and breakpoints are reused by every later screen. The Landlord Portfolio Dashboard's two-column layout (Epic 6) is the only exception to single-column.
