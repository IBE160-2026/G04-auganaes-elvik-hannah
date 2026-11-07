---
title: 'Story 1.3: Create a Home (Household or Landlord)'
type: 'feature'
created: '2026-11-07'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '38f5e4941e55214b993395bdbd4c6cb950129c25'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After signing in, a user lands on a placeholder page and cannot do anything. Every later story (invites, tasks, notifications) hangs off a Home, and no Home can exist yet (FR-1, FR-3, AD-1).

**Approach:** Add `Home` and `Membership` (Role on Membership, never on User). A signed-in user with no Home is sent to a Create Home page, chooses Household Home or Landlord Home, and becomes a Household Member or the Landlord through a Membership row. Landlords can always create more Homes; Household Members and Tenants get no second self-service entry point. The seed gets an example Household Home for Mari and Jonas. The tab bar is out of scope (team decision 2026-11-07, moved to Story 2.2).

**Decisions (team, 2026-11-07):**
- A Home has a required name (stripped, 1–60 characters) and a type. No unit type yet; Story 5.3 adds it with its own migration.
- A Landlord may create more Landlord Homes only, never a Household Home through this flow. A Landlord who also lives in a kollektiv joins it by invite (Story 1.4). PRD Open Question 3 is not widened.
- After creation the user lands on a simple Home page: the Home's name, type and the user's Role, and "Logg ut". A Landlord also sees a list of their Homes and an "Opprett nytt hjem" link. It is replaced by Task Overview in Stories 2.1–2.2.
- The seed adds only the example Household Home for Mari and Jonas. The example Landlord and Tenant come with Stories 1.4–1.5.

## Boundaries & Constraints

**Always:**
- Role is never chosen by a caller; the domain derives it from the Home type and whether the user creates or joins. Creator: Household → `household_member`, Landlord → `landlord`. Joiner (`add_member`, reused by 1.4): Household → `household_member`, Landlord → `tenant`. So a Home never mixes Household Members with a Landlord or Tenants, and a Landlord Home has exactly one Landlord by construction.
- The creation rule lives only in the domain and is enforced on the server: a user with no Membership may create either type; a user who is Landlord in at least one Home may create a Landlord Home; nobody else may. The API returns the allowed types, and the frontend uses them instead of re-implementing the rule.
- The creator of a Household Home has no creator privilege: the Membership row is the same as a later invitee's.
- Every mutation goes through `backend/app/domain/homes.py`; routes stay thin. The routes in this story are user-scoped (`/api/homes`), not Home-scoped, so `require_role` (Story 1.5) is not needed yet; list queries filter on the caller's Memberships.
- The seed step uses the domain functions, is idempotent, and never deletes or overwrites. Mari and Jonas are checked separately, so a run that stopped halfway is completed next time.
- API contract: `HomeType = Literal["household", "landlord"]`, `Role = Literal["household_member", "landlord", "tenant"]`. `HomeOut {id, name, type, role, created_at}` (role = the caller's). `GET /api/homes` → `{homes: HomeOut[] (newest first), allowed_types: HomeType[]}`; `POST /api/homes {name, type}` → 201 `HomeOut`.
- Norwegian copy only; household copy warm, landlord copy neutral. Design tokens only, mobile-first, 44×44 tap targets, inline errors at the action.

**Never:**
- No tab bar, no Home switcher, no Task Setup (Story 2.1), no invites or members list (1.4, 1.5), no Home editing or deletion.
- No `role` on `User` and no Role in the JWT.
- No Home-scoped route (`/api/homes/{home_id}/...`) in this story.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Create Household | no Memberships, `{name, type: household}` | 201, Home + Membership `household_member` | N/A |
| Create Landlord | no Memberships, `{name, type: landlord}` | 201, Home + Membership `landlord`, zero Tenants | N/A |
| Landlord creates another | Landlord in ≥1 Home, `type: landlord` | 201, new Landlord Home | N/A |
| Landlord creates Household | Landlord in ≥1 Home, `type: household` | nothing written | 409, Norwegian detail |
| Member/Tenant creates again | only `household_member`/`tenant` Memberships | nothing written | 409, Norwegian detail |
| Invalid name | empty/whitespace or over max length | nothing written | 422, mapped to the field |
| Unknown type | `type: "other"` | nothing written | 422 |
| Signed out | no Bearer | nothing written | 401 (existing refresh flow) |
| List | `GET /api/homes` | only the caller's Homes, newest first, each with the caller's Role; `allowed_types` | N/A |
| App open, no Home | signed in, list loaded and empty | redirected to Create Home | N/A |
| App open, loading or failed | `GET /api/homes` pending / fails | "Laster …" / inline error with retry | never redirects |
| After create | 201 | new Home written into the cache, then `/` shows it | no bounce back to Create Home |
| App open, Member | has a Household/Tenant Membership | Home page; Create Home not offered; direct URL redirects to Home page | N/A |
| Seed rerun | example Home exists | nothing new; "finnes allerede" | N/A |
| Seed partial | Mari's Home exists, Jonas not in it | Jonas added | Jonas already in another Home: skipped with a printed reason |

</frozen-after-approval>

## Code Map

- `backend/app/models/user.py` -- pattern for a model: UUIDv4 `id`, `DateTime(timezone=True)` via `utc_now`, named constraints. `models/__init__.py` must import new models (Alembic `env.py` registers tables through it).
- `backend/alembic/versions/300f4eef63e7_create_users.py` -- the only revision; the new one has it as `down_revision`. CI runs upgrade, downgrade base/upgrade and `alembic check`, so constraints must be named and models must match the migration.
- `backend/app/domain/accounts.py` -- domain style: plain functions taking `Session`, domain exceptions, commit inside, `IntegrityError` → domain error.
- `backend/app/permissions/current_user.py` -- `CurrentUser` dependency; reuse.
- `backend/app/routes/auth.py` -- route style: Pydantic request/response models, `SessionDep`, Norwegian `detail` constants, `StringConstraints(strip_whitespace=True, ...)` for names. `main.py` mounts routers with `prefix="/api"`.
- `backend/app/seed/__init__.py` -- `STEPS` tuple; append the new step after `seed_users`. `seed/users.py` -- `EXAMPLE_USERS`, look users up by email.
- `backend/tests/conftest.py` -- SQLite `engine`/`session` fixtures, `make_client`; `test_seed.py` asserts `STEPS == (seed_users,)` and must be updated.
- `.github/workflows/ci.yml` -- migrations job line ~83: idempotence check counts `users`; extend it to Homes and Memberships.
- `backend/app/export_openapi.py`, `frontend/openapi.json`, `frontend/src/api/schema.d.ts` -- regenerate; `test_openapi_sync.py` and CI enforce sync.
- `frontend/src/App.tsx` -- `AppRoutes`; `/` is protected by `RequireAuth`. `routes/Start.tsx` -- placeholder page with sign-out; its comment about the tab bar is now wrong.
- `frontend/src/api/queries.ts`, `api/auth.ts` -- hook and API-function pattern; no `fetch` in components. `useSignOut` clears the query cache.
- `frontend/src/components/{PrimaryButton,TextField}.tsx`, `routes/AuthForm.css`, `routes/formFocus.ts` -- reuse for the form, inline errors and focus after a server error.
- `frontend/src/test-utils/fakeApi.ts` -- `fakeApi`, `json`, `OLA` for component tests.
- `README.md` -- example-user table and "Første innlogging".
- Not to touch: `alembic/env.py`, `vercel.json`, `service-worker.ts`, auth/token code.

## Tasks & Acceptance

**Execution:**
- [x] `backend/app/models/home.py`, `models/membership.py`, `models/__init__.py` -- `Home` (`homes`) and `Membership` (`memberships`); type and Role as strings with named CHECK constraints listing every value now (`ck_homes_type`: household, landlord; `ck_memberships_role`: household_member, landlord, tenant); explicitly named PK/FK/unique (`fk_memberships_user_id_users`, `fk_memberships_home_id_homes`, `uq_memberships_user_id_home_id`), no `ondelete` (no deletion exists); index on `memberships.home_id` -- AD-1; `alembic check` ignores CHECKs, so a test covers them
- [x] `backend/alembic/versions/<rev>_create_homes_memberships.py` -- autogenerate, review by hand, working `downgrade` -- CI runs `alembic check`
- [x] `backend/app/domain/homes.py` -- `create_home`, `allowed_types`, `add_member` (joiner Role from Home type; 1.4 will reuse it), `homes_for`, `HomeCreationNotAllowed`. `create_home` locks the user's row (`with_for_update`) before the check so two parallel requests cannot both pass -- creation rule in one place
- [x] `backend/app/routes/homes.py`, `main.py` -- `GET /api/homes`, `POST /api/homes` (201; 409 with Norwegian detail) -- thin routes
- [x] `backend/tests/conftest.py`, `test_homes.py`, `test_homes_routes.py` -- turn on `PRAGMA foreign_keys=ON` in the SQLite `engine` fixture (connect event); every matrix row, plus: Role is not a column on `users`; a Landlord who joins a Household Home holds two Roles; `add_member` to a Landlord Home gives `tenant`, never a second `landlord`; a raw insert with an unknown type/role fails
- [x] `backend/app/seed/homes.py`, `seed/__init__.py`, `tests/test_seed.py` -- example Household Home "Mari og Jonas sitt hjem" with Mari (creator) and Jonas (`add_member`), each checked separately (matrix); update `STEPS` and the "finnes allerede" count assertions; tests for fresh, rerun and partial
- [x] `.github/workflows/ci.yml` -- idempotence check also asserts one Home and two Memberships
- [x] `frontend/openapi.json`, `src/api/schema.d.ts`, `src/api/homes.ts`, `src/api/queries.ts` -- `useHomes` keyed `['homes', userId]`, enabled only with a session (like `useMe`); `useCreateHome` writes the new Home into that cache before navigating
- [x] `frontend/src/routes/CreateHome.tsx` + `.css`, `routes/HomePage.tsx` (replaces `Start.tsx`: name, type, Role, "Logg ut"; Landlords also get their Homes list and an "Opprett nytt hjem" link), `App.tsx` -- `/nytt-hjem` (a Landlord with Homes sees no type choice, only the name field); `/` shows the newest Home and sends a user to `/nytt-hjem` only when the list has loaded empty; `/nytt-hjem` offers `allowed_types` and sends a user with none back to `/`
- [x] `frontend/src/App.test.tsx`, `routes/*.test.tsx` -- existing tests get a `GET /api/homes` handler and the new landing text; redirect only after an empty list (not while loading, not on error), no bounce after create, choosing a type and creating, inline 409/422, Landlord sees the Homes list and create link, a Member sees neither
- [x] `README.md` -- example Home in the user table, what to try first, the CI paragraph ("nøyaktig to brukere" → also the Home)
- [x] `sprint-status.yaml` -- 1-3 to `in-progress` at start, `review` when the PR opens
- [x] `docs/ki-logg/korrigeringer.md` -- corrections found in review

**Acceptance Criteria:**
- Given a clean clone, when the README is followed and the seed is run, then signing in as Mari shows the example Home and no Create Home prompt.
- Given a new registered user locally, when they sign in, then they are taken to Create Home, and after creating a Household Home a reload keeps them on the Home page.
- Given this PR's Vercel preview, when a new user registers and creates a Landlord Home and then a second one, then both appear for them, and the migration ran on the preview's Neon branch.

## Implementation Notes

- Migration `cf10f98fe92a_create_homes_memberships.py`: autogenerated, then `sqlmodel` AutoString replaced by `sa.String` to match the users revision. Verified on Docker Postgres 18: downgrade base → upgrade head → `alembic check` clean, seed twice gives users/homes/memberships = 2/1/2.
- `create_home` also validates name and type in the domain (ValueError), even though the route's Pydantic model already does, so seed or later callers cannot bypass it.
- 409 detail depends on what the caller may still create: a Landlord gets `LANDLORD_ONLY`, a Household Member or Tenant gets `ALREADY_IN_HOME` (`routes/homes.py`).
- `useCreateHome` writes the new Home first in the cache with `allowed_types: []` as a placeholder, then invalidates so the refetch brings the server's `allowed_types`. `CreateHome` does not redirect on the empty placeholder while the create is pending or just succeeded. The no-bounce test was checked by removing the cache write: it then fails.
- `routes/formFocus.ts` now accepts any field-error record, so the Create Home form reuses it (radio `type` and `name`).
- `sprint-status.yaml` → `review` and `korrigeringer.md` are left for when the PR opens and the code review has run.
- Review fixes (2026-11-07): `homes_for` tiebreaker on `id`, error screen only without cached data, refetch on 409, 409 declared in OpenAPI, CI checks the migrated CHECK constraints, typed test fixtures.
- The Verification command `alembic downgrade base` wiped the developer's local database on the first run. The final verification ran the migration round trip and seed against a throwaway database `husly_verify` in the same container instead (`DATABASE_URL`/`DATABASE_URL_UNPOOLED` pointed at it), then dropped it.

## Spec Change Log

## Review Triage Log

Spec review 2026-11-07 (one adversarial reviewer; all 15 findings verified against the code by the orchestrator):

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | `add_member` derived Role from Home type and refused a second Landlord, so Tenants could never be added | high | creator/joiner Role split |
| 2 | Redirect to Create Home could fire while `useHomes` is loading or failed | high | redirect only on a loaded empty list; matrix rows |
| 3 | Invalidate-then-navigate bounces back to Create Home on the stale `[]` | high | write the new Home into the cache first; test |
| 4 | `App.test.tsx:33,49,141` expect the old welcome text, no `/api/homes` handler | medium | task added |
| 5 | Design Note claimed Postgres CI covers the lock; CI runs pytest on SQLite only | medium | claim removed, "reasoned, not tested" |
| 6 | Seed step skipped Jonas forever after a half-finished run | medium | Mari and Jonas checked separately; matrix row |
| 7 | `test_seed.py:69` counts "finnes allerede" == 2 | low | task updated |
| 8 | Which Home the Home page shows was undefined | medium | newest first; Landlords see the list |
| 9 | API types and response shape implicit | medium | contract in Boundaries |
| 10 | Frontend would re-implement the creation rule | low | API returns `allowed_types` |
| 11 | CHECK values unlisted; `alembic check` ignores CHECKs | medium | values listed incl. `tenant`; test |
| 12 | SQLite FKs off in tests; FKs unnamed | low | pragma in fixture; names listed |
| 13 | One-Landlord rule only a racy domain check | low | impossible by construction (finding 1) |
| 14 | README CI paragraph, sprint-status, epic context still say tab bar → 1.3 | low | tasks added; epic context fixed now |
| 15 | Homes cache not scoped to the user | low | key on user id |

Code review 2026-11-07 (Blind Hunter, Edge Case Hunter, Verification Gap; 28 findings, verified against the code by the orchestrator):

| Finding | Verdict | Route / action |
|---|---|---|
| "Newest first" has no tiebreaker; Windows/Py 3.12 clock ties make three order tests flaky (B, E, V) | medium | patch: secondary key `Home.id`, tests use explicit `created_at` |
| Migration CHECKs never tested against the migrated schema; `alembic check` ignores them (V) | medium | patch: CI step inserts bad type/role on Postgres |
| A failed background refetch replaces an existing Home with the load error (`isError` checked before data) (B, E) | medium | patch: error screen only without data; test |
| 409 on create keeps stale `allowed_types`, retries loop (E) | low | patch: refetch on 409 |
| `POST /api/homes` 409 missing from OpenAPI/`/docs` (B) | low | patch: declared response, client regenerated |
| Test fixtures typed `object[]`/`string[]`, can drift from the schema (B) | low | patch: typed as `Home[]`/`HomeType[]` |
| Row lock against double submit has no test; SQLite ignores `FOR UPDATE` (B, V) | medium | defer: needs a concurrent Postgres test harness; reasoned only, noted in PR |
| `add_member` lets a Household Member/Tenant join a second Home; only the seed checks (B, E) | maybe-false | defer to 1.4: whether invites may add a second Home is 1.4's decision, not in this story's intent |
| `add_member` maps every `IntegrityError` to `AlreadyMember` (B, E) | low | rejected: callers pass loaded rows and the Role comes from a map, so FK/CHECK failures need a concurrent delete; fix adds a branch |
| Order by `Home.created_at`, not `Membership.created_at`, for a joined older Home (E) | low | rejected: no join path exists until 1.4 |
| Seed matches the example Home by name only, not type (E) | low | rejected: needs Mari to own a Landlord Home with that exact name |
| Placeholder `allowed_types: []` hides the Landlord's create link until the refetch (B) | low | rejected: lasts one request; a correct placeholder would copy the domain rule |
| Frontend infers Landlord from `role` for the list and title (E) | low | rejected: the list is for Landlords by team decision 3a |
| `focusFirstInvalid` signature loosened (B) | low | rejected: unlikely, fix adds generics |
| Model `type`/`role` typed `str`, `type` shadows the builtin (B) | low | rejected: values constrained by CHECK and Pydantic `Literal` at the API |
| CI seed check counts rows, not who/which Role (B) | low | rejected: pytest seed tests check names and Roles |
| Frontend test gaps: client name limit, Tenant on `/nytt-hjem`, dual Role page, no `maxLength` (B) | low | rejected: server 422 path tested; Tenant takes the same `allowed_types: []` path as the tested Member |
| Landlord greeting shows "som ." while `useMe` loads (B) | false | `useMe` has `initialData: session.user`, so the name is there whenever the page renders |
| Only the newest Home can be viewed (B) | false | team decision 3a; switching comes with the tab bar/Portfolio |
| sprint-status and spec status out of sync (B) | false | synced when the story is presented (step 5) |
| `korrigeringer.md` and KI-logg README not updated (B) | false | done with the commit and PR |

## Design Notes

- **User-scoped routes instead of Home-scoped:** `POST /api/homes` has no `home_id` yet, and `GET /api/homes` filters by the caller's Memberships, so neither needs `require_role`. This keeps 1.3 from building a partial version of 1.5's permission path.
- **Row lock against the double-click race:** without it, two parallel creates by a user with no Home both pass the rule and give a Household Member two Homes. `SELECT … FOR UPDATE` on the user row costs nothing at this load. SQLite ignores it and CI runs pytest only on SQLite, so this is reasoned, not tested; noted in the PR.
- **Creator vs. joiner Role:** deriving the Role from Home type alone cannot give Tenants. Splitting by creator/joiner keeps "no caller picks a Role" and makes a second Landlord impossible without a partial unique index.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- all pass
- `cd backend && uv run python -m app.seed && uv run python -m app.seed` -- exit 0 both times, second run says "finnes allerede"
- `cd backend && uv run alembic downgrade base && uv run alembic upgrade head && uv run alembic check` -- exit 0 on Docker Postgres 18
- `cd frontend && npm run gen:api && git diff --exit-code src/api/schema.d.ts && npm test -- --run && npm run lint && npm run build` -- all pass, no diff
