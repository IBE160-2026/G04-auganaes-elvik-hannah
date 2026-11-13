---
title: 'Story 3.2: Due/Overdue Push Notifications via Due-Check Job'
type: 'feature'
created: '2026-11-13'
status: 'in-review'
baseline_commit: '8ee040febd7d597edfbd391509b190f42c74e69e'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
  - '{project-root}/_bmad/custom/review-conventions.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Devices are registered (3.1) but nothing is ever sent, so a Member still has to open the app to learn that a task is due (FR-10, AD-8, issue #60).

**Approach:** `GET /api/internal/run-due-check`, called daily by Vercel Cron with a Bearer secret, finds every Member's due and overdue tasks and sends each Member one push covering all of them. A sender adapter (real Web Push, or a mock that records) hides delivery. The job is safe to run twice. The 3.1 risk points are closed in the same story.

## Boundaries & Constraints

**Always:**
- Day = `clock.utc_today()` (new, one line; routes now use it too instead of `utc_now().date()`). Due check: open instance of an active Task, `due_on <= today`, for every current Member of the Home (AD-16: only current Memberships, never former).
- One push per Member per run, with all their tasks across Homes. One task: title/body name it, `url` is its Task Detail path. Several: body names the first and counts the rest, `url` is `/`. Text Norwegian, payload under 3 KB.
- Idempotency: before sending, claim `(task_instance_id, user_id, day)` in table `due_notifications` (unique). Only newly claimed pairs are sent. A second or concurrent call finds them claimed and sends nothing. A failed send is logged and not retried that day (at most once, accepted risk per AD-8).
- Auth: `Authorization: Bearer <CRON_SECRET>`, compared in constant time; wrong or missing gives 401. Unset `CRON_SECRET` rejects every call on Vercel and whenever real VAPID keys are set; only local mock mode runs without it.
- Mock without VAPID keys: the mock sender records what it would send (in memory, readable by tests; logged). `push_is_mock()` picks the sender (AD-15). Tests never touch the network.
- A push service answering 404/410 for an endpoint deletes that row (covers sign-outs that never reached the server).
- SSRF: an endpoint must match a push-service host allowlist (`fcm.googleapis.com`, `updates.push.services.mozilla.com`, `*.notify.windows.com`, `web.push.apple.com`, `*.push.apple.com`), checked at registration (422) and again before each send (row skipped).
- Sign-out removal uses `POST /api/push/subscriptions/remove` (body: endpoint) instead of `DELETE` with a body; the old route is removed.
- VAPID key change: Settings' registration compares the browser subscription's `applicationServerKey` with the server's key and re-subscribes on a mismatch.
- Service worker: a tap focuses and navigates an open app window before opening a new one; notifications get `tag`, `icon` and `badge`.
- `_is_open` and `_is_active` become public (`is_open`, `is_active`) in `domain/tasks.py`; no other split. README, `.env.example` (`CRON_SECRET`), `vercel.json` (`crons`) updated.

**Decisions (Eirik, 2026-11-13):** (1) only due today or earlier counts, not «due soon»; (2) every current Member of any Role is notified; (3) claim first, a failed send is lost for that day; (4) SSRF protection is the host allowlist.

**Never:** Fairness nudge (3.3), broadcast (3.4), cadence (3.5), a notification inbox, an in-process scheduler, retry queues.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Happy path | Mari has 2 tasks due/overdue, 2 devices | One push per device, listing both; `url` `/` | N/A |
| One task | Jonas has one due task | Push names it; `url` its detail path | N/A |
| Nothing due | All tasks later | Nothing sent, nothing claimed | N/A |
| Twice | Second call, same day | Sends nothing | 200 with `sent: 0` |
| Concurrent | Two overlapping calls | Unique claim: exactly one sends | Loser's `IntegrityError` is skipped |
| Left Home | User no longer a Member | No push for that Home | N/A |
| No devices | Member has no subscription | Claimed, nothing sent | N/A |
| Dead endpoint | Sender reports 410 | Row deleted | Other devices still sent |
| Bad secret | Missing or wrong Bearer | 401, nothing scanned | N/A |
| Foreign host | Stored endpoint off the allowlist | Skipped, not POSTed | 422 at registration |

</frozen-after-approval>

## Code Map

- `backend/app/clock.py` -- add `utc_today()`; `routes/tasks.py` (lines ~170, 252, 306, 330) switch to it; `domain/tasks.due_status`, `_rows` stay as they are
- `backend/app/domain/tasks.py` -- rename `_is_open`/`_is_active` to public; update internal callers and docstring
- `backend/app/domain/due_check.py` (new) -- scan current Members' due instances, claim, build message, call sender; uses `Membership`, `Task`, `TaskInstance`, `PushSubscription`
- `backend/app/models/due_notification.py`, `alembic/versions/…` (down_revision `e5b7c9d1f3a2`), `models/__init__.py` -- claim table
- `backend/app/push/` (new): `senders.py` (Protocol, `MockSender`, `WebPushSender` over `pywebpush`, chosen by `push_is_mock()`), `hosts.py` (allowlist), like `app/ai/providers.py`
- `backend/app/routes/internal.py` (new), `main.py`, `config.py` (`get_cron_secret`), `routes/push.py` (allowlist in `Endpoint`, POST remove), `domain/push.py`
- `backend/pyproject.toml`/`uv.lock` -- pin `pywebpush`
- `backend/tests/test_permissions.py` -- the internal route has no `{home_id}`, so it needs no `require_role`; test that it is not exposed to a user token
- `frontend/src/service-worker.ts`, `api/push.ts` (key compare, POST remove), its tests; `vercel.json`, `README.md`, `.env.example`, PRD FR-10 + Revision log, `epics.md`

## Tasks & Acceptance

**Execution:**
- [ ] `clock.py`, `routes/tasks.py`, `domain/tasks.py` -- `utc_today()`, public `is_open`/`is_active` -- retro decision
- [ ] `models/due_notification.py`, migration, `domain/due_check.py` -- claim and message -- FR-10, SM-9b
- [ ] `push/senders.py`, `push/hosts.py`, `routes/internal.py`, `config.py`, `main.py`, `vercel.json` -- sender adapter, auth, cron
- [ ] `routes/push.py`, `domain/push.py`, `frontend/src/api/push.ts`, `service-worker.ts` -- 3.1 risk points
- [ ] `backend/tests/test_due_check.py`, `test_push.py`, frontend tests -- matrix cases; each test guards a named line
- [ ] README, `.env.example`, `docs/ki-logg/korrigeringer.md`, `sprint-status.yaml`, PRD/epics (`PRD-drift`) -- traceability

**Acceptance Criteria:**
- Given tasks due today and overdue, when the job runs with the right secret, then each Member gets one push naming all of theirs, and a second run sends nothing
- Given no VAPID keys, when the job runs, then the mock records the pushes and no network is used
- Given a user who left a Home, when the job runs, then nothing is sent for that Home

## Implementation Notes

- Implemented directly in the main session (no implementation subagent; the user asked for subagents only for the reviewers).
- Backend: `clock.utc_today()` now backs every `utc_now().date()` in app code; `domain/due_check.py`, `models/due_notification.py` (migration `b9d3e7a1c5f4`, checked up, `alembic check`, down, up on a temporary Postgres database, never on `husly`), `push/` (`senders.py`, `hosts.py`), `routes/internal.py`, `pywebpush==2.5.0`.
- The allowlist also accepts any subdomain of `push.services.mozilla.com` (Firefox's regional hosts), a little wider than the spec's single host.
- Frontend: `service-worker.ts` (tag, icon, badge, `renotify`, focus then navigate), `api/push.ts` (key comparison, POST remove).
- Not verifiable here: real delivery through `pywebpush` and the Vercel Cron call (both need the hosted demo). Eirik sets `CRON_SECRET` under Production in Vercel; a real run needs VAPID keys under Preview or Production.

## Spec Change Log

## Review Triage Log

| Finding | Verdict | Evidence / route |
|---|---|---|
| Cron path in `vercel.json` not tied to the route | medium | No test read `vercel.json`; a renamed route would pass everything. Patch: test reads the file and calls the path. |
| PRD-drift: «call without the correct secret is refused» vs local mock mode (3 reviewers) | medium | Code right (FR-22, AC 5). Patch: FR-10, epics note, AD-8 reworded. |
| PRD-drift: AD-8 says «has been sent», code claims before sending | medium | Patch: AD-8 revised with a dated note. |
| PRD-drift: Privacy Constraints say only the AI call leaves the system | medium | Patch: the encrypted push text is named. |
| PRD-drift: Notification reliability NFR says «sent» | medium | Patch: says «claimed», failures logged. |
| PRD-drift: FR-10 description «target only the Member(s) who haven't acted» | medium | That is FR-11. Patch: description reworded. |
| PRD-drift: tray replacement and 24 h expiry unstated | low | Patch: one sentence in FR-10. |
| PRD-drift: 10 s timeout, 200-entry mock buffer, `NAMES_SHOWN`, 401 | low | Reject: implementation choices below the requirement. |
| `due_notifications` grows without retention; no `ON DELETE` | medium | Patch: each run deletes claims from earlier days (test). Account deletion and cascades: deferred. |
| Test named «unique» does not exercise the constraint; `deque_empty`; `type: ignore`; ttl not asserted; no two-Homes test | medium | Patch: renamed, direct duplicate-insert test, helpers simplified, ttl asserted, two-Homes test added. |
| `usesKey` branch without a key untested | low | Patch: Settings test. |
| `renotify` cast hides option errors | low | Patch: narrow `PushNotificationOptions` type. |
| Failure log without cause | low | Patch: logs the exception class. |
| README lacks that Cron runs only in Production | medium | Patch: README says where `CRON_SECRET` goes. |
| Claim before send loses a day for a Member without devices, a failed or 429/5xx send, or a crash | medium | Reject: decision 3 (Eirik, 2026-11-13) and matrix row «No devices»; AD-8 accepted risk. |
| No time budget or per-Member error isolation in `run_due_check` | medium | Defer: unverified at course scale (few devices; Vercel default 300 s). |
| 401/403 from the push service (key mismatch) not handled | medium | Defer: unverified until real VAPID keys run on the demo. |
| Stored endpoint outside the allowlist skipped every day, never cleaned | low | Reject: only pre-allowlist dev rows; the fix adds a branch. |
| Stale-key unsubscribe followed by a failed subscribe leaves the old row | low | Reject: the old endpoint answers 404/410 and the job deletes the row. |
| Backend deep-link path vs `App.tsx` route only tied by strings | low | Defer: stable route from Story 2.x. |
| No `pushsubscriptionchange` handler | medium | Defer: the device re-registers when Settings is opened. |
| `focus` succeeds then `navigate` fails opens a second window; `matchAll` rejects | low | Reject: rare, fallback intended and tested. |
| Summer time: `0 6 * * *` is 08:00 in summer | false | FR-10 says «around 07:00–08:00», which covers both. |
| Allowlist wider than spec (Mozilla suffix) | low | Reject: Mozilla's own domain; noted. |
| Spec wording «first», «`sent: 0`», «under 3 KB» | false | Matches PRD («the first few»); the response fields are `members/tasks/pushes`; names are capped at 100 characters. |
| «Bearer hemmelig » (trailing space) may not reach the handler | false | The test passes with 401; a stripped header would give 200. |
| `GET` changes state | false | Vercel Cron only calls GET (AD-8). |
| Index on `(user_id, day)` | low | Reject: the table is one day long now. |

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all pass
- `cd frontend && npm test -- --run && npm run lint && npm run build` -- expected: all pass
