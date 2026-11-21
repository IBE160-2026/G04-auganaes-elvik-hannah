---
title: 'Story 6.1: Landlord Portfolio Dashboard'
type: 'feature'
created: '2026-11-21'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'fa782aa8dca15fd7a76d1ca3360d2b34b5a3e0f2'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Landlord with several Homes must open each one to see which are behind (FR-20, UJ-2).

**Approach:** One server-computed Portfolio view (`GET /api/portfolio`, `domain/portfolio.py`) with one row per Landlord Home, plus a Portfolio page and tab for Landlords with 2+ Landlord Homes. Decisions (Eirik, 2026-11-21): one row per Home (a unit is its own Home; there is no building entity, so FR-20 and the AC drop «per unit» and «building list»); the detail panel shows overdue Must tasks and a link to «Administrer hjemmet»; pull gesture plus a visible «Oppdater» button.

## Boundaries & Constraints

**Always:** Status is decided on the server with `tasks.due_status` and the UTC day (`clock.utc_today()`); the frontend never reads the browser clock. «Behind» means at least one overdue Must task among the Home's active, open instances; archived Tasks never count (FR-24). A Home without Tasks shows «Ikke satt opp», not «Alt i orden». Status is text plus tag, never color alone. The 2+ rule lives once (`portfolio.MIN_HOMES`), sent as `HomesOut.has_portfolio`. Only Homes where the caller is Landlord count. Fixed query count, never one per Home. Tests guard named lines; mock-mode and README unchanged unless needed.

**Never:** No building entity or grouping. No new tables or migrations. No broadcast or reminder action from the dashboard (UJ-2's targeted reminder is Story 3.4's admin page). No Should-task status, no per-Tenant data.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Behind | Home has ≥1 overdue Must | Row «Forsinket», count, tasks listed oldest first | N/A |
| On track | Tasks, no overdue Must (Should overdue ignored) | «Alt i orden» | N/A |
| No tasks | Home without Tasks | «Ikke satt opp» | N/A |
| Sort | Mixed | Behind first, then name, then id | N/A |
| One Landlord Home | `GET /portfolio` | 403 | Global 403 handler refetches Homes; page redirects to `/` |
| Tenant or Household user | Same | 403 | Same |
| Load fails | Network error | Inline error with retry, not blank | Norwegian message |

</frozen-after-approval>

## Code Map

- `backend/app/domain/tasks.py` -- `due_status`, `is_active`, `is_open`; reuse, do not change.
- `backend/app/domain/homes.py` -- `homes_for`/`MemberHome`; Landlord filter by role.
- `backend/app/routes/homes.py` -- `HomesOut`, `list_homes`; add `has_portfolio`.
- `backend/app/routes/deps.py`, `backend/tests/test_permissions.py` -- route has no `{home_id}`, so guard is the 403 in the domain/route.
- `frontend/src/components/TabBar.tsx` (+ comment «Portfolio tab comes with Story 6.1»), `App.tsx`, `api/queries.ts`, `api/homes.ts`, `routes/LandlordAdmin.tsx` (link target `/hjem/<id>/utleier`), `routes/TaskOverview.tsx` (skeleton and `Badge` patterns).
- `backend/openapi.json` / `frontend/src/api/schema.d.ts` -- regenerate (`test_openapi_sync.py`).

## Tasks & Acceptance

**Execution:**
- [x] `backend/app/domain/portfolio.py` -- `MIN_HOMES`, `has_portfolio`, `portfolio_of` (two queries: Landlord Homes, then open Must instances up to the UTC day + 3 days) -- FR-20 rules in one place
- [x] `backend/app/routes/portfolio.py`, `main.py`, `routes/homes.py` -- `GET /api/portfolio` (403 under 2 Landlord Homes), `has_portfolio` on `HomesOut`
- [x] `backend/tests/test_portfolio.py` -- every matrix row, archived task, other Landlord's Home never leaks, query count fixed, 403s
- [x] `frontend/src/api/portfolio.ts`, `queries.ts` -- `usePortfolio`, messages, refetch
- [x] `frontend/src/routes/Portfolio.tsx` + css, `App.tsx`, `TabBar.tsx` -- page, `/portefolje` route, tab when `has_portfolio`, skeleton rows per known Home, two columns ≥600 px collapsing at 320 px / 400 % zoom, pull-to-refresh plus «Oppdater», row opens `/hjem/<id>/utleier` on narrow screens
- [x] `frontend/src/routes/Portfolio.test.tsx`, `TabBar` test -- text tags, tab visibility, skeleton, redirect with one Home, refresh
- [x] `_bmad-output/planning-artifacts/` (PRD FR-20 + Revision log, `epics.md` Story 6.1, `sprint-status.yaml`) -- text matches code (PRD-drift)
- [x] `docs/ki-logg/korrigeringer.md` -- only if AI code errors are found

**Acceptance Criteria:**
- Given a Landlord with 2+ Landlord Homes, when they open the Portfolio, then each Home shows «Forsinket», «Alt i orden» or «Ikke satt opp», and which Homes have overdue Must tasks is visible without opening any.
- Given a Landlord with one Home, then no Portfolio tab exists.
- Given a tablet or desktop width, then a selected-Home detail column shows overdue Must tasks and a link to the Home's admin page.
- Given a keyboard or screen reader user, then «Oppdater» and rows are reachable and announced.

## Implementation Notes

- Built directly (no subagent). Backend: `domain/portfolio.py` (`MIN_HOMES`, `has_portfolio`, `portfolio_of`), `routes/portfolio.py`, `HomesOut.has_portfolio`; tests in `tests/test_portfolio.py` (the two `test_homes_routes.py` bodies gained `has_portfolio`).
- Frontend: `routes/Portfolio.tsx`, `components/StatusTag.tsx` (the design system's pill for status tags), `api/portfolio.ts`, tab in `TabBar.tsx`, route `/portefolje`. Pull-to-refresh moved from `TaskOverview` into the shared `routes/usePullToRefresh.ts` (behaviour and tests unchanged).
- Two-column switch is `matchMedia` at 37.5 em in `Portfolio.tsx` (JS decides link vs button), widened main column through `.app-shell__main:has(.portfolio)`.
- Seed is unchanged (Kari keeps one Landlord Home, so CI counts stay); README explains how to get a Portfolio by creating a second Utleiebolig.
- `useCreateHome`/`useAcceptInvite` keep the cached `has_portfolio` until the refetch, like `allowed_types`.

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run mypy .` -- expected: pass
- `cd frontend && npm test -- --run && npm run lint && npx tsc -b` -- expected: pass on Node 24

**Manual checks (if no CLI):**
- Seed two Landlord Homes, one with an overdue Must task; check the tab, tags and layout at 320, 700 and 1200 px.
