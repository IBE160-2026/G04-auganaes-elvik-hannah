---
title: 'Story 3.4: Landlord ad-hoc broadcast message'
type: 'feature'
created: '2026-11-19'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: d7f9dbe4e944cf5cbc96267516e1bcb9d812a339
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-3-2-due-overdue-push-notifications-via-due-check-job.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Landlord who spots something (a leak, a visit tomorrow) can only wait for the daily due-check. FR-12 gives the Landlord a free-form message to all Tenants of one Home, sent now. No screen for it exists yet, and "Landlord Home Admin" has no owning story (epics.md, known open points).

**Approach:** `POST /api/homes/{home_id}/broadcast` (Landlord only, through `require_role`) pushes the message directly and synchronously to every device of every current Tenant (FR-12, AD-14, AD-16). The first story that needs the Landlord Home Admin screen builds its shell at `/hjem/<id>/utleier` with the composer; 3.5 adds cadence to it.

**Decisions (Claude's choices under Eirik's one-hour mandate, 2026-11-19; Eirik reviews them in the PR):**
1. Message is trimmed and 1–300 characters. Push title "Melding fra utleier", body is the text, tap opens `/hjem/<id>`. Each send has its own tag, so a new message never replaces an older one in the tray.
2. "Sendt til N leietakere": N is the Tenants with at least one device that accepted the push. Tenants with none (no device, all failed) are `without_push`, shown as "M har ikke slått på varsler". A Home with no current Tenants answers 409 and nothing is sent.
3. No rate limit and no retry after a failed device send (a broadcast is a one-off). Both go to `deferred-work.md`.
4. A shared `push.deliver` (all of one User's devices, deleting devices the push service reports gone) is extracted from the due-check, so both senders use one loop.

## Boundaries & Constraints

**Always:** Role check server-side before anything else; the frontend shows the composer only when `HomeOut.can_broadcast` is true (never decides the rule itself). Only current Tenants are recipients (AD-16: removed ones and everyone else in the Home get nothing). Push text goes only through the existing adapter (`get_sender`; mock without VAPID keys, FR-22). All UI text Norwegian. Send confirmation in `aria-live="polite"`; failure inline with a retry button, message text kept.

**Never:** An in-app message inbox, scheduling, or editing a sent message. Sending to Household Members or the Landlord. Naming recipients in the response or UI. Touching the due-check's behaviour (only its delivery loop moves).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Send | Landlord, 2 Tenants, one with 2 devices, one with none | 3 pushes; `recipients: 1`, `without_push: 1` | N/A |
| No Tenants | Landlord, Home has only the Landlord | 409, nothing sent | Message "Det er ingen leietakere i hjemmet ennå." |
| Wrong Role | Household Member or Tenant | 403, nothing sent | Same 403 as `require_role` |
| Not a Member | Another Home's Landlord | 403 | Same 403 |
| Bad text | Empty, only spaces, or 301 characters | 422, nothing sent | Field error |
| Removed Tenant | Tenant left, still has devices | Not counted, no push | N/A |
| Gone device | Push service answers 404/410 | Device row deleted, not counted as sent | N/A |
| Failure | Server error | Composer shows error and "Prøv igjen"; text kept | Retry resends |

</frozen-after-approval>

## Code Map

- `backend/app/domain/due_check.py` -- per-Member device loop (lines ~140–165) moves to `push.deliver`; `NamedTuple` result style, claim-before-send stays.
- `backend/app/domain/push.py` -- gets `deliver(session, sender, user_id, message) -> int`; reuses `is_allowed_endpoint` SSRF check.
- `backend/app/push/senders.py` -- `PushMessage(title, body, url, tag)`, `MOCK_SENDER` records pushes (tests read `.sent`).
- `backend/app/routes/deps.py` -- `Landlord` alias exists; `ErrorOut`, `SessionDep`.
- `backend/app/routes/homes.py` -- `HomeOut`/`home_out` get `can_broadcast`; `routes/main.py` registers the new router.
- `backend/tests/test_permissions.py` -- fails if a `{home_id}` route lacks `require_role`; the new route must pass it.
- `frontend/src/routes/MembersPage.tsx`, `App.tsx`, `TaskOverview.tsx` -- page, route and link patterns to copy.
- `frontend/src/api/queries.ts`, `errors.ts` -- mutation hooks and `ApiError`; 403 handled globally, so no inline text for it.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/app/domain/push.py`, `due_check.py` -- extract `deliver`; due-check tests stay green -- one delivery loop
- [ ] `backend/app/domain/broadcast.py` -- `can_broadcast`, `send_broadcast`, `NoTenants` -- FR-12, AD-14, AD-16
- [ ] `backend/app/routes/broadcast.py`, `main.py`, `routes/homes.py` -- route, `can_broadcast` flag
- [ ] `backend/tests/test_broadcast.py` -- the matrix; each test names the line it guards
- [ ] `frontend/src/api/broadcast.ts`, `queries.ts`, `routes/LandlordAdmin.tsx` (+css, test), `App.tsx`, `TaskOverview.tsx` -- shell, composer, link; regenerate OpenAPI and `schema.d.ts`
- [ ] PRD FR-12 (+ Revision log row), `epics.md`, AD-14 note, `deferred-work.md` -- keep requirements true to the code

**Acceptance Criteria:**
- Given the Landlord sends a message, when the endpoint returns, then every current Tenant's devices were pushed before the response (no cron).
- Given a successful send, when the composer confirms, then it shows "Sendt til N leietakere" in an `aria-live="polite"` region and names nobody.
- Given a failed send, when the Landlord sees the result, then an inline error with "Prøv igjen" shows and the text is still in the field.
- Given a Household Member or Tenant opens `/hjem/<id>/utleier`, then they are sent back to the Home.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all green
- `cd frontend && npm test -- --run && npm run lint && npm run build` -- expected: all green
- `cd backend && uv run python -m app.export_openapi && cd ../frontend && npm run gen:api` -- expected: no diff after regenerating
