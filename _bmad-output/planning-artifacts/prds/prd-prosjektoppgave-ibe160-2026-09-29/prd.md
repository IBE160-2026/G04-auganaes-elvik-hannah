---
title: "PRD: AI-Driven Household Task App"
status: final
created: 2026-09-29
updated: 2026-11-12
---

## Revision log

Each change after the first final version, with the proposal that explains it. Requirement text below is kept clean; the reasons live in the proposals.

| Date | Change | Proposal |
|---|---|---|
| 2026-10-11 | MVP split into Trinn 1 and Trinn 2, FR-22 added, testable success metrics, household as primary user | `sprint-change-proposal-2026-10-11.md` |
| 2026-11-01 | Vercel is the only hosting; Open Question 2 resolved as a daily morning batch; FR-10 and FR-13 tightened | `sprint-change-proposal-2026-11-01.md` |
| 2026-11-08 | FR-23 added (leave a Home, remove Tenants); FR-3 reads "zero or more Tenants" | `sprint-change-proposal-2026-11-08.md` |
| 2026-11-09 | One rule for creating Homes (FR-1, Q3); FR-24 added (add and archive Tasks); FR-8 fixed intervals | `sprint-change-proposal-2026-11-09.md` |
| 2026-11-12 | Teacher's PRD feedback: Trinn 2 cut line decided (Q1), FR-11 rule (Q4), AI failure, limit and data (FR-14/15), FR-2 and FR-3 rules, FR-16 without "unit type", clean requirement text, account privacy, FR-1 to FR-24 count, SM-9 split, SM-15 | `sprint-change-proposal-2026-11-12.md` |
| 2026-11-12 | Story 5.1 built: FR-14 states what counts toward the 20 AI calls, the UTC day and reset time, the question rules and who may use "?"; FR-22 mentions demo marking; account data lists the daily call count | `spec-5-1-contextual-quick-answer.md` |
| 2026-11-12 | Story 5.1 follow-up: FR-14 limits the AI to the task and housework | `spec-5-1-contextual-quick-answer.md` |
| 2026-11-12 | Epic 2 retrospective: FR-9 states that days are UTC days | `epic-2-retro-2026-11-12.md` |
| 2026-11-12 | Story 3.1 built: FR-10 states the per-device registration, the 10-device cap, silent registration, best-effort removal at sign-out and the blocked-push note; account data lists the stored push devices | `spec-3-1-push-notification-permission-device-registration.md` |

# PRD: AI-Driven Household Task App

## 0. Document Purpose

This PRD translates the product brief (`brief-prosjektoppgave-ibe160-2026-09-12`) into implementable requirements for the 3-person IBE160 team. It is structured around three key user journeys, a shared glossary, and features with nested, globally numbered functional requirements (FR-1 through FR-24; FR-23 and FR-24 were added later and sit under their feature group, keeping their numbers because stories and code refer to them). It builds on the brief rather than repeating it — problem framing, competitive positioning, and long-term vision live there.

## 1. Vision

Irregular household tasks — the ones with no fixed weekly rhythm — get forgotten, and forgetting them causes real harm: mold, roommate friction, and for landlords, costly repairs and deposit disputes. This app gives any home a shared, always-current picture of what needs doing, split into non-negotiable "Must" tasks and flexible "Should" tasks, scheduled automatically so nobody has to invent a reminder for a task they don't think about until it's already a problem.

One core mechanic — create a Home, invite others into it — serves four kinds of living situations identically in structure but differently in stakes: a single occupant gets personal control; a couple or kollektiv adds fair distribution on top; a landlord gets a professional oversight tool across a property portfolio, with Tenants inheriting locked, must-do tasks they can't opt out of. An integrated AI assistant answers "how do I actually do this" questions in context, and generates a tailored onboarding guide for new Tenants.

## 2. Glossary

- **Trinn 1 / Trinn 2** — The two delivery stages of the MVP (§6). Trinn 1 is the minimal core flow that must be finished and stable first; Trinn 2 is added once Trinn 1 is stable.
- **Home** — A shared space (a household or a rental unit) that groups members, tasks, and settings. Either a Household Home (created by and open to Household Members only) or a Landlord Home (created by and containing exactly one Landlord plus Tenants). Has one or more Members.
- **Household Home** — A Home created by and open to Household Members only.
- **Landlord Home** — A Home created by a Landlord, with that Landlord as its only Landlord and zero or more Tenants.
- **Task Setup** — The one-time review, when a Home is created, of the app's recommended Tasks (done once per Home).
- **Member** — Any user linked to a Home. Role is one of: Household Member, Landlord, or Tenant.
- **Household Member** — A Member with peer standing in a Household Home — can create, adjust, invite, and complete tasks with equal permissions to every other Household Member of that Home, including the Home's creator. Covers single-occupant, samboer, and kollektiv contexts.
- **Landlord** — The sole Member of a Landlord Home with elevated permissions: sets and locks Must tasks and Frequency for Tenants, controls Notification Cadence for Tenants, can require Photo Evidence, and is the only Member of that Home who can generate invite links. Can own multiple Homes (a Portfolio).
- **Tenant** — A Member of a Landlord Home. Inherits Must/Should classification and Frequency set by the Landlord; cannot override either, and cannot invite other Members. Completes tasks like a Household Member otherwise.
- **Portfolio** — The set of Homes owned by one Landlord, viewed together in the Portfolio Dashboard.
- **Portfolio Dashboard** — The Landlord's single view of task status per Home across their Portfolio (FR-20).
- **Task** — A unit of household work belonging to a Home, with a Must/Should classification and a Frequency.
- **Must task** — A non-negotiable task. App-recommended by default; adjustable by Household Members and Landlords; locked for Tenants.
- **Should task** — A flexible, desirable-but-optional task.
- **Frequency** — How often a Task recurs. App-recommended for irregular tasks; approved or adjusted by Household Members/Landlords; locked for Tenants.
- **Task instance** — One occurrence of a Task due at a specific time, tracked for completion independently of past/future occurrences.
- **Completion** — A Member marking a Task instance done via self-checkoff. Trust-based by default (no peer verification).
- **Photo Evidence** — An optional, Landlord-required attachment proving completion of a specific Must task, scoped to task types where completion is objectively visible without capturing sensitive content. Auto-approved on upload; remains visible for Landlord review.
- **Notification Cadence** — How strictly/often a Tenant is reminded about a due or overdue task; configured by the Landlord, independent of the task's Frequency.
- **AI Assistant** — The in-app assistant providing (a) contextual quick-answers via a "?" affordance on any task, (b) full conversational chat, and (c) AI-generated onboarding guides tailored to that Home.

## 3. Target User

For Trinn 1 the Household is this product's primary user, per the brief's §Who This Serves: design and the demo flow are built around Household Members. The Landlord–Tenant role model (FR-3, FR-5, FR-8) is still part of Trinn 1 because it is the product's structural differentiator and its most testable rule set. The Landlord-facing oversight capabilities (Portfolio Dashboard, Photo Evidence, AI onboarding guide, broadcast messaging, notification cadence) make up the largest share of added scope in §4 and are delivered in Trinn 2 (see §6).

`[ASSUMPTION: the JTBD and journeys below are grounded in the team's own lived experience of shared living, not formal user research — see brief §The Problem. Treat user-need statements as founder intuition to validate, not confirmed findings.]`

### 3.1 Jobs To Be Done

- Give me one place to see what needs doing in my home, without having to remember to think about it.
- Let me trust that if someone else already did a shared task, I don't need to check or redo it.
- Help me actually do a task I don't know how to do, right when I'm stuck.
- (Landlord) Let me see, at a glance, whether my properties are being maintained — without visiting or chasing tenants manually.
- (Landlord) Let me set non-negotiable expectations for tenants and know they were met.
- (Tenant) Tell me clearly what's required of me versus what's optional, and make it easy to prove I did it.

### 3.2 Non-Users (v1)

- Users wanting a general-purpose bill-splitting or shared-expense tool (out of scope; see brief's Non-Goals around payment).
- Property managers needing accounting, contract, or rent-collection functionality (that's Hybel.no's territory, not this product's, in v1).

### 3.3 Key User Journeys

- **UJ-1. Mari and Peter close the loop on a shared home without talking about it.**
  - **In Trinn 1:** Peter opens the app himself, without push. He uses "?", checks the tasks off, and Mari sees them done (FR-7, FR-9, FR-14, FR-17). Push (FR-10) and the full chat (FR-15) are Trinn 2.
  - **Persona + context:** Mari (24) and Peter share a home (samboer or kollektiv). Both are Household Members with equal standing.
  - **Entry state:** Peter, authenticated, receives a push notification earlier in the day that the floor needs vacuuming and the bathroom needs cleaning.
  - **Path:** Peter opens the app, taps into the "?" on the bathroom task when unsure which cleaner suits tiles versus mirrors, gets an immediate answer, completes both tasks, and self-checks them off. The app recalculates their next due dates. Later, Mari — tired from work — opens the app and sees both tasks already marked done.
  - **Climax:** Mari feels relief without lifting a finger; she trusts the checkmark because Peter did the work, not because anyone verified it.
  - **Resolution:** Both irregular tasks are rescheduled automatically; neither person had to remember to set a reminder.
  - **Edge case:** If Peter had been uncertain about *how* to do a step mid-task, the same "?" affordance escalates into a full AI chat for follow-up questions.

- **UJ-2. Johan manages a property portfolio without visiting every unit.**
  - **In Trinn 1:** Johan creates a Landlord Home, invites Tenants with a link and adjusts the Must tasks (FR-1 to FR-5, FR-8). The portfolio dashboard, broadcast and onboarding guide are Trinn 2.
  - **Persona + context:** Johan owns several apartment buildings, each with multiple units, each set up as its own Home with Tenants.
  - **Entry state:** Johan, authenticated, opens the app to his portfolio dashboard.
  - **Path:** He sees aggregated maintenance/cleaning status per building and unit, notices one kollektiv is behind on cleaning, and sends a targeted reminder message straight to that Home's Tenants. Separately, he pre-provisions a new Home for a unit he's taking over next week — creating the Home, generating an invite link for the incoming Tenants, and triggering the AI-generated onboarding guide tailored to that Home. He reviews the app's suggested Must tasks for the new Home and adjusts a few to match his judgment.
  - **Climax:** Johan gets portfolio-wide visibility and can intervene precisely, without a site visit.
  - **Resolution:** The lagging Home receives Johan's message; the new Home is ready for Tenants before they've even moved in.
  - **Edge case:** If a Tenant later disputes a locked Must task, Johan (not the Tenant) is the only one who can change it.

- **UJ-3. Martin gets a task-specific nudge, not a group scolding.**
  - **In Trinn 1:** Martin sees Must tasks before Should tasks and checks the task off. The targeted reminder and the photo are Trinn 2.
  - **Persona + context:** Martin is a Tenant in the kollektiv Johan flagged, and has been falling behind specifically on cleaning.
  - **Entry state:** Martin, authenticated, is the only member of his Home who has not completed a shared cleaning task that others already finished.
  - **Path:** Because the app tracks completion per person per task instance, the reminder targets Martin specifically rather than broadcasting to the whole Home. He opens the task, sees Must tasks listed ahead of Should tasks, completes the cleaning, and — because Johan has required Photo Evidence for this Must task — photographs the cleaned drain (sluk) and uploads it from his phone.
  - **Climax:** The task is auto-approved immediately; Martin isn't blocked waiting on Johan.
  - **Resolution:** The photo remains available for Johan to review afterward if he chooses; Martin's task list updates and his next reminder follows Johan's configured cadence.
  - **Edge case:** Photo Evidence is only requested for task types where completion is objectively visible without capturing sensitive or private content (for example, a drain, not a bedroom).

- **UJ-4. Sara keeps her own place on track, solo.** Sara, living alone, gets the same experience as Mari in UJ-1 — the same recommended Must/Should tasks, the same app-proposed frequencies, the same "?" and AI chat when she's unsure how to do something — except there is no housemate to share completions with: every task in her Home is hers alone to complete. Realized by the same FRs as UJ-1 (FR-4 through FR-9, FR-14/FR-15, FR-17, FR-21); no fairness or shared-completion mechanic (FR-7, FR-11) applies, since her Home has exactly one Household Member. Fully in Trinn 1, except push.

## 4. Features

### 4.1 Homes and Membership

**Description:** Every user experience starts with a Home. A user creates one and invites others via a shareable link; invited users register and are linked automatically. A Landlord can pre-provision a Home — configuring it fully — before any Tenant has joined. Realizes UJ-1, UJ-2.

**Functional Requirements:**

#### FR-1: Create a Home
A user can create a Home. If created as a Household Home, the creator becomes a Household Member with the same standing as any later invitee — no persistent creator privilege. If created as a Landlord Home, the creator becomes its Landlord. Realizes UJ-1, UJ-2.

**Consequences (testable):**
- A newly created Household Home has one or more Household Members, all with equal permissions from the moment they join, including the creator.
- A newly created Landlord Home has exactly one Landlord and zero or more Tenants.
- Creating a Home does not require prior membership in any other Home.
- A Landlord-created Home supports full configuration (Must tasks, Frequency) with zero Tenants present.
- A user may create any number of Landlord Homes, and a Household Home only while they are not a Household Member or Tenant of another Home (the same one-Home limit as joining through an invite). A Landlord can therefore create their own Household Home, and a Household Member or Tenant can create a Landlord Home.

#### FR-2: Invite members via link
Who can generate a Home's invite link depends on Home type: in a Household Home, any Household Member can generate one; in a Landlord Home, only the Landlord can — Tenants cannot invite anyone. A user following the link can register and is linked to that Home. Realizes UJ-1, UJ-2.

**Consequences (testable):**
- An invite link resolves to registration when used by a user without an existing account, and to a "join Home" action for an existing account.
- Each invite link is scoped to exactly one Home and one intended Role (Household Member, or Tenant under a specific Landlord).
- A Tenant's attempt to generate an invite link is rejected server-side.
- An invite link is valid for 7 days and can be used once. An expired or already used link shows a clear message and links nobody to the Home.

#### FR-3: Assign and enforce Member Roles
Each Member of a Home has exactly one Role: Household Member, Landlord, or Tenant. Role determines permission tier for Must/Should and Frequency settings (see 4.2, 4.3). Realizes UJ-2, UJ-3.

**Consequences (testable):**
- A Home has either (a) only Household Members, or (b) exactly one Landlord plus zero or more Tenants (a Landlord Home exists before its first Tenant joins) — never a mix of Household Member with Landlord/Tenant in the same Home.
- Tenant-role write attempts on Landlord-locked fields are rejected at the permission layer, not just hidden in the UI.
- A user cannot read or change data in a Home they are not a current Member of: every Home-scoped request is rejected server-side.

#### FR-23: Leave a Home and remove Members
A Household Member or Tenant can leave their Home. A Landlord can remove a Tenant from a Landlord Home. A Landlord cannot leave their own Landlord Home, and a Household Member cannot remove another Household Member. Realizes UJ-1, UJ-2.

**Consequences (testable):**
- After leaving or being removed, the user has no Membership in that Home: every Home-scoped request for it is rejected, and they may create a Home or join another through an invite.
- When the last Household Member leaves a Household Home, the Home remains without Members; nothing is deleted.
- Past activity in the Home (completions, Photo Evidence) is kept and shown as «Tidligere medlem»; only current Members count for access, notifications, fairness and overviews.
- Both actions ask for confirmation, since neither can be undone.

### 4.2 Task Overview and Must/Should Prioritization

**Description:** Every task carries a Must or Should classification. The app recommends a default; Household Members and Landlords can adjust it, but Tenants inherit whatever their Landlord has set. Must tasks always surface ahead of Should tasks. For shared tasks, the system tracks completion per Member, so reminders can target only the Member who hasn't acted. Realizes UJ-1, UJ-2, UJ-3.

This Must/Should permission hierarchy — Landlord sets it, Tenant inherits it with no override — is the product's core structural positioning claim (brief §What Makes This Different: "a structural difference, not just a feature"), not one capability among equals. No competing chore app models a landlord-tenant relationship this way.

**Functional Requirements:**

#### FR-4: Recommend Must/Should classification
The app suggests a Must or Should classification for each task based on task type (for example, mold or damage risk defaults to Must). Realizes UJ-2.

**Consequences (testable):**
- Every task has a classification at creation time — either the app's recommendation or an explicit override — never unclassified.
- Given the catalog task type "Rens sluket" the recommended classification is Must; given "Avkalk vannkokeren" it is Should.

#### FR-5: Adjust classification (Household Members and Landlords only)
Household Members and Landlords can change a task's Must/Should classification. Tenants cannot. Realizes UJ-2, UJ-3.

**Consequences (testable):**
- A classification change by a Household Member or Landlord persists and is reflected to all Members of that Home, including Tenants (read-only for Tenants).
- An API or UI attempt by a Tenant to change classification is rejected.

#### FR-6: Must-first ordering
The task list displays Must tasks ahead of Should tasks. Realizes UJ-3.

**Consequences (testable):**
- Given a mixed list, all Must tasks render before any Should task regardless of due date.

#### FR-7: Shared completion status with per-member attribution
A Task instance in a Home has one shared completion status: any Member marking it complete resolves it for the whole Home. The system additionally records which Member performed each completion (attribution), independent of the shared status. Realizes UJ-1, UJ-3.

**Consequences (testable):**
- A shared Task instance completed by one Member shows as complete to all Members immediately (UJ-1's "Mari sees Peter already did it").
- Each completion event stores the completing Member's identity, queryable per Home over time (for example, "who completed this task the last N times").
- Personal-space tasks (for example, a Member's own room) are out of the app's scope — not tracked, self-managed by each Member.

### 4.3 Frequency and Scheduling

**Description:** Irregular tasks — the ones without a natural rhythm — get an app-recommended Frequency, adjustable by Household Members and Landlords, locked for Tenants. Completing a task instance automatically schedules the next one. Realizes UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-8: Recommend and set task Frequency
The app proposes a recurrence Frequency for irregular tasks. Household Members and Landlords can approve or adjust it; Tenants inherit the Landlord's setting and cannot change it. Realizes UJ-2, UJ-3.

**Consequences (testable):**
- Every recurring task has a Frequency value at creation — app-recommended or explicitly overridden.
- A Tenant's attempt to change Frequency on a Landlord Home's task is rejected.
- A Frequency is chosen from fixed intervals: 7, 14, 30, 42, 60, 90, 182 or 365 days. The recommended tasks are reviewed once per Home in Task Setup.

#### FR-24: Add and archive Tasks
After Task Setup, a Household Member or Landlord can add a Task — a catalog task type the Home does not currently have, or a custom Task with its own name — and archive a Task the Home no longer needs. Tenants cannot. Realizes UJ-1, UJ-2, UJ-4.

**Consequences (testable):**
- A custom Task has a name (unique among the Home's active Tasks), a Must/Should classification and a Frequency chosen by the user (FR-4, FR-8). It can never require Photo Evidence (FR-18, Privacy Constraints).
- An archived Task disappears from Task Overview, notifications, fairness and the Portfolio. Its history (completions, Photo Evidence) is kept. A catalog task type can be added again as a new Task.
- Archiving asks for confirmation first. Archiving every Task does not reopen Task Setup, which still runs once per Home.
- A Tenant's attempt to add or archive a Task is rejected server-side.

#### FR-9: Auto-reschedule on completion
Marking a task instance complete automatically calculates and schedules the next due date based on its Frequency. Realizes UJ-1.

**Consequences (testable):**
- Completing a task instance with a given Frequency (for example, 30 days) creates or updates the next instance to be due that same interval from the actual completion date — not from the original due date. A task completed 2 days late still yields a full interval (for example, 30 days) from the completion date, not a shortened one.
- Days are counted in UTC: due dates, the due status (due soon, overdue) and "completed today" use the server's UTC date. In Norway a completion between 00:00 and 01:00 (02:00 in summer time) therefore counts as the previous day.

### 4.4 Notifications

**Description:** The system proactively notifies Members about due and overdue tasks. For shared tasks, notifications target only the Member(s) who haven't acted. Landlords can additionally send ad-hoc messages to their Tenants and configure how strictly Tenants are reminded. Realizes UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-10: Due/overdue push notifications
The system sends a push notification to relevant Members when a task instance becomes due or overdue. Realizes UJ-1, UJ-3.

**Consequences (testable):**
- A Member with at least one due or overdue task receives one push notification per day from the daily morning due-check (scheduled around 07:00–08:00 Norwegian time; the platform may start it up to 59 minutes late), covering all of that Member's due and overdue tasks.
- A Member turns push on per device from Settings, which shows the browser's permission (granted, denied, not asked, unsupported). Each device is registered on its own, so a second device never replaces the first, and a Member has at most 10 registered devices (an 11th replaces the one registered longest ago). When permission is already granted, opening Settings registers the device without a new prompt. A device belongs to one Member at a time: signing out removes it on a best-effort basis, and otherwise it moves to the next Member who registers it, so a Member who closes the app without signing out may still have reminders reach that browser until then.
- A Member who has blocked push sees one inline, dismissible note on Task Overview, only while a task is overdue or due soon, and not again once that Member has dismissed it on that device.

#### FR-11: Fairness-based targeted notification
When completion attribution (FR-7) shows a Member has not performed any of a recurring shared task's recent completions, the system targets a reminder specifically to that Member instead of the whole Home. Realizes UJ-3.

**Consequences (testable):**
- Given a recurring shared task in a Home with at least two current Members and at least three completed instances: while the task is open and due or overdue, if Member B has none of the last 3 completions, B receives a targeted reminder and no other Member receives one from this rule. At most one such reminder is sent per task instance. The number 3 is a constant that can be changed without changing this requirement.

#### FR-12: Landlord ad-hoc broadcast message
A Landlord can send a free-form reminder message to all Tenants of a specific Home. Realizes UJ-2, UJ-3.

**Consequences (testable):**
- A sent broadcast message is delivered as a push notification to every Tenant Member of the targeted Home.

#### FR-13: Landlord-controlled notification cadence
A Landlord can configure how strictly/often Tenants of a Home are reminded about due/overdue Must tasks, independent of the task's Frequency. Tenants cannot adjust this themselves. Realizes UJ-2.

**Consequences (testable):**
- Changing the configured cadence changes the reminder frequency for all Tenants of that Home going forward, without changing the underlying task Frequency (FR-8/FR-9).
- Cadence options are whole-day intervals (for example daily, every second day, weekly), since reminders are sent by the daily due-check; no option promises more than one reminder per day.

### 4.5 AI Assistant

**Description:** An AI assistant helps in two task-completion contexts (quick contextual answer, and full chat) plus one onboarding context (a tailored guide generated when Tenants join a new Home). Realizes UJ-1, UJ-2.

Existing chore apps (Sweepy, OurHome, Tody, Flatastic) drive completion through points and leaderboards; none address a user who simply doesn't know *how* to do a task. The AI assistant is this product's answer to that different kind of friction, not an incidental nice-to-have (brief §What Makes This Different).

**Functional Requirements:**

#### FR-14: Contextual quick-answer
Any task offers a "?" affordance that returns an immediate, task-specific answer to a how-to question. Realizes UJ-1.

**Consequences (testable):**
- Tapping "?" on a task returns an answer without leaving the task view.
- Every AI-generated answer displays a visible disclaimer that the AI can be wrong and that the user should exercise caution, particularly with chemical products (for example, cleaning agents).
- With no AI API key configured, the quick-answer still returns an answer in the same structure from mock data, so the feature can be run and tested without external accounts (FR-22).
- If the AI call fails or takes longer than 10 seconds, "?" shows an error message (status "error") and can be retried; the task view and completion keep working.
- Only the task's name, its catalog type and the user's own question are sent to the AI service — no names, e-mail addresses or Home names. The UI says the question goes to an external AI service.
- A user can make at most 20 AI calls per day (quick answers and chat together). The day is a UTC day. Every call that reaches the AI provider counts, also when it fails or times out, so a retry after an error uses up one of the 20; a refused call does not count. Beyond the limit, "?" says so plainly and tells when the count restarts (00:00 UTC, shown in the user's local time). The limit also applies to the mock answers, so it can be tested offline.
- The AI answers only questions about the task and housework (cleaning, maintenance, equipment and cleaning products in the home); a question about which cleaner suits a surface is always in scope, and any other question gets a short answer that the assistant only helps with housework.
- Tapping "?" asks at once with a default question about the task; the user can also type their own question of at most 300 characters. Every Role, including Tenants, can use "?".

#### FR-15: Escalate to full AI chat
From the quick-answer, a user can open a full conversational chat with the AI assistant for follow-up questions. Realizes UJ-1.

**Consequences (testable):**
- The chat retains the originating task as context for at least the first follow-up question.
- The chat carries the same AI-can-be-wrong / chemical-caution disclaimer as the quick-answer (FR-14), visible at least once per session.
- The chat follows the same timeout, data and daily-limit rules as the quick-answer (FR-14).

**Feature-specific NFRs:**
- The AI assistant can answer chemical-related how-to questions (for example, which cleaner suits which surface); every such answer surfaces the disclaimer above rather than being scoped out. No numeric accuracy bound is set for this round — the disclaimer is the product's chosen mitigation, not a claim of verified correctness.

#### FR-16: AI-generated onboarding guide
When a Landlord provisions a Home and invites Tenants, the system generates an onboarding guide explaining how the app works, tailored to that Home. Realizes UJ-2.

**Consequences (testable):**
- A new Tenant accepting an invite can open a guide that names the Home and lists its active Must tasks with their frequencies, so two Homes with different tasks never get the same text.

### 4.6 Completion and Photo Evidence

**Description:** Completion is trust-based by default across all Home types: a Member self-checks a task off with no peer or Landlord verification required. For Landlord Homes, a Landlord can additionally require Photo Evidence on specific Must tasks, scoped to objectively-visible, non-sensitive completion states. Evidence is auto-approved on upload but remains available for Landlord review. Realizes UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-17: Self-checkoff completion
Any Member can mark a task instance complete with a single action; no confirmation from another Member is required. Realizes UJ-1.

**Consequences (testable):**
- A self-checkoff immediately updates the task's status for all Members of the Home (see FR-7).

#### FR-18: Landlord-required Photo Evidence
A Landlord can mark a specific Must task as requiring Photo Evidence from Tenants, restricted to task types where completion is objectively visible without capturing sensitive or private content. Realizes UJ-2, UJ-3.

**Consequences (testable):**
- A task flagged as requiring Photo Evidence cannot be marked complete by a Tenant without an attached photo.
- Requiring Photo Evidence is an explicit Landlord setting per task, not a system-wide default.

**Out of Scope:**
- General-purpose photo capture unrelated to proving a specific task's completion.
- Photo Evidence requirements for Household Member (non-Landlord) Homes — that tier remains fully trust-based (see UJ-1).

#### FR-19: Auto-approve with Landlord review, auto-replacing storage
Uploaded Photo Evidence auto-approves the task completion immediately; the photo remains accessible for the Landlord to review afterward, and is automatically replaced the next time the same task is completed (no accumulating photo history). Realizes UJ-3.

**Consequences (testable):**
- A Tenant uploading required Photo Evidence sees the task marked complete without waiting on Landlord action.
- The Landlord can retrieve the current photo for a task instance after the fact.
- Only the most recent photo for a given task is retained — completing the task again with a new photo discards the previous one.
- Photo access is restricted to the Home's Landlord — no other Tenant, other Landlord, or third party can view it.

**Feature-specific NFRs:**
- Photo Evidence storage and access must respect the privacy scoping described in FR-18 — see §Privacy Constraints.

### 4.7 Landlord Portfolio Dashboard

**Description:** A Landlord who owns multiple Homes sees an aggregated view of maintenance/cleaning status across all of them, enabling triage without a site visit. Realizes UJ-2.

**Functional Requirements:**

#### FR-20: Portfolio-level status dashboard
A Landlord with more than one Home sees a single view summarizing task status (on track / behind) per Home and per unit. Realizes UJ-2.

**Consequences (testable):**
- The dashboard identifies, at minimum, which Homes have overdue Must tasks, without requiring the Landlord to open each Home individually.

### 4.8 Responsive Platform

**Description:** The application is a single responsive web app usable across phone, tablet, and desktop. Realizes UJ-1, UJ-2, UJ-3, UJ-4.

**Functional Requirements:**

#### FR-21: Responsive layout across device classes
The web application renders a usable, complete layout on phone, tablet, and desktop viewport widths. Realizes UJ-1, UJ-2, UJ-3, UJ-4.

**Consequences (testable):**
- Core flows (view tasks, complete a task, receive/act on a notification, use the AI assistant, upload Photo Evidence) are fully operable at common phone, tablet, and desktop breakpoints.

**Notes:** Exact breakpoint values (px) are intentionally left to the UX pass (`bmad-ux`) rather than fixed here — this PRD sets the requirement, UX sets the pixels.

### 4.9 Local Runnability

**Description:** The app can be run and tested by anyone, including a course reviewer, without the team's accounts or keys. Added after the teacher's feedback of 2026-10-06, which rated this the largest risk to the project.

**Functional Requirements:**

#### FR-22: Run locally without external accounts
The application runs on a developer's or reviewer's own machine using a local Docker-based database, seed data and mock modes for the external services (AI, and in Trinn 2 push), with no account or key from the team.

**Consequences (testable):**
- Following the README, `docker compose up` starts a local PostgreSQL database, and one further command applies the migrations and loads seed data.
- With no AI key configured the AI assistant uses mock answers in the same `{status, answer, disclaimer}` structure and the app marks them as demo answers; with no push keys configured (Trinn 2) push uses a mock sender.
- `.env.example` lists every environment variable, with no secrets, and the README describes setup from the first story onward.
- The automated test suite runs without network access and without any key.

## 5. Non-Goals (Explicit)

- Payment processing or subscription billing, deferred to v2+ — the brief's Vision describes a future tiered-subscription model (individual/household vs. professional Landlord) as a later direction, not a v1 commitment.
- Hybel.no or any third-party rental-platform API integration, deferred to v2+ — designed to sit next to that space, not inside it.
- An in-app review/rating feature, deferred to v2+ — reviews/ratings are currently a hypothesis for measuring product success (brief §Success Criteria), not a scoped feature.
- Verification or audit of Household Member (non-Landlord) task completion — a permanent non-goal, not a v1 limitation to be lifted later: that tier stays trust-based by design.
- Photo Evidence required by default on any task — exclusively an opt-in, per-task Landlord setting, never a system-wide requirement.
- Account deletion is not built in this course version; the team aims to add it. The user row would be anonymised (past activity is already shown as «Tidligere medlem»); the Landlord case is undecided, because FR-3 requires exactly one Landlord and FR-23 forbids a Landlord leaving. Estimated at about one day.
- Broader home-management scope beyond cleaning/maintenance tasks — utilities, inventory, and similar — deferred to v2+, per brief Vision.

## 6. MVP Scope

The MVP is delivered in two stages, so that a complete app exists even if Trinn 2 is not finished.

### Trinn 1 — minimal core flow (finished and stable first)

- Home creation, link-based invites, and Role assignment (Household Member, Landlord, Tenant) — FR-1 to FR-3 — and leaving a Home / removing Tenants (FR-23, added 2026-11-08). The Tenant locks in FR-3, FR-5 and FR-8 are deliberately in Trinn 1: they are the product's differentiator and its most testable rules.
- Must/Should recommendation, adjustment, Must-first ordering, and per-member completion tracking — FR-4 to FR-7
- Frequency recommendation, adjustment, and auto-rescheduling — FR-8, FR-9, and adding/archiving Tasks — FR-24 (added 2026-11-09)
- AI assistant: contextual quick-answer — FR-14
- Self-checkoff completion — FR-17
- Responsive web layout across phone, tablet, desktop — FR-21
- Local runnability: Docker database, seed data, mock modes, README — FR-22

### Trinn 2 — added once Trinn 1 is stable

The cut line was decided on 2026-11-12 (Open Question 1).

**Must (built first):**
- Push notifications: due/overdue, Landlord broadcast, Landlord-configured cadence — FR-10, FR-12, FR-13
- Landlord-required Photo Evidence with auto-approval and review access — FR-18, FR-19

**If time permits, cut from the bottom up** (the first line is cut first):
- Landlord portfolio dashboard across multiple Homes — FR-20
- AI-generated tailored onboarding guide — FR-16
- Fairness-based targeted notification — FR-11
- AI assistant: full chat escalation — FR-15 (cut last, since Trinn 1 already has the FR-14 quick answer)

`[NOTE FOR PM]` — The journey work surfaced four features beyond the brief's original scope (portfolio dashboard, Photo Evidence, targeted notifications, AI onboarding guide); all are in Trinn 2, ordered as above.

## 7. Success Metrics

The primary metrics are the testable criteria from the brief's §Success Criteria, each traced to the requirements it validates. Each can become an automated test.

**Primary (Trinn 1)**
- **SM-1**: A Tenant cannot change a Must/Should classification or Frequency set by a Landlord; the server rejects the request (403). A Tenant also cannot add or archive Tasks (FR-24). Validates FR-3, FR-5, FR-8, FR-24.
- **SM-2**: Completing a task with Frequency N days schedules the next instance N days after the actual completion date, also when completed late. Validates FR-9.
- **SM-3**: Every new task gets an app-recommended Must or Should classification, the task list always shows Must tasks before Should tasks, and the core flows are usable at phone, tablet and desktop widths. Validates FR-4, FR-6, FR-21.
- **SM-4**: When one Member completes a shared task, every Member of that Home sees it as complete, and the completion records who did it. Validates FR-7, FR-17.
- **SM-5**: A user can create a Home without belonging to any other Home and becomes its Household Member or Landlord. Only permitted roles can generate invite links; a Tenant's attempt is rejected, and an expired or used link shows a clear message. Validates FR-1, FR-2.
- **SM-6**: A user with a Membership in one Home cannot read or change another Home's data. Validates FR-3.
- **SM-7**: The "?" quick answer shows an answer with a visible disclaimer, and works with mock answers when no API key is set. A failed or slow call (over 10 seconds) shows an error and can be retried without blocking completion; the 21st call in a day is refused with a clear message; only the task's name, catalog type and the user's question are sent. Validates FR-14, FR-22.
- **SM-8**: A reviewer can run the app locally from the README using Docker, without the team's accounts or keys, and the automated tests pass. Validates FR-22.

**Primary (Trinn 2)**
- **SM-9a**: A Landlord broadcast reaches all Tenants of the targeted Home. Validates FR-12.
- **SM-9b**: The due-check never sends a duplicate notification for the same task instance and window. Validates FR-10.
- **SM-9c**: Photo Evidence cannot be required on task types that are not flagged eligible in the task catalog. Validates FR-18.
- **SM-9d**: The portfolio dashboard lists the Homes with overdue Must tasks. Validates FR-20.
- **SM-15**: Given a recurring shared task, at least two current Members and at least three completed instances, a Member with none of the last 3 completions gets one targeted reminder while the task is open and due, and no other Member gets one from this rule. Validates FR-11.

**Directional signals** (tracked qualitatively, not measured in the course)
- **SM-10**: Fewer irregular tasks going overdue or forgotten over time.
- **SM-11**: Continued/repeat usage rather than one-time setup and abandonment.
- **SM-12** *(long-term)*: Willingness of users to leave positive reviews/ratings affirming the app holds up in practice.
- **SM-13** *(long-term)*: For kollektiv Households — fewer chore-related conflicts reported, and improved trivsel (household contentment), the emotional stake behind the fairness mechanic (FR-7, FR-11).
- **SM-14** *(long-term)*: For Landlords — fewer maintenance surprises or deposit disputes tied to neglected upkeep.

**Counter-metrics (do not optimize in isolation)**
- **SM-C1**: Notification opt-out or fatigue rate — counterbalances SM-10/SM-11; more reminders should not be pursued at the cost of users muting or abandoning the app.
- **SM-C2**: Uninstall/abandonment rate — counterbalances SM-12; a positive review from an early enthusiastic user means little if most users quietly stop returning.

## 8. Open Questions

1. `[RESOLVED 2026-11-12]` Trinn 2 is ordered by priority (§6). **Must:** FR-10, FR-12, FR-13, FR-18/19. **If time permits, cut from the bottom up:** FR-20 (cut first), FR-16, FR-11, FR-15 (cut last). Decided by Eirik on 2026-11-12 after the teacher's PRD feedback; Hannah and Steffen were unavailable and can object in the PR. FR-13 is Must because it shares the daily due-check with FR-10. Photo Evidence stays Must because it is the most distinctive Landlord–Tenant mechanism in the brief.
2. `[RESOLVED 2026-11-01]` FR-10: daily morning batch. Tasks have due dates, not due times, and UJ-1 already describes the notification arriving "earlier in the day". Vercel Cron on the free plan runs at most once a day, with up to 59 minutes' delay; a missed run means no reminders that day, an accepted risk for a course project. FR-12 broadcasts are unaffected (sent immediately, AD-14).
3. `[RESOLVED 2026-11-07]` FR-3: can one user hold both Roles across different Homes? **Resolution:** yes. Role lives on the Membership (AD-1). A Landlord can own several Landlord Homes; a Household Member or Tenant belongs to at most one Home; anyone can create Landlord Homes, and a Household Home only without another Household Member or Tenant Membership (FR-1).
4. `[RESOLVED 2026-11-12]` FR-11: the threshold is "none of the last 3 completions", with at least two current Members and at least three completed instances, while the task is open and due (see FR-11). The number 3 is a constant in the code.

## 9. Privacy Constraints

- Photo Evidence (FR-18/19) is restricted by design to task types where completion is objectively visible without capturing sensitive or private content (for example, a cleaned drain, not a general room photo). This is a product-level scoping rule, not merely a UX suggestion. It is enforced by a curated, system-controlled allowlist: the flag `photo_evidence_eligible` in the task catalog, which no user can change. Custom Tasks can never require Photo Evidence (FR-24).
- Photo retention: each photo is automatically replaced the next time the same task is completed — the system never accumulates a photo history for a task. Access is restricted to the Home's Landlord only.
- Tenant data (task history, Photo Evidence, completion records) is visible to that Tenant's Landlord by design (this is the product's core value proposition for the Landlord segment) but must not be visible to other Tenants or other Landlords outside the relevant Home.
- Account data: an account stores an e-mail address, a display name and a password hash. Other Members of a Home see only the display name, never the e-mail address. The only user-related data sent to an external service is the minimal AI call described in FR-14. The app also stores, per user and day, how many AI calls were made (a number only, never the questions or answers), and, per user and device that has turned push on, the browser's push address and its two public keys (never the Home or the Role). A Member has at most 10 such devices. Account deletion is described in §5.

## 10. Cross-Cutting NFRs

- **Permission enforcement:** Role-based restrictions (Tenant cannot alter Landlord-locked Must/Frequency settings; only Household Members/Landlords can adjust classification) must be enforced server-side, not only hidden in the UI (see FR-3, FR-5, FR-8).
- **Notification reliability:** Each due-check run records, per Member, whether a notification was sent, and failed sends are logged. Delivery is promised no further than the daily batch (Open Question 2, accepted risk); a missed batch means no reminders that day. Applies to FR-10 to FR-13.
- **Runnable without external accounts:** The app, its seed data and its automated tests must run on a reviewer's own machine without any account or key from the team; external services (AI, push, file storage) have mock modes that are used when no key is set (FR-22).
- **Responsiveness:** All core flows must remain fully usable at common phone, tablet, and desktop breakpoints (FR-21) — this is not a "nice to have" polish pass but a stated v1 requirement.

## 11. Assumptions Index

- §3 — the JTBD and journeys are grounded in the team's own lived experience, not formal user research; treat as founder intuition to validate, not confirmed findings.
