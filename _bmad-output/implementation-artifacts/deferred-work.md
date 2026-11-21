# Deferred Work

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-project-scaffold-design-tokens-responsive-app-shell.md`
  summary: Assign the tab bar from EXPERIENCE.md (Task Overview, Settings/Profile, Portfolio for Landlords) to a concrete story, since no story's acceptance criteria currently own it.
  evidence: The team chose a minimal shell without a tab bar in Story 1.1 (2026-10-25) to avoid navigation that leads nowhere. Story 1.2 (team decision 2026-11-01) also leaves it out, since every tab would lead to an empty page; moved to Story 1.3, the first story with a second signed-in page.
  outcome: Settled in Story 2.2 (PR #38, 2026-11-10): the tab bar with «Oppgaver» and «Innstillinger»; the Portfolio tab came with Story 6.1 (PR #87, 2026-11-21). Audit 2026-11-21.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-project-scaffold-design-tokens-responsive-app-shell.md`
  summary: Add an automated check that `npm run build` emits `dist/service-worker.js` at the root (no hash), so a Vite config change cannot silently break PWA registration.
  evidence: Verification-gap review of Story 1.1; the check needs a build step in the test run, which the repo does not have yet. Today it is only verified by hand via `npm run preview`.
  outcome: Settled 2026-11-01 by the CI workflow (PR #10, issue #9): the frontend job builds and then runs `test -f dist/service-worker.js` (`.github/workflows/ci.yml`, step "service-worker.js i roten av dist"). Outcome recorded 2026-11-08 (Epic 1 retro, action 4).
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Add an automated test that `backend/alembic/env.py` uses `get_migration_url()` and takes `pg_advisory_xact_lock` inside Alembic's transaction.
  evidence: Code review of Story 1.7 (R6); today only proven by hand (spec Implementation Notes). Needs a DB-backed test harness, expected with Story 1.2/1.6.
  outcome: Accepted risk 2026-11-08 (Epic 1 retrospective, P3): no Postgres concurrency test job before Epic 2; the lock is reasoned, not tested. Recorded in `epics.md` (Additional Requirements, deferred by Architecture). Revisit if the hosted demo gets real users.
  outcome: Settled 2026-11-21 (`story/pg-samtidighetstester`): `backend/tests/postgres/test_concurrency.py` races several threads, each with its own Session, against a real Postgres in the CI job «Migreringer (Postgres 18)» (eight rounds per test; locally skipped without `HUSLY_POSTGRES_TEST_URL`). `test_two_deploys_migrating_at_once_both_succeed_and_reach_head` runs two `alembic upgrade head` processes at once.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Add a CI workflow that runs pytest, ruff, Vitest, lint and build on every PR.
  evidence: Code review of Story 1.7 (R7); no workflow runs tests, so all checks are local only. Pre-existing since Story 1.1.
  outcome: Settled 2026-11-01 by PR #10 (issue #9): `.github/workflows/ci.yml` runs pytest, ruff, Vitest, ESLint and the build on every PR and on `main`, on Linux and Windows, plus migrations and seed against Postgres 18. Outcome recorded 2026-11-08 (Epic 1 retro, action 4).
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Confirm the Vercel build hook runs in `backend/` so `python -m alembic upgrade head` finds `alembic.ini` (unverified, would be high).
  evidence: Code review of Story 1.7 (R8); settle from the first preview build log.
  outcome: Settled 2026-11-01: Eirik saw `alembic_version` in the Neon branch `preview/story/1-7-hosted-demo-vercel` after the first preview build, so the build step runs in `backend/` (`.logs/eirik/997-2026-11-01-13-10-35-story-1-7-hostet-demo-vercel.md`). Outcome recorded 2026-11-08 (Epic 1 retro, action 4).
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Confirm a preview build can never migrate Neon's main branch when preview branching is off or branch creation fails (unverified, would be medium).
  evidence: Code review of Story 1.7 (R9); check what DATABASE_URL a preview gets when branching fails, and add a VERCEL_ENV guard if it is main's URL.
  outcome: Open 2026-11-21 (audit): the build step is `[tool.vercel.scripts] build` in `backend/pyproject.toml`, and `DATABASE_URL` for Preview is a hidden secret, so the CLI cannot show whether a failed branch creation would fall back to main. Eirik can check in the Neon console (Epic 1 retro, action 5).
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Confirm the Vite service on Vercel falls back to index.html for client-side deep links (unverified, would be medium).
  evidence: Code review of Story 1.7 (R10); no client routes exist yet, so settle in the first story that adds one.
  outcome: Fixed in Story 1.2, not yet confirmed. Production answered 404 for `/logg-inn` (checked 2026-11-01), so `vercel.json` now gives the frontend service a rewrite `/(.*)` → `/index.html`; Vercel applies it only after static files, so `/service-worker.js` and other files are unaffected, and `/assets/*` is excluded so a missing chunk still gives 404. Confirm on the Story 1.2 preview that `/logg-inn` loads and `/api/health` still reaches FastAPI. Confirmed 2026-11-01 on the Story 1.2 preview: `/logg-inn` loads directly and `/api/health` still reaches FastAPI (`.logs/eirik/issues.md`, R10 row; recorded 2026-11-08, Epic 1 retro, action 4). Confirmed 2026-11-21 (audit): Production answers 200 for `/logg-inn`, `/portefolje` and `/hjem/x`.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Confirm the Neon integration names preview branches exactly `preview/<git-branch>` so the cleanup workflow deletes them (unverified, would be medium).
  evidence: Code review of Story 1.7 (R11); settle with AC 4 after the merge.
  outcome: Settled 2026-11-01: after PR #8 was merged, the cleanup workflow deleted the preview branch in Neon (step `success`), so the branch name matches (`.logs/eirik/997-…md`). Later PRs are still to be checked (Epic 1 retro, action 5). Outcome recorded 2026-11-08 (Epic 1 retro, action 4).
- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-account-registration-login.md`
  summary: Let the database enforce lowercase emails (`CHECK (email = lower(email))` or a unique index on `lower(email)`), not only `accounts.normalize_email`.
  evidence: Review of Story 1.2. `uq_users_email` is on the raw column, so a write that bypasses `accounts.register` (e.g. the Story 1.6 seed) could create `Ola@…` beside `ola@…`. Low today, since register is the only write path; the 1.6 seed should call `accounts.register`.
  outcome: Partly settled in Story 1.6: the seed creates users only through `accounts.register`, so it cannot create mixed-case emails. Kept open for any later raw-SQL write until the database itself enforces lowercase.
- source_spec: none
  summary: Build the tab bar from EXPERIENCE.md (Task Overview, Settings/Profile, Portfolio for Landlords with ≥2 Homes) in Story 2.2, and add it to 2.2's acceptance criteria in epics.md.
  evidence: Split from Story 1.3 by the team (2026-11-07). After 1.3 only a placeholder Home page and sign-out exist, so the tab bar would point at near-empty pages; Story 2.2 delivers Task Overview, its first real content. 1.3 gives Landlords a plain "create another Home" link instead.
  outcome: Settled in Story 2.2 (PR #38, 2026-11-10) and Story 6.1 (PR #87, Portfolio tab, shown when `HomesOut.has_portfolio`). Audit 2026-11-21.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-create-a-home.md`
  summary: Add a concurrent Postgres test that two parallel `POST /api/homes` for a user without a Home create exactly one Home (the `with_for_update` lock in `domain/homes.create_home`).
  evidence: Code review of Story 1.3; SQLite ignores `FOR UPDATE` and CI runs pytest only on SQLite, so deleting the lock passes every check. Needs a Postgres-backed test harness (same gap as the 1.7 `env.py` lock entry).
  outcome: Accepted risk 2026-11-08 (Epic 1 retrospective, P3): no Postgres concurrency test job before Epic 2; the lock is reasoned, not tested. Recorded in `epics.md` (Additional Requirements, deferred by Architecture). Revisit if the hosted demo gets real users.
  outcome: Settled 2026-11-21 (`story/pg-samtidighetstester`): `backend/tests/postgres/test_concurrency.py` races several threads, each with its own Session, against a real Postgres in the CI job «Migreringer (Postgres 18)» (eight rounds per test; locally skipped without `HUSLY_POSTGRES_TEST_URL`). `test_two_parallel_household_creates_make_one_home`.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-create-a-home.md`
  summary: Decide in Story 1.4 whether accepting an invite may give a Household Member or Tenant a second Home, and enforce it in `domain/homes.add_member` rather than only in the seed.
  evidence: Code review of Story 1.3 (unverified, would be medium). `add_member` adds a Membership to any Home; only `seed/homes.py` skips Jonas when he is already in another Home. The 1.3 intent covers only the create flow ("not re-prompted"), so the rule for joining belongs to 1.4's invite acceptance.
  outcome: Settled in Story 1.4 (team decision 3, 2026-11-07). A user may be Household Member or Tenant in at most one Home; a Landlord may also join one such Home. Enforced in `domain/homes.add_member` (via `join_blocker`, with a user-row lock), so the seed follows the same rule. The parallel case has the same Postgres-only gap as the entry above.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-4-invite-members-accept-invite.md`
  summary: Add concurrent Postgres tests that two parallel accepts of one invite link give exactly one Membership (the `with_for_update` lock in `domain/invites.accept`), and that two parallel joins by one Household Member through different links give exactly one Membership (the user-row lock in `domain/homes.add_member`).
  evidence: Verification-gap review of Story 1.4. Removing either lock passes every check, because pytest runs on SQLite (which ignores `FOR UPDATE`) and the CI Postgres steps never run two accepts at once; `test_sequential_second_accept_fails` fails on `used_at`, not on the lock. Needs the same Postgres-backed test harness as the 1.3 `create_home` entry.
  outcome: Accepted risk 2026-11-08 (Epic 1 retrospective, P3): no Postgres concurrency test job before Epic 2; the lock is reasoned, not tested. Recorded in `epics.md` (Additional Requirements, deferred by Architecture). Revisit if the hosted demo gets real users.
  outcome: Settled 2026-11-21 (`story/pg-samtidighetstester`): `backend/tests/postgres/test_concurrency.py` races several threads, each with its own Session, against a real Postgres in the CI job «Migreringer (Postgres 18)» (eight rounds per test; locally skipped without `HUSLY_POSTGRES_TEST_URL`). `test_two_parallel_accepts_of_one_link_give_one_membership` and `test_one_user_joining_two_homes_at_once_joins_one`.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-5-view-home-members-list-enforce-role-based-permissions.md`
  summary: Add a frontend test that a session change to another user without sign-out never shows the previous user's cached Homes, invite preview or members list (the user id in `homesKey`, `inviteKey` and `membersKey`).
  evidence: Verification-gap review of Story 1.5. Dropping the user id from `membersKey` passes every test, because each test has one user and a fresh `QueryClient`, and sign-out clears the cache. The same holds for `homesKey` and `inviteKey`, so one shared test fits better than one per story.
  outcome: Settled 2026-11-21 (`fix/smaating`): `queries.test.tsx` checks that the user id is in `homesKey`, `membersKey`, `inviteKey`, `tasksKey` and `portfolioKey`, and that a session change shows the next user a fresh load; the mutation (dropping the id from `homesKey`) fails it.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-task-setup-at-home-creation.md`
  summary: Let a Household Member or Landlord add custom tasks (own name, classification and Frequency) beside the catalog's, in setup or later.
  evidence: Story 2.1, decision 5 (Eirik, 2026-11-09): setup only ticks and adjusts catalog entries. The model is ready for it: a Task copies its name from the catalog, so a custom task needs only a nullable `tasks.task_type` (and `photo_evidence_eligible` false), plus a rule for the unique `(home_id, task_type)`. No story owns it yet.
  outcome: Planned 2026-11-09 (Sprint Change Proposal 2026-11-09) as Story 2.6, with archiving (FR-24). Settled in Story 2.6 (2026-11-12): `tasks.task_type` is nullable (a custom Task has no catalog key), uniqueness of catalog type and lower-case name is a partial unique index on active Tasks only, and `domain/tasks.photo_evidence_eligible` is false for a custom Task (AD-6). Tested by `test_only_flagged_catalog_tasks_may_require_photo_evidence` and the index tests in `test_tasks.py`.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-task-setup-at-home-creation.md`
  summary: Test on Postgres that the Home-row lock in `domain/tasks.set_up_tasks` stops two concurrent setups with disjoint choices from both committing.
  evidence: The tests run on SQLite, which ignores FOR UPDATE; the overlapping-race tests prove only the unique `(home_id, task_type)` backstop. Same gap as the Epic 1 lock tests (Story 1.3/1.4 entries); needs a concurrent Postgres harness in CI.
  outcome: Settled 2026-11-21 (`story/pg-samtidighetstester`): `backend/tests/postgres/test_concurrency.py` races several threads, each with its own Session, against a real Postgres in the CI job «Migreringer (Postgres 18)» (eight rounds per test; locally skipped without `HUSLY_POSTGRES_TEST_URL`). `test_two_parallel_setups_with_different_choices_commit_only_one`.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-task-setup-at-home-creation.md`
  summary: Story 2.4 must change `domain/tasks.tasks_of` from the earliest instance to the earliest open (not completed) instance.
  evidence: `tasks_of` uses `min(TaskInstance.due_on)`; once 2.4 stores completions, a completed past instance stays the earliest and the list would show an old date as «Neste gang». The architecture revision note now says so.
  outcome: Settled in Story 2.4 (2026-11-11): every Task read goes through `domain/tasks._rows`, which joins the one open instance (`completed_at IS NULL`, at most one per Task by `uq_task_instances_open_task_id`). Tested by `test_next_due_is_the_open_instance_not_an_earlier_completed_one`.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-9-one-rule-for-creating-homes.md`
  summary: The seed's `_seed_household` skips Jonas when he has any Membership instead of asking `homes.join_blocker`, so a Jonas who is only a Landlord elsewhere is left out although the app would let him join.
  evidence: `backend/app/seed/homes.py` (`elif jonas_home_ids:`) vs `_seed_landlord`, which uses `join_blocker`; pre-existing since Story 1.6, found in the Story 1.9 code review (R7). Fix: use `join_blocker` and add a seed test with Jonas as a Landlord elsewhere.
  outcome: Settled 2026-11-21 (`fix/smaating`): `_seed_household` asks `homes.join_blocker`; `test_a_jonas_who_is_only_a_landlord_elsewhere_still_joins`.

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-adjust-task-classification-frequency.md`
  summary: Story 2.4 must switch `domain/tasks._open_instance` (the instance a Frequency change moves) to the earliest *open* instance together with `tasks_of`, so both always point at the same instance.
  evidence: Story 2.3 moves the earliest instance, which is the open one only until 2.4 adds completion. If only `tasks_of` changes, a Frequency change would move an already completed instance.
  outcome: Settled in Story 2.4 (2026-11-11): `_open_instance` and `tasks_of` read the same open instance (`_is_open`), so a Frequency change never moves a completed one. Tested by `test_only_the_open_instance_moves` and `test_a_frequency_change_after_completion_moves_only_the_open_instance`.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-adjust-task-classification-frequency.md`
  summary: After Story 2.5, moving the open instance on a Frequency change may hit `uq_task_instances_task_id_due_on` when another instance of the Task already has the new date; decide the behaviour (and test it) in 2.5.
  evidence: Story 2.3 spec review. Today every Task has one instance (seed and setup make one), so the shift cannot collide; once completion creates the next instance, a completed instance can share the date.
  outcome: Settled in Story 2.4 (2026-11-11): the unique `(task_id, due_on)` is replaced by the partial unique index `uq_task_instances_open_task_id` (one open instance per Task), so dates no longer collide; a completed instance may share the open one's date. Tested by `test_a_completed_instance_may_share_the_open_ones_date` and probed on Postgres in CI.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-6-add-and-remove-tasks.md`
  summary: Give a Tenant a neutral text when every Task of the Home is archived («Ingen oppgaver i hjemmet ennå.») instead of «Utleier har ikke satt opp oppgaver ennå.», which is only true before setup.
  evidence: Code review of Story 2.6 (Blind Hunter, Edge Case Hunter). The wording follows EXPERIENCE.md's «No active Tasks» row (decided 2026-11-09), so changing it is a UX decision, not a patch; `TASK_MESSAGES.tenantWaiting` is used for both states in `TaskOverview.tsx`.
  outcome: Settled 2026-11-21 (`fix/smaating`): a Tenant of a Home whose Tasks are all archived reads «Ingen oppgaver i hjemmet ennå.» (`TASK_MESSAGES.tenantNoTasks`); «Utleier har ikke satt opp oppgaver ennå.» stays for a Home before setup.

- source_spec: `_bmad-output/implementation-artifacts/spec-5-1-contextual-quick-answer.md`
  summary: Check «?» with a screen reader: the live region sits in a `hidden` panel, so the skeleton text at the moment of opening may not be announced, and the failure text has `role="alert"` inside the polite region.
  evidence: Code review of Story 5.1 (Blind Hunter). Jest-dom cannot show what a screen reader says. Fix if it matters: keep a visually hidden status element outside the panel and drop `role="alert"` there.
  outcome: Open 2026-11-21: manual check, part of C1 (screen reader pass) in `docs/plan-eirik-steffen-2026-11-22.md`.

- source_spec: `_bmad-output/implementation-artifacts/spec-3-1-push-notification-permission-device-registration.md`
  summary: Before Story 3.2 sends pushes, check that a stored endpoint does not point at an internal address, and consider an allowlist of known push-service hosts.
  evidence: Code review of Story 3.1 (Blind Hunter, Edge Case Hunter). 3.1 only accepts an ASCII https URL; the server does not yet POST to it, so the SSRF risk starts with 3.2.
  outcome: Settled in Story 3.2 (PR #61): `domain/push.py` checks the push address against allowed hosts before sending, so an address outside them is dropped, not called (SSRF). Audit 2026-11-21.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-1-push-notification-permission-device-registration.md`
  summary: In the service worker, focus and navigate an existing app window on `notificationclick` before opening a new one, and give notifications a `tag`, `icon` and `badge` so several pushes do not stack.
  evidence: Code review of Story 3.1 (Blind Hunter, Edge Case Hunter). Today every tap opens a new tab. It belongs with the message text and deep links of Story 3.2.
  outcome: Settled in Story 3.2 (PR #61): `frontend/src/service-worker.ts` focuses an existing window on `notificationclick` and gives each notification a `tag` and `badge`. Audit 2026-11-21.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-1-push-notification-permission-device-registration.md`
  summary: When real VAPID keys are set after devices subscribed with the dev key, compare the browser subscription's `applicationServerKey` with the server's key and re-subscribe on a mismatch.
  evidence: Code review of Story 3.1 (Edge Case Hunter). A stale subscription is stored and the push service rejects the real pushes. Matters when the hosted demo gets real keys (Story 3.2); locally the key never changes.
  outcome: Settled in Story 3.1/3.2: `frontend/src/api/push.ts` compares the subscription's `applicationServerKey` with the server's key and re-subscribes on a mismatch. Audit 2026-11-21.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-1-push-notification-permission-device-registration.md`
  summary: Remove the device's push row also when the session ends without the «Logg ut» button (expired token), or let the server drop it.
  evidence: Code review of Story 3.1 (Blind Hunter, Edge Case Hunter). FR-10 now says removal is best effort. The 3-second timeout of the sign-out request is untested (a real timer would slow the suite).
  outcome: Accepted 2026-11-21 (audit): FR-10 says removal is best effort. The server deletes a row the push service reports as gone (404/410, `domain/push.py`), so a stale device disappears on the next send. An expired session without «Logg ut» leaves the row until then.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-2-due-overdue-push-notifications-via-due-check-job.md`
  summary: Give `run_due_check` a time budget and isolate each Member's send block, so a slow push service or an unexpected error cannot cost later Members their notification.
  evidence: Code review of Story 3.2 (Edge Case Hunter, Blind Hunter), unverified, would be medium. Sends are sequential with 10 s per device and claims are committed per Member before sending. Fine at course scale; revisit if the demo gets many devices.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-2-due-overdue-push-notifications-via-due-check-job.md`
  summary: Treat 401/403 from a push service (VAPID key mismatch) as a stale device: delete the row or flag it, instead of logging «failed» every day.
  evidence: Code review of Story 3.2 (Edge Case Hunter), unverified, would be medium. Matters when real VAPID keys replace the dev key in the hosted demo; confirm what each push service answers first.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-2-due-overdue-push-notifications-via-due-check-job.md`
  summary: Add a `pushsubscriptionchange` handler to the service worker so a rotated endpoint or key re-registers without opening Settings.
  evidence: Code review of Story 3.2 (Blind Hunter), medium. Today a device is re-registered only when Settings is opened.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-2-due-overdue-push-notifications-via-due-check-job.md`
  summary: Decide `ON DELETE` behaviour for `push_subscriptions` and `due_notifications` when account deletion (PRD §5) is built, and test that deleting a user leaves no such rows.
  evidence: Code review of Story 3.2 (Blind Hunter, Edge Case Hunter). Both tables have foreign keys to `users` without `ON DELETE`; no account deletion exists yet.
  outcome: Settled in Story 1.10 (2026-11-21, AD-17): the user row is anonymised and kept, so no foreign key is ever broken and no `ON DELETE` is needed; `domain/account_deletion` deletes the user's push devices and claimed notifications by statement. Guarded by `test_every_table_that_points_at_users_or_homes_is_handled`.

- source_spec: `_bmad-output/implementation-artifacts/spec-3-2-due-overdue-push-notifications-via-due-check-job.md`
  summary: Add a test that the one-task push path (`/hjem/<home>/oppgaver/<task>`) matches a route in `frontend/src/App.tsx`.
  evidence: Code review of Story 3.2 (Verification Gap), low. The backend builds the path and the frontend defines the route; only string literals tie them together.
  outcome: Settled 2026-11-21 (`fix/smaating`): `test_the_one_task_push_path_matches_a_route_in_the_frontend` reads the `<Route path>` list in `frontend/src/App.tsx` and matches the url the due-check builds.

- source_spec: `_bmad-output/implementation-artifacts/spec-3-4-landlord-ad-hoc-broadcast-message.md`
  summary: Decide whether a Landlord needs a limit on how many broadcasts can be sent per Home per day.
  evidence: Story 3.4 decision 3: none built. A Landlord can send many messages and every Tenant device gets each one. No FR asks for a limit; add one if the PRD does.
  outcome: Accepted 2026-11-21 (audit): no FR asks for a limit (Story 3.4 decision 3). Revisit only if the PRD gets one.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-4-landlord-ad-hoc-broadcast-message.md`
  summary: Time budget for the synchronous broadcast: each device send can wait 10 s, so a Home with many Tenants and slow push services could pass the function limit.
  evidence: Story 3.4 sends in one request (AD-14). Fine for a few Tenants. Same family as the due-check's open time-budget item from Story 3.2.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-4-landlord-ad-hoc-broadcast-message.md`
  summary: Mark the Landlord's send confirmation as a demo when the mock sender is active (like the `demo` flag in Story 5.1), so «Sendt til N» is not read as delivered on Vercel without VAPID keys.
  evidence: Blind Hunter on Story 3.4. README now says it; the UI does not. Low until the hosted demo is shown to someone who sends as Landlord.
  outcome: Settled 2026-11-21 (`fix/smaating`): `BroadcastOut.demo` is true for the mock sender, and the confirmation adds «Demo: ingen ekte varsler er sendt.» (`test_the_confirmation_says_demo_only_for_the_mock_sender`).

- source_spec: `_bmad-output/implementation-artifacts/spec-3-4-landlord-ad-hoc-broadcast-message.md`
  summary: Check with a screen reader that a second send with the same count is announced (the live region gets identical text), together with the open screen reader check of the AI popover.
  evidence: Blind Hunter on Story 3.4. The notice is cleared and set in the same render batch, so the region may not see an empty state.
  outcome: Open 2026-11-21: manual check, part of C1 (screen reader pass) in `docs/plan-eirik-steffen-2026-11-22.md`.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-1-landlord-requires-photo-evidence-on-eligible-must-tasks.md`
  summary: Decide whether a Tenant should see on Task Detail that the Landlord requires a photo, before Story 4.2 adds the upload.
  evidence: Story 4.1 stores the requirement but shows it only to the Landlord. Until 4.2 a Tenant can still complete the task without a photo, so the setting has no effect.
  outcome: Settled in Story 4.2 (PR #73): a Tenant on a task that requires a photo sees «Last opp bilde» instead of the checkbox, and the server answers 409 for a tick without a photo. Audit 2026-11-21.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-1-landlord-requires-photo-evidence-on-eligible-must-tasks.md`
  summary: Show a Norwegian message with a retry when a request fails without a response (offline), in the Landlord Home Admin sections of Stories 3.4, 3.5 and 4.1.
  evidence: Edge Case Hunter on Story 4.1. A thrown network error is not an ApiError, so its raw text is shown and some retry buttons are hidden. One fix in `api/client.ts` or `errors.ts` would cover all three.
  outcome: Settled 2026-11-21 (`fix/smaating`): `failureText` in `api/errors.ts` turns an error without an answer into «Vi fikk ikke kontakt med tjenesten. Sjekk nettverket og prøv igjen.» in the three Landlord Home Admin sections, each with its retry.

- source_spec: `_bmad-output/implementation-artifacts/spec-4-1-landlord-requires-photo-evidence-on-eligible-must-tasks.md`
  summary: Tell the Landlord when a change of a task to Bør removed its Photo Evidence requirement.
  evidence: Blind Hunter on Story 4.1. A household editor or the Landlord changing Must to Should silently drops the requirement (FR-18 decision 3).
  outcome: Settled 2026-11-21 (`fix/smaating`): saving a task with a photo requirement as Bør says «Lagret. Kravet om bilde er fjernet, siden oppgaven nå er Bør.»

- source_spec: `_bmad-output/implementation-artifacts/spec-4-2-tenant-uploads-photo-evidence-with-immediate-auto-approval.md`
  summary: Run the Blob adapter against a real private store and confirm `put_blob` with `allow_overwrite` and `get_blob` behave as `BlobPhotoStore` assumes.
  evidence: The adapter is written from the SDK signatures and tested only with fakes. It cannot be exercised offline; a store has to be created in Vercel first.
  outcome: Story 4.3 (2026-11-20) found that the adapter called the async SDK functions without `await` and stored nothing; it now uses `vercel.blob.sync`, guarded by a test. Confirmed by Eirik on Vercel Preview, 2026-11-20: upload as Tenant and view as Landlord work against the real private Blob store.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-2-tenant-uploads-photo-evidence-with-immediate-auto-approval.md`
  summary: Make a photo that was stored but whose completion then failed impossible to leave behind, for example by writing to a temporary key first.
  evidence: Story 4.2 decision 6: the photo is stored before the completion commits, so a failed commit leaves the new photo under the key until the next upload.
  outcome: Settled 2026-11-21 (`fix/foto-robusthet`): `complete_with_photo` reads the previous photo before storing and puts it back (or deletes the new one) when the completion fails (`test_a_failed_completion_puts_the_old_photo_back`). A crash between the store and the restore can still leave one photo; that is the same window as before, now one write wide.

- source_spec: `_bmad-output/implementation-artifacts/spec-4-2-tenant-uploads-photo-evidence-with-immediate-auto-approval.md`
  summary: Show a Tenant who uploaded the text that was saved with the photo, or confirm the Landlord's view (Story 4.3) is the only place it appears.
  evidence: Story 4.2 saves the description but no screen shows it yet.
  outcome: Settled in Story 4.3 (2026-11-20): only the Landlord sees the photo and description; a Tenant, also the uploader, gets 403 (AC 4, NFR6).
- source_spec: `_bmad-output/implementation-artifacts/spec-4-2-tenant-uploads-photo-evidence-with-immediate-auto-approval.md`
  summary: Scrub or derive the uploader's name in the saved description when account deletion and anonymisation (PRD §5) are built.
  evidence: Blind Hunter and Edge Case Hunter on Story 4.2. `photo_evidence.description` keeps the display name at upload time, so anonymising the user row would not remove it.
  outcome: Settled in Story 1.10 (2026-11-21): `delete_account` rewrites the uploader's name in `photo_evidence.description` to «Tidligere medlem» for Homes that remain (`test_a_home_with_other_members_stays_and_keeps_the_history`).

- source_spec: `_bmad-output/implementation-artifacts/spec-4-2-tenant-uploads-photo-evidence-with-immediate-auto-approval.md`
  summary: Check that a JPEG upload is decodable (end marker or a decode) before storing it, and test two parallel uploads against Postgres.
  evidence: Edge Case Hunter on Story 4.2. Only the JPEG signature is checked, and the row lock that serializes parallel uploads does nothing on SQLite, so it is not exercised by the tests.
  outcome: Settled 2026-11-21 (`fix/foto-robusthet`): `check_photo` also requires the JPEG end marker (padding zeros allowed), so a cut-off or glued-on file is refused (`test_check_photo_refuses_a_cut_off_jpeg_and_accepts_padding`). A full decode was not added. The parallel-upload Postgres test stays with the concurrency tests.

- source_spec: `_bmad-output/implementation-artifacts/spec-4-3-landlord-reviews-evidence-auto-replacing-photo-storage.md`
  summary: Guard against the Blob cache serving old bytes for up to 60 s after a replacement (compare the object's upload time with `uploaded_at`, or set a short cache control on write), and make the info and image reads one consistent pair.
  evidence: Blind Hunter on Story 4.3 against AD-5 («the review view relies on the pointer's timestamp, not on the cached object»). The view reads straight from the store; only the local store is tested, and the real Blob behaviour is unverified.
  outcome: Accepted 2026-11-21 (Epic 4 retro A4, Eirik): known limit in AD-5. No fix built.
- source_spec: `_bmad-output/implementation-artifacts/spec-4-3-landlord-reviews-evidence-auto-replacing-photo-storage.md`
  summary: Map any non-SDK exception from the Blob read (network, timeout) to `StorageError`, and add a test that the photo-serving route guard also catches a GET under another path name.
  evidence: Edge Case Hunter on Story 4.3; the adapter catches only `BlobError` and `BlobNotFoundError`, and the route guard filters on «evidence» and «tasks» in the path.
  outcome: Settled 2026-11-21 (`fix/foto-robusthet`): the Blob adapter maps every failure of the SDK or the network to `StorageError` (`test_any_failure_of_the_blob_sdk_is_a_storage_error`), and the route guard test now covers any GET whose path names evidence, photo or image.

- source_spec: `_bmad-output/implementation-artifacts/spec-3-3-fairness-based-targeted-notification.md`
  summary: Add a test that drives `fairness._claim` into its `IntegrityError` branch (a parallel run inserted the nudge row), and batch the per-instance history queries in `apply_nudges`.
  evidence: Verification Gap and Blind Hunter on Story 3.3. The race path and the N+1 queries are untested and unbudgeted; they sit with the 3.2 time-budget item.
  outcome: Settled 2026-11-21 (`story/pg-samtidighetstester`): `backend/tests/postgres/test_concurrency.py` races several threads, each with its own Session, against a real Postgres in the CI job «Migreringer (Postgres 18)» (eight rounds per test; locally skipped without `HUSLY_POSTGRES_TEST_URL`). `test_two_runs_claiming_one_nudge_both_succeed_and_leave_one_row`. The N+1 batching in `apply_nudges` is not done (B2).

- source_spec: `_bmad-output/implementation-artifacts/spec-5-2-escalate-to-full-ai-chat.md`
  summary: The chat stream has no auto-scroll to the newest message and no maximum height, so after several exchanges the input can sit below the fold; do the screen-reader pass together with the popover (A3).
  evidence: Blind Hunter on Story 5.2; the stream is a plain growing `div`. Cosmetic for five exchanges, but the `role="log"` announces content the user may not see.
  outcome: Settled 2026-11-21 (PR #88, Epic 5 retro D1): the stream has a maximum height, scrolls to the newest line and is reachable by keyboard. The screen reader pass stays with C1.
- source_spec: `_bmad-output/implementation-artifacts/spec-5-2-escalate-to-full-ai-chat.md`
  summary: A failed chat message is shown from the mutation state, so sending a different message instead of pressing «Prøv igjen» removes it from the transcript; keep failed messages as their own list items if this matters.
  evidence: Blind Hunter on Story 5.2; the retry and the history rule (a failed turn is never sent) hold, only the transcript forgets the failed line.
  outcome: Settled 2026-11-21 (PR #88, Epic 5 retro D1): a failed message is its own line with its own «Prøv igjen», and a retry moves it to the end.
- source_spec: `_bmad-output/implementation-artifacts/spec-5-2-escalate-to-full-ai-chat.md`
  summary: Smoke test a follow-up with history against real Gemini on Preview: multi-turn `contents` with plain-text model turns must still give the JSON schema answer within 10 s.
  evidence: Verification Gap on Story 5.2; the Gemini provider is covered only over `httpx.MockTransport` and no key exists locally.
  outcome: Settled 2026-11-21: on Production three chat messages with growing history answered `ok`, `demo: false`, in 1.7–2.5 s (`epic-6-retro-2026-11-21.md`, Behavior verification).
- source_spec: `_bmad-output/implementation-artifacts/spec-5-3-ai-generated-onboarding-guide.md`
  summary: Smoke test the guide against real Gemini on Preview: the guide instruction and the `{intro}` JSON schema must give a Norwegian introduction of at most 120 words within 10 s.
  evidence: Blind Hunter and Verification Gap on Story 5.3; the Gemini guide path is covered only over `httpx.MockTransport` and no key exists locally.
  outcome: Settled 2026-11-21: on Production the guide came back with `source: "ai"`, a Norwegian introduction of about 75 words, within 2.3 s including Task Setup (`epic-6-retro-2026-11-21.md`).
- source_spec: `_bmad-output/implementation-artifacts/spec-5-3-ai-generated-onboarding-guide.md`
  summary: A Home that got the fixed introduction (AI failed or the Landlord had used the day's calls) keeps it; add a Landlord action to write it again if this matters.
  evidence: Blind Hunter on Story 5.3; `store_guide` never replaces a row by design (written once), and FR-16 now says so.
  outcome: Accepted 2026-11-21 (audit): written once by design (FR-16); a «write it again» action is not built. The Home keeps the fixed text, which is correct and general.

- source_spec: `_bmad-output/implementation-artifacts/spec-6-1-landlord-portfolio-dashboard.md`
  summary: Screen reader check of the Portfolio: nothing announces that the detail column changed when a row is selected, and focus does not move.
  evidence: Review (Verification Gap, Blind Hunter): `aria-pressed` and the swapped detail section are the only signals on tablet and up; to be checked with VoiceOver together with Story 5.1's popover check.
  outcome: Open 2026-11-21: manual check, part of C1 (screen reader pass) in `docs/plan-eirik-steffen-2026-11-22.md`.

## Audit 2026-11-21

Every entry above was read against the code on 2026-11-21 and the ones that were already done or decided got an `outcome:` line. The entries without an `outcome:` are open, and are planned as follows (the fixing PR adds the outcome):

- **Postgres concurrency tests** (create_home, invites.accept and add_member, set_up_tasks, adjust_task, photo upload, `fairness._claim`, `env.py` lock): one story with a Postgres-backed test job in CI.
- **Photo robustness** (decodable JPEG, a stored photo left behind when the completion fails, non-SDK Blob exceptions, the route guard test): one PR.
- **Small UX and tests** (neutral Tenant text when all Tasks are archived, offline message in Landlord Home Admin, notice when Bør removes the photo requirement, demo marker on the broadcast confirmation, `lower(email)` in the database, cross-user cache test, one-task push path test, seed `join_blocker`, regenerate the fixed guide text): one or two PRs.
- **Push reliability** (time budget and isolation per Member, 401/403 as a stale device, `pushsubscriptionchange`, broadcast time budget, `ON DELETE`): waits for B1 (real push on a device), as decided 2026-11-21.
- **Account deletion with anonymisation** (also scrubs the uploader's name in the photo description and decides `ON DELETE`): `bmad-correct-course`, then a story.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-10-account-deletion.md`
  summary: Join and delete race: `homes.add_member` locks the user row but not the Home, so a Tenant who joins a Landlord Home while its Landlord deletes the account can get an unhandled integrity error (500) when the Home is gone; add a Postgres concurrency test and a `FOR UPDATE` on the Home in the join path.
  evidence: Edge Case Hunter on Story 1.10. `delete_account` locks the Landlord's Homes, but the join path does not take the same lock. Rare, and the joiner only sees an error.
  outcome: Settled 2026-11-21 (`story/pg-samtidighetstester`): `backend/tests/postgres/test_concurrency.py` races several threads, each with its own Session, against a real Postgres in the CI job «Migreringer (Postgres 18)» (eight rounds per test; locally skipped without `HUSLY_POSTGRES_TEST_URL`). `homes.add_member` now locks the Home row after the user row and raises `HomeGone`, `invites.accept` locks user, Home, then link (the order account deletion uses, so no deadlock), and `test_a_landlord_deleting_while_a_tenant_joins_never_strands_either` checks both outcomes.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-10-account-deletion.md`
  summary: No throttle on wrong passwords at `POST /api/auth/delete-account` (nor at sign-in), so a stolen access token could try passwords there without a limit.
  evidence: Blind Hunter and Edge Case Hunter on Story 1.10. Accepted as a known limit at course scale: FR-25 says attempts are not limited, as for sign-in. Add a per-user or per-IP throttle for both routes if the demo gets real users.
  outcome: Accepted 2026-11-21 (Story 1.10): stated in FR-25.
