# Epic 2 Context: Task Management Core Loop

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Give every Member of a Home (Household Member, Tenant, Landlord) the core loop of Husly: a Must-first task list per Home, inline adjustment of Must/Should and Frequency for Household Members and Landlords (locked for Tenants), one-tap self-checkoff with shared status and per-member attribution, automatic rescheduling counted from the actual completion date, and adding or archiving Tasks after the first setup. It starts with Task Setup at Home creation (done) and owns the single completion domain function that Photo Evidence (Epic 4) later extends. All of Epic 2 is Trinn 1 and must run locally without team accounts.

## Stories

- Story 2.1: Task Setup at Home Creation (done)
- Story 2.2: Must-First Task Overview (includes tab bar, Home switching, logo link)
- Story 2.3: Adjust Task Classification & Frequency
- Story 2.4: Self-Checkoff Completion with Shared Status & Attribution
- Story 2.5: Auto-Reschedule on Completion
- Story 2.6: Add and Remove Tasks (built after 2.5)

## Requirements & Constraints

- **Must-first ordering:** all Must tasks render above all Should tasks regardless of due date; within a tier, order by due date. Keyboard/screen-reader focus order matches this visual order.
- **Classification and Frequency:** the app recommends Must/Should and Frequency per task type. Household Members and Landlords may change both; Tenants may not, and the rejection must happen server-side (403), not only in the UI. Frequency is picked from fixed intervals: 7, 14, 30, 42, 60, 90, 182, 365 days.
- **Completion:** any Member completes a task instance in one action, no confirmation. Status is shared for the whole Home; the completing Member is recorded and queryable per Home over time. A one-person Home never sees copy that implies a second person ("Fullført i dag", not "Fullført av deg").
- **Reschedule:** next instance is due N days after the actual completion date, never shortened for lateness. Retried completion returns the existing state unchanged (no re-attribution, no second reschedule).
- **Add/archive Tasks (Household Member, Landlord only):** catalog types the Home has no active Task for, or a custom Task (name 1–100 chars trimmed, unique among active Tasks case-insensitively, Må/Bør and Frequency required; 422 with Norwegian message otherwise). First instance due today + Frequency. Archiving is idempotent and never deletes; a catalog type can be added again as a new Task. Custom Tasks can never require Photo Evidence.
- **Active vs archived Tasks:** every behaviour-driving read (Task Overview, later due-check, fairness, Photo Evidence requirements, Portfolio) reads active Tasks only; history on archived Tasks stays reachable. `has_tasks` means "Task Setup has run" — archiving everything never reopens setup.
- **Current vs past Members:** only current Memberships count; completions by someone who has left are kept and shown as «Tidligere medlem».
- **Out of scope:** personal-space tasks (own room); gamification of any kind (no points, streaks, leaderboards); never frame a missed task as failure or shame anyone.
- **Runnable without accounts:** seed data must keep giving a reviewer a populated Task Overview (some tasks due soon/overdue); README and `.env.example` updated in the same PR as changes that need it.

## Technical Decisions

- **Layering:** routes never mutate data directly; all mutations go through domain services in `backend/app/domain`. Shared route dependencies (`SessionDep`, `ErrorOut`, role aliases) live in `backend/app/routes/deps.py`.
- **Permissions:** role lives on the Membership, resolved per request by `require_role(*roles)`, with `home_id` read from the path only. `tests/test_permissions.py` walks every route and fails if a `{home_id}` route lacks `require_role` (or vice versa) — every new Home-scoped route must sit under `/api/homes/{home_id}/...`.
- **Single completion path:** one domain function, `complete_task_instance`, marks an instance complete, records attribution and triggers the reschedule. The checkbox endpoint (and later the photo-upload endpoint) only call it; it is idempotent.
- **Data model:** Task type catalog is a versioned Python module (`backend/app/domain/task_types.py`), not a table; a Task stores the catalog key and copies name, classification and Frequency. A TaskInstance has a UTC calendar `due_on` and unique `(task_id, due_on)`. Completion attribution references the User, not the Membership. Story 2.6 adds nullable `archived_at`, nullable `task_type`, and partial unique indexes on `(home_id, task_type)` and `(home_id, lower(name))` `WHERE archived_at IS NULL` (works on Postgres and SQLite).
- **Next due date:** today `tasks_of` uses the earliest instance; Story 2.4 must change it to the earliest *open* (not completed) instance.
- **Frontend data:** no direct `fetch` or server data in `useState`; all reads/writes through TanStack Query hooks over the generated OpenAPI client. Self-checkoff uses an optimistic update with quiet retry/rollback. No real-time layer: freshness comes from refetch on mount/window focus (and pull-to-refresh on Task Overview).
- **Errors:** shared `ApiError` in `frontend/src/api/errors.ts`; backend uses `{"detail": "..."}` and standard 422 bodies. A global 403 handler in `createQueryClient` refetches Homes and members when access disappears — new Home-scoped queries must behave correctly under it.
- **Time:** use `app/clock.py` (`UtcDatetime`) for "now"/"today"; wire format is ISO 8601 UTC. Test helpers live in `backend/tests/helpers.py`.
- **Schema:** every change is an Alembic migration. Never run `alembic downgrade` against the local `husly` database — use a throwaway database.
- **Styling:** only `var(--...)` design tokens in components; no literal hex, px sizes or radii.
- **Known accepted risk:** pytest runs on SQLite, so row locks (e.g. in `set_up_tasks`) are reasoned, not tested.

## UX & Interaction Patterns

- **Task Overview** is the primary landing surface, single-column at every width. States: cold load = 3–4 skeleton rows (distinct from empty); empty (nothing due) = «Ingen oppgaver akkurat nå — nyt det! 🎉» (household) or «Ingen aktive oppgaver i dette hjemmet.» (landlord view); No active Tasks (all archived, Story 2.6) = «Ingen oppgaver i hjemmet ennå.» with «Legg til oppgave», or «Utleier har ikke satt opp oppgaver ennå.» for a Tenant.
- **Task card:** checkbox + title + inline Must/Should badge + due date. Checkbox and row are two separate focus/tap targets, checkbox first; row → Task Detail, checkbox → self-checkoff. Checkbox label names action and task («Merk 'Vask bad' som fullført»). Completed: filled checkbox, strikethrough, success-coloured note («Fullført i dag» / «Fullført av Peter»).
- **Due states never colour-only:** due soon = warning colour, bold, «Snart forfall»; overdue = danger colour, «Forfalt» (deliberately different from the Must badge text).
- **Navigation:** tab bar with Task Overview and Settings/Profile, plus Portfolio for a Landlord with ≥2 Landlord Homes. Each Home has its own Task Overview at `/hjem/<id>`; a «Dine hjem» list switches between Homes; `/` opens the most recently used Home. The «Husly» wordmark in the header is a real link to `/`. Members & Invite moves to the Task Overview header.
- **Task Detail (2.3):** Household Members/Landlords edit Must/Should and Frequency inline. Tenants see a locked toggle: dashed border, lock glyph, «Satt av utleier», `aria-readonly="true"` + `aria-describedby`, never native `disabled`. Save failures show inline error with retry.
- **Remove Task (2.6):** inline confirmation «Oppgaven forsvinner fra lista for alle i hjemmet. Det som er gjort, blir stående.» with «Ja, fjern oppgaven» / «Avbryt» (danger colour only on confirm); afterwards land on Task Overview with «Fjernet «X».» via `aria-live="polite"`.
- **Accessibility/platform:** visible 2px focus ring everywhere, tap targets ≥44×44px, reflow at 320px/400% zoom, honour `prefers-reduced-motion` for skeletons/transitions, Norwegian-only copy, pull-to-refresh on Task Overview.

## Cross-Story Dependencies

- Build order: 2.2 → 2.3 → 2.4 → 2.5 → 2.6. Story 2.2 replaces the minimal `/` list from 2.1 and introduces `/hjem/<id>`, which 2.3 (Task Detail), 2.4 (checkbox) and 2.6 (Legg til oppgave) build on.
- 2.2's card row links to Task Detail, which 2.3 builds; 2.2's checkbox target becomes functional in 2.4.
- 2.4 must switch `tasks_of` to earliest open instance; 2.5 extends the same `complete_task_instance` function; Epic 4 later calls it from photo upload.
- 2.6 depends on 2.2 (Overview), 2.3 (Detail) and 2.4 (completion history); Epics 3, 4 and 6 must read active Tasks only.
- Seed data (Mari, Jonas, Kari, Anders; example Household Home and «Storgata 12») set up as of 28/40 days ago should keep showing due-soon and overdue tasks.
