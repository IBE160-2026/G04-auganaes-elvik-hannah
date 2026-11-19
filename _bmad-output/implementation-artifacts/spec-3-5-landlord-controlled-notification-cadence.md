---
title: 'Story 3.5: Landlord-controlled notification cadence'
type: 'feature'
created: '2026-11-19'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: b13c4985cb6e1e01eed0cc45e32a5b1d1c554298
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-3-4-landlord-ad-hoc-broadcast-message.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The daily due-check (Story 3.2) reminds every Member every day about every due or overdue task. FR-13 lets a Landlord decide how strictly Tenants are reminded about due/overdue Must tasks, without touching the task's Frequency. The Landlord Home Admin shell (Story 3.4, PR #64) has no cadence control yet.

**Approach:** A per-Home setting `notification_cadence_days` (1, 2 or 7, default 1 = today's behaviour) is saved by the Landlord on `/hjem/<id>/utleier` through `PUT /api/homes/{home_id}/notification-cadence`. The due-check reads it: a Tenant is reminded about an open Must task when the number of days since its due date is divisible by the cadence. Nothing is stored per reminder, so the rule is deterministic and idempotent.

**Decisions (Claude's choices under Eirik's mandate, 2026-11-19; Eirik reviews them in the PR):**
1. Options are 1, 2 and 7 days ("Hver dag", "Annenhver dag", "Én gang i uken"): the PRD's three examples.
2. The cadence governs only Tenants' reminders about Må tasks. Household Members, the Landlord and Bør tasks keep the daily rule of FR-10.
3. The due day always reminds (0 days is divisible by every cadence). With cadence 2, a task due Monday reminds Monday, Wednesday, Friday while open.
4. This story builds on Story 3.4's shell and is based on its branch; it merges after PR #64.

## Boundaries & Constraints

**Always:** Landlord-only, server-side through `require_role` (own alias, own domain rule `can_set_cadence`). Whole days from a fixed list, validated server-side. A cadence change never touches a task's Frequency or due dates (FR-8/FR-9). The days are UTC days (`clock.utc_today`, AD-3). The frontend shows what the server's flag allows and never decides the rule. Failure shows an inline error with a retry at the action (UX-DR30).

**Never:** More than one reminder per task, Member and day (FR-10). Cadence for the broadcast (FR-12 is not limited by it). Per-task or per-Tenant cadence. Free-text intervals.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Default | New Home, no change | `notification_cadence_days` is 1; Tenants still reminded daily | N/A |
| Every second day | Cadence 2, Must task due 4 days ago, Tenant | Reminded (4 % 2 = 0) | N/A |
| Off day | Cadence 2, Must task due 3 days ago, Tenant | Not reminded | N/A |
| Due day | Cadence 7, Must task due today | Reminded | N/A |
| Weekly | Cadence 7, due 7 days ago | Reminded; due 6 or 8 days ago: not | N/A |
| Should task | Cadence 7, Bør task due 3 days ago, Tenant | Reminded (cadence is for Må only) | N/A |
| Other roles | Cadence 7, Must task due 3 days ago, Landlord | Reminded daily as before | N/A |
| Save | Landlord sends 2 | 200, Home now says 2 | N/A |
| Bad value | 3, 0, negative | 422, nothing saved | Field error |
| Wrong Role | Tenant or Household Member | 403, nothing saved | Same 403 as `require_role` |
| Frequency | Cadence changed | No task `frequency_days` or `due_on` changes | N/A |
| Failure | Server error on save | Inline error with «Prøv igjen»; the chosen value stays selected | Retry resends |

</frozen-after-approval>

## Code Map

- `backend/app/models/home.py` -- gets `notification_cadence_days` (NOT NULL, default 1, CHECK in (1, 2, 7)); migration after head `b9d3e7a1c5f4`.
- `backend/app/domain/due_check.py` -- `_due_by_member` selects Membership role, Task classification and the Home's cadence and filters in Python with a small `reminder_day` helper; claim-before-send stays.
- `backend/app/domain/broadcast.py` -- pattern for a Landlord-only rule (`can_broadcast`); cadence gets `domain/cadence.py` with `CADENCE_OPTIONS`, `can_set_cadence`, `set_cadence`, `reminder_day`.
- `backend/app/routes/homes.py` -- `HomeOut` gets `notification_cadence_days` and `can_set_cadence`; new route in `routes/cadence.py` using `Landlord` alias from `routes/deps.py`.
- `backend/tests/test_permissions.py` -- fails if the new `{home_id}` route lacks `require_role`.
- `frontend/src/routes/LandlordAdmin.tsx` (+css, test), `api/queries.ts`, `test-utils/fakeApi.ts` -- add the cadence section beside the composer.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/app/models/home.py`, new Alembic revision, `tests/test_homes.py` -- column and CHECK; migration up/down/up on a temporary database
- [ ] `backend/app/domain/cadence.py`, `due_check.py` -- rule, setter, filter in the due-check
- [ ] `backend/app/routes/cadence.py`, `main.py`, `routes/homes.py` -- route and `HomeOut` fields; regenerate OpenAPI and `schema.d.ts`
- [ ] `backend/tests/test_cadence.py` -- the matrix, each test names the line it guards
- [ ] `frontend/src/api/cadence.ts`, `queries.ts`, `routes/LandlordAdmin.tsx`, tests -- the section, saved notice in `aria-live`, inline error with retry
- [ ] PRD FR-13 (+ Revision log row), `epics.md`, AD-8 note, README, `deferred-work.md`

**Acceptance Criteria:**
- Given the Landlord saves a cadence, when the due-check next runs, then Tenants of that Home are reminded about open Must tasks only on days divisible by it.
- Given a Tenant or Household Member, when they call the route, then 403 and nothing changes.
- Given a failed save, when the Landlord sees the result, then an inline error with «Prøv igjen» shows at the section.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all green
- Migration: up, `alembic check`, down, up against a temporary database (never the local `husly`) -- expected: clean
- CI runs the frontend (Vitest, eslint, build); vitest cannot start locally in this environment.
