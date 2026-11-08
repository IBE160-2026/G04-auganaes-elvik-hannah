---
title: "Sprint Change Proposal: leave a Home and Landlord removes a Tenant"
date: 2026-11-08
status: approved
trigger: "Epic 1 retrospective (finding R2, action 8): a Household Member or Tenant who accepts the wrong invite is locked into that Home for good; Eirik decided on 2026-11-08 that Members must be able to leave and a Landlord must be able to remove Members"
scope: moderate
rollback: none needed (plan change only; no code reverted)
---

# Sprint Change Proposal — 2026-11-08

## 1. Issue summary

**Trigger.** The Epic 1 retrospective (`_bmad-output/implementation-artifacts/epic-1-retro-2026-11-08.md`, finding R2) found that nobody can leave a Home and nobody can be removed. Because a Household Member or Tenant may belong to only one Home (Story 1.4, team decision 3), a user who accepts the wrong invite link is locked into that Home for good: `join_blocker` refuses every later invite and `allowed_types` returns `[]` (`backend/app/domain/homes.py`). Demo and test accounts can only be fixed in the database. Eirik decided on 2026-11-08 that Members must be able to leave a Home and a Landlord must be able to remove Members (retrospective, Open questions 5; action 8).

**When.** Epic 1 is complete (Stories 1.1–1.7, PR #4–#20) and its retrospective actions 1–4, 7 and 9 are merged (PR #22). Epic 2 has not started. This is the cheapest moment: only Homes and Memberships exist, and nothing in Epics 2–6 references Members yet.

**Type.** New requirement from the team. It was already flagged in September as a gap (`ux-designs/…/reconcile-prd.md` #5) and excluded explicitly in Story 1.5 ("Never: no removing Members").

**Evidence.** Retrospective finding R2 with its sources; `join_blocker` and `allowed_types` in `backend/app/domain/homes.py`; Story 1.5 spec, Never section; UX `reconcile-prd.md` #5.

## 2. Scope decisions (Eirik, 2026-11-08)

1. A Household Member cannot remove another Household Member; Household Members and Tenants can only leave themselves (1A).
2. A Landlord cannot leave their own Landlord Home; a Landlord Home keeps exactly one Landlord (FR-3) (2A).
3. When the last Household Member leaves, the Household Home remains without Members; nothing is deleted (3A).
4. Leaving or removal deletes the Membership row; history (completions, Photo Evidence) is kept and shown as «Tidligere medlem» (4A).
5. A user who has left is in the no-Home state again and may create a Home or join through a new invite (5).
6. Invite links created earlier by someone who has left stay valid until used or expired; a link belongs to the Home (Story 1.4: no revoking).
7. The work becomes Story 1.8 in Epic 1, built before Story 2.1, and one cross-cutting rule (AD-16) covers Epics 2–6 instead of rewriting each story.

## 3. Impact analysis

**Epics.**
- **Epic 1** gains Story 1.8 and goes back to `in-progress`. Its retrospective stays `done`.
- **Epic 2:** Story 2.4 gains one acceptance criterion (attribution to «Tidligere medlem»).
- **Epic 3:** Stories 3.2, 3.3 and 3.4 each gain one criterion (current Members only).
- **Epic 4:** Story 4.3 gains one criterion («Tidligere medlem» as uploader).
- **Epics 5 and 6:** covered by the cross-cutting rule; no story text changes.
- No epic is removed, renumbered or resequenced. Stories: 24 + 1 = 25.

**Artifacts.**

| Artifact | Change |
|---|---|
| PRD | New FR-23 in §4.1; FR-23 added to the Trinn 1 list in §6 |
| Architecture | New AD-16; one line under the ER diagram |
| UX (EXPERIENCE.md) | IA row for Members & Invite; Component Pattern "Leave / remove confirmation"; State Patterns "Left a Home" and "Removed while signed in"; `reconcile-prd.md` #5 resolved |
| Epics | New Story 1.8; Additional Requirements gains the AD-16 rule; one AC each in 2.4, 3.2, 3.3, 3.4, 4.3; dated note on Story 1.5; Epic 1 story list and build order |
| Sprint status | `1-8-…: backlog`; `epic-1: in-progress`; action 8 `done`; build-order comment |
| Traces | `issues.md` `ondelete` item closed; retrospective rows R2 and action 8 annotated |

**Technical.** Two Home-scoped routes behind `require_role` (the 1.5 route walk covers them automatically), two domain functions in `domain/homes`, frontend actions on the existing Members & Invite page. No migration: no table references `memberships`, and the foreign keys *from* `memberships` are unaffected by deleting its rows. No change to hosting, CI or the seed.

## 4. Recommended approach

**Direct adjustment.** One new story plus small additions; no rollback (nothing built conflicts) and no MVP review (FR-23 is small and fits Trinn 1). Risk is low: the change is additive, the permission layer and the FR-3 check already exist, and the cross-cutting rule is written down before Epic 2 starts referencing Members.

## 5. Detailed change proposals

All seven were approved one by one on 2026-11-08 (incremental mode).

### 5.1 PRD — new FR-23 (`prd.md`, §4.1, after FR-3)

NEW:

> #### FR-23: Leave a Home and remove Members `[ADDED 2026-11-08 — Sprint Change Proposal 2026-11-08]`
> A Household Member or Tenant can leave their Home. A Landlord can remove a Tenant from a Landlord Home. A Landlord cannot leave their own Landlord Home, and a Household Member cannot remove another Household Member. Realizes UJ-1, UJ-2.
>
> **Consequences (testable):**
> - After leaving or being removed, the user has no Membership in that Home: every Home-scoped request for it is rejected, and they may create a Home or join another through an invite.
> - When the last Household Member leaves a Household Home, the Home remains without Members; nothing is deleted.
> - Past activity in the Home (completions, Photo Evidence) is kept and shown as «Tidligere medlem»; only current Members count for access, notifications, fairness and overviews.
> - Both actions ask for confirmation, since neither can be undone.

Also: §6 Trinn 1, the line "Home creation, link-based invites, and Role assignment … FR-1 to FR-3" gains "and leaving a Home / removing Tenants (FR-23)".

### 5.2 Architecture — new AD-16 (`ARCHITECTURE-SPINE.md`, after AD-15)

NEW:

> ### AD-16 — Only current Memberships count; history points at the User `[ADDED 2026-11-08 — Sprint Change Proposal 2026-11-08]`
>
> - **Binds:** FR-23, FR-7, FR-11, FR-18/19, FR-20; depends on AD-1, AD-2
> - **Prevents:** a former Member keeping access, receiving a Home's notifications, or being counted in fairness or the Portfolio after leaving; and losing a Home's history when someone leaves.
> - **Rule:** Leaving a Home or being removed deletes that Membership row; nothing else is deleted (no migration: no table references `memberships`). Access (`require_role`), notifications (AD-8, AD-14), fairness (FR-11) and overviews (FR-20) read only current Memberships. History rows — completion attribution (AD-3) and Photo Evidence (AD-5) — reference the User, never the Membership, and the UI shows «Tidligere medlem» when that User has no Membership in the Home. Two Home-scoped routes, both behind `require_role`: `DELETE /api/homes/{home_id}/members/me` (Household Member, Tenant) and `DELETE /api/homes/{home_id}/members/{user_id}` (Landlord; the target must be a Tenant of that Home). Both go through domain functions in `domain/homes` (AD-3 layering).

Also, under the ER diagram: "`MEMBERSHIP` rows are deleted when a Member leaves or is removed; history references `USER` (AD-16)."

### 5.3 UX — EXPERIENCE.md and reconcile-prd.md

a) IA table, row "Members & Invite", appended:

> `[REVISED 2026-11-08 — Sprint Change Proposal]` Also: «Forlat hjemmet» for Household Members and Tenants, and «Fjern» next to each Tenant for the Landlord (FR-23). The Landlord sees no leave action; Household Members see no remove action.

b) Component Patterns, new row:

> | Leave / remove confirmation | Members & Invite | Inline, not a modal: the first tap turns the button into a short explanation and two buttons, «Ja, forlat hjemmet» / «Ja, fjern Anders» and «Avbryt». Leave explains what happens: «Du mister tilgangen til «X». Oppgavene du har gjort, blir stående.» Remove names the Tenant. Danger colour is used for the confirming button only, with its text label, never colour alone. Focus moves to the confirm button and back to the original button on «Avbryt». |

c) State Patterns, two new rows:

> | Left a Home | Members & Invite → Home | After leaving, the user lands on Create Home / the invite-only state they would have as a new user, with «Du har forlatt «X».» announced via `aria-live="polite"`. |
> | Removed while signed in | Any Home-scoped surface | The next Home-scoped request for that Home answers 403; the app refetches the Homes list and sends the user to `/`, which no longer shows that Home. No error page, no silent retry loop. |

d) `reconcile-prd.md` #5 gains `[RESOLVED 2026-11-08]` → PRD FR-23, Story 1.8.

### 5.4 Epics — new Story 1.8 (`epics.md`, after Story 1.7)

NEW:

> ### Story 1.8: Leave a Home & Landlord Removes a Tenant
>
> **Stage:** Trinn 1 · **Source:** Epic 1 retrospective (R2) and Sprint Change Proposal 2026-11-08 · **FR:** FR-23 · **AD:** AD-16, AD-2
>
> As a Household Member or Tenant, I want to leave a Home I no longer belong to, and as a Landlord, I want to remove a Tenant who has moved out,
> So that nobody is locked into the wrong Home and a Landlord's Home lists only current Tenants.
>
> **Acceptance Criteria:**
>
> **Given** a Household Member or Tenant on Members & Invite
> **When** they choose «Forlat hjemmet» and confirm
> **Then** their Membership is deleted, they land on the no-Home state with «Du har forlatt «X».», and they may create a Home or join another through an invite
>
> **Given** the last Household Member of a Household Home
> **When** they leave
> **Then** the Home remains without Members and nothing else is deleted
>
> **Given** a Landlord on Members & Invite
> **When** they choose «Fjern» next to a Tenant and confirm
> **Then** that Tenant's Membership is deleted and the list updates; the Landlord sees no leave action
>
> **Given** a Household Member, a Tenant, or a Landlord targeting someone who is not a Tenant of that Home
> **When** they call the remove route directly
> **Then** the server answers 403 and nothing is deleted (AD-2); a Landlord calling the leave route also gets 403
>
> **Given** a user removed while signed in
> **When** their next Home-scoped request for that Home answers 403
> **Then** the app refetches the Homes list and sends them to `/` — no error page and no retry loop
>
> **Given** either action
> **When** the first button is tapped
> **Then** an inline confirmation with «Avbryt» appears; nothing is deleted until confirmed (UX: Leave / remove confirmation)
>
> **Given** invite links created earlier by someone who has left
> **When** they are opened
> **Then** they stay valid until used or expired, as in Story 1.4 (a link belongs to the Home, not to its creator)

Also: Story 1.5 gets a dated note that its Never item "no removing Members" is superseded by Story 1.8; the Epic 1 story list and build order are updated (Epic 1 has 8 stories, the plan 25).

### 5.5 Epics — cross-cutting rule and story additions

a) Additional Requirements, new item after "Layering & permissions":

> - **Current vs past Members (AD-16, added 2026-11-08):** only current Memberships count for access, notifications, fairness and overviews; history (completions, Photo Evidence) references the User and shows «Tidligere medlem» when that User has no Membership in the Home.

b) One acceptance criterion each, marked *Added 2026-11-08 (Sprint Change Proposal):*

| Story | New AC |
|---|---|
| 2.4 | **Given** a completion recorded by a user who has since left the Home **When** any Member views it **Then** it is attributed to «Tidligere medlem» and the completion itself is kept |
| 3.2 | **Given** a user who has left a Home **When** the due-check runs **Then** they receive no notification for that Home |
| 3.3 | **Given** a Member who has left **When** fairness is computed **Then** they are neither counted nor targeted |
| 3.4 | **Given** a removed Tenant **When** the Landlord broadcasts **Then** the recipient count and recipients include current Tenants only |
| 4.3 | **Given** evidence uploaded by a Tenant who has since been removed **When** the Landlord reviews it **Then** it shows «Tidligere medlem» as uploader and stays reviewable |

### 5.6 Sprint status

- Add `1-8-leave-a-home-landlord-removes-a-tenant: backlog` after 1-7.
- `epic-1: done` → `in-progress`; `epic-1-retrospective` stays `done`.
- Action item `epic-1-retro-item-8-…` → `done` via `sprint_status.py --set-action-status` (the action was to plan the feature).
- Build-order comment: "1-8 before 2-1".
- Verified afterwards with `sprint_status.py detect-epic --epic 1`.

### 5.7 Traces

- `.logs/eirik/issues.md`: close "Velge `ondelete` for fremmednøklene i `memberships` når «forlat hjem» … kommer" — AD-16 deletes only Membership rows, which nothing references. Revisit for `users` if account deletion is ever added.
- `epic-1-retro-2026-11-08.md`: rows R2 and action 8 gain "Planned 2026-11-08: Sprint Change Proposal 2026-11-08 → Story 1.8"; original text kept.
- README: unchanged now; the "try leaving a Home" step comes with Story 1.8's PR (CLAUDE.md).

## 6. Implementation handoff

**Scope: moderate** — backlog change (one new story, small additions to five future stories), no replan.

- **Planning edits (this change, Developer/PO):** apply 5.1–5.7 on branch `change/leave-home-remove-member`, one commit per artifact, open a PR that links this proposal.
- **Story 1.8 (Developer):** next story after this PR merges, through `bmad-build`, with its own issue, branch `story/1-8-leave-home-remove-tenant` and PR, before Story 2.1.
- **Future stories (Developer):** 2.4, 3.2–3.4 and 4.3 carry their new criteria; AD-16 is in the epic context `bmad-build` compiles.

**Success criteria.** After this PR: PRD, architecture, UX, epics and sprint status agree on FR-23/AD-16/Story 1.8, and `detect-epic --epic 1` lists `1-8-…` as pending. After Story 1.8: a Household Member or Tenant can leave, a Landlord can remove a Tenant, the route walk covers both routes, the FR-3 check still passes, and a user locked into the wrong Home can get out without database edits.
