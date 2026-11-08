---
title: 'Epic 1 retro, action 2: shared error helper, test helpers and time module'
type: 'refactor'
created: '2026-11-08'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Epic 1 retrospective (`epic-1-retro-2026-11-08.md`, findings A1–A3) found three things Epic 2 would otherwise copy a fourth time: the frontend maps HTTP errors three ways (`AuthError`, `HomeError`, `InviteError`, two `fieldErrorsFrom422`, the generic text defined three times); backend test helpers are redefined per file (`sign_up`, `register`, `new_user`/`_user`, `count`, `_auth`) and two fixtures share names with different shapes; time helpers live in odd places (`utc_now` in `models/user.py`, `as_utc` in `domain/invites.py`) and only `InviteOut.expires_at` is made timezone-aware, so `HomeOut.created_at` comes back without a zone on SQLite.

**Approach:** Pure refactor in three parts on branch `chore/epic-1-retro-tiltak`: one frontend error module, one backend test-helper module, one backend time module plus a timezone-aware datetime type for response models. No user-visible change.

**Decisions (team, 2026-11-08):** keep all three parts in one spec and one PR (split check).

## Boundaries & Constraints

**Always:**
- Behaviour stays identical: every Norwegian message, field error and status a user can see today stays the same. `toApiError(response, error, { passThrough, fallback, fields? })` works in this order: (1) only when `fields` is given and the status is 422 with an array `detail`: `ApiError(422, fallback, fields(detail))`; (2) if `typeof detail === 'string'` and the status passes (`passThrough === 'any'`, or the status is in the list): that string; (3) otherwise `fallback`. So a 422 without a `fields` mapper falls through to (2)/(3), as invites does today. Call sites:

| Call | passThrough | fallback | fields |
|---|---|---|---|
| `signIn`, `register`, `fetchMe` (`auth.ts`; `signOut` throws nothing) | `'any'` | `MESSAGES.unknown` | auth mapper |
| `fetchHomes`, `createHome` | `[409]` | `HOME_MESSAGES.unknown` | homes mapper |
| `createInvite` / `fetchInvite` / `acceptInvite` | `[409, 410]` | `createFailed` / `loadFailed` / `unknown` | none |
| `fetchMembers` | not used: `new ApiError(response.status, MEMBER_MESSAGES.loadFailed)` | — | — |

- `ApiError.fields` is `Partial<Record<string, string>>`; consumers that need `FieldErrors`/`HomeFieldErrors` narrow it with one typed helper (e.g. `fieldsOf<F>(error)`) rather than ad-hoc casts. `npm run build` (`tsc -b`, `strict`) is the gate.
- Existing tests keep their assertions; they may change imports and helper calls only. A test that must change an assertion is a signal the refactor changed behaviour — stop and report it. Behaviour evidence for the frontend: the route tests that assert the fallback texts (`MembersPage.test.tsx`, `InvitePage.test.tsx`, `CreateHome.test.tsx`, `App.test.tsx`) pass unchanged.
- Frontend: components still reach the API only through `api/queries.ts` hooks (AD-7); the shared module lives in `frontend/src/api/`.
- Backend: shared plain helper functions go in a new `tests/helpers.py`, so `conftest.py` stays fixtures plus the existing `TEST_SECRET`/`make_client` (which `test_auth_routes.py` already imports; leave that import). This deviates from the retro's wording "in `conftest.py`" and is recorded in the PR. In `helpers.py`, import `from app.domain import accounts` (the domain `register` is already imported by name in `test_homes.py`, `test_invites.py`, `test_permissions.py`) and name the API helper `register_via_api`, so no two `register`s with different shapes exist.
- `test_auth_routes.register(**overrides)` stays local: it posts the fixed `ola@example.com` body that its duplicate-email tests rely on. The file-local fixtures `household`/`rental` in `test_homes_routes.py` and `test_invites_routes.py` keep their names (pytest never mixes file-local fixtures). The engine-based counters (`counts`, `link_count`, `membership_count`) and route helpers that differ in shape (`create` vs `create_home`, `join`) stay local; `user_count` in `test_seed.py` becomes `count(session, User)`.
- `_user(session, name)` in `test_permissions.py` becomes `new_user`; the default name "Ola" and the lowercased email are fine, since `accounts.normalize_email` lowercases anyway.
- Time: one module `backend/app/clock.py` with `utc_now()` and `as_utc()` (naive → UTC, as today). `UtcDatetime = Annotated[datetime, AfterValidator(to_utc)]`, where `to_utc` attaches UTC to a naive value and converts an aware one with `astimezone(UTC)`, so every response datetime is UTC whatever the session time zone. The validator runs when the model is constructed (FastAPI does not re-validate instances), so response models are always built with normal construction, never `model_construct`. The OpenAPI schema does not change (verified: same `string`/`date-time`).
- `domain/invites.py` imports `as_utc` from `app.clock`; tests that call `invites.as_utc` switch to `app.clock.as_utc`. `domain/tokens.py:31` uses `utc_now()` (no test patches the clock).

**Never:**
- No new features, no change to API shapes beyond a zone on `created_at` under SQLite (in `GET`/`POST /api/homes` and `POST /api/invites/{token}/accept`, which return `HomeOut`), no database migration, no change to `alembic/`, `vercel.json` or the generated client other than a regenerated `schema.d.ts` if the OpenAPI schema changes.
- No fixes for the deferred retro findings (R5, R6, R8, A4, A5).

</frozen-after-approval>

## Code Map

- `frontend/src/api/auth.ts:22-96` -- `MESSAGES.unknown`, `AuthError` (status, message, `fields`), exported `fieldErrorsFrom422` (tested in `api/auth.test.ts:35-60`), `toAuthError` (422 → fields; any string `detail` passed through).
- `frontend/src/api/homes.ts:20-108` -- `HOME_MESSAGES.unknown`, `HomeError`, private `fieldErrorsFrom422`, `toHomeError` (422 → fields; only 409 passed through), `fetchMembers` (always `MEMBER_MESSAGES.loadFailed`).
- `frontend/src/api/invites.ts:32-75` -- `INVITE_MESSAGES.unknown`, `InviteError` (no fields), `toInviteError(response, error, fallback)` (409/410 passed through).
- Consumers: `routes/Register.tsx:53-59`, `routes/SignIn.tsx:42-47` (`instanceof AuthError`, `.status`, `.fields`), `routes/CreateHome.tsx:69-77` (`instanceof HomeError`), `routes/InvitePage.tsx:127` (`instanceof InviteError`).
- `backend/app/models/user.py:13` -- `utc_now`; imported by `models/home.py:10`, `models/membership.py:22`, `models/invite_link.py:22`, `domain/invites.py:23`. `backend/app/domain/invites.py:69` -- `as_utc`, used in `domain/invites.py:84` and `routes/invites.py:81`; tests `test_invites.py:77,220`. `backend/app/domain/tokens.py:31` -- `datetime.now(UTC)` inline.
- Response datetimes: `routes/homes.py:53` (`HomeOut.created_at`), `routes/invites.py:51` (`InviteOut.expires_at`).
- Duplicated test helpers: `test_auth_routes.py:20` `register(**overrides)` (fixed `REGISTER` body), `test_homes_routes.py:23` `sign_up`, `test_invites_routes.py:26,34` `register`/`sign_up`, `test_homes.py:23` and `test_invites.py:27` `new_user`, `test_permissions.py:138,144` `_user`/`_auth`, `count` in `test_homes.py:46`, `test_invites.py:52`, `test_seed.py:31`. Fixtures `household`/`rental`: 3-tuples in `test_homes_routes.py:223,232`, 2-tuples in `test_invites_routes.py:79,85`.
- `backend/pyproject.toml:25-27` -- `pythonpath = ["."]`, so `tests.helpers` imports without an `__init__.py`.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- now: `uv run --no-cache .claude/skills/bmad-retrospective/scripts/sprint_status.py update --file "_bmad-output/implementation-artifacts/sprint-status.yaml" --epic 1 --set-action-status '[{"id":"epic-1-retro-item-2-before-epic-2-shared-frontend-error-help","status":"in-progress"}]'`; `done` after merge (never hand-edit the file)
- [ ] `frontend/src/api/errors.ts` -- `GENERIC_ERROR` text, one `ApiError` class (`status`, `message`, typed `fields`), one `toApiError(response, error, { passThrough, fallback, fields })` where `passThrough` is `'any'` or a list of statuses and `fields` maps a 422 `detail` to field errors -- A1
- [ ] `frontend/src/api/auth.ts`, `homes.ts`, `invites.ts` -- use `errors.ts`; keep each module's message constants (pointing `unknown` at `GENERIC_ERROR`) and its exported `fieldErrorsFrom422` for auth; remove `AuthError`, `HomeError`, `InviteError`
- [ ] `frontend/src/routes/Register.tsx`, `SignIn.tsx`, `CreateHome.tsx`, `InvitePage.tsx` -- `instanceof ApiError`
- [ ] `frontend/src/api/errors.test.ts` -- each pass-through rule (any / [409] / [409, 410]) including a 500 with a string `detail` under each, 422 with and without a `fields` mapper, non-string `detail`, missing body
- [ ] `backend/app/clock.py` -- `utc_now`, `as_utc`, `UtcDatetime` (an `Annotated[datetime, AfterValidator(as_utc)]` for response models) -- A3
- [ ] `backend/app/models/*.py`, `domain/invites.py`, `domain/tokens.py`, `routes/homes.py`, `routes/invites.py` -- import from `app.clock`; `HomeOut.created_at` and `InviteOut.expires_at` typed `UtcDatetime`; drop the manual `as_utc` call in `routes/invites.py`
- [ ] `backend/tests/test_clock.py` -- `as_utc`: naive gains UTC, aware unchanged; `UtcDatetime`: naive gains UTC, `+01:00` becomes UTC; `HomeOut`/`InviteOut` serialise with a zone; route tests that `POST /api/homes` and `GET /api/homes` return `created_at` with a zone on SQLite (fail before the change)
- [ ] `backend/tests/helpers.py` -- `PASSWORD = "hemmelig1"`, `new_user(session, name="Ola")`, `register_via_api(client, name="Ola", **extra)`, `sign_up(client, name="Ola") -> auth header`, `auth_for(client, email)`, `count(session, model)` -- A2
- [ ] `backend/tests/test_homes.py`, `test_invites.py`, `test_permissions.py`, `test_homes_routes.py`, `test_invites_routes.py`, `test_seed.py` -- use `tests.helpers` as in Boundaries; nothing else changes
- [ ] `frontend/openapi.json`, `src/api/schema.d.ts` -- regenerate; expect no diff
- [ ] `docs/ki-logg/korrigeringer.md` -- corrections found in review

**Acceptance Criteria:**
- Given the refactor, when `uv run pytest` and `npm test` run, then every pre-existing test passes with only import or helper-call changes in its file.
- Given `grep -rn "class .*Error extends Error" frontend/src/api`, then only `ApiError` is found; and `grep -rn "def utc_now\|def as_utc" backend/app` finds only `app/clock.py`.
- Given an in-memory SQLite test client, when `GET /api/homes` is called after creating a Home, then `created_at` ends in `Z` or `+00:00`.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Spec review 2026-11-08 (one adversarial reviewer; 17 findings, verified against the code by the orchestrator):

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | 422 without a `fields` mapper undefined; invites would change message | high | order of `toApiError` spelled out |
| 2 | Fallback per call site not given | high | call-site table |
| 3 | Auth `'any'` also passes a string on 401/404/5xx | medium | order + 500 tests per rule |
| 4 | Typed `fields` lost after `instanceof` under `strict` | medium | `Partial<Record<string,string>>` + one narrowing helper; build is the gate |
| 5 | Fixture rename breaks the "only imports" rule and fixes nothing (file-local) | medium | rename dropped |
| 6 | `register` name collisions (domain vs API vs auth tests) | medium | `accounts` module import, `register_via_api` |
| 7 | `test_auth_routes.register` decision conditional | medium | stays local, reason stated |
| 8 | Engine counters, `user_count`, `create`/`create_home`/`join` not inventoried | low | listed: local, except `user_count` |
| 9 | `_user` vs `new_user` email format differs | low | noted as harmless |
| 10 | `as_utc` keeps an aware non-UTC value | low | `UtcDatetime` converts with `astimezone(UTC)` |
| 11 | `AfterValidator` runs on construction, not serialisation | low | "never `model_construct`" |
| 12 | OpenAPI unchanged | false | confirmed; no action |
| 13 | POST and accept also return `HomeOut` | low | named in Never; POST tested |
| 14 | Tests calling `invites.as_utc`; tokens clock | low | tests switch to `app.clock`; tokens safe |
| 15 | Truncated action id, no full command | low | full command |
| 16 | No external importers of moved symbols | false | confirmed; route tests named as behaviour evidence |
| 17 | `from tests.conftest import` already used; rationale clashes | low | rationale reworded |

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- all pass
- From the repo root: `(cd backend && uv run python -m app.export_openapi) && cd frontend && npm run gen:api && git diff --exit-code src/api/schema.d.ts openapi.json && npm test -- --run && npm run lint && npm run build` -- all pass, no diff
