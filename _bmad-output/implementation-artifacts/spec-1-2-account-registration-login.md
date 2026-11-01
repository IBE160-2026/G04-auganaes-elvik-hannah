---
title: 'Story 1.2: Account Registration & Login'
type: 'feature'
created: '2026-11-01'
status: 'done'
baseline_commit: 'cbf88d5417ac2b83a7a4a9123bc56f2b75a49259'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nobody can have an account yet, so no later story (Homes, invites, roles) has a user to attach to. Story 1.2 (issue #5, AD-7) adds registration, login and silent token refresh on the same origin built in Story 1.7.

**Approach:** Add a `User` table and migration, plus `/api/auth/{register,login,refresh,me}`. An access JWT is returned in the body and kept in memory, and the refresh JWT goes in an httpOnly cookie scoped to `/api/auth/refresh`. The frontend gets its first routes (sign in, register, a protected start page) and its first generated API client with TanStack Query.

**Decisions (team, 2026-11-01):**
- Registration asks for email, password and **display name** (`name`, trimmed, 1–50 characters), so 1.5 and the Task Overview can show "Mari" instead of an email.
- Password: **minimum 8**, maximum 128 characters, no composition rules.
- Signed in, the user lands on a start page "Du er logget inn som {name}" with a **"Logg ut"** button. `POST /api/auth/logout` clears the refresh cookie (204, idempotent), and the frontend drops the token and goes to `/logg-inn`.
- **No tab bar** in 1.2: every tab would lead to an empty page. The `deferred-work.md` entry moves to Story 1.3.
- The spec is kept whole despite its size (~2,900 tokens): it covers one user goal across layers.
- **Spec review (team, 2026-11-01):** the `Secure` flag is on only on Vercel, or locally when `AUTH_COOKIE_SECURE=true`, so a reviewer on Safari needs no `.env` (finding 9). The JWT gets a random `jti`, which makes rotation testable (finding 4). Register's 409 reveals that an email exists. That is accepted, because it matches EXPERIENCE.md's "Logg inn i stedet" (finding 14).

## Boundaries & Constraints

**Always:**
- Layering: `routes/auth.py` stays thin; registration and credential checks live in `domain/accounts.py`; the `User` model lives in `models/user.py`.
- JWT (HS256) carries only `sub` (user id as a string), `type` (`access`/`refresh`), `jti` (random), `iat` and `exp`. It never carries a Role (AD-2). Decoding requires all five claims and `algorithms=["HS256"]`.
- Access token 15 min, refresh token 30 days. Every refresh issues a new refresh cookie with a new value (rotation).
- Refresh and logout are `POST` only. The refresh cookie is `httpOnly`, `SameSite=Lax`, `Path=/api/auth/refresh`. `Secure` is set when `VERCEL` is set (always, whatever the variable says), or locally when `AUTH_COOKIE_SECURE=true`. Setting and clearing the cookie use the same attributes, through one helper.
- `JWT_SECRET` comes from env. If it is missing locally, a fixed dev default of at least 32 bytes is used and a warning is logged. On Vercel (`VERCEL` set), startup fails if it is missing or shorter than 32 bytes, the same pattern as `DATABASE_URL`.
- Email is stripped and lowercased before it is stored or looked up, and it is unique. Passwords are hashed with Argon2 (`pwdlib`).
- Login with an unknown email still runs one hash verification, so its timing does not reveal whether the account exists.
- The frontend calls only relative `/api/...` paths, through one `openapi-fetch` client typed from `openapi-typescript`, wrapped in TanStack Query. Components never call `fetch` directly.
- All UI copy is in Norwegian. Components use only tokens and pass `tokens.test.ts`.
- Forms meet the accessibility floor from the epic context: visible `<label>`s; `autocomplete` set to `email`/`name`/`current-password`/`new-password`; the error tied to its field with `aria-describedby` and `aria-invalid`; focus moved to the first invalid field; a single column at 320px.
- Tests run offline with no Docker (SQLite in-memory for domain/route tests).

**Never:** CORS middleware or `CORS_ORIGINS`; tokens in `localStorage`/`sessionStorage`; a Role on `User`; password reset, email verification, rate limiting or OAuth (not in Trinn 1); a refresh-token table or a revocation list.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error handling |
|---|---|---|---|
| Register OK | new email, name, valid password | 201 `{access_token, token_type, user: {id, email, name}}`, refresh cookie set | — |
| Register duplicate | `Ola@X.no ` when `ola@x.no` exists, or two concurrent registrations | 409 `{"detail": "Det finnes allerede en konto med denne e-posten."}`; UI shows it inline with a "Logg inn i stedet" link | no user created; `IntegrityError` → 409, never 500 |
| Register invalid | bad email, password <8 or >128, name blank or >50 | 422; UI shows the field-level message (also checked client-side) | — |
| Logout | with or without a cookie | 204, cookie cleared | frontend signed out either way |
| Login OK | correct credentials, any email casing | 200 as register, new cookie | — |
| Login wrong | wrong password **or** unknown email | 401 `{"detail": "Feil e-post eller passord."}`, the same body for both | inline, no reload |
| Refresh OK | valid refresh cookie | 200 new access token + rotated cookie | — |
| Refresh bad | missing/expired/tampered cookie, or an access token sent as refresh | 401, cookie cleared | frontend → signed out |
| Me | valid access token | 200 `{id, email, name}` | expired → 401 → frontend refreshes once and retries |
| 401 on `/api/auth/*` | e.g. wrong password at login | shown as is | frontend never refreshes or retries on these |
| Wrong method | `GET` refresh/logout | 405 | — |
| Access as refresh | refresh JWT sent as `Bearer` | 401 | — |
| User deleted | valid token for a missing user | 401 | — |

</frozen-after-approval>

## Code Map

- `backend/app/config.py` -- `Settings` (frozen dataclass) with `get_settings()`, `_env()` and the Vercel guard in `get_database_url()`. Add `jwt_secret` and `cookie_secure` with the same pattern. `backend/tests/test_config.py` has the autouse `clean_env`; add the new variable names there.
- `backend/app/main.py` -- `create_app(settings)` stores settings on `app.state`; mount the `auth` router with `prefix="/api"`.
- `backend/app/db.py` -- `get_engine(url)` cached, with psycopg-only `connect_args` (`prepare_threshold`, `connect_timeout`) that SQLite rejects. Add a `get_session` dependency (reading the URL from `request.app.state.settings`, like `routes/health.py:app_engine`). Tests override `get_session`; they never call `get_engine` with an SQLite URL. Keep `prepare_threshold: None` (see Design Notes).
- `backend/uv.lock` -- `email-validator` 2.3.0 is already locked via `fastapi[standard]`; do not pin it separately.
- `frontend/package.json` -- TypeScript pinned to `6.0.3`; `openapi-typescript@7.13.0` declares peer `typescript ^5.x`, so `npm ci` fails without an override.
- `backend/app/models/__init__.py` -- empty. Import `User` here, because `alembic/env.py` imports `app.models` to register tables.
- `backend/alembic/versions/` -- only `.gitkeep`. The first revision creates `users`; `alembic/env.py` is not changed.
- `backend/pyproject.toml` -- add `pyjwt`, `pwdlib[argon2]`, `email-validator` (exact pins), then `uv lock`.
- `frontend/src/App.tsx` -- placeholder start page with a disabled button "Innlogging kommer i neste versjon". Replace it with the router.
- `frontend/src/components/{AppShell,PrimaryButton}.tsx` -- reuse. `PrimaryButton` already has `disabled`/`disabledReason`; its in-flight label is "Sender…" (epic context).
- `frontend/src/{api,routes}/.gitkeep` -- empty folders reserved by the spine.
- `frontend/src/test-setup.ts` -- jsdom setup; extend it only if the router or fetch needs it.
- `frontend/vite.config.ts` -- `apiProxy` already proxies `/api` in dev and preview. Do not change it.
- `vercel.json` -- rewrites `/api/(.*)` → backend, `/(.*)` → frontend. Deep-link fallback unverified (deferred R10).
- `.github/workflows/ci.yml` -- the migrations job runs only `alembic upgrade head` on Postgres 18; the frontend job runs `npm ci`, test, lint and build. Both get one step each (see Tasks).
- Not to touch: `alembic/env.py`, `service-worker.ts`, `scripts/ki-logg/`.

## Tasks & Acceptance

**Execution:**
- [x] `backend/pyproject.toml`, `backend/uv.lock` -- add `pyjwt`, `pwdlib[argon2]` (exact pins) -- JWT, Argon2; check that argon2 wheels exist for Windows and the Vercel Python runtime
- [x] `backend/app/config.py` + `tests/test_config.py` -- `jwt_secret`, `cookie_secure`, Vercel guard -- Boundaries
- [x] `backend/app/models/user.py`, `models/__init__.py` -- `User` (`__tablename__ = "users"`: `user` is reserved in Postgres; UUIDv4 `id`, unique `email`, `name`, `password_hash`, `created_at` as `DateTime(timezone=True)`, serialised with an offset)
- [x] `backend/alembic/versions/<rev>_create_users.py` -- autogenerate, then review by hand: `timestamptz`, UUID, a named unique constraint, a working `downgrade`
- [x] `backend/app/db.py` -- `get_session`
- [x] `backend/app/domain/accounts.py` -- `register` (catches `IntegrityError` → `EmailTaken`), `authenticate` (with a dummy hash for unknown emails), `EmailTaken`
- [x] `backend/app/domain/tokens.py` -- issue and decode access/refresh tokens, checking `type`
- [x] `backend/app/permissions/current_user.py` -- `current_user` dependency from `Authorization: Bearer`
- [x] `backend/app/routes/auth.py`, `main.py` -- `register`, `login`, `refresh`, `logout`, `me`; cookie set/clear helpers in one place
- [x] `backend/tests/conftest.py`, `test_accounts.py`, `test_tokens.py`, `test_auth_routes.py` -- every matrix row. Setup: `app.dependency_overrides[get_session]` with `create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})` + `create_all`, and `TestClient(app, base_url="https://testserver")` so that Secure cookies are sent. Assert the raw `Set-Cookie` header: `HttpOnly`, `SameSite=lax`, `Path=/api/auth/refresh`, `Max-Age`, `Secure` only with `VERCEL`/`AUTH_COOKIE_SECURE=true`; logout gives `Max-Age=0` with the same path; a rotated cookie has a new value. Test emails use `example.com`
- [x] `backend/app/export_openapi.py` + `frontend/openapi.json` + `backend/tests/test_openapi_sync.py` -- write with `indent=2`, `ensure_ascii=False`, `newline="\n"`; the test compares parsed JSON with `create_app().openapi()` (not bytes, so CRLF on Windows is fine)
- [x] `frontend/package.json`, `package-lock.json` -- add `react-router`, `@tanstack/react-query`, `openapi-fetch`; dev: `openapi-typescript` with `"overrides": {"openapi-typescript": {"typescript": "$typescript"}}` (no `legacy-peer-deps`); verify that `gen:api` runs under TS 6. A `gen:api` script writes `src/api/schema.d.ts` from `openapi.json`
- [x] `frontend/src/api/{client,auth,queries}.ts` -- in-memory token store; `openapi-fetch` middleware that adds `Bearer`. A 401 on a request that carried a Bearer token, outside `/api/auth/*`, triggers one shared refresh and one retry; if refresh fails → signed out. 422s are mapped by `loc` to Norwegian field messages
- [x] `frontend/src/routes/{SignIn,Register,Start,RequireAuth}.tsx` + `.css` -- forms with labels, inline field errors, "Sender…"; on app load, one silent refresh restores the session before routes render
- [x] `frontend/src/App.tsx`, `main.tsx` -- `QueryClientProvider`, router: `/logg-inn`, `/registrer`, `/` (protected)
- [x] `frontend/src/**/*.test.tsx` -- refresh-and-retry once, shared refresh for concurrent 401s, a wrong-password 401 makes no refresh call, inline errors, redirect when signed out, no token in Web Storage
- [x] `.github/workflows/ci.yml` -- migrations job: add `alembic downgrade base && alembic upgrade head`; frontend job: add `npm run gen:api && git diff --exit-code src/api/schema.d.ts`
- [x] `.env.example`, `README.md` -- `JWT_SECRET` (≥32 bytes, how to generate one), `AUTH_COOKIE_SECURE`; "first login" steps; `gen:api` workflow; Vercel needs `JWT_SECRET` (Production + Preview)
- [x] `deferred-work.md` -- record the R10 outcome; move the tab bar entry to Story 1.3 (team decision)

**Acceptance Criteria:**
- Given Eirik has set `JWT_SECRET` for Production and Preview in Vercel, when this PR's preview deploys, then registering, logging in and reloading the page (silent refresh) work, and `/logg-inn` opened directly loads the app (not a 404). If it gives a 404, an SPA fallback is added to `vercel.json` in this PR.
- Given Safari on macOS locally (`npm run dev`, no `.env`) and Safari on macOS and iOS on the HTTPS preview, when a user logs in, then the cookie is set and a reload keeps them signed in. iOS is tested only on the preview, because an iPhone cannot reach `localhost` and no browser stores a `Secure` cookie over HTTP to a LAN IP.
- Given DevTools on the preview, when signed in, then Local/Session Storage hold no token, and the cookie shows `HttpOnly`, `Secure`, `SameSite=Lax`, path `/api/auth/refresh`.
- Given a clean clone, when the README is followed, then a user can register and log in locally without a `.env`.

## Implementation Notes

Implemented 2026-11-01 (bmad-build, implemented inline rather than by a subagent).

- **Pins:** `pyjwt==2.15.1`, `pwdlib[argon2]==0.3.1` (`argon2-cffi-bindings` 26.1.0 ships abi3 wheels for `win_amd64` and `manylinux_2_28_x86_64`, so Windows and the Vercel runtime need no compiler). `email-validator` is not pinned separately (Code Map). Frontend: `react-router` 8.5.1, `@tanstack/react-query` 5.105.1, `openapi-fetch` 0.17.0, dev `openapi-typescript` 7.13.0 with the npm override; `npm ci` from clean and `gen:api` run under TS 6.0.3.
- **Refresh rule, as built:** the middleware adds `Bearer` to every request except the four credential endpoints (`register`, `login`, `refresh`, `logout`), and only a request that carried a Bearer may refresh-and-retry. That keeps the matrix row "Me: expired → refresh once and retry" (`/api/auth/me` is under `/api/auth/*`) while the credential 401s (wrong password, bad cookie) never refresh. The retry goes straight to `fetch`, not through the middleware, so a second 401 cannot loop.
- **Start page** reads the name through `useMe()` (`GET /api/auth/me`), so the Bearer + refresh path is exercised in the real app, not only in tests.
- **`test-setup.ts`** got one shim: Node's `Request` (used under jsdom) rejects relative URLs, which browsers resolve against the page. The shim resolves them like a browser, so the client keeps relative `/api` paths.
- **R10 deep links:** production answered 404 for `/logg-inn` before this change, so the frontend service in `vercel.json` got a rewrite `/(.*)` → `/index.html` (Vercel applies rewrites after static files). To be confirmed on this PR's preview (AC 1).
- **Concurrent duplicate registration:** a two-thread test against a shared SQLite connection would be flaky, especially on Windows CI. Instead a test proves `register` does no pre-check query, so the unique constraint (`IntegrityError` → 409) is the only gate, which is exactly the path a race takes.
- **Verified locally** against Docker Postgres 18 through the Vite proxy with curl: register 201 with the cookie attributes from the spec (no `Secure` locally), duplicate in other casing 409, me 200, refresh 200, wrong and unknown login same 401, logout 204 with `Max-Age=0`, refresh after logout 401, `GET` refresh 405, `/logg-inn` 200 from Vite. Migration upgrade → downgrade → upgrade exits 0, and `alembic check` finds no drift.
- **Not verified here (needs a person):** Safari macOS/iOS and the preview ACs (1–3).

## Spec Change Log

## Review Triage Log

Spec review 2026-11-01 (one adversarial reviewer, verified against code and the npm registry; decisions on 4, 9 and 14 by the team):

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | `openapi-typescript@7.13.0` peer `typescript ^5.x` vs pinned 6.0.3 → `npm ci` ERESOLVE | high | npm `overrides`, verify gen:api |
| 2 | 401 middleware would refresh on login/refresh 401s (loop, sign-out on wrong password) | high | only Bearer requests outside `/api/auth/*`; test |
| 3 | Design note claimed rotation invalidates tokens; stateless tokens never are | medium | note rewritten |
| 4 | Same-second refresh tokens identical → rotation untestable | medium | `jti` claim (team) |
| 5 | `get_engine` psycopg `connect_args` break SQLite tests | medium | override `get_session` in tests |
| 6 | Naive `datetime` → `timestamp` without tz | medium | `DateTime(timezone=True)` |
| 7 | Migration downgrade untested in CI | medium | CI step |
| 8 | `schema.d.ts` drift not checked in CI; byte comparison breaks on CRLF | medium | CI step; parsed-JSON compare |
| 9 | `Secure` on by default locally may break Safari for a reviewer | medium | Secure only on Vercel or opt-in (team) |
| 10 | iOS cannot test against `localhost` | medium | iOS on preview only |
| 11 | TestClient on `http://testserver` drops Secure cookies | medium | `https://testserver`, assert raw header |
| 12 | Logout must clear with identical path/attributes | medium | one helper; `Max-Age=0` test |
| 13 | Methods for refresh/logout unspecified (GET + Lax = cross-site navigation) | low | POST only; 405 test |
| 14 | Register 409 reveals existence; concurrent duplicate → 500 | low | accepted and noted (team); `IntegrityError` → 409 |
| 15 | PyJWT key length/`sub` string/`require`; email-validator already locked; `.test` domains rejected; 422s in English | low | Boundaries + tasks updated |

Code review 2026-11-01 (Blind Hunter, Edge Case Hunter, Verification Gap; 33 findings, verified against the code):

| Finding | Verdict | Route / action |
|---|---|---|
| Tampered-token test edits the last base64 char, which partly holds padding bits, so it can still verify (rare flake) | medium | patch: tamper a middle char |
| Focus moved in a microtask before React renders `aria-invalid`/message after an async 401/409/422 | medium | patch: `flushSync` then focus |
| No CI check that the migration matches the models (a dropped `uq_users_email` would pass everything) | medium | patch: `alembic check` in CI |
| SPA rewrite serves HTML 200 for a missing `/assets/*` chunk | low | patch: rewrite excludes `assets/` |
| Client counts length in UTF-16 units, server in code points (emoji at 50/128) | low | patch: `[...s].length` |
| Client validates trimmed email but sends it untrimmed | low | patch: trim before sending |
| Login `email` has no max length | low | patch: `max_length=320` |
| Local `JWT_SECRET` shorter than 32 bytes accepted silently | low | patch: warning + test |
| "No pre-check" test only patched `Session.exec` | low | patch: assert the first SQL statement is the INSERT |
| `from` redirect in RequireAuth/SignIn untested, only `/` is protected | low | patch: removed until a second protected page exists |
| deferred-work called R10 "settled" before the preview check | low | patch: "fixed, not yet confirmed" |
| DB does not enforce lowercase email, only the domain does | low | defer (deferred-work, Story 1.6 seed) |
| Stateless refresh stays valid after logout/rotation | false | recorded in Design Notes |
| Register 409 reveals an existing email | false | team decision in Intent |
| Spec/sprint status mismatch | false | synced when the story is presented |
| Logout during an in-flight refresh; refresh 5xx signs out; offline logout keeps cookie; refresh for another user; IDN login spelling; `AUTH_COOKIE_SECURE=1`; email regex looser than email-validator; no `server_default` on `created_at`; dev key on a non-Vercel host; failed retry/`useMe` error state; 401 console noise on first visit | low | rejected: unlikely in everyday use, or the fix adds guards for states not shown reachable |
| `get_session` only verified by the manual curl run | low | noted, thin pass-through |
| KI-logg/korrigeringer not updated | — | done with the commit/PR |

## Design Notes

- **Stateless refresh token** (no DB table): this is enough for Trinn 1. The trade-off is that an old refresh token stays valid until its `exp` (30 days), even after rotation and after logout. Rotation and logout only replace or remove the cookie in this browser; they are not a security control. This is recorded as a known limitation in the PR. `jti` makes it possible to add a revocation list later.
- **Register 409 reveals that an email exists** (team decision): this is accepted for Trinn 1, because it matches "Logg inn i stedet". Login never reveals it.
- **`prepare_threshold` (spec-review finding #8 from 1.7):** kept. Neon's PgBouncer supports prepared statements in transaction mode, so it is probably unnecessary, but turning prepares off costs nothing at this load. Removing it is the only way to settle the question, and that is not worth the risk. Closed as "kept".
- **Refresh on 401, one at a time:** concurrent 401s, and StrictMode's double effect on app load, share one in-flight refresh promise. This avoids duplicate requests and the browser's cookie ending up as a different value than the token in memory.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- all pass
- `cd backend && uv run alembic upgrade head && uv run alembic downgrade base && uv run alembic upgrade head` -- exits 0 on Docker Postgres 18
- `cd frontend && npm run gen:api && git diff --exit-code src/api/schema.d.ts && npm test -- --run && npm run lint && npm run build` -- all pass, no diff

**Manual checks:**
- Through `npm run dev` + `uv run fastapi dev`: register, reload (still signed in), wait or force token expiry (still signed in), wrong password (inline error).
