# Epic 2 Context: Task Management Core Loop

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Give every Home a living task list and close the core loop of the product. When a Home is created, the user reviews a recommended set of irregular household tasks (each with a Must/Should classification and a Frequency) and accepts or adjusts it. Members then see a Must-first Task Overview, Household Members and Landlords adjust classification and Frequency while Tenants see them locked, any Member checks a task off in one tap with shared status and per-member attribution, and the next occurrence is scheduled from the actual completion date. This is what makes Husly more than an account system: forgotten irregular tasks (mold, drains, filters) get scheduled without anyone inventing a reminder. The whole epic is Trinn 1 and builds on Epic 1's Homes, Memberships and `require_role`. Its single completion function is extended by Epic 4 (Photo Evidence) later.

## Stories

- Story 2.1: Task Setup at Home Creation
- Story 2.2: Must-First Task Overview
- Story 2.3: Adjust Task Classification & Frequency
- Story 2.4: Self-Checkoff Completion with Shared Status & Attribution
- Story 2.5: Auto-Reschedule on Completion

## Requirements & Constraints

- **Recommended classification:** every Task gets a Must or Should classification at creation, from its task type (mold or damage risk defaults to Must) or an explicit override. A Task is never unclassified.
- **Recommended Frequency:** every recurring Task has a Frequency (in days) at creation, app-recommended or overridden. Household Members and Landlords may approve or adjust it.
- **Permission tiers:** Household Members and Landlords may change classification and Frequency. Tenants never can: a direct API attempt is rejected with 403, not just hidden in the UI. This Landlord-sets/Tenant-inherits hierarchy is the product's core differentiator.
- **Landlord Homes with zero Tenants** must be fully configurable (tasks created and ready before anyone joins).
- **Must-first ordering:** all Must tasks render above any Should task regardless of due date; within a tier, order by due date.
- **Shared completion:** one Task instance has one shared status. Any Member completing it resolves it for the whole Home, with no confirmation from anyone else. Each completion stores who did it, queryable per Home over time (the basis for the fairness rule in Epic 3).
- **Reschedule:** completing a Task instance with Frequency N schedules the next one N days after the actual completion date, also when completed late (2 days late on 30 days still gives a full 30 days).
- **Former Members:** only current Memberships count for access and overviews. A completion by someone who has since left stays and is shown as «Tidligere medlem».
- **Out of scope:** personal-space tasks (a Member's own room) are never tracked. No gamification (points, streaks, leaderboards).
- **Runnable for a reviewer:** the seed must give a populated Task Overview straight after seeding, with no team accounts or keys. Tests run offline.
- **Success checks:** a Tenant's change to classification or Frequency gets 403; reschedule N days from the completion date holds also when late; every new task has a classification and the list is always Must-first.

## Technical Decisions

- **Entities (glossary names, verbatim):** `Task` (belongs to a Home, references one `TaskType`, holds classification and Frequency), `TaskInstance` (one dated occurrence, completed independently of past and future ones), `MemberCompletion` (attribution). Attribution references the **User**, never the Membership, so history survives a Member leaving.
- **TaskType catalog:** a versioned, system-seeded catalog in the repository, never hardcoded in a component or route. One entry per type: name, default classification, recommended Frequency in days, and `photo_evidence_eligible` (not Landlord-editable; enforced in Epic 4). Initial catalog: at least 8 types covering both classifications, at least 2 photo-eligible. The starter table in Story 2.1 is a proposal the team confirms in the PR.
- **One completion path:** a single domain function `complete_task_instance` is the only code that marks an instance complete, records attribution and triggers the reschedule. The checkbox endpoint calls it now, and the photo-upload endpoint will call it in Epic 4. It is idempotent: a retried call on a completed instance returns the existing state without re-attributing or rescheduling.
- **Layering and permissions:** routes stay thin. Every mutation goes through `backend/app/domain`. Every Home-scoped route has `{home_id}` in the path and uses `require_role(*roles)`. `tests/test_permissions.py` fails otherwise. The role check is per request against the Membership row, never a JWT claim.
- **Frontend data:** all server reads and writes go through TanStack Query hooks on the generated OpenAPI client (`openapi-typescript`), with no direct `fetch` and no server data in `useState`. Errors go through the shared `ApiError`. Self-checkoff is an optimistic mutation with quiet retry/rollback. Freshness comes from refetch on mount and window focus, with no WebSocket/SSE.
- **Dates and data:** UUIDv4 ids. ISO 8601 UTC on the wire, using `app/clock.py` (`UtcDatetime`) for aware datetimes. Errors use FastAPI's `{"detail": ...}`. Every schema change is an Alembic migration. Test `alembic downgrade` against a temporary database, never the local `husly` database.
- **Seed:** extend the ordered seed steps (`uv run python -m app.seed`). They must be idempotent and look up earlier rows by natural key. The seed refuses any non-local database.
- **Pending refactor:** route modules import shared schemas and `SessionDep` from each other. The Epic 1 retro deferred a shared schemas module to "when Epic 2 adds routes".
- **Accepted risk:** row locks are reasoned but not tested on Postgres, because pytest runs on SQLite.

## UX & Interaction Patterns

- **Task Setup** follows Create Home for both Home types: review the recommended list, adjust classification or Frequency, confirm, and land on Task Overview.
- **Task Overview** is the primary landing surface and stays single-column at every width.
  - 3–4 skeleton rows during cold load, distinct from the Empty state («Ingen oppgaver akkurat nå — nyt det! 🎉»).
  - Pull-to-refresh.
  - Focus order matches the visual order (Must before Should).
- **Tab bar** (Story 2.2): Task Overview and Settings/Profile, plus Portfolio for a Landlord with 2 or more Homes. It replaces the placeholder Home page. Members & Invite moves to the Task Overview header.
- **Task card:**
  - The checkbox and the row are two separate focus/tap targets, checkbox first. The checkbox completes the task and the row opens Task Detail.
  - The Must/Should badge always shows the text label, with colour as reinforcement only.
  - Due soon: warning colour, bold, «Snart forfall». Overdue: danger colour, «Forfalt».
  - Completed: filled checkbox, struck-through title, success note («Fullført i dag» / «Fullført av Peter»). A one-person Home never references a second person.
  - Checkbox label, for example «Merk 'Vask bad' som fullført».
- **Frequency/Must toggle on Task Detail:**
  - Editable inline for Household Members and Landlords.
  - Locked for Tenants: dashed border, lock glyph, «Satt av utleier», `aria-readonly="true"` plus `aria-describedby`, never native `disabled`.
  - A failed save shows an inline error with retry at the field.
- **Offline checkbox tap:** apply the update optimistically and retry quietly, with no blocking modal.
- **General:** tap targets of at least 44px, visible focus ring, token-only styling (`var(--…)`, `must-badge`/`should-badge` tokens), Norwegian-only copy, and a warm household register that never shames a missed task.

## Cross-Story Dependencies

- **2.1 → 2.2:** 2.1 must redirect to Task Overview, which 2.2 builds. Story 2.1 needs at least a minimal Overview route, or the redirect target has to be agreed.
- **2.2 → 2.3:** a row tap in 2.2 opens Task Detail, and 2.3 edits on it. No story explicitly owns building the Task Detail screen itself.
- **2.4 + 2.5:** both share `complete_task_instance` and `MemberCompletion`. Epic 4 (4.2) reuses it unchanged, and Epic 3 (due-check, fairness rule) reads TaskInstance due dates and attribution.
- **2.1 → Epic 4:** the `photo_evidence_eligible` flag must exist in the 2.1 catalog, although AD-6 is tagged Trinn 2.
- **2.1 → seed:** 2.1 extends the existing seed steps (Mari/Jonas household Home, Kari/Anders landlord Home).
- **Epic 5:** the «?» quick-answer (5.1, Trinn 1) attaches to Task Detail.
- **Landlord Home Admin:** bulk editing is Trinn 2, and no story owns it yet.
