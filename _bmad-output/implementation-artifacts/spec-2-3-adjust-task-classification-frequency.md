---
title: 'Story 2.3: Adjust Task Må/Bør and Frequency on Task Detail'
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

**Problem:** After Task Setup, a Task's Må/Bør and Frequency can never change; Task Detail (Story 2.2) is read-only. A Household or Landlord cannot correct priorities, and nothing stops a Tenant from changing them via the API once an edit route exists (issue #40; FR-5, FR-8, UX-DR30).

**Approach:** One domain function and one route (`PATCH /api/homes/{home_id}/tasks/{task_id}`) change a Task's classification and/or Frequency, allowed only for Household Members and the Landlord. Task Detail shows the two fields as an editable form with «Lagre endringer» for them, and as locked, focusable read-only fields («Satt av utleier») for Tenants; a failed save shows an inline error with «Prøv igjen».

**Decisions (team, 2026-11-11):**
1. **A new Frequency moves the open due date (1b):** the open instance's `due_on` becomes `due_on − stored Frequency + new Frequency` (same start point, new interval), in the same transaction; it may become overdue at once. A classification-only change, or a Frequency equal to the stored one, leaves the date alone. 2.5 reschedules from completion with the stored Frequency.
2. **Saved with a button (2b):** the two controls are a form with «Lagre endringer»; nothing is sent until it is pressed. Only fields whose draft differs from the server's current value are sent; with no difference nothing is sent and «Ingen endringer å lagre.» is announced. On success «Lagret» is announced and the form shows the saved values. Leaving with unsaved changes gives no warning.

## Boundaries & Constraints

**Always:**
- Server-side permission: `require_role` runs first, so a Tenant gets 403 for any body or `task_id`. `ADJUST_ROLES = SETUP_ROLES` and `can_adjust_tasks(role)` in `domain/tasks` are the one rule; `adjust_task` raises `ValueError` for another role (as `set_up_tasks`); `HomeOut.can_adjust_tasks` carries it to the frontend.
- A `task_id` not in the path's Home → 404 «Fant ikke oppgaven.».
- Request fields typed `Classification | None` / `Frequency | None`: wrong values are a shape 422 (standard body); `null` = absent; all absent → 422 «Ingen endring.». Values equal to the stored ones → 200, nothing written.
- The Task row is locked (`with_for_update`, as `set_up_tasks`) before the shift, so parallel saves cannot mix Frequency and date (SQLite ignores it; accepted risk).
- Response = the edited Task as `TaskOut`; the client then invalidates the Home's tasks query so order comes from the server.
- Tenant view: per field a `<input type="text" readOnly aria-readonly="true" aria-describedby=…>` showing the value, lock glyph `aria-hidden`, dashed border; no `select`/radio, never `disabled`.

**Never:** a migration; a separate admin screen; editing the name; client-side role logic; touching other Tasks, Homes or the catalog.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error handling |
|---|---|---|---|
| Må→Bør | Household Member, `{classification:"should"}` | 200; Overview lists it among Bør; `due_on` unchanged | N/A |
| Longer | Landlord, 30→60, open due 2026-12-01 | open due 2026-12-31 | N/A |
| Shorter past today | 365→7, start 65 days ago | open due 58 days ago → `overdue` | N/A |
| No-op | value equal to stored, or resend | 200, nothing written | N/A |
| Tenant | any body, any `task_id` | 403 | UI: global 403 handler, no inline error |
| Foreign/unknown Task | another Home's Task id | 404 | UI: invalidate tasks; TaskLoader guard returns to the overview |
| Bad shape | `frequency_days:10`, `"x"`, `{}` | 422 | `{}`/all null → «Ingen endring.» |
| Save fails | 5xx or network | draft kept; error at the form, «Prøv igjen» submits the current draft | `GENERIC_ERROR` for both (deliberate) |
| Stale form | another member saved; refetch arrives | untouched fields show the new server value; Save on untouched fields sends nothing | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/domain/tasks.py:26,50,121,159` -- `SETUP_ROLES`, `can_set_up_tasks`, role guard and row-lock pattern in `set_up_tasks`, `tasks_of`. Add `ADJUST_ROLES`, `can_adjust_tasks`, `TaskNotFound`, `NO_CHANGE`, `adjust_task(session, membership, task_id, classification=None, frequency_days=None) -> TaskWithDue`; the instance to move comes from one helper `_open_instance(session, task_id)` (earliest instance until 2.4 makes it "earliest open").
- `backend/app/domain/task_types.py:14,18` -- `Classification`, `Frequency` literals.
- `backend/app/routes/tasks.py:42-90` -- `TaskChoiceIn` pattern; factor one `task_out(row, today)` out of `tasks_out`; add `AdjustTaskRequest` and the PATCH route (responses 403/404 `ErrorOut`).
- `backend/app/routes/deps.py:34` -- add `TaskAdjuster` over `ADJUST_ROLES`; keep `TaskSetter`.
- `backend/app/routes/homes.py:46-60,80-82` -- `HomeOut.can_adjust_tasks` + both `home_out` sites.
- `backend/tests/test_permissions.py` -- stays green.
- `frontend/src/routes/TaskDetail.tsx:37,62` -- `Detail` gets the form; draft state is `null` per field (= show `task.*`), diffed against the current `task`.
- `frontend/src/api/tasks.ts:39,108` -- options from `FREQUENCY_LABELS` (no catalog query); `adjustTask` with `toApiError(passThrough: [404, 422])`.
- `frontend/src/api/queries.ts:30-46,251` -- global 403 handler (incl. `MutationCache`); `useAdjustTask(homeId)` invalidates `tasksKey`, on 404 too. Persistent empty `role="status"` region for «Lagret»/«Ingen endringer å lagre.»; `PrimaryButton pending` blocks double submit; focus stays on the button.
- `frontend/src/routes/TaskDetail.css` -- tokens `--color-surface-raised`/`--color-surface-base`, `--color-ink-secondary`, `--radius-sm`; no `--radius-full` (`styles/tokens.test.ts:14`).
- `frontend/src/test-utils/fakeApi.ts:56` -- `can_adjust_tasks` on every fixture, a Tenant fixture, PATCH handler factory (200/403/404/500).
- Seed (`backend/app/seed/tasks.py:52`) makes one instance per Task: the shift is safe on fresh data.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/app/domain/tasks.py` -- rule, `_open_instance`, `adjust_task` (guard, lock, shift, no-op)
- [ ] `backend/app/routes/{tasks,deps,homes}.py` -- PATCH, `TaskAdjuster`, flag
- [ ] `backend/tests/test_tasks.py` -- shift both ways, already overdue, classification-only, equal value, only earliest instance moves, other Tasks/Homes untouched, role guard
- [ ] `backend/tests/test_tasks_routes.py`, `test_homes_routes.py` -- roles × fields, Tenant + foreign id = 403, 404, 422 shapes, flag values
- [ ] `frontend/openapi.json`, `src/api/schema.d.ts` -- regenerate
- [ ] `frontend/src/api/{tasks,queries}.ts`, `test-utils/fakeApi.ts` -- client, hook, fixtures
- [ ] `frontend/src/routes/TaskDetail.{tsx,css,test.tsx}` -- form, locked view, statuses, error + retry, 403 silent, 404 back, stale-form test
- [ ] `README.md` -- fix line 133 («redigering kommer i Story 2.3») and add «Prøv å justere oppgaver (Story 2.3)» on a freshly seeded DB
- [ ] `_bmad-output/planning-artifacts/epics.md` (Story 2.3) -- "Note 2026-11-11 (team decisions, Story 2.3 spec)": save button instead of saving on change, "reflected" = after refetch, error at the form, decision 1; mirror decision 1 in the architecture revision notes
- [ ] `_bmad-output/implementation-artifacts/deferred-work.md` -- Story 2.4 must switch `_open_instance` together with `tasks_of`; after 2.5, moving may hit `uq_task_instances_task_id_due_on`

**Acceptance Criteria:**
- Given Mari changes «Rens sluket» to Bør in «Mari og Jonas sitt hjem» and saves, when Jonas presses «Oppdater» on his overview, then it is listed among Bør.
- Given Anders (Tenant) on a «Storgata 12» Task, when the page renders, then both fields are read-only inputs reachable by Tab, announced with «Satt av utleier», with no select or radio.
- Given a save fails, when Mari presses «Prøv igjen» after the server recovers, then the draft is saved and the error disappears.
- Given Mari picks a new Frequency without saving, when she leaves and returns, then the stored Frequency shows and nothing was sent.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Spec review 2026-11-11 (one adversarial reviewer; 21 findings, all verified against the code by the orchestrator, all taken in): 422 from Pydantic literals (high); stale form undoing another's edit (high); `aria-readonly` needs a role → read-only inputs (high); epics.md deviation note (high); README line 133; `_open_instance` + deferred-work for 2.4/2.5; row lock; no-op and null semantics; 403-before-404 order; domain role guard; 404 in UI; retry submits current draft, shared message; domain/frontend tests; `ADJUST_ROLES`/`TaskAdjuster`; options from `FREQUENCY_LABELS`; status region, pending, focus; tokens and `--radius-full`; fakeApi fixtures; `HomeOut` sites; verifiable AC 1; seed note.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check .` -- all pass
- `cd frontend && npm test && npm run lint && npm run build` -- all pass

**Manual checks:**
- Chrome smoke on a throwaway DB (not `husly`): Mari edits both fields, Overview reorders, due date moves; Anders sees the locked view; a forced 500 shows the error and retry works.
