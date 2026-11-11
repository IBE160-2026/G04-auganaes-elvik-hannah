# Deferred Work

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-project-scaffold-design-tokens-responsive-app-shell.md`
  summary: Assign the tab bar from EXPERIENCE.md (Task Overview, Settings/Profile, Portfolio for Landlords) to a concrete story, since no story's acceptance criteria currently own it.
  evidence: The team chose a minimal shell without a tab bar in Story 1.1 (2026-10-25) to avoid navigation that leads nowhere. Story 1.2 (team decision 2026-11-01) also leaves it out, since every tab would lead to an empty page; moved to Story 1.3, the first story with a second signed-in page.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-project-scaffold-design-tokens-responsive-app-shell.md`
  summary: Add an automated check that `npm run build` emits `dist/service-worker.js` at the root (no hash), so a Vite config change cannot silently break PWA registration.
  evidence: Verification-gap review of Story 1.1; the check needs a build step in the test run, which the repo does not have yet. Today it is only verified by hand via `npm run preview`.
  outcome: Settled 2026-11-01 by the CI workflow (PR #10, issue #9): the frontend job builds and then runs `test -f dist/service-worker.js` (`.github/workflows/ci.yml`, step "service-worker.js i roten av dist"). Outcome recorded 2026-11-08 (Epic 1 retro, action 4).
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Add an automated test that `backend/alembic/env.py` uses `get_migration_url()` and takes `pg_advisory_xact_lock` inside Alembic's transaction.
  evidence: Code review of Story 1.7 (R6); today only proven by hand (spec Implementation Notes). Needs a DB-backed test harness, expected with Story 1.2/1.6.
  outcome: Accepted risk 2026-11-08 (Epic 1 retrospective, P3): no Postgres concurrency test job before Epic 2; the lock is reasoned, not tested. Recorded in `epics.md` (Additional Requirements, deferred by Architecture). Revisit if the hosted demo gets real users.
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
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Confirm the Vite service on Vercel falls back to index.html for client-side deep links (unverified, would be medium).
  evidence: Code review of Story 1.7 (R10); no client routes exist yet, so settle in the first story that adds one.
  outcome: Fixed in Story 1.2, not yet confirmed. Production answered 404 for `/logg-inn` (checked 2026-11-01), so `vercel.json` now gives the frontend service a rewrite `/(.*)` → `/index.html`; Vercel applies it only after static files, so `/service-worker.js` and other files are unaffected, and `/assets/*` is excluded so a missing chunk still gives 404. Confirm on the Story 1.2 preview that `/logg-inn` loads and `/api/health` still reaches FastAPI. Confirmed 2026-11-01 on the Story 1.2 preview: `/logg-inn` loads directly and `/api/health` still reaches FastAPI (`.logs/eirik/issues.md`, R10 row; recorded 2026-11-08, Epic 1 retro, action 4).
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
- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-create-a-home.md`
  summary: Add a concurrent Postgres test that two parallel `POST /api/homes` for a user without a Home create exactly one Home (the `with_for_update` lock in `domain/homes.create_home`).
  evidence: Code review of Story 1.3; SQLite ignores `FOR UPDATE` and CI runs pytest only on SQLite, so deleting the lock passes every check. Needs a Postgres-backed test harness (same gap as the 1.7 `env.py` lock entry).
  outcome: Accepted risk 2026-11-08 (Epic 1 retrospective, P3): no Postgres concurrency test job before Epic 2; the lock is reasoned, not tested. Recorded in `epics.md` (Additional Requirements, deferred by Architecture). Revisit if the hosted demo gets real users.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-create-a-home.md`
  summary: Decide in Story 1.4 whether accepting an invite may give a Household Member or Tenant a second Home, and enforce it in `domain/homes.add_member` rather than only in the seed.
  evidence: Code review of Story 1.3 (unverified, would be medium). `add_member` adds a Membership to any Home; only `seed/homes.py` skips Jonas when he is already in another Home. The 1.3 intent covers only the create flow ("not re-prompted"), so the rule for joining belongs to 1.4's invite acceptance.
  outcome: Settled in Story 1.4 (team decision 3, 2026-11-07). A user may be Household Member or Tenant in at most one Home; a Landlord may also join one such Home. Enforced in `domain/homes.add_member` (via `join_blocker`, with a user-row lock), so the seed follows the same rule. The parallel case has the same Postgres-only gap as the entry above.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-4-invite-members-accept-invite.md`
  summary: Add concurrent Postgres tests that two parallel accepts of one invite link give exactly one Membership (the `with_for_update` lock in `domain/invites.accept`), and that two parallel joins by one Household Member through different links give exactly one Membership (the user-row lock in `domain/homes.add_member`).
  evidence: Verification-gap review of Story 1.4. Removing either lock passes every check, because pytest runs on SQLite (which ignores `FOR UPDATE`) and the CI Postgres steps never run two accepts at once; `test_sequential_second_accept_fails` fails on `used_at`, not on the lock. Needs the same Postgres-backed test harness as the 1.3 `create_home` entry.
  outcome: Accepted risk 2026-11-08 (Epic 1 retrospective, P3): no Postgres concurrency test job before Epic 2; the lock is reasoned, not tested. Recorded in `epics.md` (Additional Requirements, deferred by Architecture). Revisit if the hosted demo gets real users.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-5-view-home-members-list-enforce-role-based-permissions.md`
  summary: Add a frontend test that a session change to another user without sign-out never shows the previous user's cached Homes, invite preview or members list (the user id in `homesKey`, `inviteKey` and `membersKey`).
  evidence: Verification-gap review of Story 1.5. Dropping the user id from `membersKey` passes every test, because each test has one user and a fresh `QueryClient`, and sign-out clears the cache. The same holds for `homesKey` and `inviteKey`, so one shared test fits better than one per story.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-task-setup-at-home-creation.md`
  summary: Let a Household Member or Landlord add custom tasks (own name, classification and Frequency) beside the catalog's, in setup or later.
  evidence: Story 2.1, decision 5 (Eirik, 2026-11-09): setup only ticks and adjusts catalog entries. The model is ready for it: a Task copies its name from the catalog, so a custom task needs only a nullable `tasks.task_type` (and `photo_evidence_eligible` false), plus a rule for the unique `(home_id, task_type)`. No story owns it yet.
  outcome: Planned 2026-11-09 (Sprint Change Proposal 2026-11-09) as Story 2.6, with archiving (FR-24). Closed when Story 2.6 is built.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-task-setup-at-home-creation.md`
  summary: Test on Postgres that the Home-row lock in `domain/tasks.set_up_tasks` stops two concurrent setups with disjoint choices from both committing.
  evidence: The tests run on SQLite, which ignores FOR UPDATE; the overlapping-race tests prove only the unique `(home_id, task_type)` backstop. Same gap as the Epic 1 lock tests (Story 1.3/1.4 entries); needs a concurrent Postgres harness in CI.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-task-setup-at-home-creation.md`
  summary: Story 2.4 must change `domain/tasks.tasks_of` from the earliest instance to the earliest open (not completed) instance.
  evidence: `tasks_of` uses `min(TaskInstance.due_on)`; once 2.4 stores completions, a completed past instance stays the earliest and the list would show an old date as «Neste gang». The architecture revision note now says so.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-9-one-rule-for-creating-homes.md`
  summary: The seed's `_seed_household` skips Jonas when he has any Membership instead of asking `homes.join_blocker`, so a Jonas who is only a Landlord elsewhere is left out although the app would let him join.
  evidence: `backend/app/seed/homes.py` (`elif jonas_home_ids:`) vs `_seed_landlord`, which uses `join_blocker`; pre-existing since Story 1.6, found in the Story 1.9 code review (R7). Fix: use `join_blocker` and add a seed test with Jonas as a Landlord elsewhere.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-adjust-task-classification-frequency.md`
  summary: Story 2.4 must switch `domain/tasks._open_instance` (the instance a Frequency change moves) to the earliest *open* instance together with `tasks_of`, so both always point at the same instance.
  evidence: Story 2.3 moves the earliest instance, which is the open one only until 2.4 adds completion. If only `tasks_of` changes, a Frequency change would move an already completed instance.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-adjust-task-classification-frequency.md`
  summary: After Story 2.5, moving the open instance on a Frequency change may hit `uq_task_instances_task_id_due_on` when another instance of the Task already has the new date; decide the behaviour (and test it) in 2.5.
  evidence: Story 2.3 spec review. Today every Task has one instance (seed and setup make one), so the shift cannot collide; once completion creates the next instance, a completed instance can share the date.
