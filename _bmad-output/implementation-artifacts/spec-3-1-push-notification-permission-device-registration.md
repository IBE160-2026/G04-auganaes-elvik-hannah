---
title: 'Story 3.1: Push Notification Permission & Device Registration'
type: 'feature'
created: '2026-11-12'
status: 'done'
baseline_commit: '0041d8d12f53011adf2aa360ed236ab8d510f8ea'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
  - '{project-root}/_bmad/custom/review-conventions.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Members cannot receive reminders: the service worker has no push support, no device is registered, and Settings says nothing about notification permission (FR-10, UX-DR17/31, issue #55).

**Approach:** Settings shows the browser's push permission status plainly and lets a Member turn notifications on. Granting creates a PushSubscription that the server stores per User and per device. A denied permission gives one dismissible inline note on Task Overview. Sending is Story 3.2.

## Boundaries & Constraints

**Always:**
- One row per device: `endpoint` is unique, and a second device adds a row, never overwrites. Registering an endpoint that exists (re-subscribe, or another User on the same browser) updates its owner and keys instead of failing. The call is idempotent. At most `MAX_SUBSCRIPTIONS_PER_USER = 10` rows per User (constant in `domain/push.py`); a new one beyond that removes the oldest.
- Sign-out removes this device's row first (`DELETE /api/push/subscriptions` with the endpoint, own rows only, 204 also when none), so a later User on a shared browser never gets the previous User's reminders. It is not an unsubscribe UI.
- With permission «granted» and no stored row for this device (e.g. another User signed in on a browser that already allowed push), Settings registers the device silently on open. This is not a permission request.
- Without an active service-worker registration (dev server, or unsupported) there is no subscribe attempt: Settings says «støttes ikke her», never an endless wait.
- Push routes are user-scoped (`/api/push/...`, `CurrentUser`), not Home-scoped. Every Role may register. A user only ever touches their own rows.
- Without VAPID keys (`VAPID_PUBLIC_KEY`/`VAPID_PRIVATE_KEY` unset) the server hands out a fixed dev public key, so subscribing works locally and offline (FR-22, AD-15). The README and `.env.example` say so and are updated in this PR; `test_env_example` must stay green.
- Permission status comes from the browser (`Notification.permission`): granted, denied, not asked, or «støttes ikke» (e.g. iOS Safari outside an installed PWA, with a hint to add to Home Screen). Text is Norwegian.
- Denied note: shown on Task Overview only while the Home has at least one task with `due_status` overdue or soon (server's value, never the browser clock). It is a single inline, dismissible note, never a modal. Dismissal is kept per user and device in `localStorage` (like `lastHome.ts`) and it is not shown again.
- The service worker gets only the `push` and `notificationclick` handlers needed to show a notification and open a URL carried in the payload. Message text and deep links belong to 3.2.

**Never:** Sending pushes, `pywebpush`, cron or the due-check job (3.2). No unsubscribe UI, no notification inbox. No server-side storage of permission state. No auto-prompt on page load; permission is asked only after a tap.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| First device | `PUT /api/push/subscriptions` with endpoint + p256dh + auth | 204; one row for the User | 401 not signed in; 422 bad body |
| Second device | Same User, new endpoint | A second row; the first is untouched | N/A |
| Same endpoint again | Same User and endpoint | Row updated, still one row | N/A |
| Endpoint of another User | Different User posts an existing endpoint | Row moves to the caller | N/A |
| Over the cap | An 11th device registers | 204; the oldest row is gone, 10 remain | N/A |
| Sign-out | Signed-in device with a row | Row deleted, then the session ends | A failed DELETE must not block sign-out |
| Granted, no row | Permission granted, this endpoint not stored | Silent registration on Settings open | Failure shows the error line |
| Denied | `Notification.permission === 'denied'` | Settings shows «blokkert»; overview note appears once something is due, until dismissed | N/A |
| Subscribe fails | `pushManager.subscribe` or the PUT rejects | Settings shows an error line, status unchanged, retry possible | `ApiError` via `toApiError` |

</frozen-after-approval>

## Code Map

- `backend/app/models/task.py`, `models/ai_usage.py` -- model style to copy (SQLModel, named constraints, UTC `created_at`); register the new model in `models/__init__.py`
- `backend/alembic/versions/a8c2f4d6b1e3_create_ai_usage.py` -- latest revision (`down_revision` for the new migration, hand-written)
- `backend/app/domain/ai_usage.py` -- domain-function style; new `domain/push.py` (`register_subscription`, upsert by endpoint)
- `backend/app/routes/ai.py`, `routes/deps.py`, `main.py` -- route style, `SessionDep`, `ErrorOut`; add `routes/push.py` and include it. `permissions/current_user.py` gives `CurrentUser`
- `backend/app/config.py` -- add `get_vapid_public_key()` with a dev default (like `DEV_JWT_SECRET`); `.env.example`, `README.md`
- `backend/tests/test_permissions.py` -- guard for `{home_id}` routes; push routes have none, so no `require_role`
- `frontend/src/service-worker.ts` -- add `push`/`notificationclick`; `tsconfig.sw.json` already types it
- `frontend/src/routes/Settings.tsx`, `TaskOverview.tsx` -- new «Varsler» section; denied note
- `frontend/src/api/` -- new `push.ts` (browser permission, subscribe, PUT) and hooks in `queries.ts`; `lastHome.ts` for the per-user `localStorage` pattern; `openapi.json` and `schema.d.ts` regenerate (`test_openapi_sync`)
- `frontend/src/no-browser-clock.test.ts` -- must stay green

## Tasks & Acceptance

**Execution:**
- [x] `backend/app/models/push_subscription.py`, `alembic/versions/…`, `models/__init__.py` -- table `push_subscriptions` (id, user_id FK, unique endpoint, p256dh, auth, created_at, updated_at) -- one row per device
- [x] `backend/app/domain/push.py`, `routes/push.py`, `main.py`, `config.py` -- upsert, `GET /api/push/config` (public key, `mock` flag) and `PUT /api/push/subscriptions` -- FR-10 prerequisite
- [x] `backend/tests/test_push.py` -- domain and route tests per the matrix (two devices, same endpoint, endpoint moved, 401, only own rows)
- [x] `frontend/src/service-worker.ts`, `api/push.ts`, `api/queries.ts` -- push handlers; status, `enablePush()`, mutation -- UX-DR31
- [x] `frontend/src/routes/Settings.tsx`, `TaskOverview.tsx` + tests -- status, enable button, denied note and dismissal
- [x] `frontend/src/api/queries.ts` (sign-out) -- delete this device's row before sign-out, ignoring failure
- [x] `README.md`, `.env.example`, `docs/ki-logg/korrigeringer.md`, `sprint-status.yaml` (3-1 in-progress → review), PRD/epics check (`PRD-drift`) -- traceability and runnability; PR links issue #55

**Acceptance Criteria:**
- Given a Member opens Settings, then permission status (granted, denied, not asked, unsupported) is shown plainly
- Given they tap «Slå på varsler» and the browser grants, then a subscription is stored for them and that device
- Given a second device grants, then the User has two independent rows
- Given permission is denied and a task is overdue or due soon, then Task Overview shows one dismissible note and never again once dismissed
- Given no VAPID keys, then everything above works offline against the mock key

## Implementation Notes

- Implemented directly in the main session (no implementation subagent: the user had not asked for subagents).
- Backend: `models/push_subscription.py`, migration `e5b7c9d1f3a2` (checked up, `alembic check`, down, up on a temporary Postgres database, never on the local `husly`), `domain/push.py`, `routes/push.py`, `config.py` (`DEV_VAPID_PUBLIC_KEY`, `push_is_mock`, `get_vapid_public_key`), `tests/test_push.py`. The dev key was generated with `openssl`; its private half was not kept.
- The sign-out DELETE carries the endpoint in a JSON body, not the URL, so the endpoint never lands in access logs.
- Frontend: `api/push.ts`, hooks in `queries.ts`, «Varsler» section in `Settings.tsx`, `DeniedPushNote` in `TaskOverview.tsx`, push handlers in `service-worker.ts` (still import-free; its test loads it by a variable path so the webworker lib stays out of the app's TypeScript program).
- Found while testing: the first Settings code registered the device twice after one tap (button, then the silent effect); the silent registration now runs only when the page opens.
- Docs: `.env.example`, README, FR-10 (clean consequences plus a Revision log row), a note in `epics.md` before Story 3.2, `korrigeringer.md`.

## Spec Change Log

## Review Triage Log

| Finding | Verdict | Evidence / route |
|---|---|---|
| Service worker `appPath` accepts `/\evil.example` | medium | Browsers read `\` as `/`, so `openWindow` could leave the app. Patch: resolve with `new URL` and compare the origin; tests for `//`, `https:` and backslash. |
| Silent-registration error stays after a working retry | medium | `register.isError` was never cleared. Patch: `register.reset()` in `turnOn`; test added. |
| `readPushStatus` can reject, leaving «Laster …» for ever | medium | `getRegistration` can throw. Patch: catch gives «unsupported»; test added. |
| Sign-out test used a 500 and never reached the `catch`; DELETE body not asserted | medium | openapi-fetch does not throw on 500. Patch: network error, body asserted. The 3 s timeout stays untested (deferred). |
| `IntegrityError` retry in `register_subscription` untested | medium | Mutation check: `raise` instead of `continue` fails the new test. Patch. |
| Silent registration failure and «granted, no subscription» untested | medium | Patch: two tests. |
| Service-worker tests could pass vacuously | low | Patch: non-optional listener call, call counts. |
| Endpoint accepts any string (SSRF with 3.2, non-ASCII index limit) | medium | Patch: ASCII https pattern, 422 tests. Host check deferred to 3.2. |
| No live region for the changed status text | low | Patch: `aria-live="polite"`. |
| PRD-drift: account data lacks push subscriptions | medium | Code right, text silent. PRD Account data and Revision log row. |
| PRD-drift: FR-10 sign-out reads as a guarantee; «once per device» vs per user; silent registration and «oldest» unstated | medium | PRD FR-10 reworded (best effort, per Member and device, silent registration, longest-ago replaced). |
| PRD-drift: epics Note lacks the fourth state; Note and log dated 11-13 | low | Epics note and PRD row fixed (today is 2026-11-12). |
| `notificationclick` opens a new window; no tag/icon | medium | Real but belongs with 3.2's text and links. Defer. |
| Subscription made with another `applicationServerKey` | medium | Only after keys change in the hosted demo. Defer. |
| Row removed only on explicit sign-out | medium | FR-10 now says best effort. Defer the expired-session path. |
| `DeniedPushNote` initial state when `userId` is undefined | false | Task Overview sits behind `RequireAuth`, so a session exists on every render; a user change signs out and remounts. |
| Note not updated when permission changes while the page is open | low | Rejected: rare, and the fix adds an event subscription. |
| Cap race for two different endpoints; double-miss `RuntimeError` | low | Rejected: needs concurrent registrations by one user; the cap is hygiene, not a rule. |
| Service worker still installing reads as «unsupported» on first visit | low | Rejected: gone after the worker activates; the fix adds a wait. |
| `_trim` «oldest» means least recently registered | low | Intended; PRD now says «registered longest ago». |
| Silent registration on every Settings open costs one PUT | false | Idempotent and by design (spec). |

## Design Notes

The dev public key is a fixed P-256 point generated once; its private half is discarded, since the mock sender (3.2) never delivers. Browsers accept it for `subscribe`, so the registration path is exercised for real even locally.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all pass
- `cd frontend && npm test -- --run && npm run lint && npm run build` -- expected: all pass

**Manual checks (if no CLI):**
- Settings in a production build (`npm run build && npm run preview`, or Docker), since the service worker registers only there: grant, deny, and a second profile as a second device; two rows in `push_subscriptions`
