---
title: 'Story 2.1: Task Setup at Home Creation'
type: 'feature'
created: '2026-11-09'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A new Home has no tasks, so Husly does nothing yet for the irregular chores it exists for (FR-4, FR-8). There is no Task data model; Stories 2.2–2.5 and Epics 3–4 all need one (issue #28).

**Approach:** Add a TaskType catalog, `Task` and each Task's first `TaskInstance`. After Create Home, a Household Member or Landlord reviews the recommended tasks, adjusts Must/Should and Frequency, unticks tasks that do not fit, and confirms; all Tasks are created in one request through `domain/tasks` behind `require_role`. The user lands on `/`, which shows a minimal task list until Story 2.2 replaces it. The seed gives both example Homes tasks.

**Decisions (Eirik, 2026-11-09):** (1) Land on `/` with a minimal list (name, Må/Bør, Frequency, next due date); 2.2 replaces it. (2) The catalog is a versioned Python module, not a table; a Task stores its catalog key. (3) The eight starter entries are agreed (Code Map). (4) The first instance is due on setup date + Frequency; the seed sets up tasks as of an earlier date so some are due soon or overdue. (5) In setup a task can be unticked; no custom tasks now, but the model must allow them later (a Task carries its own name). (6) Frequency is chosen from fixed intervals: 7, 14, 30, 42, 60, 90, 182, 365 days («Hver uke», «Hver 2. uke», «Hver måned», «Hver 6. uke», «Hver 2. måned», «Hver 3. måned», «Hvert halvår», «Hvert år»). (7) Whenever the shown Home has no Tasks, `/` sends a Household Member or Landlord to Task Setup; a Tenant sees «Utleier har ikke satt opp oppgaver ennå.» The seed gives «Mari og Jonas sitt hjem» and «Storgata 12» tasks. (8, after spec review) Task Setup is never a dead end: the setup page has «Medlemmer og invitasjon» and «Logg ut» at the bottom, and a Landlord's «Dine hjem» list shows «Sett opp oppgaver» next to each Home without Tasks that the Landlord may set up.

## Boundaries & Constraints

**Always:**
- Catalog entry: `key`, Norwegian `name`, `classification` (`must`/`should`), `frequency_days`, `photo_evidence_eligible`; plus a `CATALOG_VERSION`. Recommendations come only from the catalog, never from a component or route (AD-6).
- A Task stores `home_id`, `task_type` (catalog key), its own `name` (copied at creation), `classification`, `frequency_days`. Every Task has a classification and a Frequency (FR-4, FR-8); the server accepts only `must`/`should`, known keys, no duplicates, at least one task, and Frequencies from the fixed list (422 with Norwegian messages otherwise).
- Setup is Home-scoped behind `require_role("household_member", "landlord")`; a Tenant, outsider or unknown Home gets the same 403. A Landlord Home without Tenants can be set up. Who may set up is one domain rule, `can_set_up_tasks(role)`, sent as `HomeOut.can_set_up_tasks` (like `can_invite`); `HomeOut.has_tasks` says whether the Home has any Task (set wherever `HomeOut` is returned).
- Setup runs once per Home: if the Home already has Tasks, nothing is created and the answer is 409. `set_up_tasks` locks the Home row (`select(Home)…with_for_update()`) before checking; an `IntegrityError` on the unique `(home_id, task_type)` is rolled back and becomes 409 too, never 500. SQLite ignores the lock (accepted risk, as in Epic 1).
- API: `POST /api/homes/{home_id}/tasks/setup` takes `{tasks: [{task_type, classification, frequency_days}]}` and returns 201 with the same `TasksOut` as `GET /api/homes/{home_id}/tasks`: `{tasks: [{id, task_type, name, classification, frequency_days, due_on}]}`, ordered Must, then `due_on`, then `name`, then `id`. `classification` and `frequency_days` are `Literal` types, so `schema.d.ts` gives unions and the frontend label map is checked at compile time. Shape errors are Pydantic 422s (the client shows a generic message; the form cannot produce them); domain errors (empty list, unknown or duplicate key) are 422 with a Norwegian string `detail`.
- Model: `tasks` and `task_instances` both have `created_at`; `task_instances` has a unique `(task_id, due_on)`. «Next due» is the earliest instance of a Task (2.1 makes exactly one; Story 2.4 adds completion fields). Both models are exported from `app/models/__init__.py`.
- Dates: `TaskInstance.due_on` is a `date`, computed from `utc_now().date()` + Frequency, sent as ISO `YYYY-MM-DD` and formatted on the client from its parts (never `new Date('YYYY-MM-DD')`, which is UTC midnight).
- Frontend state: the tasks query key is `['tasks', homeId, userId]`. A successful setup writes the POST answer to that key and to `HomeOut.has_tasks` in the homes cache, then navigates to `/` with `replace`. A 409 does not navigate: it awaits a refetch of tasks and homes and lets the setup page's guard route to `/` (as `useLeaveHome`). A 403 shows no inline error (the global handler refetches and the guards route). Create Home navigates to setup with `replace`, so Back cannot reach `/nytt-hjem` and create a second Home.
- Guards on the setup page, in order: Homes loading → «Laster …»; Home not in the list → `/`; `!can_set_up_tasks` or `has_tasks` → `/`. Tasks are fetched only once the Home is found. The page renders `PendingNotice` (a Landlord who just left a Household may land here first).
- Setup form: each row is a `fieldset` with the task name as `legend`; «Ta med» checkbox, a Må/Bør radio pair with a unique `name` per row, an interval `<select>`. An unticked row's controls stay enabled (no native `disabled`). «Velg minst én oppgave.» is shown inline and focus goes to the first checkbox. `PrimaryButton` with `pending`.
- Reuse `ApiError`, TanStack Query hooks (AD-7), `UtcDatetime`, `tests/helpers.py`, design tokens (`--color-must-badge`/`--color-should-badge`), Norwegian copy («Må»/«Bør» as badge text, colour only as reinforcement), 44×44 targets, visible focus.

**Never:**
- No completion, reschedule, Must-first overview, tab bar, Task Detail or editing after setup (Stories 2.2–2.5). No Photo Evidence logic beyond the flag (Epic 4). No custom tasks. No `task_types` table.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Accept as is | New Home, confirm all 8 | 201; 8 Tasks with catalog values; each has one instance due today + Frequency | N/A |
| Adjust | «Vask stekeovnen» to Må, «Hver 2. måned» | Task stored as `must`, 60 | N/A |
| Untick | 2 of 8 unticked | 6 Tasks | N/A |
| Nothing ticked | 0 tasks | nothing created | 422 «Velg minst én oppgave.» (client checks first) |
| Bad input | unknown key, duplicate key, Frequency 10, classification `maybe` | nothing created | 422 |
| Already set up | Home has Tasks; second tab or double click | nothing created; client refetches and goes to `/` | 409 |
| Landlord, no Tenants | Kari's new Landlord Home | 201 | N/A |
| Tenant / outsider / unknown Home | POST setup | nothing created | 403, same body |
| Home page, no Tasks | Household Member or Landlord | redirect to `/hjem/<id>/oppgaveoppsett` | N/A |
| Landlord, several Homes | an older Home has no Tasks | «Dine hjem» shows «Sett opp oppgaver» for it; the link opens its setup | N/A |
| Setup page exits | user wants to invite first or sign out | «Medlemmer og invitasjon» and «Logg ut» on the setup page work | N/A |
| Home page, no Tasks, Tenant | Anders | «Utleier har ikke satt opp oppgaver ennå.» | N/A |
| Home page with Tasks | any Member | list: name, Må/Bør badge, interval label, «Neste gang: <dato>» | N/A |
| Setup page, not allowed | Tenant opens the URL, Home already set up, or Home not among the user's | redirect to `/` | N/A |
| Setup fails | 5xx / network | inline error, «Prøv igjen», still on setup | never silent |
| Setup 403 | removed meanwhile | no inline error; global handler refetches, guards route | N/A |
| Home page, tasks fail to load | any Member | load error with «Prøv igjen» in the task section; rest of the page (Medlemmer, Logg ut) still shown | N/A |
| Seed | `uv run python -m app.seed` twice | both Homes have 8 Tasks; some due within a week, some overdue; second run adds nothing and prints «Oppgavene i «X» er allerede satt opp» | N/A |
| Seed, Home skipped | Mari or Kari was skipped by the Homes step (in another Home) | no tasks are set up in any other Home; no crash | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/domain/homes.py` -- `create_home` (locks the User row; setup locks the Home row instead), `can_invite`/`can_leave` (pattern for `can_set_up_tasks`).
- `backend/app/models/__init__.py` -- registers tables for `create_all` and Alembic; add `Task`, `TaskInstance`.
- `backend/app/routes/homes.py` -- `SessionDep`, `ErrorOut`, `HomeOut`/`home_out`, `AnyMember`, `FORBIDDEN`; `routes/invites.py` imports from it (the retro's deferred shared module).
- `backend/app/models/home.py`, `membership.py`; `alembic/versions/fa600902c94e_*.py` -- model and migration style (named constraints, `sa.String`, CHECKs tested in tests).
- `backend/app/seed/homes.py` -- `_seed_household`, `_seed_landlord`, idempotent by natural key, through the domain.
- `backend/tests/conftest.py:64-74` (SQLite `create_all`), `helpers.py`, `test_permissions.py` (route walk), `test_clock.py` (builds `HomeOut`), `test_seed.py` (`FULL`, step order, `count("finnes allerede") == 6`, skip cases at 183-195 and 229-240).
- `.github/workflows/ci.yml:86-130` -- seed count step asserts `(2, 4, 1)`; the CHECK step lists named CHECKs by hand (`alembic check` ignores them).
- `frontend/src/routes/MembersPage.tsx:35-37,50,58-61` -- guard pattern (fetch after the Home is found), «Tilbake til hjemmet», no inline error on 403.
- `frontend/src/test-utils/fakeApi.ts:29,44-52` -- unknown routes answer 404; `OLAS_HOME` fixture. `HomePage.test`, `CreateHome.test`, `MembersPage.test`, `InvitePage.test`, `App.test` render routes that will call the new endpoints.
- `frontend/src/routes/CreateHome.tsx:69` (`onSuccess: navigate('/', { replace: true })`), `HomePage.tsx:25,78` (shows `homes[0]` only; the only «Logg ut»), `App.tsx` (routes), `api/homes.ts`, `api/queries.ts`, `test-utils/fakeApi.ts`.
- Catalog (decision 3): `vask-badet` Vask badet grundig (must, 42); `rens-sluket` Rens sluket (must, 30, photo); `kjokkenviftefilter` Rens filteret i kjøkkenviften (must, 60, photo); `avkalk-vannkoker` Avkalk vannkokeren (should, 60); `bak-kjoleskapet` Vask bak og under kjøleskapet (should, 90); `stekeovn` Vask stekeovnen (should, 90); `gulv` Støvsug og vask gulvene (should, 14); `dusjfuger` Vask fugene i dusjen (should, 90).

## Tasks & Acceptance

**Execution:**
- [ ] `sprint-status.yaml` -- `epic-2` and `2-1-…` to `in-progress`; `review` when the PR opens.
- [ ] `backend/app/routes/deps.py` (new) -- move `SessionDep`, `ErrorOut` and the role aliases (`AnyMember` etc.) there; `homes.py`, `invites.py` import them -- the retro's deferred shared module, before a third route module copies the pattern.
- [ ] `backend/app/domain/task_types.py` -- `TaskType` (frozen), `TASK_TYPES`, `CATALOG_VERSION = 1`, `FREQUENCY_DAYS`, lookup by key.
- [ ] `backend/app/models/task.py` + migration -- `tasks` (FK home, CHECK classification, CHECK frequency > 0, unique `(home_id, task_type)`, `created_at`), `task_instances` (FK task, `due_on` date, `created_at`, unique `(task_id, due_on)`); export both in `models/__init__.py`.
- [ ] `backend/app/domain/tasks.py` -- `can_set_up_tasks`, `set_up_tasks(session, membership, choices, today=None)`, `tasks_of(session, home_id)` (with next instance), `TasksAlreadySetUp`.
- [ ] `backend/app/routes/tasks.py` -- `GET /api/task-types` (signed in; catalog + Frequency list), `POST /api/homes/{home_id}/tasks/setup` (201, 403/409/422 declared), `GET /api/homes/{home_id}/tasks` (any Member; Must first, then `due_on`); `HomeOut.can_set_up_tasks`.
- [ ] `backend/app/seed/tasks.py` + `seed/__init__` -- set up both Homes with catalog values, Mari's as of 28 days ago and Storgata 12 as of 40 days ago, so some instances are due soon or overdue. Find each Home by the creator's Membership and name (as `_own_home`); skip if missing or already set up, with its own message.
- [ ] `backend/tests/test_task_types.py`, `test_tasks.py`, `test_tasks_routes.py`, `test_clock.py`, `test_seed.py` -- every backend matrix row (incl. an overlapping race → 409, seed skip cases, updated counts and messages); catalog invariants (≥8, both classes, ≥2 photo, unique keys, Frequency in list); 409 on a second setup; `fr3_violations` unchanged.
- [ ] `.github/workflows/ci.yml` -- seed step also asserts 16 tasks and 16 instances; CHECK step gets `ck_tasks_classification` and `ck_tasks_frequency_days`.
- [ ] `frontend/openapi.json`, `src/api/schema.d.ts` -- regenerate.
- [ ] `frontend/src/api/tasks.ts`, `api/queries.ts` -- fetch/setup functions, messages, `FREQUENCY_LABELS: Record<Frequency, string>`, `formatDueOn`, `tasksKey`, `useTaskTypes`, `useTasks`, `useSetUpTasks` (per Always: cache writes, `replace`, 409 refetch).
- [ ] `frontend/src/routes/TaskSetup.tsx` + `.css`, `App.tsx` -- route `/hjem/:homeId/oppgaveoppsett`: one row per catalog entry with «Ta med» checkbox, Må/Bør radio pair, interval `<select>`; «Lagre oppgavene»; inline error with retry; guards per Always; «Medlemmer og invitasjon» link and «Logg ut» at the bottom (decision 8).
- [ ] `frontend/src/routes/CreateHome.tsx`, `HomePage.tsx` + `.css` -- after create go to setup (`replace`); Home page task list section «Oppgaver», redirect or Tenant text when empty; «Sett opp oppgaver» in «Dine hjem» for Homes with `can_set_up_tasks && !has_tasks` (decision 8).
- [ ] `frontend/src/**/*.test.tsx`, `test-utils/fakeApi.ts` -- default `GET …/tasks` handler and `can_set_up_tasks`/`has_tasks` in fixtures; every frontend matrix row; no bounce after setup success or 409; Back after setup does not reach Create Home; badge text; focus on error; date shown correctly in a negative UTC offset.
- [ ] `ARCHITECTURE-SPINE.md` -- `[REVISED 2026-11-09]` note under Core entities: TASK_TYPE is a code catalog; `epics.md` Story 2.1 note with decisions 2–6.
- [ ] `deferred-work.md` -- custom tasks (decision 5).
- [ ] `README.md` -- seed now gives tasks; "Prøv oppgaveoppsett" steps.
- [ ] `docs/ki-logg/korrigeringer.md` -- corrections found in review.

**Acceptance Criteria:**
- Given a user who just created a Home, when they confirm Task Setup with one adjusted and one unticked task, then they land on `/` and see the Tasks with the adjusted values and without the unticked one.
- Given the seed, when Mari signs in, then `/` lists eight tasks and at least one is due within a week or overdue.
- Given the route walk in `test_permissions.py`, when the suite runs, then the new `{home_id}` routes pass without editing that file.

## Design Notes

- **Custom tasks later:** a Task copies `name` from the catalog, so a later custom task needs only a nullable `task_type` (and `photo_evidence_eligible` false), no data rewrite.
- **Seed as of an earlier date:** `set_up_tasks(today=…)` lets the seed create realistic due dates through the domain instead of editing rows.
- **UTC date:** `due_on` uses the UTC date; between 00:00 and 01:00/02:00 Norwegian time it is a day behind. Accepted for Trinn 1; revisit if Epic 3's daily check needs Oslo dates (`zoneinfo` needs `tzdata` on Windows).

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all pass
- `cd frontend && npm test -- --run && npm run lint && npm run build` -- expected: all pass
- `alembic upgrade head` / `downgrade -1` against a throwaway database `husly_verify`, never `husly` -- expected: clean round trip

## Implementation Notes

## Spec Change Log

## Review Triage Log

Spec review 2026-11-09 (one adversarial reviewer; 19 findings, all verified against the code by the orchestrator, all taken in):

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | Setup redirect is a dead end: «Logg ut» and Members only on `/`; a Landlord's older Homes never reach setup | high | decision 8 (Eirik): exits on the setup page, «Sett opp oppgaver» in «Dine hjem» |
| 2 | Success can bounce back to setup: cache keys not named | high | `['tasks', homeId, userId]` + `has_tasks` written before `navigate(…, replace)` |
| 3 | 409 navigates before the refetch and bounces | high | await refetch, no navigate (as `useLeaveHome`) |
| 4 | Lock was on the wrong row; disjoint race passes; IntegrityError → 500 | medium | lock the Home row; IntegrityError → 409; SQLite gap accepted |
| 5 | Setup guards miss a foreign Home; a 403 would show an inline error | medium | guard order; no inline error on 403 |
| 6 | Existing frontend tests 404 on the new GET and miss new fields | medium | fakeApi default handler, fixtures, files named |
| 7 | CI seed counts and CHECK list | medium | `ci.yml` task |
| 8 | `test_seed` counts/order and skip cases; `.one()` crash | medium | lookup by creator + name; own message; skip tests |
| 9 | New models not registered in `models/__init__` | medium | Code Map + task |
| 10 | POST response and request shape undefined | medium | identical `TasksOut`; request shape stated |
| 11 | Two 422 shapes | medium | Pydantic for shape (generic), domain for rules (Norwegian string) |
| 12 | Model gaps for 2.4/2.5; unstable order | medium | `created_at`, unique `(task_id, due_on)`, Must → due → name → id |
| 13 | Back from setup reaches Create Home | low | `replace` |
| 14 | 1.8 notice lost when `/` redirects to setup | low | `PendingNotice` on setup |
| 15 | Form accessibility under-specified | low | fieldset/legend, unique radio names, no `disabled`, focus rule |
| 16 | Frequency list duplicated | low | `Literal` types → typed label map |
| 17 | `new Date('YYYY-MM-DD')` off by one | low | format from parts; test |
| 18 | `deps.py` half-done; redundant index | low | role aliases moved; index dropped |
| 19 | Missing tests (several Homes, no bounce, race, load error) | low | matrix rows and test task |
