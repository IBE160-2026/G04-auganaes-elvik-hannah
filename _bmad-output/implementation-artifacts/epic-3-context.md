# Epic 3 Context: Notifications

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Members get a push notification when a task becomes due or overdue, with a fairness nudge when one Member has fallen behind on a shared recurring task. Landlords can send ad-hoc broadcasts to Tenants and set how strictly Tenants are reminded. NFR2 makes silence trustworthy: no notification must mean "nothing due". Trinn 2, Must group (Story 3.1 is included because push cannot work without it).

## Stories

- Story 3.1: Push Notification Permission & Device Registration
- Story 3.2: Due/Overdue Push Notifications via Due-Check Job
- Story 3.3: Fairness-Based Targeted Notification
- Story 3.4: Landlord Ad-Hoc Broadcast Message
- Story 3.5: Landlord-Controlled Notification Cadence

## Requirements & Constraints

- FR-10 due/overdue push, FR-11 fairness nudge, FR-12 landlord broadcast, FR-13 landlord cadence.
- Push is push-only: no in-app notification inbox. Notification text names the tasks; a single-task notification opens Task Detail, several tasks open Task Overview.
- FR-22/NFR7/AD-15: the app and the automated tests run offline without team accounts. Push sits behind an adapter with a mock implementation chosen automatically when VAPID keys are missing. The mock records what it would have sent.
- If push permission is denied, Task Overview shows one dismissible inline note. It is never a modal and never a repeating nag.
- All text in the UI is Norwegian.

## Technical Decisions

- AD-12: PWA shell with `manifest.json` and a registered service worker. iOS Safari 16.4+ supports Web Push only for a Home-Screen-installed PWA, so one shared "Add to Home Screen" prompt is shown once per Member per device (tracked client-side).
- PushSubscription (endpoint + keys) belongs to a User, one row per device. A second device never overwrites the first.
- AD-8: `GET /api/internal/run-due-check`, called once a day by Vercel Cron (`0 6 * * *` UTC) with `Authorization: Bearer <CRON_SECRET>`. It is idempotent per task instance per day.
- AD-9: nudge when a Member has 0 completions in the last 3 instances of a recurring shared task and at least one other Member completed one of them.
- AD-14: the broadcast is sent directly and synchronously, independent of cron.
- Role rules are enforced server-side through `require_role`; shared route dependencies live in `backend/app/routes/deps.py`.
- The server decides the due state (`domain/tasks.due_status`). The frontend never reads the browser clock.

## UX & Interaction Patterns

- Settings (`/innstillinger`) shows the current push permission status plainly: granted, denied or not yet asked.

## Cross-Story Dependencies

- 3.2–3.5 all depend on the PushSubscriptions and the push adapter from 3.1.
- Retro item 3 was decided 2026-11-13, before Story 3.2:
  - **Day:** the UTC day stays. The cron fires at 06:00 UTC (07:00/08:00 in Oslo), so the UTC and Norwegian calendar dates are the same when the job runs; only ticks between 00:00 and 01:00/02:00 local time differ, as FR-9 already says. Story 3.2 adds one `clock.utc_today()` for the routes and the due check, so switching to Europe/Oslo later is one line plus FR-9/AD-3 (then `bmad-correct-course`).
  - **`domain/tasks.py` (566 lines):** not split. The due check goes in a new `domain/due_check.py` (and fairness in `domain/fairness.py` for 3.3); `_is_open` and `_is_active` become public so it can reuse them across Homes. Split when 3.3 has to change `_rows`, or when the file passes about 650 lines.
