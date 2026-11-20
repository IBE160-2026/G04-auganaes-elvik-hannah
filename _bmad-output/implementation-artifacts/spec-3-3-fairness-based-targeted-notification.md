---
title: 'Story 3.3: Fairness-based targeted notification'
type: 'feature'
created: '2026-11-20'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 01d7eca
context:
  - '{project-root}/_bmad-output/implementation-artifacts/spec-3-2-due-overdue-push-notifications-via-due-check-job.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The daily due-check (3.2) reminds every current Member of every due task, so the Member who always does a shared task is nagged as much as the one who never does (FR-11, AD-9, UJ-3).

**Approach:** When a shared recurring task's last three completions show that some Members did none while another current Member did at least one, the first reminder for that open instance goes only to those Members (the targets), once per instance, and the others get nothing for that instance that day. Later days remind everyone as in 3.2. The text is the normal due text. The number 3 is one constant in `domain/fairness.py`.

**Decisions (Claude's choices under Eirik's mandate, 2026-11-20; Eirik reviews them in the PR):**
1. *Replacement, not addition.* The nudge replaces the regular reminder for that instance on that run, for everyone: targets get it, the others skip it. FR-10 says targeting a Member who has not done their share is FR-11, and the story's point is that the reminder goes to whoever has not done it. «Once per instance» then means: after the nudge day the regular daily reminders resume for everyone, so no one is left unreminded.
2. *Who counts.* Current Household Members and Tenants only. The Landlord does not do the tasks, so is neither counted among the «at least two current Members», nor a target, nor a completer (a Landlord and one Tenant is not a shared task). A user who has left counts for nothing (AD-16).
3. *Window.* The last 3 completed instances of the task (any date), and the task must have at least 3 completed. It fires only if at least one current counted Member completed at least one of them, and only for those with none. Nobody completing (all by former Members) means no nudge and the regular reminder applies.
4. *Respects the cadence.* Only Members who would be reminded on this run by FR-13 take part, so a nudge never lands on a day a Tenant's cadence skips.
5. *Claim before send.* A row in `fairness_nudges` (unique on the task instance) is inserted before sending, so a second or parallel run sends no second nudge; a failed send is not retried (as AD-8). A run that loses the race sends nothing for that instance.
6. Nothing new for the user to see: no setting, no UI, no copy different from the normal due text.

## Boundaries & Constraints

**Always:** Active Tasks only; current Memberships only; UTC day through `today`; one claim per instance; the rule in one place (`domain/fairness.py`), read by the due-check.

**Never:** A different text or tone, a count or a name of who did the work in the message, a setting, a UI, a change to the daily claim (`due_notifications`) or to FR-13's cadence rule, touching Landlord messages (FR-12).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior |
|----------|--------------|---------------------------|
| Fires | Household of Mari, Jonas; last 3 completions all Mari; open instance due today | Jonas gets the normal due push; Mari gets none for it; one `fairness_nudges` row |
| Next day | Same instance still open | Both get the regular reminder; no second nudge |
| Fewer than 3 completed | 2 completions | No nudge; everyone reminded |
| One Member | Home with one counted Member | No nudge |
| Nobody completed | Last 3 by a Member who left | No nudge; everyone reminded |
| Shared evenly | Each counted Member has at least one of the 3 | No nudge |
| Landlord Home | Landlord plus one Tenant, Tenant did all 3 | No nudge (one counted Member); the Landlord is never a target |
| Two targets | 3 Members, one did all 3 | Both others get the push, the doer none |
| Already completed | Instance completed | Not due, so no nudge |
| Cadence | Tenant target on a day the cadence skips a Must task | No nudge that run; the instance is not claimed |
| Race | `fairness_nudges` row taken by a parallel run | Nothing sent for that instance in this run |

</frozen-after-approval>

## Code Map

- `backend/app/domain/fairness.py` -- `WINDOW = 3`, pure `nudge_targets(counted, completers)`, and `apply_nudges(session, by_member)`; reads completions and Home Memberships.
- `backend/app/domain/due_check.py` -- calls `apply_nudges` after `_due_by_member`; `DueTask` already carries instance, task and Home ids.
- `backend/app/models/fairness_nudge.py`, `models/__init__.py`, new Alembic revision -- table `fairness_nudges` (instance id unique, created_at).
- `backend/tests/test_fairness.py` -- the matrix; each test names its line.
- Docs: PRD FR-11 and FR-10 (+ Revision log), `epics.md` Story 3.3 revision note, AD-9 note, README, `deferred-work.md`.

## Tasks & Acceptance

**Execution:**
- [ ] model, revision, `domain/fairness.py` -- table and the rule
- [ ] `domain/due_check.py` -- apply nudges between selection and claim
- [ ] `tests/test_fairness.py` -- the matrix
- [ ] docs above

**Acceptance Criteria:**
- Given Mari did the last 3 completions and Jonas none, when the job runs on a due day, then only Jonas is reminded about that instance and only once.
- Given the rule does not hold (fewer than 3, one Member, nobody current completed, evenly shared), then everyone is reminded as before.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all green
- CI runs the migration check against Postgres.
