# Deferred Work

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-project-scaffold-design-tokens-responsive-app-shell.md`
  summary: Assign the tab bar from EXPERIENCE.md (Task Overview, Settings/Profile, Portfolio for Landlords) to a concrete story, since no story's acceptance criteria currently own it.
  evidence: The team chose a minimal shell without a tab bar in Story 1.1 (2026-10-25) to avoid navigation that leads nowhere. Story 1.2 (team decision 2026-11-01) also leaves it out, since every tab would lead to an empty page; moved to Story 1.3, the first story with a second signed-in page.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-project-scaffold-design-tokens-responsive-app-shell.md`
  summary: Add an automated check that `npm run build` emits `dist/service-worker.js` at the root (no hash), so a Vite config change cannot silently break PWA registration.
  evidence: Verification-gap review of Story 1.1; the check needs a build step in the test run, which the repo does not have yet. Today it is only verified by hand via `npm run preview`.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Add an automated test that `backend/alembic/env.py` uses `get_migration_url()` and takes `pg_advisory_xact_lock` inside Alembic's transaction.
  evidence: Code review of Story 1.7 (R6); today only proven by hand (spec Implementation Notes). Needs a DB-backed test harness, expected with Story 1.2/1.6.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Add a CI workflow that runs pytest, ruff, Vitest, lint and build on every PR.
  evidence: Code review of Story 1.7 (R7); no workflow runs tests, so all checks are local only. Pre-existing since Story 1.1.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Confirm the Vercel build hook runs in `backend/` so `python -m alembic upgrade head` finds `alembic.ini` (unverified, would be high).
  evidence: Code review of Story 1.7 (R8); settle from the first preview build log.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Confirm a preview build can never migrate Neon's main branch when preview branching is off or branch creation fails (unverified, would be medium).
  evidence: Code review of Story 1.7 (R9); check what DATABASE_URL a preview gets when branching fails, and add a VERCEL_ENV guard if it is main's URL.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Confirm the Vite service on Vercel falls back to index.html for client-side deep links (unverified, would be medium).
  evidence: Code review of Story 1.7 (R10); no client routes exist yet, so settle in the first story that adds one.
  outcome: Fixed in Story 1.2, not yet confirmed. Production answered 404 for `/logg-inn` (checked 2026-11-01), so `vercel.json` now gives the frontend service a rewrite `/(.*)` → `/index.html`; Vercel applies it only after static files, so `/service-worker.js` and other files are unaffected, and `/assets/*` is excluded so a missing chunk still gives 404. Confirm on the Story 1.2 preview that `/logg-inn` loads and `/api/health` still reaches FastAPI.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-hosted-demo-vercel-services-neon.md`
  summary: Confirm the Neon integration names preview branches exactly `preview/<git-branch>` so the cleanup workflow deletes them (unverified, would be medium).
  evidence: Code review of Story 1.7 (R11); settle with AC 4 after the merge.
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
- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-create-a-home.md`
  summary: Decide in Story 1.4 whether accepting an invite may give a Household Member or Tenant a second Home, and enforce it in `domain/homes.add_member` rather than only in the seed.
  evidence: Code review of Story 1.3 (unverified, would be medium). `add_member` adds a Membership to any Home; only `seed/homes.py` skips Jonas when he is already in another Home. The 1.3 intent covers only the create flow ("not re-prompted"), so the rule for joining belongs to 1.4's invite acceptance.
