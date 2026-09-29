---
title: "PRD: AI-Driven Household Task App"
status: final
created: 2026-09-29
updated: 2026-09-29
---

# PRD: AI-Driven Household Task App

## 0. Document Purpose

This PRD translates the product brief (`brief-prosjektoppgave-ibe160-2026-09-12`) into implementable requirements for the 3-person IBE160 team. It is structured around three key user journeys, a shared glossary, and features with nested, globally numbered functional requirements (FR-1 through FR-21). It builds on the brief rather than repeating it — problem framing, competitive positioning, and long-term vision live there.

## 1. Vision

Irregular household tasks — the ones with no fixed weekly rhythm — get forgotten, and forgetting them causes real harm: mold, roommate friction, and for landlords, costly repairs and deposit disputes. This app gives any home a shared, always-current picture of what needs doing, split into non-negotiable "Must" tasks and flexible "Should" tasks, scheduled automatically so nobody has to invent a reminder for a task they don't think about until it's already a problem.

One core mechanic — create a Home, invite others into it — serves four kinds of living situations identically in structure but differently in stakes: a single occupant gets personal control; a couple or kollektiv adds fair distribution on top; a landlord gets a professional oversight tool across a property portfolio, with Tenants inheriting locked, must-do tasks they can't opt out of. An integrated AI assistant answers "how do I actually do this" questions in context, and generates a tailored onboarding guide for new Tenants.

## 2. Glossary

- **Home** — A shared space (a household or a rental unit) that groups members, tasks, and settings. Either a Household Home (created by and open to Household Members only) or a Landlord Home (created by and containing exactly one Landlord plus Tenants). Has one or more Members.
- **Member** — Any user linked to a Home. Role is one of: Household Member, Landlord, or Tenant.
- **Household Member** — A Member with peer standing in a Household Home — can create, adjust, invite, and complete tasks with equal permissions to every other Household Member of that Home, including the Home's creator. Covers single-occupant, samboer, and kollektiv contexts.
- **Landlord** — The sole Member of a Landlord Home with elevated permissions: sets and locks Must tasks and Frequency for Tenants, controls Notification Cadence for Tenants, can require Photo Evidence, and is the only Member of that Home who can generate invite links. Can own multiple Homes (a Portfolio).
- **Tenant** — A Member of a Landlord Home. Inherits Must/Should classification and Frequency set by the Landlord; cannot override either, and cannot invite other Members. Completes tasks like a Household Member otherwise.
- **Portfolio** — The set of Homes owned by one Landlord, viewed together in the Portfolio Dashboard.
- **Task** — A unit of household work belonging to a Home, with a Must/Should classification and a Frequency.
- **Must task** — A non-negotiable task. App-recommended by default; adjustable by Household Members and Landlords; locked for Tenants.
- **Should task** — A flexible, desirable-but-optional task.
- **Frequency** — How often a Task recurs. App-recommended for irregular tasks; approved or adjusted by Household Members/Landlords; locked for Tenants.
- **Task instance** — One occurrence of a Task due at a specific time, tracked for completion independently of past/future occurrences.
- **Completion** — A Member marking a Task instance done via self-checkoff. Trust-based by default (no peer verification).
- **Photo Evidence** — An optional, Landlord-required attachment proving completion of a specific Must task, scoped to task types where completion is objectively visible without capturing sensitive content. Auto-approved on upload; remains visible for Landlord review.
- **Notification Cadence** — How strictly/often a Tenant is reminded about a due or overdue task; configured by the Landlord, independent of the task's Frequency.
- **AI Assistant** — The in-app assistant providing (a) contextual quick-answers via a "?" affordance on any task, (b) full conversational chat, and (c) AI-generated onboarding guides tailored to a Home's unit type.

## 3. Target User

The Landlord is this product's primary user — the one whose needs it is designed around, per the brief's §Who This Serves. That's why Landlord-facing capabilities (Portfolio Dashboard, Photo Evidence, AI onboarding guide, broadcast messaging) make up the largest share of added scope in §4. Household Members remain a fully-served, equally real segment; the weighting reflects design priority, not lesser investment in the household experience.

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
  - **Persona + context:** Mari (24) and Peter share a home (samboer or kollektiv). Both are Household Members with equal standing.
  - **Entry state:** Peter, authenticated, receives a push notification earlier in the day that the floor needs vacuuming and the bathroom needs cleaning.
  - **Path:** Peter opens the app, taps into the "?" on the bathroom task when unsure which cleaner suits tiles versus mirrors, gets an immediate answer, completes both tasks, and self-checks them off. The app recalculates their next due dates. Later, Mari — tired from work — opens the app and sees both tasks already marked done.
  - **Climax:** Mari feels relief without lifting a finger; she trusts the checkmark because Peter did the work, not because anyone verified it.
  - **Resolution:** Both irregular tasks are rescheduled automatically; neither person had to remember to set a reminder.
  - **Edge case:** If Peter had been uncertain about *how* to do a step mid-task, the same "?" affordance escalates into a full AI chat for follow-up questions.

- **UJ-2. Johan manages a property portfolio without visiting every unit.**
  - **Persona + context:** Johan owns several apartment buildings, each with multiple units, each set up as its own Home with Tenants.
  - **Entry state:** Johan, authenticated, opens the app to his portfolio dashboard.
  - **Path:** He sees aggregated maintenance/cleaning status per building and unit, notices one kollektiv is behind on cleaning, and sends a targeted reminder message straight to that Home's Tenants. Separately, he pre-provisions a new Home for a unit he's taking over next week — creating the Home, generating an invite link for the incoming Tenants, and triggering the AI-generated onboarding guide tailored to that unit type. He reviews the app's suggested Must tasks for the new Home and adjusts a few to match his judgment.
  - **Climax:** Johan gets portfolio-wide visibility and can intervene precisely, without a site visit.
  - **Resolution:** The lagging Home receives Johan's message; the new Home is ready for Tenants before they've even moved in.
  - **Edge case:** If a Tenant later disputes a locked Must task, Johan (not the Tenant) is the only one who can change it.

- **UJ-3. Martin gets a task-specific nudge, not a group scolding.**
  - **Persona + context:** Martin is a Tenant in the kollektiv Johan flagged, and has been falling behind specifically on cleaning.
  - **Entry state:** Martin, authenticated, is the only member of his Home who has not completed a shared cleaning task that others already finished.
  - **Path:** Because the app tracks completion per person per task instance, the reminder targets Martin specifically rather than broadcasting to the whole Home. He opens the task, sees Must tasks listed ahead of Should tasks, completes the cleaning, and — because Johan has required Photo Evidence for this Must task — photographs the cleaned drain (sluk) and uploads it from his phone.
  - **Climax:** The task is auto-approved immediately; Martin isn't blocked waiting on Johan.
  - **Resolution:** The photo remains available for Johan to review afterward if he chooses; Martin's task list updates and his next reminder follows Johan's configured cadence.
  - **Edge case:** Photo Evidence is only requested for task types where completion is objectively visible without capturing sensitive or private content (for example, a drain, not a bedroom).

- **UJ-4. Sara keeps her own place on track, solo.** Sara, living alone, gets the same experience as Mari in UJ-1 — the same recommended Must/Should tasks, the same app-proposed frequencies, the same "?" and AI chat when she's unsure how to do something — except there is no housemate to share completions with: every task in her Home is hers alone to complete. Realized by the same FRs as UJ-1 (FR-4 through FR-9, FR-14/FR-15, FR-17, FR-21); no fairness or shared-completion mechanic (FR-7, FR-11) applies, since her Home has exactly one Household Member.

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

#### FR-2: Invite members via link
Who can generate a Home's invite link depends on Home type: in a Household Home, any Household Member can generate one; in a Landlord Home, only the Landlord can — Tenants cannot invite anyone. A user following the link can register and is linked to that Home. Realizes UJ-1, UJ-2.

**Consequences (testable):**
- An invite link resolves to registration when used by a user without an existing account, and to a "join Home" action for an existing account.
- Each invite link is scoped to exactly one Home and one intended Role (Household Member, or Tenant under a specific Landlord).
- A Tenant's attempt to generate an invite link is rejected server-side.

#### FR-3: Assign and enforce Member Roles
Each Member of a Home has exactly one Role: Household Member, Landlord, or Tenant. Role determines permission tier for Must/Should and Frequency settings (see 4.2, 4.3). Realizes UJ-2, UJ-3.

**Consequences (testable):**
- A Home has either (a) only Household Members, or (b) exactly one Landlord plus one or more Tenants — never a mix of Household Member with Landlord/Tenant in the same Home.
- Tenant-role write attempts on Landlord-locked fields are rejected at the permission layer, not just hidden in the UI.

### 4.2 Task Overview and Must/Should Prioritization

**Description:** Every task carries a Must or Should classification. The app recommends a default; Household Members and Landlords can adjust it, but Tenants inherit whatever their Landlord has set. Must tasks always surface ahead of Should tasks. For shared tasks, the system tracks completion per Member, so reminders can target only the Member who hasn't acted. Realizes UJ-1, UJ-2, UJ-3.

This Must/Should permission hierarchy — Landlord sets it, Tenant inherits it with no override — is the product's core structural positioning claim (brief §What Makes This Different: "a structural difference, not just a feature"), not one capability among equals. No competing chore app models a landlord-tenant relationship this way.

**Functional Requirements:**

#### FR-4: Recommend Must/Should classification
The app suggests a Must or Should classification for each task based on task type (for example, mold or damage risk defaults to Must). Realizes UJ-2.

**Consequences (testable):**
- Every task has a classification at creation time — either the app's recommendation or an explicit override — never unclassified.

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

#### FR-9: Auto-reschedule on completion
Marking a task instance complete automatically calculates and schedules the next due date based on its Frequency. Realizes UJ-1.

**Consequences (testable):**
- Completing a task instance with a given Frequency (for example, 30 days) creates or updates the next instance to be due that same interval from the actual completion date — not from the original due date. A task completed 2 days late still yields a full interval (for example, 30 days) from the completion date, not a shortened one.

### 4.4 Notifications

**Description:** The system proactively notifies Members about due and overdue tasks. For shared tasks, notifications target only the Member(s) who haven't acted. Landlords can additionally send ad-hoc messages to their Tenants and configure how strictly Tenants are reminded. Realizes UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-10: Due/overdue push notifications
The system sends a push notification to relevant Members when a task instance becomes due or overdue. Realizes UJ-1, UJ-3.

**Consequences (testable):**
- A Member with at least one due or overdue task receives a push notification within a defined delivery window (see Open Questions for exact timing).

#### FR-11: Fairness-based targeted notification
When completion attribution (FR-7) shows a Member has rarely or never performed completions for a recurring shared task relative to other Members, the system can target a reminder specifically to that Member — independent of the task's current shared completion status. Realizes UJ-3.

**Consequences (testable):**
- Given a recurring shared task where Member A has completed it the last several times and Member B has not completed it at all in that period, a targeted reminder is sent to Member B specifically rather than broadcast to the whole Home.

#### FR-12: Landlord ad-hoc broadcast message
A Landlord can send a free-form reminder message to all Tenants of a specific Home. Realizes UJ-2, UJ-3.

**Consequences (testable):**
- A sent broadcast message is delivered as a push notification to every Tenant Member of the targeted Home.

#### FR-13: Landlord-controlled notification cadence
A Landlord can configure how strictly/often Tenants of a Home are reminded about due/overdue Must tasks, independent of the task's Frequency. Tenants cannot adjust this themselves. Realizes UJ-2.

**Consequences (testable):**
- Changing the configured cadence changes the reminder frequency for all Tenants of that Home going forward, without changing the underlying task Frequency (FR-8/FR-9).

### 4.5 AI Assistant

**Description:** An AI assistant helps in two task-completion contexts (quick contextual answer, and full chat) plus one onboarding context (a tailored guide generated when Tenants join a new Home). Realizes UJ-1, UJ-2.

Existing chore apps (Sweepy, OurHome, Tody, Flatastic) drive completion through points and leaderboards; none address a user who simply doesn't know *how* to do a task. The AI assistant is this product's answer to that different kind of friction, not an incidental nice-to-have (brief §What Makes This Different).

**Functional Requirements:**

#### FR-14: Contextual quick-answer
Any task offers a "?" affordance that returns an immediate, task-specific answer to a how-to question. Realizes UJ-1.

**Consequences (testable):**
- Tapping "?" on a task returns an answer without leaving the task view.
- Every AI-generated answer displays a visible disclaimer that the AI can be wrong and that the user should exercise caution, particularly with chemical products (for example, cleaning agents).

#### FR-15: Escalate to full AI chat
From the quick-answer, a user can open a full conversational chat with the AI assistant for follow-up questions. Realizes UJ-1.

**Consequences (testable):**
- The chat retains the originating task as context for at least the first follow-up question.
- The chat carries the same AI-can-be-wrong / chemical-caution disclaimer as the quick-answer (FR-14), visible at least once per session.

**Feature-specific NFRs:**
- The AI assistant can answer chemical-related how-to questions (for example, which cleaner suits which surface); every such answer surfaces the disclaimer above rather than being scoped out. No numeric accuracy bound is set for this round — the disclaimer is the product's chosen mitigation, not a claim of verified correctness.

#### FR-16: AI-generated onboarding guide
When a Landlord provisions a Home and invites Tenants, the system generates an onboarding guide explaining how the app works, tailored to that Home's unit type. Realizes UJ-2.

**Consequences (testable):**
- A new Tenant accepting an invite receives or can access a guide referencing their specific Home/unit type, not a generic document identical across all Homes.

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
- Photo access is restricted to the Home's Landlord and the product's own support staff — no other Tenant, other Landlord, or third party can view it.

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

## 5. Non-Goals (Explicit)

- Payment processing or subscription billing, deferred to v2+ — the brief's Vision describes a future tiered-subscription model (individual/household vs. professional Landlord) as a later direction, not a v1 commitment.
- Hybel.no or any third-party rental-platform API integration, deferred to v2+ — designed to sit next to that space, not inside it.
- An in-app review/rating feature, deferred to v2+ — reviews/ratings are currently a hypothesis for measuring product success (brief §Success Criteria), not a scoped feature.
- Verification or audit of Household Member (non-Landlord) task completion — a permanent non-goal, not a v1 limitation to be lifted later: that tier stays trust-based by design.
- Photo Evidence required by default on any task — exclusively an opt-in, per-task Landlord setting, never a system-wide requirement.
- Broader home-management scope beyond cleaning/maintenance tasks — utilities, inventory, and similar — deferred to v2+, per brief Vision.

## 6. MVP Scope

- Home creation, link-based invites, and Role assignment (Household Member, Landlord, Tenant) — FR-1 to FR-3
- Must/Should recommendation, adjustment, Must-first ordering, and per-member completion tracking — FR-4 to FR-7
- Frequency recommendation, adjustment, and auto-rescheduling — FR-8, FR-9
- Push notifications: due/overdue, targeted-to-individual, Landlord broadcast, Landlord-configured cadence — FR-10 to FR-13
- AI assistant: contextual quick-answer, full chat escalation, AI-generated tailored onboarding guide — FR-14 to FR-16
- Self-checkoff completion; Landlord-required Photo Evidence with auto-approval and review access — FR-17 to FR-19
- Landlord portfolio dashboard across multiple Homes — FR-20
- Responsive web layout across phone, tablet, desktop — FR-21

`[NOTE FOR PM]` — This PRD's journey work surfaced four features beyond the brief's original scope — see Open Question 1 for the list and a provisional cut order.

## 7. Success Metrics

No quantitative targets are set for this round — there is no IBE160 grading rubric yet, and the brief's own Success Criteria are qualitative for this semester (see brief §Success Criteria).

**Primary**
- **SM-1**: The core loop functions end-to-end for both a Household Member Home and a Landlord/Tenant Home (create Home → invite → task overview → notification → completion, including AI assistant use). Validates FR-1 through FR-21 collectively.

**Directional signals** (tracked qualitatively, not targeted numerically this round)
- **SM-2**: Fewer irregular tasks going overdue or forgotten over time.
- **SM-3**: Continued/repeat usage rather than one-time setup and abandonment.
- **SM-4**: Willingness of users to leave positive reviews/ratings affirming the app holds up in practice (see brief).
- **SM-5**: For kollektiv Households — fewer chore-related conflicts reported, and improved trivsel (household contentment), the emotional stake behind the fairness mechanic (FR-7, FR-11).
- **SM-6**: For Landlords — fewer maintenance surprises or deposit disputes tied to neglected upkeep.

**Counter-metrics (do not optimize in isolation)**
- **SM-C1**: Notification opt-out or fatigue rate — counterbalances SM-2/SM-3; more reminders should not be pursued at the cost of users muting or abandoning the app.
- **SM-C2**: Uninstall/abandonment rate — counterbalances SM-4; a positive review from an early enthusiastic user means little if most users quietly stop returning.

## 8. Open Questions

1. Given the brief's own scope-risk flag plus four journey-derived additions (portfolio dashboard, photo evidence, targeted notifications, AI onboarding guide), should any of FR-11, FR-16, FR-18/19, or FR-20 be explicitly deferred past the mid-December deadline? Recommend revisiting at Architecture/Sprint Planning once effort is better understood. If scope must shrink, a provisional cut order (lowest-value-first, pending team validation): (1) FR-20 Portfolio Dashboard — nice-to-have oversight, not blocking the core loop for a single Landlord; (2) FR-16 AI onboarding guide — a Landlord can substitute a manual message short-term; (3) FR-11 fairness-based targeting — degrades gracefully to broadcast-only reminders (FR-10/FR-12); FR-18/19 Photo Evidence is deliberately last, since it's the most distinctive Landlord-Tenant trust mechanism named in the brief's differentiation case.
2. FR-10: what is the acceptable delivery window for due/overdue push notifications (immediate, daily batch, and so on)?
3. FR-3: can a Landlord also be a Household Member of their own separate personal Home — that is, can one user hold both Roles across different Homes — or is a user's Role fixed account-wide?
4. FR-11: what threshold defines "rarely or never performed completions" for fairness-based targeting (for example, zero completions in the last N instances)? Needs a concrete rule before implementation.

## 9. Assumptions Index

- §3 — the JTBD and journeys are grounded in the team's own lived experience, not formal user research; treat as founder intuition to validate, not confirmed findings.
- §Privacy Constraints — the Photo Evidence content-safety enforcement mechanism (curated allowlist vs. Landlord judgment) is undecided, deferred to architecture.
- §6 `[NOTE FOR PM]` — the four journey-derived features beyond the brief's original list are assumed to remain in scope for v1 pending team confirmation given the timeline; see Open Question 1.

## Privacy Constraints

- Photo Evidence (FR-18/19) is restricted by design to task types where completion is objectively visible without capturing sensitive or private content (for example, a cleaned drain, not a general room photo). This is a product-level scoping rule, not merely a UX suggestion — Landlords should not be able to configure Photo Evidence for task types that would incidentally capture private spaces or belongings. `[ASSUMPTION: the enforcement mechanism (a curated, system-controlled allowlist of eligible task types vs. Landlord judgment with no system check) is not yet decided — deferred to architecture.]`
- Photo retention: each photo is automatically replaced the next time the same task is completed — the system never accumulates a photo history for a task. Access is restricted to the Home's Landlord and the product's own support staff only.
- Tenant data (task history, Photo Evidence, completion records) is visible to that Tenant's Landlord by design (this is the product's core value proposition for the Landlord segment) but should not be visible to other Tenants or other Landlords outside the relevant Home.

## Cross-Cutting NFRs

- **Permission enforcement:** Role-based restrictions (Tenant cannot alter Landlord-locked Must/Frequency settings; only Household Members/Landlords can adjust classification) must be enforced server-side, not only hidden in the UI (see FR-3, FR-5, FR-8).
- **Notification reliability:** Push notifications (FR-10 to FR-13) must be delivered reliably enough that a Household Member or Tenant can trust the absence of a notification to mean "nothing due" — a missed notification undermines the product's core value proposition (avoiding forgotten tasks).
- **Responsiveness:** All core flows must remain fully usable at common phone, tablet, and desktop breakpoints (FR-21) — this is not a "nice to have" polish pass but a stated v1 requirement.
