---
title: 'Story 1.7: Hosted Demo on Vercel (Services + Neon)'
type: 'feature'
created: '2026-11-01'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '8fb4faa62e015d46d4ccf5d8c664ba9535e26881'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Only the static frontend is online; the API has no host, so Story 1.2's login could not be tried on a PR preview. Vercel is the course's only hosting (sprint-change-proposal-2026-11-01, Story 1.7, issue #6, AD-7, AD-15).

**Approach:** Deploy `frontend/` and `backend/` as Vercel Services in the existing project `g04husly` on one domain (`/api/*` → FastAPI), with Neon Postgres per environment, migrations in the backend build, and the same `/api` origin locally through the Vite proxy. Remove Story 1.1's CORS code.

## Boundaries & Constraints

**Always:**
- Local running from the README keeps working with Docker alone, without any Vercel or Neon account (AD-15). Tests stay offline.
- The app reads `DATABASE_URL` (pooled); migrations prefer `DATABASE_URL_UNPOOLED` (direct) when it is set. Any `postgres://` or `postgresql://` URL becomes `postgresql+psycopg://` in one function in `config.py` by swapping only the scheme prefix (never re-parsing, so `%`-encoded passwords and the query string `sslmode`/`channel_binding` survive). Other schemes pass through unchanged. An empty string counts as unset.
- On Vercel (env `VERCEL` set), a missing `DATABASE_URL` is an error, never a silent fallback to localhost.
- Concurrent builds of the same branch cannot run migrations at the same time: `pg_advisory_xact_lock(<named constant>)` is the first statement *inside* Alembic's `begin_transaction()`. Never a session lock before it (SQLAlchemy autobegin would make Alembic roll everything back while exiting 0, and a session lock is meaningless through PgBouncer).
- Secrets only in Vercel / GitHub settings, never in the repo.
- Region (team decision 2026-11-01): EU (Frankfurt). Neon `aws-eu-central-1` and Vercel function region `fra1`, so household data stays in the EU and function and database sit together.

**Never:**
- No CORS middleware, no `CORS_ORIGINS` (AD-7).
- No auth, users or models (Story 1.2), no seed data (Story 1.6), no cron or Blob (Trinn 2).
- No second Vercel project.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Neon URL | `postgresql://u:p@h/db?sslmode=require&channel_binding=require` | `postgresql+psycopg://u:p@h/db?sslmode=require&channel_binding=require` | N/A |
| Heroku-style URL | `postgres://u:p@h/db` | `postgresql+psycopg://u:p@h/db` | N/A |
| Already normalised | `postgresql+psycopg://...` | unchanged | N/A |
| Local, nothing set | no env | Docker default `...@localhost:5433/husly` | N/A |
| Encoded password | `postgresql://u:p%40ss@h/db` | `postgresql+psycopg://u:p%40ss@h/db` | N/A |
| Other scheme | `postgresql+asyncpg://...` or `mysql://...` | unchanged | N/A |
| Vercel, no DB | `VERCEL=1`, `DATABASE_URL` unset or `""` | — | `RuntimeError` with a Norwegian message naming the Neon integration |
| Migration URL | both URLs set | unpooled used | falls back to `DATABASE_URL` |
| Cross-origin request | `Origin: http://evil.example` on `/api/health` | 200, no `access-control-allow-origin` header | N/A |
| DB health, DB up | `GET /api/health/db` | 200 `{"database": "ok"}` | N/A |
| DB health, DB down | `SQLAlchemyError` on connect | 503 `{"detail": "Databasen svarer ikke"}` (fixed text) | cause logged server-side; no stack trace or URL in the body |

</frozen-after-approval>

## Code Map

- `backend/app/config.py` -- `get_database_url`, `Settings`; has `parse_origins`/`DEFAULT_CORS_ORIGINS` to delete. Add `normalize_database_url`, `get_migration_url`.
- `backend/app/main.py` -- `create_app(settings)`; delete `CORSMiddleware`. Routers are mounted with `prefix="/api"`; keep that, because Vercel passes the full path through.
- `backend/app/routes/health.py` -- `/health`; add `/health/db`.
- `backend/alembic/env.py` -- already reads `get_database_url()` with `%` escaping and `NullPool`; switch to `get_migration_url()` and add the advisory lock. No migrations exist yet (`versions/.gitkeep`).
- `backend/pyproject.toml` -- `[tool.fastapi] entrypoint = "app.main:app"` exists; add `[tool.vercel.scripts] build`.
- `backend/tests/test_config.py`, `test_health.py` -- CORS tests to replace, not extend.
- `frontend/vite.config.ts` -- uses `vitest/config` `defineConfig`; keep the service-worker rolldown setup untouched.
- `.env.example`, `README.md` (sections "Kjøre appen lokalt", "Mappestruktur", "Nettversjon" line at the top) -- update.
- `ARCHITECTURE-SPINE.md` conventions row "State & cross-cutting" -- the secrets list lacks `CRON_SECRET`, `BLOB_READ_WRITE_TOKEN`; add them with a dated note (found by the epic-context compile).
- `docker-compose.yml` -- `image: postgres:17`, volume `husly-db:/var/lib/postgresql/data`. Neon was created with Postgres 18.6 (no version choice in the Vercel dialog), so local moves to 18 (spine: same major in both).
- Not to touch: `frontend/src/**`, `scripts/ki-logg/`.

## Tasks & Acceptance

**Execution:**
- [x] `vercel.json` -- services `frontend` (`root: "frontend/"`, `framework: "vite"`, `outputDirectory: "dist"`) and `backend` (`root: "backend/"`, `framework: "fastapi"`, `entrypoint: "app.main:app"`); rewrites `/api/(.*)` → backend, then `/(.*)` → frontend -- one domain (AD-7)
- [x] `backend/app/config.py` -- normalisation, migration URL, Vercel guard; drop CORS -- I/O matrix
- [x] `backend/app/db.py` -- `get_engine(url)` cached per URL, built from `settings.database_url` (one source of truth): `pool_pre_ping=True` (Neon scale-to-zero), `connect_args={"prepare_threshold": None}` with a comment (prepared statements behind PgBouncer transaction mode fail on reuse; kept until verified unnecessary) -- reused by 1.2; tests clear the cache
- [x] `backend/app/routes/health.py` -- `GET /api/health/db` runs `SELECT 1` through the app's engine (settings on `app.state`), catches only `SQLAlchemyError` -- proves the pooled connection on the demo
- [x] `backend/app/main.py` -- remove CORS
- [x] `backend/alembic/env.py` -- `get_migration_url()`; xact lock as above (online mode only)
- [x] `backend/pyproject.toml` -- `[tool.vercel.scripts] build = "python -m alembic upgrade head"`
- [x] `backend/tests/test_config.py`, `test_health.py`, `test_db_health.py` -- the matrix rows; DB health via dependency override, no real DB
- [x] `frontend/vite.config.ts` + `frontend/vite.config.test.ts` (`// @vitest-environment node`, added to `tsconfig.node.json`, outside `src/`) -- one `apiProxy` constant `/api` → `http://127.0.0.1:8000` (not `localhost`: Node may try `::1` first) used for `server.proxy` and `preview.proxy`; test asserts both
- [x] `.github/workflows/neon-preview-cleanup.yml` -- on `pull_request: closed`, `neondatabase/delete-branch-action@v3` with `project_id: vars.NEON_PROJECT_ID`, `branch: preview/${{ github.head_ref }}`, `api_key: secrets.NEON_API_KEY`, `continue-on-error: true` (a PR may never have had a branch); job skipped when the variable is unset
- [x] `docker-compose.yml` -- `postgres:18`; mount the volume at `/var/lib/postgresql` (the 18 image keeps data in `/var/lib/postgresql/18/docker` and rejects the old `/data` mount); rename the volume to `husly-db-18` so an existing 17 volume gives a fresh database instead of an error -- added after approval, 2026-11-01
- [x] `.env.example`, `README.md`, `ARCHITECTURE-SPINE.md`, `epic-1-context.md` -- as in Code Map, plus Postgres 18 in README ("Starter PostgreSQL 18", volume name, how to delete the old `husly-db` volume), the spine's Stack row (Neon Postgres 18, dated note) and epic-1-context's Stack line; README gets "Nettversjon (valgfri)": URL, optional, owner-only dashboards, rollback (tag `v0.1-for-vercel-hosting`, Root Directory `frontend`, preset Vite)

**Acceptance Criteria:**
- Given Eirik's dashboard steps are done (Neon connected with preview branching, Root Directory = repo root, preset Services), when this PR's preview deploys, then `/` serves the app with `/service-worker.js`, `/api/health` and `/api/health/db` answer 200, and the Neon console shows `preview/story/1-7-hosted-demo-vercel` with an `alembic_version` table.
- Given a failing migration, when the build hook runs, then it exits non-zero (proved locally with an uncommitted revision that raises; output recorded in the PR).
- Given the PR is merged, when `main` deploys, then <https://g04husly.vercel.app> serves `/`, `/service-worker.js`, `/api/health` and `/api/health/db`, and Neon's main branch has `alembic_version`.
- Given the PR is merged, when the workflow runs, then the preview branch is gone from Neon (or the fallback is explained in the PR).
- Given `npm run dev` and `uv run fastapi dev`, when `http://localhost:5173/api/health` is opened, then it answers through the proxy.

## Implementation Notes

Implemented 2026-11-01 (dispatch). Code done and verified locally; the dashboard steps and the preview/production ACs remain.

- `vercel.json` checked against Vercel's docs (services/routing/config-reference, 2026): `services` key (not `experimentalServices`), rewrite `destination: {"service": ...}`, the service receives the full `/api/...` path. `[tool.vercel.scripts] build` runs after dependency install (FastAPI docs); the working directory is still unverified, check the first build log.
- Deviation: `vite.config.ts` now splits Vitest into two projects (`app`: jsdom + `src/test-setup.ts`; `config`: node, `vite.config.test.ts`). The shared setup file touches `window`, so `// @vitest-environment node` alone made the config test crash, and `frontend/src/**` was off-limits. `eslint.config.js` lists the new test file as a Node file. Service-worker rolldown setup untouched.
- Local proofs (Postgres 18.6 in Docker): `alembic upgrade head` exits 0 and creates `alembic_version`; an uncommitted revision that runs DDL and then raises exits 1 and leaves neither the table nor a version row; a psql session holding `pg_advisory_xact_lock(MIGRATION_LOCK_ID)` made `alembic upgrade head` wait ~3 s and then succeed. Through `npm run dev` + `uv run fastapi dev`: `localhost:5173/api/health` 200, `/api/health/db` `{"database":"ok"}`, 503 `{"detail":"Databasen svarer ikke"}` with the DB stopped (cause logged), and ok again after restart (`pool_pre_ping`).
- `MIGRATION_LOCK_ID = 0x6875736C79` ("husly" in ASCII) in `backend/alembic/env.py`.

## Spec Change Log

## Review Triage Log

Spec review 2026-11-01 (one adversarial reviewer, verified against code and docs):

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | Session advisory lock before `begin_transaction()` makes Alembic roll back while exiting 0 | high | xact lock inside the transaction; verification checks `alembic_version` |
| 2 | Session lock through PgBouncer is meaningless | high | solved by #1 |
| 3 | delete-branch action fails when no branch exists | medium | `continue-on-error` |
| 4 | No proof that a failing migration fails the build | medium | local uncommitted failing revision, recorded in PR |
| 5 | Epic AC is about `main`/production, spec only checked preview | medium | post-merge AC added |
| 6 | Matrix gaps: `%` password, empty string, other schemes | medium | rows and rule added |
| 7 | Engine read env, ignoring `Settings`; cache leaks across tests | medium | engine from settings, cache cleared |
| 8 | `prepare_threshold` unnecessary on Neon's pooler | maybe-false | kept with a comment; settled when 1.2 runs repeated queries through the pooler |
| 9 | `localhost` may resolve to `::1`; test inside `src/` is type-checked twice | low | `127.0.0.1`, shared constant, test outside `src/` |
| 10 | Preset name unverified; merges to main break builds; Postgres major; region in vercel.json | low | first three in Design Notes; region stays in dashboard (top-level `regions` in services mode unverified) |
| 11 | Build hook cwd unverified | low | noted; check first build log |
| 12 | `/health/db` body and exception scope | low | fixed text, `SQLAlchemyError` only, logged |

Code review 2026-11-01 (blind hunter, edge-case hunter, verification gap; verified by the orchestrator):

| # | Finding | Verdict | Route / evidence |
|---|---|---|---|
| R1 | `pool_pre_ping` and `prepare_threshold` untested; removing them keeps all tests green | low | patch: test records `create_engine` kwargs |
| R2 | No connect timeout; `/api/health/db` can hang to the function timeout instead of 503 | low | patch: `connect_timeout` in `connect_args`, asserted by R1's test |
| R3 | Cleanup workflow has default `GITHUB_TOKEN` scopes | low | patch: `permissions: {}` |
| R4 | README volume cleanup uses `grep`, fails in PowerShell/cmd | low | patch: `docker volume ls --filter name=husly-db` |
| R5 | README "forrige versjon blir stående" hides that a committed migration persists if a later build step fails | low | patch: note that migrations must stay backward-compatible |
| R6 | `env.py` wiring (`get_migration_url`, xact lock) only proven by hand | medium | defer: needs a DB-backed test harness (1.2/1.6) |
| R7 | No CI runs pytest/Vitest/lint | medium | defer: pre-existing, not caused by 1.7 |
| R8 | Build hook cwd unverified (`alembic.ini` lookup) | maybe-false | defer: settled by the first preview build log (AC 1) |
| R9 | If preview branching is off or fails, a preview build could migrate Neon main | maybe-false | defer: depends on whether the integration ever hands a preview the main URL; branching is on and AC 1 checks the preview branch |
| R10 | Deep links may 404 on the Vite service without an SPA fallback | maybe-false | defer: no client routes yet (grep found none); settle when the first route lands |
| R11 | Neon may name the preview branch differently than `preview/<head_ref>` | maybe-false | defer: settled by AC 4 (branch gone after merge) |
| R12 | `create_engine` errors from a malformed URL or unsupported scheme escape the `try` (500, not 503) | low | rejected: needs a misconfigured URL; fix restructures the dependency |
| R13 | `continue-on-error` also hides auth/project-id failures | low | rejected: visible in the Neon console and checked by AC 4; a 404-only filter adds logic |
| R14 | Spec `in-review` vs sprint-status `in-progress` | false | the workflow syncs sprint-status at presentation |
| R15 | Vitest deviation missing from `korrigeringer.md`; KI-logg summary row missing | low | handled at PR time (CLAUDE.md process), not code |
| R16 | Bare `/api` goes to the SPA | low | rejected: nothing calls bare `/api` |
| R17 | Service worker cache headers; Node version not pinned on Vercel | false | Vercel revalidates non-hashed static files and honours `engines` in package.json |
| R18 | Public `/api/health/db` wakes Neon | low | rejected: intended public probe (Design Notes) |
| R19 | Narrower Vitest include could skip future `*.spec`/out-of-`src` tests | low | rejected: same files collected (6 files, 127 tests); project convention is `src/**/*.test.*` |
| R20 | Missing `DATABASE_URL` on Vercel also takes down `/api/health` | false | intended by the frozen I/O matrix (error, no fallback) |
| R21 | Whitespace or uppercase scheme not normalised | low | rejected: integration-set values; unlikely |
| R22 | No `lock_timeout` on the advisory lock | low | rejected: xact lock is released when a hung build's connection drops |

## Design Notes

Dashboard steps (Eirik, in order): (1) Storage → Neon → create the database in `aws-eu-central-1` (done 2026-11-01; the dialog offered no version choice and gave Postgres 18.6), enable "Create database branch for deployment" for **Preview** only; (2) Settings → Build and Deployment: Root Directory empty (repo root), Framework Preset **Services** (confirm the exact dropdown name); (3) Settings → Functions: region `fra1`; (4) in GitHub, variable `NEON_PROJECT_ID` and secret `NEON_API_KEY`. Until the PR merges, other branches' previews fail, because `main` has no `vercel.json` yet. Production stays on its last good deployment, so nothing else is merged to `main` until 1.7 lands. Pushes without a PR also create Neon branches the workflow never deletes. Unverified: that the build hook runs in `backend/` with deps installed; check the first preview build log.

`/api/health/db` is the one public probe that shows the demo reaches Neon. It reveals nothing beyond up or down.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all pass
- `cd frontend && npm test -- --run && npm run lint && npm run build` -- expected: all pass
- `docker compose up -d --wait && cd backend && uv run alembic upgrade head && docker compose exec db psql -U husly -c '\dt alembic_version'` -- expected: the table exists (proves the migration committed)
- `curl -s https://<preview-url>/api/health/db` -- expected: `{"database":"ok"}`
