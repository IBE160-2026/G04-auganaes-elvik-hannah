---
title: 'Story 1.7: Hosted Demo on Vercel (Services + Neon)'
type: 'feature'
created: '2026-11-01'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: ''
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
- Not to touch: `frontend/src/**`, `scripts/ki-logg/`, `docker-compose.yml`.

## Tasks & Acceptance

**Execution:**
- [ ] `vercel.json` -- services `frontend` (`root: "frontend/"`, `framework: "vite"`, `outputDirectory: "dist"`) and `backend` (`root: "backend/"`, `framework: "fastapi"`, `entrypoint: "app.main:app"`); rewrites `/api/(.*)` → backend, then `/(.*)` → frontend -- one domain (AD-7)
- [ ] `backend/app/config.py` -- normalisation, migration URL, Vercel guard; drop CORS -- I/O matrix
- [ ] `backend/app/db.py` -- `get_engine(url)` cached per URL, built from `settings.database_url` (one source of truth): `pool_pre_ping=True` (Neon scale-to-zero), `connect_args={"prepare_threshold": None}` with a comment (prepared statements behind PgBouncer transaction mode fail on reuse; kept until verified unnecessary) -- reused by 1.2; tests clear the cache
- [ ] `backend/app/routes/health.py` -- `GET /api/health/db` runs `SELECT 1` through the app's engine (settings on `app.state`), catches only `SQLAlchemyError` -- proves the pooled connection on the demo
- [ ] `backend/app/main.py` -- remove CORS
- [ ] `backend/alembic/env.py` -- `get_migration_url()`; xact lock as above (online mode only)
- [ ] `backend/pyproject.toml` -- `[tool.vercel.scripts] build = "python -m alembic upgrade head"`
- [ ] `backend/tests/test_config.py`, `test_health.py`, `test_db_health.py` -- the matrix rows; DB health via dependency override, no real DB
- [ ] `frontend/vite.config.ts` + `frontend/vite.config.test.ts` (`// @vitest-environment node`, added to `tsconfig.node.json`, outside `src/`) -- one `apiProxy` constant `/api` → `http://127.0.0.1:8000` (not `localhost`: Node may try `::1` first) used for `server.proxy` and `preview.proxy`; test asserts both
- [ ] `.github/workflows/neon-preview-cleanup.yml` -- on `pull_request: closed`, `neondatabase/delete-branch-action@v3` with `project_id: vars.NEON_PROJECT_ID`, `branch: preview/${{ github.head_ref }}`, `api_key: secrets.NEON_API_KEY`, `continue-on-error: true` (a PR may never have had a branch); job skipped when the variable is unset
- [ ] `.env.example`, `README.md`, `ARCHITECTURE-SPINE.md` -- as in Code Map; README gets "Nettversjon (valgfri)": URL, optional, owner-only dashboards, rollback (tag `v0.1-for-vercel-hosting`, Root Directory `frontend`, preset Vite)

**Acceptance Criteria:**
- Given Eirik's dashboard steps are done (Neon connected with preview branching, Root Directory = repo root, preset Services), when this PR's preview deploys, then `/` serves the app with `/service-worker.js`, `/api/health` and `/api/health/db` answer 200, and the Neon console shows `preview/story/1-7-hosted-demo-vercel` with an `alembic_version` table.
- Given a failing migration, when the build hook runs, then it exits non-zero (proved locally with an uncommitted revision that raises; output recorded in the PR).
- Given the PR is merged, when `main` deploys, then <https://g04husly.vercel.app> serves `/`, `/service-worker.js`, `/api/health` and `/api/health/db`, and Neon's main branch has `alembic_version`.
- Given the PR is merged, when the workflow runs, then the preview branch is gone from Neon (or the fallback is explained in the PR).
- Given `npm run dev` and `uv run fastapi dev`, when `http://localhost:5173/api/health` is opened, then it answers through the proxy.

## Implementation Notes

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

## Design Notes

Dashboard steps (Eirik, in order): (1) Storage → Neon → create the database in `aws-eu-central-1` with Postgres 17 (neither can be changed later), enable "Create database branch for deployment" for **Preview** only; (2) Settings → Build and Deployment: Root Directory empty (repo root), Framework Preset **Services** (confirm the exact dropdown name); (3) Settings → Functions: region `fra1`; (4) in GitHub, variable `NEON_PROJECT_ID` and secret `NEON_API_KEY`. Until the PR merges, other branches' previews fail, because `main` has no `vercel.json` yet. Production stays on its last good deployment, so nothing else is merged to `main` until 1.7 lands. Pushes without a PR also create Neon branches the workflow never deletes. Unverified: that the build hook runs in `backend/` with deps installed; check the first preview build log.

`/api/health/db` is the one public probe that shows the demo reaches Neon. It reveals nothing beyond up or down.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all pass
- `cd frontend && npm test -- --run && npm run lint && npm run build` -- expected: all pass
- `docker compose up -d --wait && cd backend && uv run alembic upgrade head && docker compose exec db psql -U husly -c '\dt alembic_version'` -- expected: the table exists (proves the migration committed)
- `curl -s https://<preview-url>/api/health/db` -- expected: `{"database":"ok"}`
