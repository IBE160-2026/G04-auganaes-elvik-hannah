---
title: 'Story 3.2: Due/Overdue Push Notifications via Due-Check Job'
type: 'feature'
created: '2026-11-13'
status: 'in-progress'
baseline_commit: '25235d3f35d6152719cc2c1c0b0e8114d235ab60'
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

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all pass
- `cd frontend && npm test -- --run && npm run lint && npm run build` -- expected: all pass
