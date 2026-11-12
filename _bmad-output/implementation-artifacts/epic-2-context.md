# Epic 2 Context: Task Management Core Loop

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Give every Member of a Home (Household Member, Tenant, Landlord) the core loop of Husly: a Must-first task list per Home, inline adjustment of Må/Bør and Frequency for Household Members and Landlords (locked for Tenants), one-tap self-checkoff with shared status and per-member attribution, automatic rescheduling counted from the actual completion date, and adding or archiving Tasks after the first setup. Stories 2.1 to 2.3 are done; 2.4 and 2.5 are built together (PR #44, in review); the next story is 2.6. The epic owns the single completion domain function that Photo Evidence (Epic 4) later extends. All of Epic 2 is Trinn 1 and must run locally without team accounts.

## Stories

- Story 2.1: Task Setup at Home Creation (done)
- Story 2.2: Must-First Task Overview (done)
- Story 2.3: Adjust Task Classification & Frequency (done)
- Story 2.4: Self-Checkoff Completion with Shared Status & Attribution (review, PR #44)
- Story 2.5: Auto-Reschedule on Completion (review, built with 2.4)
- Story 2.6: Add and Remove Tasks (next)

## Requirements & Constraints

- **Who may adjust (2.3):** Household Members and Landlords can change a Task's Må/Bør classification and Frequency. Tenants cannot; they inherit the Landlord's setting. The rejection must happen server-side (403), not only by hiding controls — a Tenant calling the API directly is refused for both fields.
- **Effect of a change:** it persists and is visible to every Member of that Home, Tenants included (read-only), on their next refetch. A new Frequency governs the next auto-reschedule. The planning docs do not say whether an already-open instance's due date shifts when Frequency changes — an open decision for the 2.3 spec.
- **Frequency values:** chosen only from fixed intervals 7, 14, 30, 42, 60, 90, 182, 365 days («Hver uke» … «Hvert år»); anything else is rejected with 422.
- **Must-first ordering:** all Must tasks above all Should tasks regardless of due date; by due date within a tier. A classification change therefore moves the Task between tiers on Task Overview.
- **Completion (2.4/2.5):** any Member completes an instance in one action, no confirmation; status is shared for the Home; the completing User is recorded and queryable per Home. One-person Homes never see copy implying a second person («Fullført i dag»). Next instance is due N days after the actual completion date; retried completion changes nothing.
- **Add/archive (2.6):** Household Member/Landlord only; catalog types without an active Task, or custom Tasks (name 1–100 chars trimmed, unique among active Tasks case-insensitively). Archiving is idempotent and never deletes. Custom Tasks can never require Photo Evidence.
- **Active vs archived / current vs past:** behaviour-driving reads use active Tasks and current Memberships only; history is kept and a departed completer shows as «Tidligere medlem». `has_tasks` means "Task Setup has run".
- **Out of scope:** personal-space tasks, any gamification, shaming copy for missed tasks.
- **Runnable without accounts:** seed data keeps giving a reviewer a populated Task Overview, including a Landlord Home with a Tenant (Kari/Anders) to show the locked state; README and `.env.example` updated in the same PR as changes that need it.

## Technical Decisions

- **Layering:** routes never mutate data; all mutations go through domain services in `backend/app/domain` (tasks live in `domain/tasks`). Shared route dependencies (`SessionDep`, `ErrorOut`, role aliases) are in `backend/app/routes/deps.py`.
- **Permissions:** role lives on the Membership, resolved per request by `require_role(*roles)` with `home_id` read from the path only, never from a token claim. Every Home-scoped route sits under `/api/homes/{home_id}/...`; `tests/test_permissions.py` fails if a `{home_id}` route lacks `require_role` (or vice versa). The endpoint must also verify the Task belongs to that `home_id`. Permission rules belong in the domain layer and are tested there (the pattern from `can_leave`/`can_remove`: compute a flag server-side and send it to the frontend rather than re-deriving role logic in components).
- **Data model:** the task-type catalog is a versioned Python module (`domain/task_types.py`), not a table. A Task copies name, classification and Frequency at creation, so editing a Task never touches the catalog and a new catalog version never rewrites Tasks. Photo-evidence eligibility is read from the catalog by key, never stored on the Task. A TaskInstance has a UTC calendar `due_on`; a Task has at most one open instance (partial unique index `uq_task_instances_open_task_id` on `task_id WHERE completed_at IS NULL`), and completion is two columns on the instance (`completed_at`, `completed_by_user_id`). 2.6 adds nullable `archived_at`, nullable `task_type` and partial unique indexes `WHERE archived_at IS NULL`.
- **Next due date:** every Task read goes through `domain/tasks._rows`, which joins the one open instance; a Frequency change moves only that instance. Archived Tasks must be excluded there (2.6).
- **Single completion path:** `complete_task_instance` alone marks complete, records attribution (referencing the User, not the Membership) and triggers the reschedule; idempotent. Checkbox and later photo upload only call it.
- **Frontend data:** no direct `fetch` or server data in `useState`; reads/writes via TanStack Query hooks over the generated OpenAPI client (regenerate types after API changes). Self-checkoff is optimistic; other saves need not be. After a mutation, invalidate the Home's tasks query so Overview and Detail agree. No real-time layer — freshness from refetch on mount/window focus.
- **Errors:** shared `ApiError` in `frontend/src/api/errors.ts`; backend uses `{"detail": "..."}` (Norwegian message) and standard 422 bodies. A global 403 handler in `createQueryClient` refetches Homes and members when access disappears; new mutations must not fight it.
- **Time:** `app/clock.py` (`UtcDatetime`) for now/today; ISO 8601 UTC on the wire. Test helpers in `backend/tests/helpers.py`.
- **Schema:** every change is an Alembic migration; run `alembic downgrade` only against a throwaway database, never the local `husly`.
- **Styling:** only `var(--...)` design tokens; no literal hex, px or radii.
- **Accepted risk:** pytest runs on SQLite, so row-lock behaviour is reasoned, not tested.

## UX & Interaction Patterns

- **Task Detail** (`/hjem/<id>/oppgaver/<taskId>`, minimal read-only since 2.2) is where 2.3 adds inline editing of Må/Bør and Frequency — no separate admin screen. Single column at every width.
- **Frequency/Must toggle, editable state** (Household Member, Landlord): white surface, solid border, directly editable.
- **Locked state** (Tenant): `surface-base` fill, dashed border, lock glyph and the label «Satt av utleier». Stays focusable: `aria-readonly="true"` plus `aria-describedby` pointing at the label — never native `disabled`, never a greyed control without explanation.
- **Save failure:** inline error at the field with a retry affordance, distinct from the offline/network state; never a silent failure.
- **Badges** read «Må»/«Bør» (Norwegian-only UI), text always present, colour only reinforcement. Due states: «Snart forfall» (warning, bold, within 3 days) and «Forfalt» (danger), computed server-side (`due_status`, `days_until_due`).
- **Task card (2.4):** checkbox then row as two focus targets; checkbox label names action and task («Merk 'Vask bad' som fullført»); completed = filled checkbox, strikethrough, success note.
- **Remove Task (2.6):** inline confirmation «Oppgaven forsvinner fra lista for alle i hjemmet. Det som er gjort, blir stående.» with «Ja, fjern oppgaven» / «Avbryt»; then Task Overview with «Fjernet «X».» via `aria-live="polite"`. Tenants never see add/remove controls.
- **Accessibility:** visible 2px focus ring, tap targets ≥44×44px, reflow at 320px/400% zoom, focus order follows visual order, every control labelled with action and state, honour `prefers-reduced-motion`.

## Cross-Story Dependencies

- Build order: 2.3 → 2.4 → 2.5 → 2.6 (2.6 is stacked on the 2.4 branch while PR #44 is open). 2.3 extends 2.2's read-only Task Detail; 2.6 adds «Fjern oppgaven» to the same page and «Legg til oppgave» to Task Overview, reusing 2.3's Må/Bør and Frequency controls and the fixed Frequency list.
- 2.3's Frequency change must be what 2.5's reschedule reads (Frequency stored on the Task).
- 2.4 moves in the checkbox/focus-order AC from 2.2 and switches `tasks_of` to the earliest open instance; 2.5 extends `complete_task_instance`; Epic 4 calls it from photo upload.
- A later Landlord Home Admin surface (bulk Må/Bør, Frequency, Photo Evidence) reuses the same domain rules; the Portfolio tab moved to Story 6.1.
- Epics 3, 4 and 6 must read active Tasks and current Memberships only.
