---
title: "Sprint Change Proposal: one rule for creating Homes, and adding and removing Tasks"
date: 2026-11-09
status: approved
trigger: "Two team requests found during Story 2.1 (PR #29) on 2026-11-09: a Landlord cannot create their own Household Home (issue #30), and nobody can add or remove Tasks after Task Setup (issue #31)"
scope: moderate
rollback: none needed (plan change only; no code reverted)
---

# Sprint Change Proposal — 2026-11-09

## 1. Issue summary

**Trigger.** Two requests from Eirik on 2026-11-09, both found while checking Story 2.1 (PR #29):

- **Issue #30** (Vercel preview check): a Landlord can only create more Landlord Homes. They can get a Household Home only through someone else's invite, so a Landlord who lives alone or is the first in a kollektiv cannot create their own private Home. This is the Story 1.3 rule (`spec-1-3-create-a-home.md`: *"A Landlord may create more Landlord Homes only"*), enforced in `allowed_types` (`backend/app/domain/homes.py`). It is one half of Epic 1 retrospective finding **R1**: the creation rule (1.3) and the joining rule (1.4) were never reconciled, and the other half is that a Household Member or Tenant can never create a Landlord Home (`allowed_types` returns `[]`). R1 was accepted as built with "revisit together with action 8".
- **Issue #31** (catalog approval in PR #29): after Task Setup nobody can add a catalog task that was unticked, create a custom task (deferred in Story 2.1, decision 5, `deferred-work.md`) or remove a task. Only changing Må/Bør and Frequency is planned (Story 2.3).

**When.** Epic 1 is done (Stories 1.1–1.8). Story 2.1 is merged (PR #29), and the status update is merged (PR #32). Stories 2.2–2.5 have not started, so Task Overview, Task Detail and completion do not exist yet.

**Type.** New requirements from the team, not defects: both behaviours are deliberate rules of earlier stories.

**Evidence.** Issues #30 and #31; `allowed_types`/`join_blocker` in `backend/app/domain/homes.py`; Story 1.3 spec (Boundaries, matrix row "Landlord creates Household" → 409); Epic 1 retrospective R1 and Open question 1; Story 2.1 spec decision 5 and `deferred-work.md`.

**Found while analysing (not in the issues).**

1. `fr3_violations` is *not* affected by #30, although the issue lists it: FR-3 is checked per Home, and a Landlord who creates a Household Home is its `household_member`, so no Home mixes Roles.
2. `/` shows only the newest Home (`frontend/src/routes/HomePage.tsx`, `const [home] = homes.data.homes`). With #30 more users hold Homes of both kinds but see the tasks of one. This is the open UX gap `reconcile-prd.md` #3 (no Home switcher).
3. Removing a Task conflicts with AD-16 once Story 2.4 stores completions: history must be kept, so a removed Task must be archived, not deleted, and the unique `(home_id, task_type)` would then block adding the same catalog type again.
4. Plan drift from the previous correct-course: Story 1.8 and FR-23 are missing from the Delivery stages table and "Stage per FR" in `epics.md`, from the Trinn 1 comment in `sprint-status.yaml`, and from the architecture's `binds`/`scope`. Fixed in this change.

## 2. Scope decisions (Eirik, 2026-11-09)

1. **One rule for creating Homes (#30, closes R1).** Anyone may create any number of Landlord Homes. A Household Home may be created only by a user who is not already a Household Member or Tenant of another Home — the same one-Home limit as joining through an invite (Story 1.4).
2. **Home switching belongs to Story 2.2**, which rebuilds the Home page anyway: one Task Overview per Home (`/hjem/<id>`) and a «Dine hjem» list for every user with more than one Home.
3. **Removing a Task archives it** (`archived_at`); history stays, and the unique rules apply to active Tasks only, so a catalog type can be added again.
4. **Adding and removing Tasks becomes Story 2.6 in Trinn 1**, built after 2.5 (it needs Task Overview, Task Detail and completion history).
5. **The creation rule is delivered as Story 1.9 before Story 2.2**, with its own issue (#30), branch and PR.
6. **Custom Tasks** follow the issue's proposal: the same Roles as Task Setup (Household Member, Landlord; not Tenant); name 1–100 characters, unique among the Home's active Tasks (case-insensitive); Må/Bør and a Frequency from the fixed list required; never Photo Evidence (AD-6).
7. **Archiving every Task does not reopen Task Setup.** Setup still runs once per Home; `has_tasks` means "setup has run", and the Home shows a "No active Tasks" state with «Legg til oppgave».
8. **No restore action.** An archived catalog task is added again as a new Task; archiving is confirmed inline first.

## 3. Impact analysis

**Epics.**
- **Epic 1** gains Story 1.9 and goes back to `in-progress`; its retrospective stays `done`.
- **Epic 2** gains Story 2.6 and FR-24; Story 2.2 gains one acceptance criterion (Home switching); Story 2.1's note records the meaning of `has_tasks`.
- **Epics 3, 4 and 6:** covered by one cross-cutting rule (only active Tasks drive behaviour); no story text changes. Story 2.6 states that a custom Task can never require Photo Evidence (Story 4.1, AD-6).
- **Epic 5:** unaffected.
- No epic is removed, renumbered or resequenced. Stories: 25 + 2 = 27. Build order: 1.9 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6.

**Artifacts.**

| Artifact | Change |
|---|---|
| PRD | Revision note; FR-1 consequence and Open Question 3 note (creation rule); new FR-24 in §4.3; FR-24 in Trinn 1 (§6); SM-1 extended |
| Architecture | `binds`/`scope` gain FR-23 and FR-24; ER diagram `TASK_TYPE |o--o{ TASK`; revision note (`archived_at`, nullable `task_type`, partial unique indexes, active-only reads, `has_tasks`); AD-6 sentence on custom Tasks; Capability map rows |
| UX (EXPERIENCE.md) | Foundation note; IA rows Create Home and Task Detail revised, new row Add Task; Component Pattern "Remove Task confirmation"; State Patterns "No active Tasks" and "Task removed" |
| UX (reconcile-prd.md) | #2, #3 and #9 resolved |
| Epics | New Stories 1.9 and 2.6; dated notes on Story 1.3, the Epic 1 note and Story 2.1; one AC in Story 2.2; Additional Requirements rule "Active vs archived Tasks"; FR inventory, coverage map, Stage per FR, Delivery stages and Epic List |
| Sprint status | `1-9-…` and `2-6-…` as `backlog`; `epic-1: in-progress`; build-order comment |
| Traces | Retrospective R1 and Open question 1 annotated; `deferred-work.md` custom-task entry gains an outcome; comments on issues #30 and #31; CLAUDE.md status |

**Technical.**
- *Story 1.9:* no migration. `allowed_types` and `join_blocker` share one statement of the one-Home limit in `domain/homes`; 409 messages and the Create Home copy change; the Story 1.3/1.4 tests change (matrix row "Landlord creates Household" → 201). `fr3_violations`, CI and the seed are unchanged.
- *Story 2.6:* one migration (`tasks.archived_at`, nullable `task_type`, partial unique indexes on `(home_id, task_type)` and `(home_id, lower(name))` where `archived_at IS NULL`; both Postgres and SQLite support them); add and archive routes behind `require_role` (the route walk covers them); `tasks_of` and later readers filter active Tasks.
- No change to hosting or the local Docker setup.

## 4. Recommended approach

**Direct adjustment.** Two new stories plus small additions. No rollback: nothing built conflicts, and Story 1.9 changes one domain rule. No MVP review: both stories fit Trinn 1, though Trinn 1 grows by two stories before the mid-December deadline; if time runs short, Story 2.6 is the natural candidate to move to Trinn 2. Effort is low (1.9) to medium (2.6); risk is low, because the permission layer, the FR-3 check and the history rule (AD-16) already exist, and the data model from Story 2.1 was built to allow custom Tasks.

## 5. Detailed change proposals

All eight were approved one by one on 2026-11-09 (incremental mode).

### 5.1 PRD (`prds/prd-prosjektoppgave-ibe160-2026-09-29/prd.md`)

a) Revision note after the 2026-11-01 note (frontmatter `updated: 2026-11-09`):

> **Revision 2026-11-09:** Two team requests found during Story 2.1 (issues #30, #31; see `sprint-change-proposal-2026-11-09.md`): one rule for creating Homes replaces the Story 1.3 rule (FR-1, Open Question 3), and a new FR-24 lets Household Members and Landlords add and archive Tasks after Task Setup.

b) FR-1, new last consequence:

> - `[REVISED 2026-11-09]` A user may create any number of Landlord Homes, and a Household Home only while they are not a Household Member or Tenant of another Home — the same one-Home limit as joining through an invite (Story 1.4). A Landlord can therefore create their own Household Home, and a Household Member or Tenant can create a Landlord Home.

c) Open Question 3, appended (existing text kept):

> `[REVISED 2026-11-09]` The creation rule now matches the joining rule (FR-1): anyone may create Landlord Homes, and a Household Home only without another Household Member or Tenant Membership. This closes R1 (issue #30, Story 1.9).

d) New FR-24 in §4.3, after FR-8:

> #### FR-24: Add and archive Tasks `[ADDED 2026-11-09 — Sprint Change Proposal 2026-11-09]`
> After Task Setup, a Household Member or Landlord can add a Task — a catalog task type the Home does not currently have, or a custom Task with its own name — and archive a Task the Home no longer needs. Tenants cannot. Realizes UJ-1, UJ-2, UJ-4.
>
> **Consequences (testable):**
> - A custom Task has a name (unique among the Home's active Tasks), a Must/Should classification and a Frequency chosen by the user (FR-4, FR-8). It can never require Photo Evidence (FR-18, Privacy Constraints).
> - An archived Task disappears from Task Overview, notifications, fairness and the Portfolio. Its history (completions, Photo Evidence) is kept. A catalog task type can be added again as a new Task.
> - Archiving asks for confirmation first. Archiving every Task does not reopen Task Setup, which still runs once per Home.
> - A Tenant's attempt to add or archive a Task is rejected server-side.

e) §6 Trinn 1: "Frequency recommendation, adjustment, and auto-rescheduling — FR-8, FR-9" gains ", and adding/archiving Tasks — FR-24 (added 2026-11-09)".

f) SM-1: "… (403). A Tenant also cannot add or archive Tasks (FR-24). Validates FR-3, FR-5, FR-8, FR-24."

### 5.2 Architecture (`architecture/architecture-prosjektoppgave-ibe160-2026-10-04/ARCHITECTURE-SPINE.md`)

a) Frontmatter: `updated: '2026-11-09'`; `scope` and `binds` gain FR-23 (missed on 2026-11-08) and FR-24.

b) ER diagram: `TASK_TYPE ||--o{ TASK : categorizes` → `TASK_TYPE |o--o{ TASK : categorizes`.

c) New revision note after the 2026-11-09 note under Core entities:

> `[REVISED 2026-11-09 — Sprint Change Proposal 2026-11-09]` — FR-24 (Story 2.6): a `TASK` gains a nullable `archived_at` (UTC). `task_type` becomes nullable: a custom Task has no catalog key and keeps its own name, classification and Frequency. The unique `(home_id, task_type)` and a new unique `(home_id, lower(name))` apply to active Tasks only, as partial unique indexes `WHERE archived_at IS NULL`, so a catalog task type or a name can be added again after archiving. Archiving never deletes: an archived Task and its instances, completions and Photo Evidence stay, as AD-16 keeps history. Every read that drives behaviour — Task Overview, the due-check (AD-8), fairness (AD-9), Photo Evidence requirements (AD-6) and the Portfolio (FR-20) — reads active Tasks only. `HomeOut.has_tasks` keeps meaning "Task Setup has run" (any Task, archived or not), so archiving every Task does not reopen setup.

d) AD-6, Rule, new last sentence:

> A custom Task (no catalog key, FR-24) is never eligible. Eligibility is read from the catalog by key, so a Task without a key has none. `[ADDED 2026-11-09]`

e) Capability map: "Frequency & Scheduling (FR-8–9)" → "Frequency & Scheduling (FR-8–9), add/archive Tasks (FR-24)", governed by AD-3, AD-2, AD-6; "Homes & Membership (FR-1–3)" → "(FR-1–3, FR-23)", governed by AD-1, AD-2, AD-16.

The creation rule (#30) needs no AD: AD-1 already allows one User different Roles in different Homes.

### 5.3 UX (`ux-designs/ux-prosjektoppgave-ibe160-2026-09-29/`)

Frontmatter of EXPERIENCE.md: `updated: 2026-11-09`.

a) Foundation note (OQ3), appended:

> `[REVISED 2026-11-09 — Sprint Change Proposal]` Any user may now hold Homes of both kinds (PRD FR-1). Story 2.2 gives every user with more than one Home a «Dine hjem» list and one Task Overview per Home (`/hjem/<id>`). Before Story 2.2, `/` still shows the newest Home.

b) IA row "Create Home", appended:

> `[REVISED 2026-11-09]` Reached from «Opprett nytt hjem» on the Home page by anyone who may still create a Home. Every type the user may create is offered (`allowed_types`): Landlord Home always, Household Home only without another Household Member or Tenant Membership (PRD FR-1, Story 1.9).

c) New IA row after Task Detail:

> | Add Task | Task Overview «Legg til oppgave» | Household Member, Landlord | `[ADDED 2026-11-09]` Add a catalog task type the Home does not have (same row as Task Setup: Må/Bør, Frequency) or a custom Task (name, Må/Bør, Frequency). One Task per save. Lands back on Task Overview with the new Task shown (PRD FR-24). Tenants see no «Legg til oppgave». |

d) IA row "Task Detail", appended:

> `[REVISED 2026-11-09]` Household Members and the Landlord also get «Fjern oppgaven» (archive, PRD FR-24), confirmed inline. Tenants never see it.

e) New Component Pattern:

> | Remove Task confirmation | Task Detail | `[ADDED 2026-11-09]` Same inline pattern as Leave / remove confirmation: «Fjern oppgaven» turns into «Oppgaven forsvinner fra lista for alle i hjemmet. Det som er gjort, blir stående.» with «Ja, fjern oppgaven» and «Avbryt». Danger colour only on the confirming button. |

f) New State Patterns:

> | No active Tasks | Task Overview | `[ADDED 2026-11-09]` Setup has run but every Task is archived: «Ingen oppgaver i hjemmet ennå.» with «Legg til oppgave» for Household Members and the Landlord, and «Utleier har ikke satt opp oppgaver ennå.» for a Tenant. Distinct from Empty task list (nothing due). Task Setup is not shown again. |
> | Task removed | Task Detail → Task Overview | `[ADDED 2026-11-09]` After archiving, the user lands on Task Overview with «Fjernet «X».» announced via `aria-live="polite"`. |

g) `reconcile-prd.md`: #2 `[RESOLVED 2026-11-09]` → Task Setup (Story 2.1) and Add Task (PRD FR-24, Story 2.6); #3 `[RESOLVED 2026-11-09]` → «Dine hjem» and one Task Overview per Home in Story 2.2; #9 `[RESOLVED 2026-11-09]` → PRD Open Question 3 and FR-1.

### 5.4 Epics — new Story 1.9 (`epics.md`, after Story 1.8)

> ### Story 1.9: One Rule for Creating Homes
>
> **Stage:** Trinn 1 · **Source:** issue #30, Epic 1 retrospective (R1), Sprint Change Proposal 2026-11-09 · **FR:** FR-1, FR-3 · **AD:** AD-1, AD-3
>
> As a user who already belongs to a Home,
> I want to create the other kind of Home when my situation calls for it,
> So that a Landlord can have a private Household Home and a Household Member or Tenant can start renting out a unit, without needing an invite.
>
> **Acceptance Criteria:**
>
> **Given** a Landlord with no Household Member or Tenant Membership
> **When** they open Create Home
> **Then** both Household Home and Landlord Home are offered, and choosing Household Home makes them its Household Member (FR-1)
>
> **Given** a Household Member or Tenant
> **When** they open Create Home
> **Then** only Landlord Home is offered, and creating one makes them its Landlord while their existing Membership is unchanged
>
> **Given** a user who is already a Household Member or Tenant somewhere
> **When** they call `POST /api/homes` with `type: household` directly
> **Then** the server answers 409 with «Du er allerede med i «X». Du kan bare være med i ett hjem om gangen.», the same as joining (Story 1.4), and nothing is written
>
> **Given** the creation rule and the joining rule
> **When** their source is inspected
> **Then** both read one domain statement of the one-Home limit in `domain/homes` (`allowed_types` and `join_blocker` share it), so they cannot drift apart again (AD-3)
>
> **Given** any user who may still create a Home
> **When** the Home page renders
> **Then** «Opprett nytt hjem» is shown, and after creating, the user goes on to Task Setup (Story 2.1)
>
> **Given** any created Home
> **When** `fr3_violations` runs in the tests and CI
> **Then** it is still empty: a Home never mixes Household Members with a Landlord or Tenants
>
> **Given** the Story 1.3 and 1.4 test matrices
> **When** this story is delivered
> **Then** the row «Landlord creates Household» expects 201, a new row covers a Household Member creating a Landlord Home, and the README describes the rule where it explains creating a Home

Story 1.3 gains, below its ACs:

> *Revised 2026-11-09 (Sprint Change Proposal, Story 1.9):* the AC "a Household Member/Tenant is not re-prompted to create another Home" and the rule "a Landlord may create more Landlord Homes only" are replaced by one rule: Landlord Homes always, Household Home only without another Household Member or Tenant Membership.

The Epic 1 note "Update 2026-11-07" gains the same note in one sentence.

### 5.5 Epics — new Story 2.6 (`epics.md`, after Story 2.5)

> ### Story 2.6: Add and Remove Tasks
>
> **Stage:** Trinn 1 · **Source:** issue #31, Sprint Change Proposal 2026-11-09 · **FR:** FR-24, FR-4, FR-8 · **AD:** AD-2, AD-3, AD-6, AD-16 · **Builds on:** 2.2 (Task Overview), 2.3 (Task Detail), 2.4 (completion history)
>
> As a Household Member or Landlord,
> I want to add tasks my Home needs and remove the ones it no longer needs,
> So that the task list keeps matching my Home after the first setup.
>
> **Acceptance Criteria:**
>
> **Given** a Household Member or Landlord on Task Overview
> **When** they choose «Legg til oppgave»
> **Then** Add Task offers the catalog task types the Home has no active Task for, each with its recommended Må/Bør and Frequency to adjust, and a custom Task with name, Må/Bør and Frequency (FR-24)
>
> **Given** a catalog task type or a custom Task is saved
> **When** the user lands back on Task Overview
> **Then** the new Task is listed in Must-first order with its first instance due on today + Frequency, like Task Setup (Story 2.1)
>
> **Given** a custom Task
> **When** it is saved
> **Then** it must have a name of 1–100 characters (trimmed) that no other active Task in the Home has (case-insensitive), a Må/Bør classification and a Frequency from the fixed list, or the server answers 422 with a Norwegian message shown at the field (FR-4, FR-8)
>
> **Given** a custom Task
> **When** a Landlord later tries to require Photo Evidence on it (Story 4.1)
> **Then** the server rejects it, since only catalog types flagged `photo_evidence_eligible` qualify (AD-6)
>
> **Given** a Household Member or Landlord on Task Detail
> **When** they choose «Fjern oppgaven» and confirm inline
> **Then** the Task is archived: it disappears from Task Overview for every Member, its instances and completions stay, and the user lands on Task Overview with «Fjernet «X».» (UX: Remove Task confirmation, Task removed)
>
> **Given** a catalog task type whose Task was archived
> **When** it is added again
> **Then** it becomes a new Task with a new first due date; the archived Task and its history are unchanged
>
> **Given** a repeated archive of the same Task (double tap, second tab)
> **When** the request arrives
> **Then** nothing changes and the user is not shown an error
>
> **Given** a Home whose every Task is archived
> **When** a Member opens Task Overview
> **Then** it shows the No active Tasks state, and Task Setup is not offered again (`has_tasks` means setup has run)
>
> **Given** a Tenant
> **When** they view Task Overview or Task Detail, or call the add or archive routes directly
> **Then** they see neither «Legg til oppgave» nor «Fjern oppgaven», and the server answers 403 (AD-2; the route walk in `test_permissions.py` covers the new routes)
>
> **Given** adding or archiving fails server-side
> **When** the user sees the result
> **Then** an inline error with a retry affordance shows at the action (UX-DR30)
>
> **Given** this story is delivered
> **When** the README is read
> **Then** it describes how to add a custom Task and remove a Task, and `deferred-work.md`'s custom-task entry has its outcome

### 5.6 Epics — other changes (`epics.md`)

a) Story 2.2, new AC (*Added 2026-11-09 (Sprint Change Proposal)*):

> **Given** a user with more than one Home (for example a Landlord with their own Household Home, Story 1.9)
> **When** they use the app
> **Then** each Home has its own Task Overview at `/hjem/<id>`, a «Dine hjem» list lets them switch between their Homes, and `/` opens the most recently used Home. The Portfolio tab (Landlord with ≥2 Landlord Homes) is unchanged.

b) Additional Requirements, new item after "Current vs past Members":

> - **Active vs archived Tasks (FR-24, added 2026-11-09):** an archived Task is never deleted, and every read that drives behaviour — Task Overview, the due-check and fairness (Epic 3), Photo Evidence requirements (Epic 4) and the Portfolio (Epic 6) — reads active Tasks only. History on an archived Task (completions, Photo Evidence) stays reachable where that history is shown. `has_tasks` means Task Setup has run.

c) Inventory and coverage: new FR-24 line under Functional Requirements; FR-1 line gains "(creation rule revised 2026-11-09, Story 1.9)"; FR Coverage Map gains "FR-24: Epic 2 (Story 2.6 — add and remove Tasks; added 2026-11-09)" and FR-1 "+ Story 1.9"; "Stage per FR" Trinn 1 gains FR-23 (missed on 2026-11-08) and FR-24.

d) Delivery stages: Trinn 1 becomes `1.1–1.9, 2.1–2.6, 5.1` (1.8 was missing); the Overview gains "*Revision 2026-11-09:* Story 1.9 (creation rule, issue #30) and Story 2.6 (add and remove Tasks, issue #31) added; 27 stories."

e) Epic List: Epic 2 gains FR-24 under "FRs covered" and "… and add or remove Tasks after setup (Story 2.6)."

f) Story 2.1, appended to the 2026-11-09 note:

> *Sprint Change Proposal 2026-11-09:* custom Tasks (decision 5) are planned in Story 2.6, and `has_tasks` keeps meaning "Task Setup has run" once Tasks can be archived.

### 5.7 Sprint status (`implementation-artifacts/sprint-status.yaml`)

- Add `1-9-one-rule-for-creating-homes: backlog` after 1-8 and `2-6-add-and-remove-tasks: backlog` after 2-5.
- `epic-1: done` → `in-progress`; `epic-1-retrospective` stays `done`.
- Build-order comment: Trinn 1 becomes "1-1 til 1-9, 2-1 til 2-6, 5-1" (1-8 was missing); new line "1-9 (én regel for å opprette hjem, issue #30) kommer før 2-2; 2-6 (legge til og fjerne oppgaver, issue #31) kommer etter 2-5 (correct-course 2026-11-09)."
- `last_updated` updated; verified with `sprint_status.py detect-epic --epic 1` and `--epic 2`. No action items change.

### 5.8 Traces

- `epic-1-retro-2026-11-08.md`: row R1 and Open question 1 gain "*Resolved 2026-11-09: Sprint Change Proposal 2026-11-09 → one rule for creating Homes, Story 1.9.*"; original text kept.
- `deferred-work.md`: the custom-task entry (Story 2.1, decision 5) gains `outcome: Planned 2026-11-09 (Sprint Change Proposal 2026-11-09) as Story 2.6, with archiving (FR-24).`
- Issues #30 and #31: a comment linking this proposal and the story. #30 is closed by Story 1.9's PR (`Closes #30`); #31 stays open until Story 2.6 is built.
- CLAUDE.md status: next is Story 1.9, then Story 2.2.

## 6. Implementation handoff

**Scope: moderate** — backlog change (two new stories, additions to Stories 1.3, 2.1 and 2.2, one cross-cutting rule), no replan.

- **Planning edits (this change, Developer/PO):** apply 5.1–5.8 on branch `change/create-rule-and-custom-tasks`, one commit per artifact, open a PR that links this proposal.
- **Story 1.9 (Developer):** next story after this PR merges, through `bmad-build`, with issue #30, branch `story/1-9-create-rule` and its own PR, before Story 2.2.
- **Story 2.2 (Developer):** carries the new Home-switching AC.
- **Story 2.6 (Developer):** after Story 2.5, through `bmad-build`; the "Active vs archived Tasks" rule is in the epic context `bmad-build` compiles.

**Success criteria.** After this PR: PRD, architecture, UX, epics and sprint status agree on FR-1, FR-24, Story 1.9 and Story 2.6, and `detect-epic` lists `1-9-…` and `2-6-…` as pending. After Story 1.9: a Landlord can create their own Household Home, a Household Member or Tenant can create a Landlord Home, and `fr3_violations` stays empty. After Story 2.6: a custom Task can be added and a Task removed without losing its history.
