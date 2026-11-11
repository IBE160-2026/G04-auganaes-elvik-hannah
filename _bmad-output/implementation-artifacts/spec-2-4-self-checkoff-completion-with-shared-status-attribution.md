---
title: 'Story 2.4: Self-Checkoff Completion with Shared Status & Attribution'
type: 'feature'
created: '2026-11-11'
status: 'in-progress'
route: 'dispatch'
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
- [ ] `backend/app/models/task.py` + migration + `ci.yml` probes
- [ ] `backend/app/domain/tasks.py` -- one open-instance helper, `complete_task_instance`
- [ ] `backend/app/routes/tasks.py` -- `TaskOut` fields, completion route
- [ ] `backend/tests/test_tasks.py`, `test_tasks_routes.py`, `test_seed.py`, `app/seed/tasks.py` -- matrix rows, seed completion
- [ ] `frontend/openapi.json`, `src/api/schema.d.ts` -- regenerate
- [ ] `frontend/src/api/{tasks,queries}.ts`, `test-utils/fakeApi.ts`
- [ ] `frontend/src/routes/TaskOverview.{tsx,css,test.tsx}`, `TaskDetail.{tsx,test.tsx}` -- tests: focus order and labels; network error then success (stays checked, one saved POST); 500 retried; 404 rolls back only that card with a visible message; refetch during a pending POST keeps it checked; double tap = one request; completed box ignores click/Space; copy variants; Detail note
- [ ] `README.md` -- «Prøv å krysse av oppgaver (Story 2.4)» incl. the offline limit
- [ ] `_bmad-output/planning-artifacts/epics.md` (2.4, 2.5) and architecture revision note -- decisions, completion columns and one-open-instance index, AD-9 counts `completed_by_user_id` over a Task's last 3 completed instances; `sprint-status.yaml` 2.5 with 2.4
- [ ] `_bmad-output/implementation-artifacts/deferred-work.md` -- outcomes for the two "earliest open" entries and the 2.5 date collision

**Acceptance Criteria:**
- Given Jonas ticks «Rens sluket», when Mari presses «Oppdater», then her card reads «Fullført i dag av Jonas» with a checked box.
- Given a screen reader on Task Overview, when tabbing, then each card gives the checkbox («Merk «Rens sluket» som fullført») and then the row link.
- Given the network drops when Jonas ticks, when it returns with the app open, then the completion is saved without any action from him and the card never flipped back.
- Given a one-person Home, when Sara completes a task, then no completion text names a person.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Spec review 2026-11-11 (one adversarial reviewer; 23 findings, evidence checked by the orchestrator): all taken in. Refetch during pending mutation (high), migration partial index unchecked in CI (high), lock order vs `adjust_task`, per-task rollback, retry 5xx, in-memory offline limit (team decision 5), hidden aria-live region, seed task choice, `IntegrityError` race, shared `_task_with_due`, named frontend tests, server receive time, Task Detail deviation (team decision 6), inert checkbox details, `nothingDue` and optimistic `completed_on`, `formatDueOn` clock, UTC midnight accepted, destructive downgrade, stale instance id row, per-Home membership, AD-9 note, 2.5 status, stale line refs.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check .` -- all pass
- `cd frontend && npm test && npm run lint && npm run build` -- all pass
- `alembic upgrade head` / `downgrade -1` / `upgrade head` against a throwaway Postgres database (not `husly`) -- all pass

**Manual checks:**
- Chrome smoke on a throwaway DB: Jonas ticks, Mari refreshes and sees «av Jonas»; offline tick in DevTools, back online, saved; Jonas leaves, Mari sees «tidligere medlem».
