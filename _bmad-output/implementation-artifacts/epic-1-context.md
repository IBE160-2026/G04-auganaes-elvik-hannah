# Epic 1 Context: Foundation — Accounts, Homes & Roles

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Lay the foundation every later epic builds on. Users can register and log in, create a Home (Household or Landlord), invite others through a scoped link, and have their Role (Household Member, Landlord, Tenant) enforced on the server. Underneath sits a responsive, installable app shell with the design tokens wired in, the backend layering (routes → permissions → domain → persistence), local running with Docker as the primary path, and an optional hosted demo on the course's Vercel project, which is the only hosting the course supports. A course reviewer must be able to run and test the app without the team's accounts or keys. The whole epic is Trinn 1, the minimal core flow that has to be finished and stable before any Trinn 2 work starts.

## Stories

- Story 1.1: Project Scaffold, Design Tokens & Responsive App Shell (done)
- Story 1.2: Account Registration & Login
- Story 1.3: Create a Home (Household or Landlord)
- Story 1.4: Invite Members via Scoped Link & Accept Invite
- Story 1.5: View Home Members List & Enforce Role-Based Permissions
- Story 1.6: Run Locally with Docker, Seed Data and Mock Modes
- Story 1.7: Hosted Demo on Vercel (Services + Neon) (done, built before Story 1.2)

## Requirements & Constraints

- **Homes:** A user can create a Home without belonging to another one. The creator of a Household Home is a Household Member with no creator privilege. The creator of a Landlord Home is its only Landlord, and the Home must be fully configurable with zero Tenants. A Home holds either only Household Members, or one Landlord plus Tenants, never a mix.
- **Invites:** Any Household Member can invite to a Household Home (Role: Household Member). Only the Landlord can invite to a Landlord Home (Role: Tenant). A Tenant calling the invite endpoint directly is rejected by the server. A link leads a new user to registration and a logged-in user to a "join Home" action. A used or expired link shows a clear message, never a 404. The default link policy (single-use, 7-day expiry, regenerable by whoever can invite) is an unconfirmed assumption: confirm it in the Story 1.4 PR.
- **Isolation:** A Member of Home A cannot read or change Home B, whatever their Role in A. Role rules are enforced on the server, never only hidden in the UI.
- **Multi-Home scope:** v1 has no Home switcher. A Household Member or Tenant gets one self-service "create a Home" entry point. Landlords are never blocked from creating more Homes, because the Epic 6 portfolio depends on it.
- **Responsive:** Usable on phone, tablet and desktop. At 320 CSS px / 400% zoom every surface reflows to one column with no horizontal scroll.
- **Local runnability:** `docker compose up` plus one documented command (migrations + seed) gives a working app with at least two example users, whose credentials are in the README. The seed is idempotent. The test suite passes offline with no keys. `.env.example` lists every variable the app reads, with no secrets, and `.env` is gitignored. The README must work on macOS and Windows (Git Bash) and say how mock mode shows in the UI. Every story that changes setup updates README and `.env.example` in the same PR.
- **Hosted demo (optional):** Must never be required to run, test or review the app. No secret is committed; the README gives the URL (g04husly.vercel.app), says the demo is optional and that only the project owner sees the Vercel and Neon dashboards, and explains rollback (tag `v0.1-for-vercel-hosting`, Root Directory back to `frontend`).
- **Must be covered by automated tests:** Home creation and invite rules (including Tenant rejection and the expired-link message), cross-Home isolation, and a local run from the README with passing tests.
- **Copy is Norwegian only.** No i18n library.

## Technical Decisions

- **Stack (as built in 1.1):** Python 3.12 with dependencies managed by `uv`; FastAPI pinned 0.162.0; SQLModel; Alembic. PostgreSQL 18 in `docker-compose.yml` on host port 5433 (the hosted Neon database is also Postgres 18; keep the majors equal). Moved from 17 on 2026-11-01, because Neon created the database with 18.6 (Story 1.7). Frontend: React 19 (exact pin), TypeScript 6.0.3 (capped by `typescript-eslint`), Vite, TanStack Query v5; Node engines `^22.22.2 || ^24.15.0 || >=26.0.0`. Tests: pytest and Vitest. No project generator.
- **Source tree:** Repo root holds `docker-compose.yml`, `vercel.json` (added in 1.7), `.env.example`, `README.md`. `frontend/src/{api,components,routes,styles}` plus `service-worker.ts` and `public/manifest.json`. `backend/app/{routes,domain,permissions,models}`; `seed/`, `ai/` and `notifications/` are added by the stories that need them.
- **Layering:** Dependencies point downward only. Routes are thin; every mutation and external call goes through a domain service.
- **Roles:** Role lives on `Membership` (User↔Home join), never on `User`. The JWT carries only `user_id`. Every Home-scoped route takes `home_id` as a path parameter and uses `require_role(home_id, allowed_roles)`, which loads the caller's Membership row from the database, never from a token claim, body or query.
- **Same origin and auth:** All API routes are mounted under `/api` (the existing route is `/api/health`), and the frontend calls only relative `/api/...` paths. Locally, the Vite dev and preview servers proxy `/api` to the backend on port 8000. On Vercel, a top-level rewrite sends `/api/*` to the FastAPI service (which sees the full path, prefix included) and everything else to the Vite service. A short-lived access token is returned in the response body and held only in React memory, never `localStorage`. A long-lived refresh token is an `httpOnly`/`Secure`/`SameSite=Lax` cookie scoped to `/api/auth/refresh`, the only endpoint that exchanges it. No CORS middleware and no `CORS_ORIGINS` (Story 1.7 removed them; do not reintroduce). Test login in Safari (macOS and iOS), locally and on the PR preview; if Safari rejects the `Secure` cookie on `http://localhost`, relax it via an environment variable for local running only, never in the hosted demo.
- **Hosted demo (built in Story 1.7):** One Vercel project (`g04husly`, Hobby plan), Root Directory at the repo root, `vercel.json` declaring `frontend/` and `backend/` as Vercel Services (Vercel Services is in beta). The backend runs as a Vercel Function. Neon connects through the Vercel integration, which sets `DATABASE_URL`; use Neon's pooled connection string, and normalise the URL scheme for SQLAlchemy/psycopg (the app uses `postgresql+psycopg://`) in one place in the config. `alembic upgrade head` runs in the build step, and a failed migration fails the build. Each PR preview uses its own Neon branch `preview/<git-branch>`, deleted when the PR closes (the free plan allows 10 branches). Fallback if that cleanup is impossible on the free plan: migrate only on `main`, explained in the PR. On Vercel a missing `DATABASE_URL` is an error, never a fallback to localhost. Trinn 1 needs no cron, push or Blob there; later the daily Vercel Cron (`CRON_SECRET`) and private Vercel Blob (`BLOB_READ_WRITE_TOKEN`, local-filesystem mock when unset) arrive in Trinn 2.
- **Frontend data:** No direct `fetch`/`axios` in components and no server data in `useState`. All server access goes through TanStack Query hooks on one client generated with `openapi-typescript` from FastAPI's OpenAPI schema. No real-time layer: refetch on mount and window focus.
- **Entities:** `User`, `Home` (type Household or Landlord), `Membership` (one Role per Home), `InviteLink` (token, target Role, used/expired/revoked state, separate from Membership).
- **Conventions:** Glossary names (`Member` is the Home-scoped actor, `User` the account row). UUIDv4 IDs. ISO 8601 UTC on the wire. Errors use FastAPI's `{"detail": ...}` and the standard 422 body. Every schema change is a committed Alembic migration. Secrets (DB URL, JWT signing key, later Gemini/VAPID/`CRON_SECRET`/`BLOB_READ_WRITE_TOKEN`) come only from environment variables (Vercel project settings in the demo).
- **Mock adapters:** Each external service has an adapter whose mock is chosen automatically when its key is missing. Tests always use the mocks. The AI mock arrives with Story 5.1.

## UX & Interaction Patterns

- **Tokens:** CSS custom properties generated or copied once from DESIGN.md's frontmatter into `frontend/src/styles/`. Components use only `var(--...)`, never literal hex, px or radius values.
- **Type and shape:** System font stack, `rem` against a 16px root, weights 500/700, no webfont. The pill shape is reserved for badges, status tags and primary buttons. Light mode only.
- **Breakpoints (mobile-first):** phone ≤599px, tablet 600–1023px, desktop ≥1024px. Task surfaces stay single-column.
- **Accessibility floor:** 2px focus ring with 2px offset, never suppressed; tap targets ≥44×44px; `prefers-reduced-motion` zeroes transitions; focus order follows reading order; labels describe action and state.
- **Primary button:** One dominant action per screen. In-flight state swaps text to "Sender…", never a spinner alone; disabled carries its reason in `aria-describedby` when not obvious.
- **PWA:** Manifest and service worker from day one (served at `/service-worker.js` in the demo too); a shared "Add to Home Screen" prompt shown once per device.
- **Auth states:** Failed login shows an inline field-level error, no page reload, no hint about whether the email exists. An invited email that already has an account is offered "Logg inn i stedet". An invalid or expired invite shows "Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra [utleier/husstandsmedlem]."
- **Members & Invite:** Shows every Member with their Role. For a Tenant the invite control is absent, not disabled. A failed invite generation shows an inline error with retry.
- **Tone:** Household copy warm and slightly playful, Landlord copy neutral, no gamification.

## Cross-Story Dependencies

- **Build order:** 1.1 (done) → 1.7 (done) → 1.2 → 1.6 → 1.3, 1.4, 1.5.
- **1.2 builds on 1.7's same-origin setup** (Vite `/api` proxy locally, `/api/*` rewrite on Vercel, no CORS), so login can be tried on its PR preview against a real backend and its own Neon branch. The first story that adds a client-side route (likely 1.2) must confirm the Vite service on Vercel falls back to `index.html` for deep links, and should build the tab bar from EXPERIENCE.md, which no story owns yet.
- **1.2 or 1.6** brings the DB-backed test harness that the open Story 1.7 check (Alembic `env.py` uses the migration URL and an advisory lock) is waiting for.
- **1.6 builds on** 1.1 and 1.2 (users) and owns the seed command. 1.3 (example Household Home) and 2.1 (example tasks) extend that command rather than replacing it.
- **1.5's `require_role`** is the permission path every Home-scoped route in Epics 2–6 uses; the Epic 2 Tenant locks depend on it.
- The shell's tokens, button and breakpoints are reused by every later screen.
