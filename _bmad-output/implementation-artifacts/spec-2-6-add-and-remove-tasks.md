---
title: 'Story 2.6: Add and Remove Tasks'
type: 'feature'
created: '2026-11-12'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md'
  - '{project-root}/_bmad/custom/review-conventions.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After Task Setup nobody can add a Task the Home needs or drop one it no longer needs; a Task is a catalog entry or nothing, and nothing can be removed (issue #31; FR-24, FR-4, FR-8, AD-2, AD-3, AD-6, AD-16).

**Approach:** Two domain functions (`add_task`, `archive_task`) and two routes for Household Members and Landlords. «Legg til oppgave» opens one page that adds one catalog Task or one custom Task; «Fjern oppgaven» on Task Detail archives with an inline confirmation. Archiving sets `archived_at`; nothing is deleted, and every behaviour-driving read sees active Tasks only.

**Decisions (Eirik, 2026-11-12; the rest were mine and are in Boundaries):**
1. **One Add Task page (1a):** a radio list of the catalog types the Home has no active Task for, plus «Egen oppgave» last. A catalog choice shows its recommended Må/Bør and Frequency to adjust; «Egen oppgave» shows a name field and the same two controls. One save button, one Task per save.
2. **Placement (2a):** «Legg til oppgave» sits in the Task Overview header next to «Medlemmer og invitasjon», for Household Members and Landlords only.
3. **Notices (3a):** after adding, Task Overview shows «La til «X».»; after removing, «Fjernet «X».» — both through the one-time notice of Story 1.8 (`aria-live`, shown once).
4. **Not before setup (4a):** adding while Task Setup has not run answers 409 «Sett opp oppgavene først.», so a single add can never close the one-time setup.

## Boundaries & Constraints

**Always:**
- Who may: `tasks.ADJUST_ROLES` (the setup roles) through the existing `TaskAdjuster` and `HomeOut.can_adjust_tasks`, which now also means add and archive. No new flag; a Tenant gets 403 from `require_role` before the body is read, and the `test_permissions.py` walk covers both routes.
- Names: the rule is "an active Task's name is unique, case-insensitively", checked in the domain on both paths with `strip()` and `casefold` (inner whitespace is kept). A custom Task's `name` is trimmed, 1–100 characters; a catalog Task's name is the catalog's, so adding a catalog type whose name an active custom Task already uses is refused too. Archive, add custom «Rens sluket», then add the catalog type is refused with the same message. There is no cap on active Tasks per Home (accepted).
- Custom Task: `classification` and `frequency_days` from the fixed lists. Exactly one of `task_type` and `name` is given. Every rule violation is 422 with a Norwegian message at the field.
- `tasks.task_type` becomes nullable (custom Task) and `tasks.archived_at` is added. `uq_tasks_home_id_task_type` is replaced by partial unique indexes on active Tasks: `(home_id, task_type)` and `(home_id, lower(name))`, both `WHERE archived_at IS NULL`, plus a plain `ix_tasks_home_id`. A catalog type can be added again after archiving as a new Task with a new first instance (today + Frequency); the archived Task and its history stay unchanged.
- Archive finds the Task by id and Home without the archived filter and sets `archived_at` only if null, so an already archived Task answers 204 and changes nothing, while PATCH and the completion route (which filter archived Tasks) answer 404 for the same id. A Task of another Home or an unknown id is 404 «Fant ikke oppgaven.». Adjust and complete treat an archived Task as not found (404), so a tick or edit on a stale card rolls back with the existing message.
- Every Task read (`_rows`, so list, adjust, complete and add) excludes archived Tasks. `has_tasks` and `home_ids_with_tasks` keep counting all Tasks, so archiving the last one shows «Ingen oppgaver i hjemmet ennå.» and never reopens setup.
- Seed and the CI counts (16 Tasks, 17 instances) stay unchanged.
- Eligibility for Photo Evidence is a domain function reading the catalog by key; a Task without a `task_type` is never eligible (AD-6). Story 4.1 calls it.
- Locks like `adjust_task`: the Task row `FOR UPDATE` when archiving; adding locks the Home row like `set_up_tasks`. One duplicate message for type and name: «Hjemmet har allerede en oppgave som heter «X».» An `IntegrityError` from either index rolls back, re-runs the domain checks to pick the message, and otherwise answers 422 with the generic one; it is never mapped to `TasksAlreadySetUp`.
- Frontend: no `fetch` or server data in `useState`; hooks over the generated client; types regenerated. After adding, the tasks query is refetched before navigating, so the list shows the new Task. A 403 shows no inline message (global handler). Failures show an inline error with retry at the action (UX-DR30). Remove uses `ConfirmAction` (danger colour on the confirming button only). Add Task form: no radio is preselected and Save without a choice shows «Velg en oppgave.» at the radio group; switching radios resets Må/Bør and Frequency to that choice's defaults and keeps a typed name; when every catalog type is active only «Egen oppgave» is shown, preselected; choosing «Egen oppgave» moves focus to the name field; the radio group has a legend, and the remove confirm button's accessible name includes the Task. A «La til»/«Fjernet» notice is set in the same tick as the navigation and never shown on a later page (tested). Tokens only; ≥44×44 targets.
- Migration, in order: drop the `UniqueConstraint` `uq_tasks_home_id_task_type` (`drop_constraint`), alter `task_type` to nullable, add `archived_at`, create the two partial unique indexes and `ix_tasks_home_id`. Downgrade, in order: delete instances of custom and archived Tasks, delete those Tasks, `SET NOT NULL`, recreate the constraint. `alembic check` must be clean after `upgrade head` (CI runs it after downgrade base and upgrade); if the expression or partial index shows a diff, fix the model definition and say how. Migration with downgrade; the downgrade deletes custom and archived Tasks with their instances to restore the old constraint, and is for throwaway databases only. README and `.env.example` updated in the same PR (README only; no new variables).

**Never:** a second setup; editing a catalog Task's name; restoring an archived Task; deleting data; bulk add or remove; changing the 2.3 adjust or 2.4 completion rules; Photo Evidence UI (Epic 4).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error handling |
|---|---|---|---|
| Add catalog | Mari adds «Avkalk vannkokeren» (Bør, 60 d), no active Task of it | 201, new Task and instance due today+60; Overview lists it with «La til «Avkalk vannkokeren».» | N/A |
| Add custom | name «  Vask gardiner  », Bør, 90 d | 201, name stored trimmed | N/A |
| Bad name | empty after trim, 101 chars, or equal to an active Task's name in other case | 422 with message | shown at the name field |
| Both or neither | `task_type` and `name` both set, or both missing | 422 «Velg en oppgave eller skriv et navn.» | shown at the form |
| Active type exists | catalog type the Home already has (stale list) | 422 «Hjemmet har allerede «X».» | shown; list refetched |
| Unknown type or bad value | key not in the catalog; Frequency 5 | 422 | shown |
| Before setup | Home has no Tasks | 409 «Sett opp oppgavene først.» | guard routes to setup |
| Archive | Mari removes «Rens sluket» and confirms | 204; gone from list for everyone; instances and completions kept; «Fjernet «Rens sluket».» | N/A |
| Archive twice | double tap, second tab | 204 both times, no change | no error shown |
| Add after archive | «Rens sluket» again | new Task, new first date; archived row untouched | N/A |
| Tick or adjust archived | stale card | 404 «Fant ikke oppgaven.» | card rolls back, refetch |
| Last Task archived | every Task archived, `has_tasks` still true | adjusters see «Ingen oppgaver i hjemmet ennå.» + «Legg til oppgave»; a Tenant sees «Utleier har ikke satt opp oppgaver ennå.» (decided in EXPERIENCE.md); never «nyt det» | setup not offered |
| Catalog name taken | catalog type whose name an active custom Task uses | 422 duplicate message | shown; catalog list refetched |
| Archive, custom, re-add | archive «Rens sluket», add custom «Rens sluket», add the catalog type | third step 422 | shown |
| Tenant | any add or archive | no buttons; 403 | global 403 handler |
| Foreign ids | Task of another Home | 404 | refetch |
| Custom and photo | custom Task | eligibility false | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/models/task.py` (`Task`) -- `task_type` nullable, `archived_at` (timestamptz, null); replace `uq_tasks_home_id_task_type` with the two partial unique indexes (`postgresql_where` and `sqlite_where`; the name index on `func.lower(name)`) and `ix_tasks_home_id`.
- `backend/alembic/versions/` -- hand-written revision after `c4e1d2a7b9f3`; downgrade as in Boundaries.
- `.github/workflows/ci.yml` (Postgres probe step) -- probe the migrated DB: second active Task with the same type or lower-case name rejected; archived one with the same type or name accepted. `alembic check` ignores `postgresql_where`; pytest uses `create_all`.
- `backend/app/domain/tasks.py` -- `_rows` and the two lookups in `adjust_task`/`complete_task_instance` filter `archived_at IS NULL`; new `add_task(session, membership, task_type, name, classification, frequency_days, today=None) -> TaskWithDue`, `archive_task(session, membership, task_id, now=None) -> None`, `photo_evidence_eligible(task) -> bool`, `TasksNotSetUp`, message constants; `can_adjust_tasks` comment says it covers add and archive. Reuse `_validate` rules (`BAD_CLASSIFICATION`, `BAD_FREQUENCY`), `set_up_tasks`'s Home lock and first-instance code (extract the shared line, do not copy).
- `backend/app/routes/tasks.py` -- `AddTaskRequest`, `POST /homes/{home_id}/tasks` (201, `TaskAdjuster`, 403/409/422), `DELETE /homes/{home_id}/tasks/{task_id}` (204; `responses` for 403 and 404 so the client types them). `TaskOut.task_type` becomes `str | None`.
- `backend/tests/test_tasks.py`, `test_tasks_routes.py`, `test_permissions.py` (stays green), `test_task_types.py` -- every matrix row, the eligibility function, both index backstops on SQLite (`create_all`) and Postgres (CI probes), archived Task not read by list, adjust or complete (DELETE 204 but PATCH and completion 404), a re-added catalog type leaving the archived Task's completions untouched, and `task_type: null` in the list and Detail responses.
- `frontend/openapi.json`, `src/api/schema.d.ts` -- regenerate.
- `frontend/src/api/tasks.ts` -- `addTask`, `archiveTask`, messages (`added(name)`, `removed(name)`, `addFailed`, `archiveFailed`, `noTasks`).
- `frontend/src/api/queries.ts` -- `useAddTask(homeId)` (notice, refetch tasks, then resolves), `useArchiveTask(homeId)` (notice, refetch; 404 refetches).
- `frontend/src/routes/AddTask.tsx`, `AddTask.css`, `AddTask.test.tsx`, `src/App.tsx` -- route `/hjem/:homeId/legg-til-oppgave`; guards: unknown Home → "/", not `can_adjust_tasks` or no `has_tasks` → the Home's overview. Reuse the Setup row's pill and select styling (`TaskSetup.css`) rather than a new look; `TaskSetup.tsx`'s radio and frequency pieces may be extracted if that avoids copying.
- `frontend/src/routes/TaskOverview.tsx`, `.css`, `.test.tsx` -- header link for adjusters; empty-Tasks state (`views.length === 0` is not «nyt det»).
- `frontend/src/routes/TaskDetail.tsx`, `.test.tsx` -- «Fjern oppgaven» (`ConfirmAction`) for adjusters; success navigates to the overview.
- `frontend/src/test-utils/fakeApi.ts` -- add/archive handlers, archived fixtures.
- `README.md`, `epics.md` (Story 2.6 note on decisions and the notices), `deferred-work.md` (custom-task outcome), `sprint-status.yaml` -- same PR.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/app/models/task.py` + migration + `ci.yml` probes -- schema and index backstops
- [ ] `backend/app/domain/tasks.py` -- `add_task`, `archive_task`, archived filter, eligibility
- [ ] `backend/app/routes/tasks.py` -- the two routes, `TaskOut.task_type` nullable
- [ ] `backend/tests/*` -- matrix rows and permissions
- [ ] `frontend/openapi.json`, `src/api/schema.d.ts`, `src/api/{tasks,queries}.ts`, `src/test-utils/fakeApi.ts`
- [ ] `frontend/src/routes/AddTask.*`, `App.tsx` -- Add Task page and route
- [ ] `frontend/src/routes/TaskOverview.*`, `TaskDetail.*` -- link, empty state, remove
- [ ] `README.md`, `epics.md`, `deferred-work.md`, `sprint-status.yaml`

**Acceptance Criteria:**
- Given Mari on Task Overview, when she adds a catalog Task or a custom Task and saves, then she lands back on the list with «La til «X».» announced and the Task listed in Must-first order.
- Given Mari on Task Detail, when she presses «Fjern oppgaven» and confirms, then she lands on Task Overview with «Fjernet «X».», the Task is gone for Jonas after a refresh, and its instances and completions are still in the database. If it is added again as a catalog Task it starts without history.
- Given Anders (Tenant), when he opens Overview or Detail, then he sees neither button, and a direct `POST` or `DELETE` is 403.
- Given a screen reader on Add Task, when tabbing, then the radio group, the Må/Bør pills, the Frequency select (and the name field for «Egen oppgave») and the save button are labelled with their task and state, and an error is announced at its field.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Spec review 2026-11-12 (one adversarial reviewer; 15 findings, evidence checked by the orchestrator against `bb9ad4eac78d`, `env.py`, `ci.yml` and `TaskOverview.tsx`): all taken in. Catalog name vs active custom name, archive-then-re-add sequence, `IntegrityError` mapping, Add form state, archive-vs-404 lookup split, Tenant empty-state copy, notice left behind after navigation, ordered migration and downgrade steps, `alembic check` after the expression index, collation claim weakened, no cap on active Tasks (accepted), `responses` on DELETE, seed and CI counts unchanged, a11y focus and names, three test gaps.

## Design Notes

The name uniqueness check runs in the domain (clear message) and the partial index is the backstop for a race (same pattern as `set_up_tasks` and `(home_id, task_type)`). Postgres `lower()` depends on the database collation and SQLite's is ASCII-only, so the domain compares with Python `casefold` before the insert and the SQLite test covers ASCII only (noted in the test). The index is the race backstop (ASCII under a `C` collation); the Unicode rule is the domain check.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check .` -- all pass
- `cd frontend && npm test && npm run lint && npm run build` -- all pass
- `alembic upgrade head` / `downgrade -1` / `upgrade head` against a throwaway Postgres database (not `husly`) -- all pass

**Manual checks:**
- Chrome smoke on a throwaway DB: Mari adds a catalog and a custom Task, removes one and adds it again; Anders (Tenant) sees no buttons; Jonas refreshes and sees the changes.
