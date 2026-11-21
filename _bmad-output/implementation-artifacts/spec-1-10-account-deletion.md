---
title: 'Story 1.10: Delete an Account'
type: 'feature'
created: '2026-11-21'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '38144e4'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** PRD §5 promised account deletion; a user's e-mail and name stay in the system for good, and four deferred items wait for it (`ON DELETE`, the uploader's name in the photo description).

**Approach:** `POST /api/auth/delete-account` with the password anonymises the user and deletes what only exists for them in one transaction (`domain/account_deletion.py`, AD-17). Decisions (Eirik, 2026-11-21): a Landlord with a Tenant is refused (409) until the Tenants are removed; everything else as in `sprint-change-proposal-2026-11-21.md`.

## Boundaries & Constraints

**Always:** The `users` row is kept (anonymised, `deleted_at`), so no `ON DELETE` and no migration of foreign keys. All dependent deletes are by statement in one transaction; stored photos are removed after the commit, best effort. A wrong password is 400 (never 401/403, which the client reacts to). Tokens of a deleted account are refused (`current_user`, refresh). A test reads the tables that point at `users` or `homes` from the metadata and fails for an unhandled one.

**Never:** No deleting the user row, no deleting history in Homes that remain, no change to FR-3 or FR-23 text beyond the exception line, no Landlord transfer feature.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Household Member, others remain | correct password | anonymised, Membership gone, completions stay as «Tidligere medlem», Home stays | N/A |
| Last Member of a Home | correct password | Home, Tasks, photos deleted | N/A |
| Landlord, no Tenants | correct password | Landlord Homes deleted with photos | N/A |
| Landlord with a Tenant | correct password | 409 naming the Homes, nothing changed | message shown inline |
| Wrong password | any | 400, nothing changed | «Passordet stemmer ikke.» |
| Photo store fails after commit | store raises | account still deleted, warning logged | N/A |
| Failure in the middle | exception | everything rolled back | N/A |
| Deleted account | old token, refresh, login | 401 | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/domain/account_deletion.py` -- the rules; `tables_pointing_at` for the guard test.
- `backend/app/models/user.py`, `alembic/versions/a7c9e1b3d5f2_users_deleted_at.py` -- `deleted_at`.
- `backend/app/storage/*` -- `PhotoStore.delete` (local, Blob via `delete_blob`).
- `backend/app/routes/auth.py`, `permissions/current_user.py`, `domain/accounts.py` -- route and refusals.
- `frontend/src/components/DeleteAccount.tsx`, `routes/Settings.tsx`, `api/auth.ts`, `api/queries.ts`.

## Tasks & Acceptance

**Execution:**
- [x] Backend: model, migration, storage `delete`, `account_deletion`, route, refusals in `current_user`, refresh and `authenticate`
- [x] `backend/tests/test_account_deletion.py` (16 tests), `test_homes.py` guard updated for the second place that deletes Memberships
- [x] Frontend: `DeleteAccount`, Settings section, `useDeleteAccount`, six tests
- [x] PRD (FR-25, §5, Privacy, Revision log), epics (Story 1.10), AD-17, README, `sprint-status.yaml`
- [x] `deferred-work.md`: outcomes for `ON DELETE` and the uploader's name

**Acceptance Criteria:** see Story 1.10 in `epics.md`.

## Implementation Notes

- Built directly. Each test names the line it guards; mutation checks (no tenant check, push devices kept, e-mail not anonymised, description not scrubbed, every Home deleted, session not cleared) each fail a test.
- `fairness_nudges` have no user column, so they are deleted only with a Home (the plan text said «fairness records»; corrected in PRD, epics and AD-17).
- The local branch was first cut from a `main` without PR #91 and merged with `origin/main` before the commit.
- Not tested against Postgres or real Blob (`delete_blob` only by signature); the CI migration job runs the new revision up and down.

## Spec Change Log

## Review Triage Log

Code review 2026-11-21 (Blind Hunter B, Edge Case Hunter E, Verification Gap V; about 30 findings, verified against the code):

| Finding | Verdict | Route / action |
|---|---|---|
| The refresh route's `deleted_at` check is not guarded: the test's 401 came from the cleared cookie (E, V) | medium | patch: the test copies the cookie before the deletion and re-sends it; mutation shows it fails without the check |
| `OnboardingGuide` and `FairnessNudge` deletes untested (V) | medium | patch: both rows added to the Home test; each delete removed in turn fails it |
| `BlobPhotoStore.delete` untested and absent from the calling-convention guard (B, E, V) | medium | patch: `iscoroutinefunction` on `delete_blob`, a faked-SDK test of the key and both error mappings, a local read-back test |
| `store.delete` raising something other than `StorageError` gives a 500 after the commit (E) | medium | patch: `except Exception`, logged with the traceback |
| Two Members deleting at once can leave an empty Home; the same account deleted twice in parallel (B, E) | medium | patch: user row and all the user's Homes locked `FOR UPDATE` in id order, then the deleted check; Postgres only, test deferred |
| `test_a_deleted_user_cannot_delete_again` passes through the unusable hash (B) | medium | patch: the test gives the user a real hash, so only `is_deleted` can refuse |
| Filler assertions (`assert link.token` and similar); the other Member's rows not proved to survive (B, V) | low | patch: removed; the other Member's push device and notification are asserted |
| The browser's push subscription, the last-Home key and the closed note stay on the device (B) | medium | patch: removed after a successful deletion, with a test |
| PRD-drift: photo deletion is best effort, Home-scoped deletions, an emptied Household Home loses its history, wrong password and no attempt limit (B, E, V) | medium | patch to text: FR-25, AD-17, Story 1.10 AC, Revision log |
| README: what seed restores; Kari's other Homes (B) | low | patch: reworded |
| No throttle on wrong passwords (B, E) | low | accepted: stated in FR-25, `deferred-work.md` |
| A Tenant joining while the Landlord deletes can get a 500 (E) | low | defer: `deferred-work.md` (needs a Postgres test) |
| «answers 409» in the epics AC (E) | low | patch: «refuses» |
| `delete_blob` against the real store not read back (B, V) | medium, not testable here | defer: confirmed by the Postgres/Blob smoke after deploy (see PR) |

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check .` -- all pass
- `cd frontend && npm test -- --run && npm run lint && npx tsc -b` -- all pass (Node 24)
