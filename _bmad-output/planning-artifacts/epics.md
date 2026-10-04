---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories, step-04-final-validation]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-prosjektoppgave-ibe160-2026-09-29/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-prosjektoppgave-ibe160-2026-10-04/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/ux-designs/ux-prosjektoppgave-ibe160-2026-09-29/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-prosjektoppgave-ibe160-2026-09-29/EXPERIENCE.md
---

# Husly - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Husly (placeholder name — an AI-driven household task management web app), decomposing the requirements from the PRD, the DESIGN.md/EXPERIENCE.md UX design contract, and the ARCHITECTURE-SPINE.md into implementable stories.

Note on numbering: the PRD, Architecture, and UX documents all use the hyphenated form `FR-1`...`FR-21` as the canonical requirement IDs (also used in the Architecture's `binds:` frontmatter and Capability → Architecture Map). This document keeps that exact numbering rather than renumbering to `FR1` to preserve traceability across documents.

## Requirements Inventory

### Functional Requirements

FR-1: Create a Home. A user can create a Home. If created as a Household Home, the creator becomes a Household Member with the same standing as any later invitee — no persistent creator privilege. If created as a Landlord Home, the creator becomes its Landlord.

FR-2: Invite members via link. Who can generate a Home's invite link depends on Home type: in a Household Home, any Household Member can generate one; in a Landlord Home, only the Landlord can — Tenants cannot invite anyone.

FR-3: Assign and enforce Member Roles. Each Member of a Home has exactly one Role: Household Member, Landlord, or Tenant. Role determines permission tier for Must/Should and Frequency settings.

FR-4: Recommend Must/Should classification. The app suggests a Must or Should classification for each task based on task type (for example, mold or damage risk defaults to Must).

FR-5: Adjust classification (Household Members and Landlords only). Household Members and Landlords can change a task's Must/Should classification. Tenants cannot.

FR-6: Must-first ordering. The task list displays Must tasks ahead of Should tasks.

FR-7: Shared completion status with per-member attribution. A Task instance in a Home has one shared completion status: any Member marking it complete resolves it for the whole Home. The system additionally records which Member performed each completion.

FR-8: Recommend and set task Frequency. The app proposes a recurrence Frequency for irregular tasks. Household Members and Landlords can approve or adjust it; Tenants inherit the Landlord's setting and cannot change it.

FR-9: Auto-reschedule on completion. Marking a task instance complete automatically calculates and schedules the next due date based on its Frequency, counted from the actual completion date (not the original due date).

FR-10: Due/overdue push notifications. The system sends a push notification to relevant Members when a task instance becomes due or overdue.

FR-11: Fairness-based targeted notification. When completion attribution (FR-7) shows a Member has rarely or never performed completions for a recurring shared task relative to other Members, the system can target a reminder specifically to that Member.

FR-12: Landlord ad-hoc broadcast message. A Landlord can send a free-form reminder message to all Tenants of a specific Home.

FR-13: Landlord-controlled notification cadence. A Landlord can configure how strictly/often Tenants of a Home are reminded about due/overdue Must tasks, independent of the task's Frequency.

FR-14: Contextual quick-answer. Any task offers a "?" affordance that returns an immediate, task-specific answer to a how-to question, always with a visible AI-can-be-wrong / chemical-caution disclaimer.

FR-15: Escalate to full AI chat. From the quick-answer, a user can open a full conversational chat with the AI assistant for follow-up questions, retaining the originating task as context for at least the first follow-up.

FR-16: AI-generated onboarding guide. When a Landlord provisions a Home and invites Tenants, the system generates an onboarding guide explaining how the app works, tailored to that Home's unit type.

FR-17: Self-checkoff completion. Any Member can mark a task instance complete with a single action; no confirmation from another Member is required.

FR-18: Landlord-required Photo Evidence. A Landlord can mark a specific Must task as requiring Photo Evidence from Tenants, restricted to task types where completion is objectively visible without capturing sensitive or private content.

FR-19: Auto-approve with Landlord review, auto-replacing storage. Uploaded Photo Evidence auto-approves the task completion immediately; the photo remains accessible for Landlord review and is automatically replaced the next time the same task is completed (no accumulating history).

FR-20: Portfolio-level status dashboard. A Landlord with more than one Home sees a single view summarizing task status (on track / behind) per Home and per unit.

FR-21: Responsive layout across device classes. The web application renders a usable, complete layout on phone, tablet, and desktop viewport widths.

### NonFunctional Requirements

NFR1: Permission enforcement. Role-based restrictions (Tenant cannot alter Landlord-locked Must/Frequency settings; only Household Members/Landlords can adjust classification) must be enforced server-side, not only hidden in the UI (binds FR-3, FR-5, FR-8).

NFR2: Notification reliability. Push notifications (FR-10 to FR-13) must be delivered reliably enough that a Household Member or Tenant can trust the absence of a notification to mean "nothing due" — a missed notification undermines the product's core value proposition.

NFR3: Responsiveness. All core flows must remain fully usable at common phone, tablet, and desktop breakpoints (FR-21) — a stated v1 requirement, not a polish pass.

NFR4: AI chemical-answer disclaimer, no accuracy bound. The AI assistant can answer chemical-related how-to questions (for example, which cleaner suits which surface); every such answer must surface the AI-can-be-wrong disclaimer rather than being scoped out. No numeric accuracy bound is set for this round — the disclaimer is the product's chosen mitigation, not a claim of verified correctness (binds FR-14, FR-15).

NFR5: Photo Evidence privacy scoping. Photo Evidence is restricted by design to task types where completion is objectively visible without capturing sensitive or private content; each photo is auto-replaced on the next completion (no accumulating history); access is restricted to the Home's Landlord and the product's own support staff only — no other Tenant, other Landlord, or third party can view it (binds FR-18, FR-19).

NFR6: Tenant data visibility scoping. Tenant data (task history, Photo Evidence, completion records) is visible to that Tenant's Landlord by design but must not be visible to other Tenants or other Landlords outside the relevant Home.

### Additional Requirements

No starter/greenfield template tool is specified by Architecture — it instead defines a committed source tree (`frontend/`, `backend/`) to scaffold directly; Epic 1 Story 1 should set up this tree rather than running an external project generator.

- **Layering & permissions:** Routes never mutate data or call external services directly — every mutating/permission-sensitive operation flows through a domain-service layer (AD-3). Role lives on the User↔Home Membership join entity, never on the User account (AD-1) — one User can hold different Roles in different Homes. Every Home-scoped route resolves the caller's Role per-request via a `require_role(home_id, allowed_roles)` dependency that loads the Membership row — never from a JWT claim (AD-2).
- **Task completion:** One domain function (`complete_task_instance`) is the sole code path marking a Task instance complete, recording attribution, and triggering the FR-9 reschedule; it is idempotent on retried requests (AD-3).
- **AI service:** One backend AI service wraps every Gemini call (quick-answer, chat, onboarding-guide generation); every response is a structured object `{status: "ok" | "low_confidence" | "error", answer, disclaimer}` with the disclaimer always its own field (AD-4). The onboarding guide is generated once per Home at provisioning time and persisted, not regenerated per view (AD-4, FR-16).
- **Photo Evidence storage:** `PhotoEvidence` is 1:1 with `Task` (not `TaskInstance`); each task's photo is stored under a fixed key (`tasks/{task_id}/evidence.jpg`) in Supabase Storage, overwritten on each new upload — no per-completion history row (AD-5). Task types carry a system-seeded, non-Landlord-editable `photo_evidence_eligible` flag; the endpoint setting FR-18's requirement rejects the request server-side if the Task's type isn't flagged eligible (AD-6).
- **Auth:** Short-lived JWT access token returned in the login response body and kept only in React memory (never `localStorage`); long-lived refresh token as an `httpOnly`/`Secure`/`SameSite=None` cookie, exchanged only at a dedicated `/refresh` endpoint. CORS lists the exact Vercel origin with `allow_credentials=True` (never a wildcard); the generated API client sends every request with `credentials: "include"` (AD-7).
- **Due/notification job:** A dedicated `POST /internal/run-due-check` endpoint runs the due/overdue scan (FR-10, FR-11's fairness nudge); an external free cron service (cron-job.org) calls it every 10–14 minutes. The endpoint is safe to call concurrently/more often than scheduled — it tracks per-Task-Instance whether a notification was already sent for the current window (AD-8). Fairness-nudge rule: fire a targeted nudge to a Member with 0 completions in the last 3 instances of a recurring shared task, provided at least one other Member completed at least one of those 3 (AD-9, resolves PRD Open Question 4). Landlord broadcast (FR-12) is sent directly and synchronously on request, independent of the due-check cron (AD-14).
- **No real-time layer:** Freshness comes from TanStack Query refetching on mount/window-focus — no WebSocket/SSE infrastructure (AD-10).
- **Frontend data layer:** No component calls `fetch`/`axios` directly or holds server data in local `useState` — all server reads/writes go through TanStack Query hooks backed by one generated API client (from the backend's OpenAPI schema via `openapi-typescript`, never hand-written types). The self-checkoff mutation (FR-17) uses TanStack Query's optimistic-update pattern; the photo-evidence-upload mutation (FR-19) is deliberately pessimistic — the UI waits for the upload-and-auto-approve response before showing complete (AD-11).
- **PWA shell:** `frontend/` includes a `manifest.json` and a registered service worker from day one, plus one shared "Add to Home Screen" install-prompt component shown once per Member per device (tracked client-side) — required for Web Push to reach iOS Safari (iOS 16.4+ only supports Web Push for a Home-Screen-installed PWA) (AD-12, binds FR-10, FR-21).
- **Design tokens:** DESIGN.md's tokens are implemented once as CSS custom properties generated/copied from DESIGN.md's frontmatter — no component file contains a literal hex color, px size, or border-radius value, only `var(--...)` references (AD-13).
- **Naming/data conventions:** Entity names match the PRD Glossary verbatim (`Home`, `Member`, `Role`, `Task`, `TaskInstance`, `Frequency`, `PhotoEvidence`, `NotificationCadence` — never `User` for the Home-scoped actor). IDs are UUIDv4 everywhere. Dates/times are ISO 8601 UTC on the wire. Errors use FastAPI's default `{"detail": "..."}` shape; validation errors use the standard Pydantic 422 body.
- **Schema changes:** Every schema change is an Alembic migration committed to the repo — never a manual change against the shared Supabase instance; a schema change is announced to the other two developers before pushing it (single shared dev database, no isolation).
- **Deployment/infrastructure:** React/Vite SPA static build on Vercel; FastAPI/uvicorn on Render (free tier); Postgres + Storage bucket via Supabase (free tier); external cron via cron-job.org; Google Gemini API for AI. One shared environment covers both development and the course demo/submission — no separate staging.
- **Secrets:** Gemini key, VAPID keys, DB URL, JWT signing key via environment variables only, never committed.
- **Core entities (names/relationships only):** User, Membership (scoped to one Role per Home), Home, InviteLink (own validity state: token, target Role, used/expired/revoked, distinct from Membership), Task, TaskType (system-seeded catalog carrying `photo_evidence_eligible`), TaskInstance, MemberCompletion (attribution), PhotoEvidence (per-Task), NotificationCadenceSetting (Landlord Homes), PushSubscription (per User, one per device). `[ASSUMPTION carried from Architecture, confirm with team before building]`: invite link default policy is single-use + 7-day expiry, regenerable by whoever can invite.
- **Explicitly deferred by Architecture (flag for sprint planning, not pre-decided):** observability/logging strategy (left to Render/Supabase defaults + basic logging); automated testing strategy (pytest/Vitest suggested, not binding); rate-limiting/abuse protection on AI endpoints (none beyond the one-service chokepoint + Gemini's own free-tier cap); internationalization infrastructure (not needed — Norwegian-only v1 per UX).

### UX Design Requirements

**Design tokens**
UX-DR1: Implement DESIGN.md's color tokens (primary `#6E62CC`, secondary `#B67F98`, accent `#5B96B1`, surface-base, surface-raised, ink-primary, ink-secondary, success, warning, danger, must-badge, should-badge, focus-ring) as CSS custom properties generated from DESIGN.md's frontmatter — no component may hardcode a hex value (AD-13).
UX-DR2: Implement the typography tokens (`display` 1.5rem/700, `title` 1.125rem/700, `body` 0.9375rem/500, `meta` 0.78125rem/500, `badge` 0.625rem/700 uppercase-tracked) in `rem` units against a 16px root, using the system font stack (`-apple-system`/`BlinkMacSystemFont`/Segoe UI/Roboto) — no custom webfont, no fixed-px type scale.
UX-DR3: Implement the spacing scale (4/8/12/16/24/32/48px) and rounded-corner tokens (`sm` 8px / `md` 14px / `lg` 20px / `full` pill) as shared tokens; reserve the pill shape for badges, status tags, and primary buttons only.

**Reusable components (behavioral specs, names match DESIGN.md verbatim)**
UX-DR4: Primary button — pill shape, one dominant action per screen; default/pressed (8% darker overlay)/disabled (`ink-secondary` background)/in-flight ("Sender…" text swap, never a spinner alone) states; disabled state carries an accessible reason via `aria-describedby` when the disable condition is non-obvious.
UX-DR5: Task card — checkbox + title + inline Must/Should badge + due date below; checkbox and row are two independently focusable tap targets, checkbox first in tab order, row second (row tap → Task Detail, checkbox → direct self-checkoff per FR-17); completed state shows filled checkbox, strikethrough title, due-date line replaced by a success-colored completion note.
UX-DR6: Must/Should badge — pill shape, badge typography, always renders the text label ("Must"/"Should") inline with the task title; color is reinforcement only, never the sole cue.
UX-DR7: Status tag (Portfolio row's overdue/on-track indicator) — pill shape, always carries a text label ("Forsinket"/"Alt i orden"), never color alone; danger tag if any Must task is overdue in that Home, success tag if fully on-track.
UX-DR8: Portfolio row — tighter padding than task card, `sm` radius, building name + unit count + the status tag (UX-DR7); tap navigates to that Home's Landlord Home Admin.
UX-DR9: Quick-answer popover — anchored to the task's "?" affordance, opens inline (not a full navigation); loading state is a skeleton line (not a spinner) announced via `aria-live="polite"`; the arriving answer is announced the same way; always shows the FR-14 disclaimer beneath the answer; a second tap ("Ask more") pushes into AI Chat carrying the task as context (FR-15).
UX-DR10: Photo evidence upload — renders only when FR-18 applies to the specific task; camera/file-picker affordance; upload auto-approves the task immediately with no pending/review state (FR-19); every uploaded photo requires an accessible description on save (for example, "Bildebevis lastet opp av Martin, 29. sep" — never the file input's default filename).
UX-DR11: Invite link control — renders only for roles permitted to invite (any Household Member or a Landlord); for a Tenant, the control is absent from the layout entirely, not present-and-disabled.
UX-DR12: Broadcast composer — free-form text field with a send action (FR-12); confirms with recipient count ("Sendt til N leietakere") rather than naming individuals; the send confirmation is announced via `aria-live="polite"` for screen-reader users, not shown only as a visual toast.
UX-DR13: Frequency/Must toggle — two visual/behavioral states: *editable* (Household Member/Landlord — white surface, solid border) and *locked* (Tenant — `surface-base` fill, dashed border, lock glyph + "Satt av utleier" label). The locked state stays focusable, implemented with `aria-readonly="true"` + `aria-describedby` pointing at the "Satt av utleier" text — never the native `disabled` attribute.

**Information architecture / navigation**
UX-DR14: Implement the 9-surface IA with its stated role access: Sign in/Register (all); Create Home + Task Setup step reviewing/adjusting recommended Must/Should tasks (Household Member, Landlord); Task Overview, Task Detail, AI Chat (Household Member, Tenant, Landlord per-Home); Members & Invite (any Household Member, Landlord only — not Tenants); Landlord Portfolio Dashboard (Landlord, shown only when they own ≥2 Homes); Landlord Home Admin (Landlord — bulk Must/Should, Frequency, Photo Evidence requirement, notification cadence, broadcast composer); Settings/Profile (all).
UX-DR15: On Task Detail, Household Members get the Must/Should classification and Frequency fields directly editable inline (FR-5, FR-8) with no separate admin screen; Tenants see the same fields rendered via the locked Frequency/Must toggle (UX-DR13).
UX-DR16: A first-time Tenant's Task Overview visit surfaces the AI-generated onboarding guide (FR-16) as a one-time dismissible card at the top of the list — not a separate surface — re-reachable later from Settings if dismissed.
UX-DR17: No in-app notification inbox — a push notification deep-links straight to Task Detail (FR-10/FR-11/FR-12 stay push-only).

**State patterns (each with its specified copy/treatment, not left generic)**
UX-DR18: Cold load (Task Overview, Landlord Portfolio Dashboard) — 3–4 skeleton placeholder cards/rows while data loads, distinct from the Empty state.
UX-DR19: Task due soon — due date in `warning` color, bold, plus the word "Snart forfall" (never color/weight alone).
UX-DR20: Task overdue — due date in `danger` color plus the word "Forfalt" (deliberately distinct wording from the Must badge's "Must" label).
UX-DR21: Task completed — checkbox filled, title strikethrough, due-date line replaced by a success-colored completion note ("Fullført i dag" / "Fullført av Peter").
UX-DR22: Empty task list — "Ingen oppgaver akkurat nå — nyt det! 🎉" (household) or "Ingen aktive oppgaver i dette hjemmet." (landlord Home Admin) — never an illustration with no text.
UX-DR23: Invalid or expired invite link — "Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra [utleier/husstandsmedlem]." — never a generic 404.
UX-DR24: Failed login — inline field-level error, not a full-page reload; message never confirms or denies whether an email/username exists.
UX-DR25: Duplicate registration attempt via invite link — if the invited email already has an account, offer "Logg inn i stedet" rather than a flat error.
UX-DR26: Tenant views a locked field — rendered read-only with visible lock affordance + "Satt av utleier" label via `aria-readonly` — never a disabled-looking grayed control with no explanation.
UX-DR27: AI answer pending — short inline skeleton-line loading state announced via `aria-live="polite"`, not a full-screen spinner.
UX-DR28: AI cannot answer / low confidence — says so plainly ("Usikker på svaret her — spør gjerne på nytt eller sjekk med noen andre") rather than guessing silently; the FR-14 disclaimer stays visible regardless of confidence.
UX-DR29: Photo evidence uploaded — immediate auto-approve confirmation ("Lastet opp — oppgaven er fullført"), never a "pending landlord review" state.
UX-DR30: Form submission failure (invite generation, cadence/toggle save, broadcast send) — inline error at the field or action with a retry affordance, distinct from the offline/network-error state.
UX-DR31: No push permission granted — Settings row shows current status plainly; if denied, Task Overview shows a single dismissible inline note (not a modal), never a repeating nag.
UX-DR32: Offline/network error on a pending optimistic action (for example, a checkbox tap) — local optimistic update where safe, with a quiet retry, no blocking error modal for a transient blip.

**Interaction primitives**
UX-DR33: Tap-to-act throughout; the Task card checkbox is the one primitive that completes a task directly without opening Task Detail.
UX-DR34: "?" is always a tap-to-reveal inline popover, never hover-only (touch-first).
UX-DR35: Long-press is unused/reserved — no custom long-press menus.
UX-DR36: Pull-to-refresh on Task Overview and Landlord Portfolio Dashboard only.
UX-DR37: No gamification mechanics anywhere in the product (no points, streaks, or leaderboards) — a deliberate rejection of the pattern used by Sweepy/OurHome/Tody.

**Accessibility**
UX-DR38: Honor WCAG 1.4.4/1.4.10 zoom and reflow — `rem`-based type scale, single-column reflow at 320 CSS px width / 400% zoom on every surface, including the two-column Landlord Portfolio Dashboard.
UX-DR39: Visible 2px focus-ring outline (≥4.3:1 contrast against both surface tones) on every interactive element, including split focus targets (task-card checkbox and row as separate stops) — never suppressed for aesthetic reasons.
UX-DR40: Tap targets ≥44×44px throughout.
UX-DR41: Focus order follows visual reading order on every surface — task list top-to-bottom, Must tasks before Should tasks (matching FR-6 exactly).
UX-DR42: Every interactive element carries an accessible label describing both the action and current state (the checkbox: "Merk 'Vask bad' som fullført"; the quick-answer popover and AI Chat message stream both `aria-live="polite"` on new content; the broadcast composer's send confirmation; uploaded photo evidence's accessible description).
UX-DR43: `prefers-reduced-motion` is honored for every transition and loading skeleton — the resulting state still appears, just without the animated transition.

**Responsive & platform**
UX-DR44: Implement the committed breakpoints — phone up to 599px, tablet 600–1023px, desktop 1024px and above — mobile-first.
UX-DR45: Task Overview and Task Detail remain single-column at every width. The Landlord Portfolio Dashboard is the one surface that gains a second column (building list + detail split) at the tablet breakpoint and above.
UX-DR46: At 320 CSS px width / 400% browser zoom, every surface — including the two-column Dashboard — collapses to single-column with no horizontal scroll.
UX-DR47: Ship as an installable PWA from day one (`manifest.json` + registered service worker), with a shared "Add to Home Screen" install-prompt shown once per Member per device.

**Voice and tone / brand**
UX-DR48: All copy is Norwegian-only in v1, including AI-generated answers — no `lang` mixing.
UX-DR49: Household-register copy is warm and a little playful ("Bra jobba — badet er ferdig! 🎉", "Peter tok denne i dag."); Landlord-register copy is neutral and information-first ("Bygg A — 1 forsinket must-oppgave.", "Sendt til 4 leietakere.") — both drawn from the same token set and component library, never a separate visual theme.
UX-DR50: Never frame a missed task as a failure or shame the person who didn't do it, in either register.

### FR Coverage Map

FR-1: Epic 1 - Create a Home (Household or Landlord)
FR-2: Epic 1 - Invite members via link, scoped by Home type and inviter role
FR-3: Epic 1 - Assign and enforce Member Roles (server-side)
FR-4: Epic 2 - Recommend Must/Should classification (incl. at Home-creation Task Setup)
FR-5: Epic 2 - Adjust classification (Household Members and Landlords only)
FR-6: Epic 2 - Must-first ordering of the task list
FR-7: Epic 2 - Shared completion status with per-member attribution
FR-8: Epic 2 - Recommend and set task Frequency
FR-9: Epic 2 - Auto-reschedule on completion
FR-10: Epic 3 - Due/overdue push notifications
FR-11: Epic 3 - Fairness-based targeted notification
FR-12: Epic 3 - Landlord ad-hoc broadcast message
FR-13: Epic 3 - Landlord-controlled notification cadence
FR-14: Epic 5 - Contextual quick-answer ("?")
FR-15: Epic 5 - Escalate to full AI chat
FR-16: Epic 5 - AI-generated onboarding guide
FR-17: Epic 2 - Self-checkoff completion
FR-18: Epic 4 - Landlord-required Photo Evidence
FR-19: Epic 4 - Auto-approve with Landlord review, auto-replacing storage
FR-20: Epic 6 - Portfolio-level status dashboard
FR-21: Epic 1 (foundation: responsive app shell, design tokens, PWA) - Epic 6 (dashboard-specific two-column breakpoint behavior)

## Epic List

### Epic 1: Foundation — Accounts, Homes & Roles
Users can register and log in, create a Home (Household or Landlord), invite others via a scoped link, and have their Role (Household Member, Landlord, Tenant) correctly enforced server-side everywhere. This epic also establishes the responsive, installable app shell (design tokens as CSS custom properties per AD-13, PWA manifest + service worker + install prompt per AD-12, phone/tablet/desktop breakpoints per FR-21/UX-DR44) that every later epic's screens build on, plus the domain-service/permission-dependency layering (AD-1, AD-2, AD-3 scaffold) and JWT auth split (AD-7).
**FRs covered:** FR-1, FR-2, FR-3 (+ FR-21 at the shell level)

### Epic 2: Task Management Core Loop
Household Members, Tenants, and Landlords can see a Must-first task list for their Home, (for Household Members/Landlords) adjust a task's Must/Should classification and Frequency inline, self-checkoff a task in one tap, see shared completion status update immediately with per-member attribution, and have the next occurrence auto-scheduled from the actual completion date. Includes the Task Setup step at Home creation (reviewing/accepting the app's recommended task list). Implements the single `complete_task_instance` domain function (AD-3) that Epic 4 (Photo Evidence) will later extend.
**FRs covered:** FR-4, FR-5, FR-6, FR-7, FR-8, FR-9, FR-17

### Epic 3: Notifications
Members receive a push notification when a task becomes due or overdue, with fairness-based targeting when one Member has fallen behind on a shared task; Landlords can send ad-hoc broadcast messages to their Tenants and configure how strictly Tenants are reminded. Implements the external cron-driven due-check endpoint (AD-8), the fairness-nudge rule (AD-9), and the direct/synchronous broadcast path (AD-14).
**FRs covered:** FR-10, FR-11, FR-12, FR-13

### Epic 4: Photo Evidence
A Landlord can flag a specific Must task (restricted to system-eligible task types) as requiring Photo Evidence; a Tenant uploads a photo from their phone and the task auto-approves immediately, with the photo staying available for Landlord review and being auto-replaced on the next completion. Extends Epic 2's completion domain function and photo-eligibility gating (AD-5, AD-6).
**FRs covered:** FR-18, FR-19

### Epic 5: AI Assistant
Any Member can tap "?" on a task for an immediate, disclaimer-carrying how-to answer, escalate to a full AI chat for follow-up questions, and a new Tenant receives an AI-generated onboarding guide tailored to their Home's unit type when they join. Implements the single server-mediated AI service (AD-4) wrapping all Gemini calls behind one structured response shape.
**FRs covered:** FR-14, FR-15, FR-16

### Epic 6: Landlord Portfolio Dashboard
A Landlord who owns more than one Home sees a single aggregated view of on-track/behind status across all their Homes and units, letting them triage without a site visit — including the dashboard's own tablet-and-up two-column (list + detail) responsive behavior.
**FRs covered:** FR-20 (+ FR-21 dashboard-specific behavior)

## Epic 1: Foundation — Accounts, Homes & Roles

Users can register and log in, create a Home (Household or Landlord), invite others via a scoped link, and have their Role correctly enforced server-side everywhere — on top of a responsive, installable app shell with DESIGN.md's tokens wired in from the start.

`[ASSUMPTION carried from PRD Open Question 3 / EXPERIENCE.md's Foundation note, unresolved at the PRD level]`: v1 does not design a Home-switcher UI. A Landlord may own and switch between multiple Homes via the Portfolio Dashboard (Epic 6) — that mechanism is Landlord-specific and already scoped. A Household Member or Tenant is assumed to belong to at most one Home for the main self-service flow (Story 1.3); nothing technically prevents them from also accepting a second invite link (Story 1.4) into another Home, but no UI exists for switching between multiple simultaneous non-Landlord Memberships. If this turns out to matter for the team's actual usage, revisit before Epic 1 is built — it is a scope decision, not an oversight.

### Story 1.1: Project Scaffold, Design Tokens & Responsive App Shell

As a visitor opening the app for the first time,
I want it to load with the product's visual identity and work well on my device,
So that I can trust and use it comfortably regardless of phone/tablet/desktop.

**Acceptance Criteria:**

**Given** a visitor opens the app on a phone-width viewport (≤599px)
**When** the page loads
**Then** it renders single-column using DESIGN.md's tokens as CSS custom properties (no hardcoded hex/px in component code), with no horizontal scroll at 320 CSS px / 400% zoom

**Given** the same app on tablet (600–1023px) and desktop (≥1024px)
**When** the page loads
**Then** the shared shell adapts at the committed breakpoints without layout breakage

**Given** a visitor on a mobile browser
**When** they open the app
**Then** a `manifest.json` and registered service worker are present, and a shared "Add to Home Screen" install-prompt shows once per device (client-side tracked) — not repeated on every visit

**Given** the backend scaffold
**When** a developer runs the FastAPI service locally
**Then** a health-check endpoint responds 200, Alembic is wired for migrations, and the source tree matches the committed layout (`backend/app/{routes,domain,permissions,models}`, `frontend/src/{api,components,routes,styles}`)

**Given** any frontend component
**When** its styling is inspected
**Then** it references only `var(--...)` tokens for color/radius/spacing (AD-13)

**Given** the app's type scale
**When** any text renders
**Then** sizes are specified in `rem` against a 16px root using the system font stack (`-apple-system`/`BlinkMacSystemFont`/Segoe UI/Roboto) — no custom webfont, no fixed-px sizing (UX-DR2), and the `{rounded.full}` pill shape is reserved for badges, status tags, and primary buttons only (UX-DR3)

**Given** the global stylesheet
**When** `prefers-reduced-motion: reduce` is set
**Then** all transition/animation durations are overridden to zero

**Given** any interactive element in the shell
**When** it receives keyboard focus
**Then** a 2px focus-ring outline with 2px offset is visible and never suppressed

**Given** any tap target in the shell
**When** measured
**Then** it is at least 44×44px

**Given** the shared primary-button component used throughout the app
**When** its states are inspected
**Then** default, pressed (8% darker overlay), disabled (`ink-secondary` background), and in-flight ("Sender…" text swap, never a spinner alone) are all implemented, with the disabled state carrying an accessible reason via `aria-describedby` when the disable condition is non-obvious (UX-DR4)

### Story 1.2: Account Registration & Login

As a new user,
I want to register an account and log in,
So that I can access my Homes securely.

**Acceptance Criteria:**

**Given** a visitor with no account
**When** they submit a valid email + password
**Then** a User row is created and they receive a short-lived JWT access token in the response body (kept only in frontend memory) plus an httpOnly/Secure/SameSite=None refresh cookie (AD-7)

**Given** a registered user
**When** they submit correct credentials
**Then** they receive a fresh access token + refresh cookie and land inside the app

**Given** a registered user
**When** they submit an incorrect password or unknown email
**Then** an inline field-level error displays without a full-page reload, and the message never reveals whether the email exists

**Given** an expired access token
**When** a request is made
**Then** the frontend calls `/refresh` using the httpOnly cookie to get a new access token transparently, without forcing re-login

**Given** the backend CORS configuration
**When** a request arrives from the deployed Vercel origin
**Then** it is accepted with `allow_credentials=True` against that exact origin; other origins are rejected

### Story 1.3: Create a Home (Household or Landlord)

As an authenticated user with no Home yet,
I want to create a Home as either a Household Home or a Landlord Home,
So that I can start organizing tasks for my living situation or property.

**Acceptance Criteria:**

**Given** an authenticated user with no existing Home
**When** they choose "Household Home"
**Then** a Home is created and they become a Household Member via a Membership row — same standing as any later invitee (FR-1)

**Given** an authenticated user with no existing Home
**When** they choose "Landlord Home"
**Then** a Home is created and they become its Landlord via a Membership row, supporting full configuration with zero Tenants present

**Given** the Membership entity
**When** inspected
**Then** Role is stored on Membership, never on User — the same User can later hold a different Role in a different Home (AD-1)

**Given** a user whose only Membership(s) are Household Member or Tenant
**When** they open the app
**Then** they are not re-prompted to create another Home through this flow (v1 assumption: a Household Member/Tenant has at most one self-service "create a Home" entry point — see the Epic 1 note on PRD Open Question 3)

**Given** a Landlord who already owns one or more Homes
**When** they choose to create another Home (for example, from the Portfolio Dashboard, per UJ-2)
**Then** the Create Home flow runs again and a new Landlord Home is added to their portfolio — Landlords are never blocked from creating additional Homes, since Epic 6's Portfolio Dashboard depends on this being possible

### Story 1.4: Invite Members via Scoped Link & Accept Invite

As a Household Member or Landlord,
I want to generate an invite link scoped to my Home,
So that I can bring others in with the right Role.

**Acceptance Criteria:**

**Given** a Household Home
**When** any Household Member generates an invite link
**Then** it is scoped to that Home and Role "Household Member" (FR-2)

**Given** a Landlord Home
**When** the Landlord generates an invite link
**Then** it is scoped to that Home and Role "Tenant"

**Given** a Landlord Home
**When** a Tenant calls the invite-generation endpoint directly
**Then** the server rejects it

**Given** a valid, unused invite link
**When** a user without an account opens it
**Then** they are routed to registration and auto-linked to that Home with the link's Role on completion

**Given** a valid invite link
**When** a logged-in user without that Home opens it
**Then** they see a "join Home" action, and joining creates their Membership with the link's Role

**Given** an expired or already-used invite link
**When** anyone opens it
**Then** they see "Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra [utleier/husstandsmedlem]" rather than a generic 404

**Given** an invite link whose target email already has an account
**When** that person opens it while logged out
**Then** they are offered "Logg inn i stedet" rather than a flat error

**Given** invite-link generation fails server-side
**When** the Member sees the result
**Then** an inline error with a retry affordance shows at the action — not a silent failure (UX-DR30)

### Story 1.5: View Home Members List & Enforce Role-Based Permissions

As a Member of a Home,
I want to see who else is in my Home and trust that permissions are enforced server-side,
So that Tenant-locked actions can never be bypassed.

**Acceptance Criteria:**

**Given** any authenticated Member
**When** they open Members & Invite
**Then** they see every current Member and their Role

**Given** a Tenant viewing Members & Invite
**When** the screen renders
**Then** the invite-link control is absent entirely (not disabled)

**Given** any Home-scoped route
**When** a request includes `home_id`
**Then** `require_role(home_id, allowed_roles)` loads the caller's Membership row for `(user_id, home_id)` and checks that row's Role — never a JWT claim, body, or query param (AD-2)

**Given** a user with a Membership in Home A but not Home B
**When** they call a Home B route
**Then** the request is rejected regardless of their Role in Home A

**Given** a Home with only Household Members
**When** inspected
**Then** it never also contains a Landlord/Tenant row, and vice versa

## Epic 2: Task Management Core Loop

Household Members, Tenants, and Landlords can see a Must-first task list, adjust classification/Frequency where permitted, self-checkoff a task in one tap with shared status and attribution, and have the next occurrence auto-scheduled from the actual completion date.

### Story 2.1: Task Setup at Home Creation

As a user setting up a new Home,
I want to review the app's recommended Must/Should task list (with recommended Frequency) and accept or adjust it,
So that my Home starts with a sensible, personalized task list instead of an empty one.

**Acceptance Criteria:**

**Given** a newly created Home (Household or Landlord)
**When** the Task Setup step loads
**Then** the app displays a recommended list of Tasks, each with a default Must or Should classification based on task type (FR-4) and a recommended Frequency (FR-8)

**Given** the Task Setup step
**When** the user accepts the list as-is
**Then** every recommended Task is created for that Home with its app-recommended classification and Frequency — never left unclassified

**Given** the Task Setup step
**When** the user adjusts a Task's classification or Frequency before confirming
**Then** the Task is created with the user's override instead of the app's recommendation

**Given** Task Setup completes
**When** the user is redirected
**Then** they land on Task Overview for that Home

**Given** a Landlord pre-provisioning a Home before any Tenant has joined
**When** they complete Task Setup
**Then** the Tasks are created and ready, independent of Tenant presence

### Story 2.2: Must-First Task Overview

As a Household Member, Tenant, or Landlord,
I want to see my Home's tasks with Must tasks listed first,
So that I always know what's non-negotiable before what's optional.

**Acceptance Criteria:**

**Given** a Home with both Must and Should tasks due
**When** a Member opens Task Overview
**Then** all Must tasks render above any Should task, regardless of due date (FR-6)

**Given** multiple tasks within the same tier
**When** the list renders
**Then** they are ordered by due date within that tier

**Given** Task Overview is loading
**When** data hasn't arrived yet
**Then** 3-4 skeleton placeholder rows render, distinct from the Empty state

**Given** a Home with no tasks due
**When** Task Overview finishes loading
**Then** it shows "Ingen oppgaver akkurat nå — nyt det! 🎉" (household) or the landlord-admin equivalent, never a bare illustration with no text

**Given** a task card
**When** the checkbox and the row are both present
**Then** they are two independently focusable tap targets in that order in the tab sequence (checkbox first), with the row tap navigating to Task Detail

**Given** a task's Must/Should badge
**When** rendered
**Then** it always carries the text label ("Must"/"Should") inline with the title — never color alone

**Given** a task due soon
**When** its due date renders
**Then** it shows in warning color, bold weight, and the word "Snart forfall" — never color/weight alone (UX-DR19)

**Given** an overdue task
**When** its due date renders
**Then** it shows in danger color and the word "Forfalt" — deliberately distinct wording from the Must badge's "Must" label (UX-DR20)

**Given** Task Overview
**When** the Member pulls down to refresh
**Then** the list refetches — pull-to-refresh is supported on this surface (UX-DR36)

**Given** Task Overview's focus order
**When** a keyboard/screen-reader user tabs through the list
**Then** it matches the visual reading order — Must tasks before Should tasks, top to bottom (UX-DR41)

### Story 2.3: Adjust Task Classification & Frequency

As a Household Member or Landlord,
I want to change a task's Must/Should classification and Frequency,
So that the task list matches my Home's real priorities, while Tenants see a stable, locked view.

**Acceptance Criteria:**

**Given** a Household Member or Landlord viewing Task Detail
**When** they change a task's Must/Should classification
**Then** the change persists and is immediately reflected to all Members of that Home, including Tenants (read-only) (FR-5)

**Given** a Tenant
**When** they attempt to change classification via the API directly
**Then** the request is rejected server-side, not just hidden in the UI

**Given** a Household Member or Landlord viewing Task Detail
**When** they adjust a task's Frequency
**Then** the new Frequency is saved and governs the next auto-reschedule (FR-8)

**Given** a Tenant on a Landlord Home's task
**When** they attempt to change Frequency
**Then** the request is rejected server-side

**Given** a Tenant viewing Task Detail
**When** the Frequency/Must toggle renders
**Then** it shows the locked visual state (dashed border, lock glyph, "Satt av utleier" label) implemented with `aria-readonly="true"` + `aria-describedby` — never the native `disabled` attribute

**Given** a Household Member or Landlord viewing Task Detail
**When** the Frequency/Must toggle renders
**Then** it shows the editable visual state and is directly editable inline, with no separate admin screen required

**Given** a classification or Frequency save fails server-side
**When** the Household Member or Landlord sees the result
**Then** an inline error with a retry affordance shows at the field — not a silent failure (UX-DR30)

### Story 2.4: Self-Checkoff Completion with Shared Status & Attribution

As any Member of a Home,
I want to mark a task instance complete with one tap and trust that it's recorded,
So that my housemates immediately see it's done without me needing to tell them.

**Acceptance Criteria:**

**Given** any Member
**When** they tap a task card's checkbox
**Then** the task instance is marked complete in a single action with no confirmation step required (FR-17)

**Given** a shared Task instance just completed by one Member
**When** any other Member of the Home opens Task Overview
**Then** it shows as complete immediately (FR-7)

**Given** a completion event
**When** it's recorded
**Then** the completing Member's identity is stored alongside it, queryable per Home over time

**Given** a completed task card
**When** rendered
**Then** the checkbox is filled, the title is struck through, and the due-date line is replaced by a success-colored completion note (for example, "Fullført i dag" / "Fullført av Peter")

**Given** a one-person Household Home (Sara, UJ-4)
**When** she completes a task
**Then** the completion note never references a second person ("Fullført i dag," not "Fullført av deg")

**Given** a personal-space task (for example, a Member's own room)
**When** the product's scope is checked
**Then** no such task exists in the app — personal-space tasks remain out of scope, self-managed outside the app

**Given** a checkbox tap while offline or on a flaky connection
**When** the request can't complete immediately
**Then** the UI applies the optimistic update locally and quietly retries — no blocking error modal for a transient network blip (UX-DR32)

**Given** a task-card checkbox
**When** a screen-reader user focuses it
**Then** it announces an accessible label describing the action and task (for example, "Merk 'Vask bad' som fullført") (UX-DR42)

### Story 2.5: Auto-Reschedule on Completion

As any Member completing a recurring task,
I want the next occurrence scheduled automatically,
So that I never have to remember to set a reminder for an irregular task myself.

**Acceptance Criteria:**

**Given** a task instance with a Frequency of N days
**When** it's marked complete
**Then** the next instance is scheduled N days from the actual completion date — not from the original due date (FR-9)

**Given** a task completed 2 days late with a 30-day Frequency
**When** the next instance is calculated
**Then** it is scheduled a full 30 days from the completion date, not a shortened interval

**Given** the single `complete_task_instance` domain function
**When** either the checkbox endpoint (FR-17) or (in a later epic) the photo-upload endpoint calls it
**Then** both paths produce identical completion, attribution, and reschedule behavior with no duplicated logic (AD-3)

**Given** an already-completed task instance
**When** `complete_task_instance` is called again on it (for example, a retried request)
**Then** it returns the existing completion state unchanged rather than re-attributing or re-scheduling

## Epic 3: Notifications

Members receive a push notification when a task becomes due or overdue, with fairness-based targeting when one Member has fallen behind; Landlords can send ad-hoc broadcasts and configure how strictly Tenants are reminded.

### Story 3.1: Push Notification Permission & Device Registration

As a Member using the app on a device,
I want to grant push notification permission and have my device registered,
So that I can actually receive due/overdue reminders and broadcasts.

**Acceptance Criteria:**

**Given** a Member opens Settings
**When** they view it
**Then** their current push-permission status (granted/denied/not-yet-asked) is shown plainly

**Given** a Member grants push permission
**When** the browser confirms
**Then** a PushSubscription (endpoint + keys) is created and linked to that User and that specific device

**Given** a Member uses a second device
**When** they grant permission there too
**Then** a second, independent PushSubscription is stored for that User — one per device, not overwriting the first

**Given** a Member denies push permission
**When** they later reach their first due task contextually
**Then** Task Overview shows a single dismissible inline note explaining that reminders won't arrive — never a repeating nag, never a modal

### Story 3.2: Due/Overdue Push Notifications via Due-Check Job

As a Member with a task due or overdue,
I want to be notified by push without having to check the app myself,
So that I never silently miss a task.

**Acceptance Criteria:**

**Given** a dedicated `POST /internal/run-due-check` endpoint
**When** it is called
**Then** it scans for task instances that are due or overdue and sends a push notification to the relevant Member(s) (FR-10)

**Given** an external cron service calling this endpoint every 10-14 minutes
**When** it fires on schedule
**Then** the due/overdue scan runs without needing an in-process scheduler (AD-8)

**Given** the endpoint is called twice in quick succession (concurrent or overlapping triggers)
**When** both calls scan the same due/overdue window
**Then** no Member receives a duplicate notification for the same task instance and window

**Given** a Member receives a due/overdue push notification
**When** they tap it
**Then** it deep-links directly to that task's Task Detail — no in-app notification inbox exists

### Story 3.3: Fairness-Based Targeted Notification

As a Member who already did a shared recurring task multiple times,
I want the reminder to go to whoever hasn't done it, not to everyone,
So that completion feels fair rather than me nagging my housemates.

**Acceptance Criteria:**

**Given** a recurring shared task where Member A completed the last 3 instances and Member B completed 0 of those 3
**When** the due-check job runs
**Then** a targeted nudge notification is sent to Member B specifically, not broadcast to the whole Home (FR-11, AD-9)

**Given** a recurring shared task where no Member has completed any of the last 3 instances
**When** the due-check job runs
**Then** the fairness nudge does not fire — the regular due/overdue notification still applies instead

**Given** Martin (UJ-3) receives a fairness-targeted nudge
**When** he reads it
**Then** the copy is indistinguishable in tone from a normal due/overdue reminder — no "you're the only one" framing

### Story 3.4: Landlord Ad-Hoc Broadcast Message

As a Landlord,
I want to send a free-form message to all Tenants of one Home right away,
So that I can flag something without waiting for the next scheduled check.

**Acceptance Criteria:**

**Given** a Landlord viewing Landlord Home Admin
**When** they compose and send a broadcast message
**Then** it is delivered as a push notification to every Tenant Member of that Home (FR-12)

**Given** the broadcast is sent
**When** it is processed
**Then** it is sent directly and synchronously by the broadcast endpoint — independent of and not waiting on the due-check cron cadence (AD-14)

**Given** a successful send
**When** the composer confirms
**Then** it shows the recipient count ("Sendt til N leietakere") rather than naming individuals, announced via `aria-live="polite"`

**Given** the broadcast send fails server-side
**When** the Landlord sees the result
**Then** the composer shows an inline error with a retry affordance rather than silently discarding the message

### Story 3.5: Landlord-Controlled Notification Cadence

As a Landlord,
I want to configure how strictly Tenants of a Home are reminded about due/overdue Must tasks,
So that I can match reminder pressure to how seriously that property needs it.

**Acceptance Criteria:**

**Given** a Landlord on Landlord Home Admin
**When** they change the notification cadence setting for a Home
**Then** it is saved and governs how often Tenants of that Home receive due/overdue reminders going forward (FR-13)

**Given** a cadence change
**When** it takes effect
**Then** it does not alter any task's underlying Frequency (FR-8/FR-9) — the two remain independent

**Given** a Tenant
**When** they attempt to change their Home's notification cadence
**Then** the request is rejected server-side — cadence is Landlord-only

**Given** a cadence save fails server-side
**When** the Landlord sees the result
**Then** an inline error with a retry affordance shows at the action — not a silent failure (UX-DR30)

## Epic 4: Photo Evidence

A Landlord can flag a specific Must task (restricted to system-eligible task types) as requiring Photo Evidence; a Tenant uploads a photo and the task auto-approves immediately, with the photo staying available for Landlord review and being auto-replaced on the next completion.

### Story 4.1: Landlord Requires Photo Evidence on Eligible Must Tasks

As a Landlord,
I want to require Photo Evidence on specific Must tasks whose completion is objectively visible,
So that I can trust completion was actually done without visiting in person.

**Acceptance Criteria:**

**Given** a Task type flagged `photo_evidence_eligible` in the system-seeded catalog
**When** a Landlord sets the Photo Evidence requirement on a Must task of that type
**Then** the requirement is saved (FR-18)

**Given** a Task type NOT flagged eligible
**When** a Landlord (or a direct API call) attempts to set the Photo Evidence requirement on it
**Then** the server rejects the request — eligibility is enforced in the data layer, not just hidden in the UI (AD-6)

**Given** the Photo Evidence requirement
**When** set
**Then** it is an explicit per-task Landlord setting, not a system-wide default — other Must tasks on the same Home remain unaffected

**Given** a Household Member (non-Landlord) Home
**When** Photo Evidence is considered
**Then** no Photo Evidence requirement option is exposed at all — that tier remains fully trust-based

### Story 4.2: Tenant Uploads Photo Evidence with Immediate Auto-Approval

As a Tenant completing a task that requires Photo Evidence,
I want to upload a photo and have the task marked done right away,
So that I'm never blocked waiting on my Landlord.

**Acceptance Criteria:**

**Given** a Must task flagged as requiring Photo Evidence
**When** a Tenant attempts to mark it complete without an attached photo
**Then** the action is blocked — a photo is required

**Given** a Tenant uploads a photo via camera or file picker
**When** the upload completes
**Then** the task is auto-approved and marked complete immediately — no pending/review state is ever shown (FR-19)

**Given** the photo-upload mutation
**When** it is in flight
**Then** the UI waits for the upload-and-auto-approve response before showing complete (pessimistic, not optimistic) — because an upload has a real failure mode a checkbox tap doesn't (AD-11)

**Given** the upload
**When** it completes
**Then** it requires an accessible description saved alongside it (for example, "Bildebevis lastet opp av Martin, 29. sep") — never the raw filename

**Given** the upload fails (bad connection)
**When** the failure occurs
**Then** the upload control shows a retry — never a silent failure that leaves the task looking incomplete for an unclear reason

**Given** this same upload completes the task
**When** the underlying completion path is inspected
**Then** it calls the same `complete_task_instance` domain function as the plain checkbox (Epic 2.5's AD-3), not a separate/duplicated completion path

### Story 4.3: Landlord Reviews Evidence & Auto-Replacing Photo Storage

As a Landlord,
I want to see the current photo evidence for a task and trust old photos don't pile up or leak,
So that I can review after the fact without the system becoming a privacy liability.

**Acceptance Criteria:**

**Given** a Tenant has uploaded Photo Evidence for a task
**When** the Landlord opens that task afterward
**Then** they can retrieve and view the current photo (FR-19)

**Given** a task's photo is stored
**When** inspected
**Then** it lives under a fixed, server-computed key (`tasks/{task_id}/evidence.jpg`) tied to the Task, not the Task Instance (AD-5)

**Given** the same task is completed again with a new photo
**When** the new upload completes
**Then** it overwrites the existing key — only the most recent photo is retained, no accumulating history (FR-19, AD-5)

**Given** a stored photo
**When** access is attempted
**Then** only that Home's Landlord and the product's own support staff can view it — no other Tenant, other Landlord, or third party can (NFR5)

**Given** a Tenant's task history and Photo Evidence
**When** visibility is checked
**Then** it is visible to that Tenant's own Landlord but never to other Tenants or other Landlords outside that Home (NFR6)

## Epic 5: AI Assistant

Any Member can tap "?" on a task for an immediate, disclaimer-carrying how-to answer, escalate to a full AI chat, and a new Tenant receives an AI-generated onboarding guide tailored to their Home's unit type when they join.

### Story 5.1: Contextual Quick-Answer ("?")

As any Member unsure how to do a task step,
I want to tap "?" and get an immediate, specific answer without leaving the task,
So that I can get unstuck right when I need it.

**Acceptance Criteria:**

**Given** a task
**When** a Member taps its "?" affordance
**Then** an inline popover opens (not a full navigation) and calls the one backend AI service wrapping Gemini (AD-4) — React never calls the Gemini API directly

**Given** the AI call is in flight
**When** the popover is open
**Then** it shows a skeleton-line loading state (not a spinner), announced via `aria-live="polite"`

**Given** the AI responds
**When** the answer renders
**Then** it displays as a structured object `{status, answer, disclaimer}` with the disclaimer shown in its own field beneath the answer, visible on every answer regardless of status (FR-14, AD-4)

**Given** a chemical-related how-to question (for example, which cleaner suits which surface)
**When** the AI answers
**Then** the disclaimer still surfaces — the question is never scoped out (NFR4)

**Given** the AI returns status "low_confidence" or "error"
**When** the popover renders
**Then** it says so plainly ("Usikker på svaret her — spør gjerne på nytt eller sjekk med noen andre") rather than guessing silently, and the disclaimer remains visible regardless of confidence

**Given** a "?" answer fails to load (network/AI error)
**When** Peter is mid-task (UJ-1)
**Then** he can still complete the task without an answer — the failure never blocks task completion

**Given** any AI-generated answer
**When** it renders
**Then** it is in Norwegian only, matching the page's declared `lang` — the AI is instructed to never mix languages in a response (UX-DR48)

### Story 5.2: Escalate to Full AI Chat

As a Member who needs more than a quick answer,
I want to continue the conversation in a full chat,
So that I can ask follow-up questions about the same task.

**Acceptance Criteria:**

**Given** the quick-answer popover
**When** the Member taps "Ask more"
**Then** it pushes into AI Chat, carrying the originating task as context for at least the first follow-up question (FR-15)

**Given** the AI Chat
**When** any message arrives
**Then** the AI-can-be-wrong/chemical-caution disclaimer is visible at least once per session, and new messages in the stream are announced via `aria-live="polite"`

**Given** AI Chat
**When** it calls the backend
**Then** it uses the same shared AI service (AD-4) as the quick-answer — not a separate implementation

### Story 5.3: AI-Generated Onboarding Guide for New Tenants

As a new Tenant joining a Home,
I want a short guide tailored to this specific Home/unit type,
So that I understand how the app and my obligations work without asking my Landlord to explain everything.

**Acceptance Criteria:**

**Given** a Landlord provisions a Home and invites Tenants
**When** the onboarding guide is generated
**Then** it is generated once per Home at provisioning time and persisted — not regenerated on every view (FR-16, AD-4)

**Given** a new Tenant accepts an invite
**When** they first open Task Overview
**Then** the guide surfaces as a one-time dismissible card at the top of the list — referencing their specific Home/unit type, not a generic document identical across all Homes

**Given** the Tenant dismisses the card
**When** they want to see it again later
**Then** it remains reachable from Settings

**Given** the guide generation
**When** it runs
**Then** it goes through the same single backend AI service (AD-4) as the other AI surfaces, with the disclaimer applied consistently if the guide contains how-to content

## Epic 6: Landlord Portfolio Dashboard

A Landlord who owns more than one Home sees a single aggregated view of on-track/behind status across all their Homes and units, letting them triage without a site visit.

### Story 6.1: Landlord Portfolio Dashboard

As a Landlord who owns multiple Homes,
I want a single view summarizing status across all of them,
So that I can triage without visiting each one individually.

**Acceptance Criteria:**

**Given** a Landlord who owns more than one Home
**When** they open the Portfolio Dashboard
**Then** they see a single view summarizing task status (on track / behind) per Home and per unit (FR-20)

**Given** a Home with at least one overdue Must task
**When** the dashboard renders that Home's row
**Then** it carries a danger status tag with the text label "Forsinket" — never color alone; a fully on-track Home shows "Alt i orden"

**Given** the dashboard is cold-loading
**When** data hasn't arrived yet
**Then** skeleton rows render for each known Home rather than a blank screen

**Given** a Landlord taps a portfolio row
**When** the tap registers
**Then** they navigate to that Home's Landlord Home Admin

**Given** the dashboard on a tablet (600-1023px) or desktop (≥1024px) viewport
**When** it renders
**Then** it gains a second column (building list alongside the selected building's detail) rather than list-then-navigate

**Given** the dashboard at 320 CSS px width / 400% browser zoom
**When** rendered
**Then** it — including the two-column layout — collapses to single-column with no horizontal scroll

**Given** a Landlord who owns exactly one Home
**When** they check for this surface
**Then** the Portfolio Dashboard tab/entry does not appear — it is shown only for Landlords with ≥2 Homes

**Given** the Portfolio Dashboard
**When** the Landlord pulls down to refresh
**Then** it refetches aggregated status — pull-to-refresh is supported on this surface (UX-DR36)
