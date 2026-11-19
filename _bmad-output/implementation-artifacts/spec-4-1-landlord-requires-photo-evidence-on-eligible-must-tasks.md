---
title: 'Story 4.1: Landlord requires Photo Evidence on eligible Must tasks'
type: 'feature'
created: '2026-11-19'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 12e7ffbbe49a6aca8a8f5edf7afa32a9fd62c429
context:
  - '{project-root}/_bmad-output/implementation-artifacts/spec-3-5-landlord-controlled-notification-cadence.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-3-4-landlord-ad-hoc-broadcast-message.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** FR-18 lets a Landlord require Photo Evidence on a specific Must task whose completion is objectively visible (AD-6). The catalog already carries a system-seeded `photo_evidence_eligible` flag (Story 2.1), but nothing stores a requirement or enforces eligibility on the server, and the Landlord Home Admin page (Stories 3.4 and 3.5) has no place to set it.

**Approach:** A per-task flag `tasks.requires_photo_evidence` (default false) is set by the Landlord through `PUT /api/homes/{home_id}/tasks/{task_id}/photo-evidence-requirement`. The server refuses to turn it on unless the task is a Must task of a catalog type flagged eligible; turning it off is always allowed. The Landlord Home Admin page lists the Home's eligible Must tasks, each with a checkbox. This story only stores the requirement; stopping a Tenant from completing without a photo is Story 4.2 (FR-19).

**Decisions (Claude's choices under Eirik's mandate, 2026-11-19; Eirik reviews them in the PR):**
1. The requirement is a boolean column on `tasks`. AD-5's `PhotoEvidence` row (the photo, 1:1 with Task) is Story 4.2's, so no table is created here.
2. Setting it on a custom task, a non-eligible type or a Should task answers 409 with its own Norwegian message. Turning it off is allowed for any task, even one that is no longer eligible.
3. Changing a task to Bør clears its requirement, because FR-18 is about Must tasks. Changing it back to Må does not restore it.
4. The checkbox list shows only tasks the server says may require a photo (Må, eligible type, active), so there is no disabled checkbox to explain. A short note says which tasks can and that Tenants then must attach a photo.
5. Until Story 4.2 is built, a saved requirement changes nothing for a Tenant. The PR says so.

## Boundaries & Constraints

**Always:** Landlord-only, server-side through `require_role` (own domain rule `can_require_photo_evidence`). Eligibility is read from the catalog by key and checked in the domain, never from the request or the UI (AD-6). Other tasks in the Home stay untouched (one task per call). An archived task or a task in another Home is the same 404 as the other task routes. The frontend shows only what the server's flag and the task's own flags allow.

**Never:** Upload, storage or viewing of photos (Stories 4.2 and 4.3). Blocking a completion (4.2). A Household Home option of any kind: no flag, no checkbox (a Household Member and the Landlord-less Home never see it). Per-Home or system-wide default. Letting the client send or change eligibility.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Require | Landlord, Must task of eligible type | 200, `requires_photo_evidence: true`; other tasks unchanged | N/A |
| Not eligible | Landlord, Must task of a type without the flag | 409, nothing saved | «Denne oppgavetypen kan ikke kreve bildebevis.» |
| Custom task | Landlord, custom Must task (no catalog key) | 409, nothing saved | Same message |
| Should task | Landlord, Bør task of an eligible type | 409, nothing saved | «Bare Må-oppgaver kan kreve bildebevis.» |
| Turn off | Task already requiring | 200, false, whatever its current state | N/A |
| Downgrade | Requirement on, task changed to Bør | `requires_photo_evidence` is false afterwards | N/A |
| Wrong Role | Tenant or Household Member | 403, nothing saved | Same 403 as `require_role` |
| Other Home | Task id from another Home, or archived | 404 | `TASK_NOT_FOUND` |
| Household Home | Household Member | `can_require_photo_evidence` false in `HomeOut`; no checkbox | N/A |
| Failure | Server error | Inline error with «Prøv igjen»; checkbox shows the saved state | Retry resends |

</frozen-after-approval>

## Code Map

- `backend/app/domain/tasks.py` -- `photo_evidence_eligible(task)` already reads the catalog by key (AD-6); `adjust_task` clears the flag on a change to Bør. The file is 566 lines; new code goes in `domain/photo_evidence.py`.
- `backend/app/models/task.py` -- `Task` gets `requires_photo_evidence` (NOT NULL, server default false); migration after head `c4e8a2f6b1d7`.
- `backend/app/routes/tasks.py` -- `TaskOut` gets `requires_photo_evidence` and `photo_evidence_eligible`; `TASK_NOT_FOUND`, `TaskAdjuster` pattern in `routes/deps.py` for a `PhotoEvidenceSetter` alias.
- `backend/app/routes/homes.py` -- `HomeOut.can_require_photo_evidence`.
- `backend/tests/test_permissions.py` -- fails if the new `{home_id}` route lacks `require_role`.
- `frontend/src/routes/LandlordAdmin.tsx` (+css, test), `api/queries.ts`, `api/tasks.ts`, `test-utils/fakeApi.ts` -- a third section beside the composer and the cadence.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/app/models/task.py`, new Alembic revision, `.github/workflows/ci.yml` -- column; the migration is proven by the CI job «Migreringer (Postgres 18)»
- [ ] `backend/app/domain/photo_evidence.py`, `tasks.py` -- rule, setter, clearing on downgrade
- [ ] `backend/app/routes/photo_evidence.py`, `main.py`, `deps.py`, `routes/tasks.py`, `routes/homes.py` -- route and fields; regenerate OpenAPI and `schema.d.ts`
- [ ] `backend/tests/test_photo_evidence.py` -- the matrix, each test names the line it guards
- [ ] `frontend/src/api/photoEvidence.ts`, `queries.ts`, `routes/LandlordAdmin.tsx`, tests -- the section
- [ ] PRD FR-18 (+ Revision log row), `epics.md`, AD-6 note, README, `deferred-work.md`

**Acceptance Criteria:**
- Given a Landlord and an eligible Must task, when they require Photo Evidence, then it is saved and no other task changes.
- Given a custom, non-eligible or Should task, when the Landlord (or a direct API call) tries, then the server answers 409.
- Given a Household Member or a Tenant, when they call the route, then 403, and the Home never exposes a requirement option to them.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all green
- CI runs the frontend (Vitest, eslint, build) and the migration; vitest and Alembic cannot run locally here.
