---
title: 'Story 2.4: Self-Checkoff Completion with Shared Status & Attribution'
type: 'feature'
created: '2026-11-11'
status: 'done'
route: 'dispatch'
baseline_commit: '6aade20431f12a9b9850d085b2ee0e0965a03cc3'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md'
  - '{project-root}/_bmad/custom/review-conventions.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** No one can mark a Task done: Task Overview rows are links only, there is no completion state in the database, and «Neste gang» reads the earliest instance whether or not it is done (issue #43; FR-7, FR-9, FR-17, UX-DR32, UX-DR42, AD-3, AD-16).

**Approach:** One domain function `complete_task_instance` (AD-3) records who completed which instance and when, and schedules the next instance; one route exposes it to every Member. Each Task Overview row gets a checkbox before the row link that completes the Task optimistically, retries quietly on transient failures, and shows the completed state with attribution («tidligere medlem» for a departed completer).

**Decisions (Eirik, 2026-11-11):**
1. **Completed state lasts while the next due date is «later» (1b):** a card shows its Task's latest completion as long as the open instance's `due_status` is `later`; once it is due soon or overdue, the card shows the due line and an empty checkbox again.
2. **The next instance is made in 2.4 (2b):** `complete_task_instance` also creates the next instance due on the completion's UTC date + the stored Frequency (FR-9). The completion time is when the server receives it. Story 2.5 is closed in the same PR: its ACs point to named tests here (a deviation from epics.md, noted there and in `sprint-status.yaml`).
3. **No undo (3a):** a completed card's checkbox is inert: stays checked, `aria-disabled="true"`, `aria-label` ««X» er fullført»; click or Space sends nothing.
4. **Copy (4a):** «Fullført i dag» / «Fullført i går» / «Fullført 3. november» (year when not this year), plus « av Peter» when another current Member of this Home did it, « av tidligere medlem» when the completer has no Membership in this Home; one's own completion never has a name, in any Home.
5. **Offline ticks live in memory only (6a):** a tick made offline is sent when the connection returns, as long as the app stays open; a reload or closing the app while offline loses it. Stated in README.
6. **Task Detail shows, not completes (13b):** Detail shows the completion note read-only; completing from Detail (EXPERIENCE.md) is left to Epic 4, where Photo Evidence lands on Detail. Noted in epics.md.

## Boundaries & Constraints

**Always:**
- Completion is addressed by instance id, so a retry after a lost response, a double tap, or a second Member hits the same instance and changes nothing: no new attribution, no second next instance (AD-3). Response = the Task as the list shows it (200).
- Any Member (`AnyMember`); a Task outside the path's Home, or an instance not of that Task → 404 «Fant ikke oppgaven.» (Task checked first).
- Lock order: the Task row (as `adjust_task`), then the instance, so completion and a Frequency change serialize. An `IntegrityError` on the next instance (a race) → rollback and return the current state, 200.
- A Task has at most one open instance (partial unique index); `tasks_of`, `_open_instance` and every Task response read it through one helper.
- Attribution references the User; the server sends who (`you` / `member` + name / `former_member`, Membership in *this* Home) and `completed_this_year`. The frontend never compares ids, reads roles or the browser clock.
- Checkbox first, row link second, two focus stops; controlled native `<input type="checkbox">`, `aria-label` «Merk «X» som fullført»; ≥44×44 target; tokens only.
- Optimistic: the completed state comes from pending mutations merged over the query data, so no refetch («Oppdater», pull, focus, reconnect) flips it back while the request is pending. Network errors, 5xx, 408 and 429 retry quietly with backoff (paused offline); any other rejection rolls back that one Task, refetches, and shows a visible inline message with `aria-live`, never a modal.
- UTC calendar dates, as `due_status` (a tick 00:00–01:00 Norwegian time counts as the day before: accepted).
- Migration with downgrade; downgrade deletes completed instances and is for throwaway databases only.

**Never:** a confirmation step; undo; persisted offline queue; completion from Task Detail; personal-space tasks; gamification or shaming copy; real-time push; changing the 2.3 adjust rules.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error handling |
|---|---|---|---|
| Complete | Jonas ticks «Rens sluket» (30 d) on 2026-11-11 | 200; instance completed by Jonas; open instance due 2026-12-11; card completed | N/A |
| Late completion | due 11-09, completed 11-11, 30 d | next due 12-11 | N/A |
| Same day as setup | open due 12-11 completed 11-11 | next due 12-11 beside the completed one | N/A |
| Retry / race / double tap | same instance id again, anyone | 200, unchanged; one next instance; still Jonas | N/A |
| Stale old instance id | a completed instance whose Task is due again | 200, current state, no message | N/A |
| Seen by another | Mari refreshes | «Fullført i dag av Jonas» | N/A |
| Own / one-person | Jonas or Sara views own | «Fullført i dag» | N/A |
| Departed | Jonas leaves (or is only a Member elsewhere) | «… av tidligere medlem», completion kept | N/A |
| Due again | open instance due soon | due line, empty checkbox | N/A |
| Adjust after completion | Frequency change | moves only the open instance; PATCH response keeps the completion | N/A |
| Tenant | Anders ticks | 200 (photo rule is Epic 4) | N/A |
| Foreign ids | other Home's Task, or other Task's instance | 404 | that card rolls back, refetch, visible message |
| Not a Member | any | 403 | global 403 handler |
| Transient | network error, 500/502/504 | card stays completed; retried | no message |

</frozen-after-approval>

## Code Map

- `backend/app/models/task.py` (`TaskInstance`) -- `completed_at` (timestamptz, null), `completed_by_user_id` (uuid FK `users`, null), `ck_task_instances_completion` (both null or both set). Replace `uq_task_instances_task_id_due_on` with partial unique index `uq_task_instances_open_task_id` on `task_id WHERE completed_at IS NULL` (`postgresql_where` and `sqlite_where`). Columns on the instance, not a MEMBER_COMPLETION table.
- `backend/alembic/versions/` -- hand-written revision after `bb9ad4eac78d`; downgrade deletes completed instances, drops columns/index, restores the old unique constraint.
- `.github/workflows/ci.yml` (Postgres step with the `ck_` probes) -- probe the migrated DB: second open instance rejected, completed one with the same date accepted, `ck_task_instances_completion` enforced (`alembic check` ignores `postgresql_where`; pytest uses `create_all`).
- `backend/app/domain/tasks.py` -- `tasks_of`, `_open_instance`, `_next_due`, `adjust_task`'s return: one `_task_with_due` path reading the open instance and the latest completion (batched per list, not per row). New `complete_task_instance(session, membership, task_id, instance_id, now=None) -> TaskWithDue` with the lock order and `IntegrityError` rule; `TaskWithDue` grows `instance_id` and completion fields. Membership check per Home: batched like `homes.is_member`.
- `backend/app/routes/tasks.py` -- `TaskOut.instance_id`, `TaskOut.completion: CompletionOut | None` (`completed_on`, `days_since`, `completed_this_year`, `by`, `name` only for `member`; null unless decision 1 shows it). `task_out` takes the viewer's user id (list, setup, adjust, complete). `POST /homes/{home_id}/tasks/{task_id}/instances/{instance_id}/completion`, `AnyMember`, 403/404 `ErrorOut`.
- `backend/app/seed/tasks.py`, `tests/test_seed.py` -- Jonas completes `avkalk-vannkoker` (60 d) 2 days before seeding, only in the run that set the Home up and only if Jonas is a Member; keep the due-soon assertion.
- `backend/tests/test_tasks.py`, `test_tasks_routes.py` -- every matrix row; decision 1 boundary; former member incl. Member elsewhere; `test_permissions.py` stays green.
- `frontend/src/api/tasks.ts` -- `completeTask`, `completionText(task)` (no `new Date()`), messages incl. rollback text.
- `frontend/src/api/queries.ts` -- `useCompleteTask(homeId)` with a `mutationKey`; `retry` for non-`ApiError` and 5xx/408/429; on other errors refetch the tasks; global 403 handler unchanged. A `useTasksWithPending(homeId)` (or equivalent) merges pending completions via `useMutationState`.
- `frontend/src/routes/TaskOverview.tsx` (`TaskRow`, `TaskListBody`) -- checkbox + link siblings; completed: checked inert box, strikethrough, success note; `nothingDue` treats completed cards as not due; visible rollback message.
- `frontend/src/routes/TaskOverview.css`, `TaskDetail.tsx` -- Detail shows the note read-only.
- `frontend/src/test-utils/fakeApi.ts` -- fixtures with `instance_id`/`completion`; completion handler (200/404/500/network error, pausable).
- `frontend/openapi.json`, `src/api/schema.d.ts` -- regenerate.

## Tasks & Acceptance

**Execution:**
- [x] `backend/app/models/task.py` + migration + `ci.yml` probes
- [x] `backend/app/domain/tasks.py` -- one open-instance helper, `complete_task_instance`
- [x] `backend/app/routes/tasks.py` -- `TaskOut` fields, completion route
- [x] `backend/tests/test_tasks.py`, `test_tasks_routes.py`, `test_seed.py`, `app/seed/tasks.py` -- matrix rows, seed completion
- [x] `frontend/openapi.json`, `src/api/schema.d.ts` -- regenerate
- [x] `frontend/src/api/{tasks,queries}.ts`, `test-utils/fakeApi.ts`
- [x] `frontend/src/routes/TaskOverview.{tsx,css,test.tsx}`, `TaskDetail.{tsx,test.tsx}` -- tests: focus order and labels; network error then success (stays checked, one saved POST); 500 retried; 404 rolls back only that card with a visible message; refetch during a pending POST keeps it checked; double tap = one request; completed box ignores click/Space; copy variants; Detail note
- [x] `README.md` -- «Prøv å krysse av oppgaver (Story 2.4)» incl. the offline limit
- [x] `_bmad-output/planning-artifacts/epics.md` (2.4, 2.5) and architecture revision note -- decisions, completion columns and one-open-instance index, AD-9 counts `completed_by_user_id` over a Task's last 3 completed instances; `sprint-status.yaml` 2.5 with 2.4
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` -- outcomes for the two "earliest open" entries and the 2.5 date collision

**Acceptance Criteria:**
- Given Jonas ticks «Rens sluket», when Mari presses «Oppdater», then her card reads «Fullført i dag av Jonas» with a checked box.
- Given a screen reader on Task Overview, when tabbing, then each card gives the checkbox («Merk «Rens sluket» som fullført») and then the row link.
- Given the network drops when Jonas ticks, when it returns with the app open, then the completion is saved without any action from him and the card never flipped back.
- Given a one-person Home, when Sara completes a task, then no completion text names a person.

## Implementation Notes

- Migration `c4e1d2a7b9f3`. `ck_task_instances_completion` is `(completed_at IS NULL) = (completed_by_user_id IS NULL)`. Ran upgrade, `downgrade -1`, upgrade, `alembic check`, `downgrade base` and upgrade, the seed twice, and every CI Python probe against a throwaway database (`husly_scratch_24`, dropped afterwards). The local `husly` database was not touched.
- `_rows` reads the list in three queries whatever its length: Tasks joined to the open instance, the latest completion per Task (`max(completed_at)` subquery) with the User, and the completers' Memberships in this Home. `test_the_list_is_read_in_three_queries_whatever_its_length` checks it.
- The seed picks the Task to complete by its values (Bør, 60 days), not by the key `avkalk-vannkoker`, because `test_task_types.py` forbids catalog keys in seed modules (AD-6). `kjokkenviftefilter` is also 60 days but is Må. The full seed now has 17 TaskInstances (`test_seed.FULL` and the CI count are updated).
- Frontend: one `useMutation` per card (`useCompleteTask`), with `mutationKey` `['complete-task', homeId, userId]`. `useTasksWithPending` merges the pending ones over the query data as `TaskView.pending`. A pending card shows «Fullført i dag», because one's own completion has no name and happens today, so there is no optimistic `completed_on`.
- Retries: transient failures (non-`ApiError`, 5xx, 408, 429) are retried at most `COMPLETE_RETRIES` = 8 times with TanStack's default backoff (about 2 minutes). Offline time does not count, because TanStack pauses. After the last retry the card rolls back with the message. The spec does not say how many retries; endless retries on a persistent 500 would leave a checked card that was never saved.
- On success, an in-flight tasks refetch is cancelled (it may be older than the completion), and the server's Task replaces the cached one in place. The list is not refetched, so cards do not move under the user's finger. The Must-first order is updated on the next refetch (focus, «Oppdater»).
- An inert completed box ignores the change in `onChange` and relies on the controlled `checked`. `preventDefault` on click was tried and left the DOM unchecked: React's restore and the browser's canceled-click restore both run.
- Task Detail shows the note under «Status» and merges pending ticks the same way. The 2.2 tab order in README now names the checkbox.
- Orchestrator check against the diff: the checkbox sat in a 44×44 `<span>`, so only the drawn box (`--space-5`) took a tap; changed to a `<label>` so the whole 44×44 area ticks it (Boundaries: ≥44×44 target). Re-ran pytest (565), Vitest (384), ruff, ESLint and build: all pass. Every matrix row has a covering test that ran.
- Chrome smoke 2026-11-12 on a throwaway DB `husly_smoke` (backend :8001, Vite :5174 with a temporary config, all removed afterwards; `husly` untouched), all passed: Mari's fresh seed shows «Avkalk vannkokeren» checked, `aria-disabled`, «Fullført 10. november av Jonas Berg»; Tab order «Oppdater» → box «Merk «Rens sluket» som fullført» → row link → next box; label target 44×67. Jonas completes the overdue «Støvsug og vask gulvene» (14 d) via the API: 200, next due 2026-11-26 (14 days from the completion, not from 29 Oct); the same instance id again: 200, unchanged. Mari presses «Oppdater»: «Fullført i dag av Jonas Berg». Mari ticks «Rens sluket» by clicking the label edge outside the drawn box: checked, struck through, «Fullført i dag» (no name), label ««Rens sluket» er fullført»; a click and Space on it send nothing (3 completion POSTs in the log: Jonas ×2, Mari ×1). Backend stopped (Vite answers 502), Mari ticks «Vask badet grundig»: card stays checked, no message; backend restarted: saved without any action (DB: completed by Mari, next instance 2026-12-24). Jonas leaves (`DELETE …/members/me` 204), Mari refreshes: «Fullført i dag av tidligere medlem» and «Fullført 10. november av tidligere medlem», completions kept; Task Detail shows «Status: Fullført i dag av tidligere medlem» and no checkbox. DB check: 16 open instances for 16 Tasks. Not exercised in the browser: the browser's own offline mode (`navigator.onLine` pause); covered by the frontend test «saves a tick made offline when the connection returns».

## Spec Change Log

## Review Triage Log

Spec review 2026-11-11 (one adversarial reviewer; 23 findings, evidence checked by the orchestrator): all taken in. Refetch during pending mutation (high), migration partial index unchecked in CI (high), lock order vs `adjust_task`, per-task rollback, retry 5xx, in-memory offline limit (team decision 5), hidden aria-live region, seed task choice, `IntegrityError` race, shared `_task_with_due`, named frontend tests, server receive time, Task Detail deviation (team decision 6), inert checkbox details, `nothingDue` and optimistic `completed_on`, `formatDueOn` clock, UTC midnight accepted, destructive downgrade, stale instance id row, per-Home membership, AD-9 note, 2.5 status, stale line refs.

Code review 2026-11-11 (Blind Hunter B, Edge Case Hunter E, Verification Gap V; 23 findings, verified against the code by the orchestrator):

| Finding | Verdict | Route / action |
|---|---|---|
| Settled state after a successful tick never observed: `setQueryData`/`cancelQueries` in `useCompleteTask.onSuccess` can be deleted with all tests green (V, pre-verified) | medium | patch: distinguishable stored completion, GET count, stale GET in flight |
| Partial index leaves completed instances without a `task_id` index; latest-completion subquery unindexed; model comment wrong (B) | medium | patch: plain index `(task_id, completed_at)` in model and migration |
| 403 on the completion POST untested (V, B) | low | patch: test no card message + global refetch |
| `isTransient` (408/429) untested (V) | low | patch: unit test |
| Task Detail pending merge untested (B, V other) | low | patch: one Detail test |
| ERD still draws MEMBER_COMPLETION (B) | low | patch: ERD line |
| EXPERIENCE.md Task Detail row not marked REVISED for decision 6 (B) | low | patch: REVISED sentence |
| README does not say the completion note counts UTC days (B) | low | patch: one sentence |
| CI CHECK probe covers one direction only (B) | low | patch: reverse probe |
| Retries-exhausted path has no UI test (V, B) | low | rejected: needs fake timers over ~2 min of backoff; the cap is the implementer's choice, the predicate is now unit-tested |
| Stale tick (old instance id, Task already due again) unchecks silently with 200 (E, B) | low | rejected: needs a list ≥4 days stale without any refetch (mount/focus refetch); fix adds a server flag and UI branch; matrix row "Stale old instance id" chose 200, no message |
| Error message lost if the card unmounts during a failing retry (E) | low | rejected: card still rolls back; rare; fix adds a second mutation-state read |
| Route reads `utc_now()` after the domain: a tick at 23:59:59.9 UTC can read «i går» (E) | low | rejected: sub-second window; UTC midnight already accepted |
| `IntegrityError` other than the partial index answered as 200 (E) | false | the only reachable constraint on that commit is the partial index: FK targets (Task, User from the Membership) exist and both completion fields are set together |
| Migration fails if a Task already has two open instances (E) | false | before 2.4 every Task has exactly one instance: `set_up_tasks` creates one and nothing else creates or moves instances into a second row |
| Seed `next()` raises StopIteration if the catalog loses its 60-day Bør (E) | low | rejected: loud failure on a catalog edit is correct; `test_seed` catches it |
| Seed rerun after a failed completion never adds it (E) | low | rejected: the completion runs in the same seed transaction sequence right after setup; a partial failure is a crashed seed, rerun on a fresh DB |
| Seeded completion predates the instance's `created_at` (B) | low | rejected: invisible to users; backdating `created_at` adds seed-only code |
| Detail shows the old «Frist» beside «Fullført i dag» while pending (B) | low | rejected: only during the short pending window or offline; fix adds a branch |
| `isTransient` retries programming errors (non-`ApiError`) (B) | low | rejected: such a bug still ends in rollback + message after the cap; narrowing to fetch's error shape is brittle across browsers |

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check .` -- all pass
- `cd frontend && npm test && npm run lint && npm run build` -- all pass
- `alembic upgrade head` / `downgrade -1` / `upgrade head` against a throwaway Postgres database (not `husly`) -- all pass

**Manual checks:**
- Chrome smoke on a throwaway DB: Jonas ticks, Mari refreshes and sees «av Jonas»; offline tick in DevTools, back online, saved; Jonas leaves, Mari sees «tidligere medlem».
