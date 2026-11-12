---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories, step-04-final-validation]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-prosjektoppgave-ibe160-2026-09-29/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-prosjektoppgave-ibe160-2026-10-04/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/ux-designs/ux-prosjektoppgave-ibe160-2026-09-29/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-prosjektoppgave-ibe160-2026-09-29/EXPERIENCE.md
updated: 2026-11-01
---

# Husly - Epic Breakdown

> **Revision 2026-11-01:** Vercel is now the course's only supported hosting (see `sprint-change-proposal-2026-11-01.md`). New Story 1.7 (hosted demo on Vercel, built before Story 1.2); Story 1.2 becomes same-origin (no CORS, `SameSite=Lax`); Story 3.2 uses a daily Vercel Cron and a split deep-link rule; Story 3.5 gets whole-day cadence options; Stories 4.2 and 4.3 move to a private Vercel Blob store served only through the backend.

## Overview

This document provides the complete epic and story breakdown for Husly (placeholder name — an AI-driven household task management web app), decomposing the requirements from the PRD, the DESIGN.md/EXPERIENCE.md UX design contract, and the ARCHITECTURE-SPINE.md into implementable stories.

> **Revision 2026-10-11:** Updated in response to the teacher's feedback of 2026-10-06 (see `sprint-change-proposal-2026-10-11.md`). Every story now carries a **Stage** (Trinn 1 or Trinn 2), a new Story 1.6 makes the app runnable locally (FR-22), and acceptance criteria for README/`.env.example` and mock modes were added to existing stories. Story numbers are unchanged so that traceability is kept. The document now has 23 stories (the earlier "20" was a miscount of the 22 that existed).

> **Revision 2026-11-09:** Story 1.9 (one rule for creating Homes, issue #30) and Story 2.6 (add and remove Tasks, issue #31) added, with FR-24; see `sprint-change-proposal-2026-11-09.md`. The document now has 27 stories.

> **Revision 2026-11-12:** The teacher's PRD feedback (see `sprint-change-proposal-2026-11-12.md`): Trinn 2 is split into Must and If time permits with a cut order, the FR-11 rule is concrete (Story 3.3), AI failure, daily limit and call content are acceptance criteria (Stories 5.1 and 5.2), and "unit type" is replaced by the Home's name and active Must tasks (Story 5.3). No story is added or renumbered.

### Known open points (from the readiness check, 2026-10-11)

These do not block Trinn 1 but must be resolved before the stories they touch are built.

- **Screens without an owning story (Trinn 2).** "Landlord Home Admin" is used by Stories 3.4, 3.5, 4.1 and 6.1, and "Settings" by Stories 3.1 and 5.3, but no story builds the screen itself. Decide before Epic 3: either the first story that needs the screen builds its shell, or a small shell story is added.
- **Invite link policy (settled 2026-11-07).** "Single-use plus 7-day expiry" in Story 1.4 and the architecture was an assumption until the team confirmed it.
  - *Settled 2026-11-07 (team decision, Story 1.4 spec):* single-use, 7-day expiry; "Lag ny lenke" makes another link and earlier unused links stay valid; no revoking in v1.

### Delivery stages

Trinn 1 is the minimal core flow that must be finished and stable first, so a complete app exists even if Trinn 2 is not finished.

| Stage | Stories |
|---|---|
| **Trinn 1** | 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 5.1 |
| **Trinn 2, Must** | 3.1, 3.2, 3.4, 3.5, 4.1, 4.2, 4.3 (FR-10, FR-12, FR-13, FR-18, FR-19) |
| **Trinn 2, if time permits** | 6.1 (FR-20), 5.3 (FR-16), 3.3 (FR-11), 5.2 (FR-15) |

The cut order for the last row is from left to right: 6.1 is cut first and 5.2 last (PRD Open Question 1, decided 2026-11-12). Story 3.1 belongs to the Must group because push cannot work without it.

Epic 5 is split between the stages: the quick-answer (5.1) is Trinn 1, the chat (5.2) and onboarding guide (5.3) are Trinn 2. The Tenant locks in Stories 1.4, 2.3 and 1.5 are Trinn 1 on purpose: they are the product's differentiator and its most testable rules, even though the household is the primary user for Trinn 1.

Note on numbering: the PRD, Architecture, and UX documents all use the hyphenated form `FR-1`...`FR-24` as the canonical requirement IDs (also used in the Architecture's `binds:` frontmatter and Capability → Architecture Map). This document keeps that exact numbering rather than renumbering to `FR1` to preserve traceability across documents.

## Requirements Inventory

### Functional Requirements

FR-1: Create a Home (creation rule revised 2026-11-09, Story 1.9). A user can create a Home. If created as a Household Home, the creator becomes a Household Member with the same standing as any later invitee — no persistent creator privilege. If created as a Landlord Home, the creator becomes its Landlord.

FR-2: Invite members via link. Who can generate a Home's invite link depends on Home type: in a Household Home, any Household Member can generate one; in a Landlord Home, only the Landlord can — Tenants cannot invite anyone. A link is valid for 7 days and can be used once; an expired or used link shows a clear message.

FR-3: Assign and enforce Member Roles. Each Member of a Home has exactly one Role: Household Member, Landlord, or Tenant. Role determines permission tier for Must/Should and Frequency settings. A user cannot read or change data in a Home they are not a current Member of.

FR-4: Recommend Must/Should classification. The app suggests a Must or Should classification for each task based on task type (for example, mold or damage risk defaults to Must; "Rens sluket" is Must, "Avkalk vannkokeren" is Should).

FR-5: Adjust classification (Household Members and Landlords only). Household Members and Landlords can change a task's Must/Should classification. Tenants cannot.

FR-6: Must-first ordering. The task list displays Must tasks ahead of Should tasks.

FR-7: Shared completion status with per-member attribution. A Task instance in a Home has one shared completion status: any Member marking it complete resolves it for the whole Home. The system additionally records which Member performed each completion.

FR-8: Recommend and set task Frequency. The app proposes a recurrence Frequency for irregular tasks. Household Members and Landlords can approve or adjust it; Tenants inherit the Landlord's setting and cannot change it.

FR-9: Auto-reschedule on completion. Marking a task instance complete automatically calculates and schedules the next due date based on its Frequency, counted from the actual completion date (not the original due date).

FR-10: Due/overdue push notifications. The system sends a push notification to relevant Members when a task instance becomes due or overdue.

FR-11: Fairness-based targeted notification. When completion attribution (FR-7) shows a Member has none of a recurring shared task's last 3 completions (at least two current Members, at least three completed instances), the system targets a reminder to that Member only, while the task is open and due, at most once per task instance.

FR-12: Landlord ad-hoc broadcast message. A Landlord can send a free-form reminder message to all Tenants of a specific Home.

FR-13: Landlord-controlled notification cadence. A Landlord can configure how strictly/often Tenants of a Home are reminded about due/overdue Must tasks, independent of the task's Frequency.

FR-14: Contextual quick-answer. Any task offers a "?" affordance that returns an immediate, task-specific answer to a how-to question, always with a visible AI-can-be-wrong / chemical-caution disclaimer. A failed or slow call (over 10 seconds) shows an error and can be retried; at most 20 AI calls per user per day; only the task's name, catalog type and the user's question are sent.

FR-15: Escalate to full AI chat. From the quick-answer, a user can open a full conversational chat with the AI assistant for follow-up questions, retaining the originating task as context for at least the first follow-up, under the same timeout, data and daily-limit rules as FR-14.

FR-16: AI-generated onboarding guide. When a Landlord provisions a Home and invites Tenants, the system generates an onboarding guide explaining how the app works, tailored to that Home: it names the Home and lists its active Must tasks with their frequencies.

FR-17: Self-checkoff completion. Any Member can mark a task instance complete with a single action; no confirmation from another Member is required.

FR-18: Landlord-required Photo Evidence. A Landlord can mark a specific Must task as requiring Photo Evidence from Tenants, restricted to task types where completion is objectively visible without capturing sensitive or private content.

FR-19: Auto-approve with Landlord review, auto-replacing storage. Uploaded Photo Evidence auto-approves the task completion immediately; the photo remains accessible for Landlord review and is automatically replaced the next time the same task is completed (no accumulating history).

FR-20: Portfolio-level status dashboard. A Landlord with more than one Home sees a single view summarizing task status (on track / behind) per Home and per unit.

FR-21: Responsive layout across device classes. The web application renders a usable, complete layout on phone, tablet, and desktop viewport widths.

FR-22: Run locally without external accounts. The application runs on a developer's or reviewer's machine using a local Docker-based database, seed data and mock modes for the external services (AI, and in Trinn 2 push), with no account or key from the team.
FR-23: Leave a Home and remove Members (added 2026-11-08, Sprint Change Proposal 2026-11-08). A Household Member or Tenant can leave their Home; a Landlord can remove a Tenant from a Landlord Home. A Landlord cannot leave their own Landlord Home, and a Household Member cannot remove another Household Member. History stays and shows «Tidligere medlem»; only current Members count.

FR-24: Add and archive Tasks (added 2026-11-09, Sprint Change Proposal 2026-11-09). After Task Setup, a Household Member or Landlord can add a catalog or custom Task and archive a Task; Tenants cannot. Custom Tasks never require Photo Evidence; archiving keeps history.

### NonFunctional Requirements

NFR1: Permission enforcement. Role-based restrictions (Tenant cannot alter Landlord-locked Must/Frequency settings; only Household Members/Landlords can adjust classification) must be enforced server-side, not only hidden in the UI (binds FR-3, FR-5, FR-8).

NFR2: Notification reliability. Push notifications (FR-10 to FR-13) must be delivered reliably enough that a Household Member or Tenant can trust the absence of a notification to mean "nothing due" — a missed notification undermines the product's core value proposition.

NFR3: Responsiveness. All core flows must remain fully usable at common phone, tablet, and desktop breakpoints (FR-21) — a stated v1 requirement, not a polish pass.

NFR4: AI chemical-answer disclaimer, no accuracy bound. The AI assistant can answer chemical-related how-to questions (for example, which cleaner suits which surface); every such answer must surface the AI-can-be-wrong disclaimer rather than being scoped out. No numeric accuracy bound is set for this round — the disclaimer is the product's chosen mitigation, not a claim of verified correctness (binds FR-14, FR-15).

NFR5: Photo Evidence privacy scoping. Photo Evidence is restricted by design to task types where completion is objectively visible without capturing sensitive or private content; each photo is auto-replaced on the next completion (no accumulating history); access is restricted to the Home's Landlord and the product's own support staff only — no other Tenant, other Landlord, or third party can view it (binds FR-18, FR-19).

NFR6: Tenant data visibility scoping. Tenant data (task history, Photo Evidence, completion records) is visible to that Tenant's Landlord by design but must not be visible to other Tenants or other Landlords outside the relevant Home.

NFR7: Runnable without external accounts. The app, its seed data and its automated tests must run on a reviewer's own machine without any account or key from the team; external services have mock modes used when no key is set (binds FR-22, AD-15).

### Additional Requirements

No starter/greenfield template tool is specified by Architecture — it instead defines a committed source tree (`frontend/`, `backend/`) to scaffold directly; Epic 1 Story 1 should set up this tree rather than running an external project generator.

- **Layering & permissions:** Routes never mutate data or call external services directly — every mutating/permission-sensitive operation flows through a domain-service layer (AD-3). Role lives on the User↔Home Membership join entity, never on the User account (AD-1) — one User can hold different Roles in different Homes. Every Home-scoped route resolves the caller's Role per-request via a `require_role(home_id, allowed_roles)` dependency that loads the Membership row — never from a JWT claim (AD-2). `[REVISED 2026-11-08]` — delivered as `require_role(*roles)` (Story 1.4, reused in Story 1.5): the roles are given when the dependency is built, and `home_id` is read from the path only (`Path()`), never from the query or body. `backend/tests/test_permissions.py` walks every route and fails if a `{home_id}` route lacks `require_role` or `require_role` sits on a route without `{home_id}`.
- **Current vs past Members (AD-16, added 2026-11-08):** only current Memberships count for access, notifications, fairness and overviews; history (completions, Photo Evidence) references the User and shows «Tidligere medlem» when that User has no Membership in the Home.
- **Active vs archived Tasks (FR-24, added 2026-11-09):** an archived Task is never deleted, and every read that drives behaviour — Task Overview, the due-check and fairness (Epic 3), Photo Evidence requirements (Epic 4) and the Portfolio (Epic 6) — reads active Tasks only. History on an archived Task (completions, Photo Evidence) stays reachable where that history is shown. `has_tasks` means Task Setup has run.
- **Task completion:** One domain function (`complete_task_instance`) is the sole code path marking a Task instance complete, recording attribution, and triggering the FR-9 reschedule; it is idempotent on retried requests (AD-3).
- **AI service:** One backend AI service wraps every Gemini call (quick-answer, chat, onboarding-guide generation); every response is a structured object `{status: "ok" | "low_confidence" | "error", answer, disclaimer}` with the disclaimer always its own field (AD-4). The onboarding guide is generated once per Home at provisioning time and persisted, not regenerated per view (AD-4, FR-16).
- **Photo Evidence storage:** `PhotoEvidence` is 1:1 with `Task` (not `TaskInstance`); each task's photo is stored under a fixed key (`tasks/{task_id}/evidence.jpg`) in a private Vercel Blob store, overwritten on each new upload — no per-completion history row; the photo is only served through a backend route that runs `require_role` first, never as a permanent Blob URL (AD-5). Task types carry a system-seeded, non-Landlord-editable `photo_evidence_eligible` flag; the endpoint setting FR-18's requirement rejects the request server-side if the Task's type isn't flagged eligible (AD-6).
- **Auth:** Short-lived JWT access token returned in the login response body and kept only in React memory (never `localStorage`); long-lived refresh token as an `httpOnly`/`Secure`/`SameSite=Lax` cookie scoped to `/api/auth/refresh`, the only endpoint that exchanges it. The frontend calls the API only through relative `/api/...` paths on the same origin (Vercel rewrite in the hosted demo, Vite proxy locally), so no CORS configuration exists (AD-7).
- **Due/notification job:** A dedicated `GET /api/internal/run-due-check` endpoint runs the due/overdue scan (FR-10's daily batch, FR-11's fairness nudge); Vercel Cron calls it once a day (`0 6 * * *` UTC) with `Authorization: Bearer <CRON_SECRET>`, and requests without that secret are rejected. The endpoint is safe to call concurrently or twice — it tracks per Task Instance whether the notification for the current day was already sent (AD-8). Fairness-nudge rule: fire a targeted nudge to a Member with 0 completions in the last 3 instances of a recurring shared task, provided at least one other Member completed at least one of those 3 (AD-9, resolves PRD Open Question 4). Landlord broadcast (FR-12) is sent directly and synchronously on request, independent of the due-check cron (AD-14).
- **No real-time layer:** Freshness comes from TanStack Query refetching on mount/window-focus — no WebSocket/SSE infrastructure (AD-10).
- **Frontend data layer:** No component calls `fetch`/`axios` directly or holds server data in local `useState` — all server reads/writes go through TanStack Query hooks backed by one generated API client (from the backend's OpenAPI schema via `openapi-typescript`, never hand-written types). The self-checkoff mutation (FR-17) uses TanStack Query's optimistic-update pattern; the photo-evidence-upload mutation (FR-19) is deliberately pessimistic — the UI waits for the upload-and-auto-approve response before showing complete (AD-11).
- **PWA shell:** `frontend/` includes a `manifest.json` and a registered service worker from day one, plus one shared "Add to Home Screen" install-prompt component shown once per Member per device (tracked client-side) — required for Web Push to reach iOS Safari (iOS 16.4+ only supports Web Push for a Home-Screen-installed PWA) (AD-12, binds FR-10, FR-21).
- **Design tokens:** DESIGN.md's tokens are implemented once as CSS custom properties generated/copied from DESIGN.md's frontmatter — no component file contains a literal hex color, px size, or border-radius value, only `var(--...)` references (AD-13).
- **Naming/data conventions:** Entity names match the PRD Glossary verbatim (`Home`, `Member`, `Role`, `Task`, `TaskInstance`, `Frequency`, `PhotoEvidence`, `NotificationCadence` — never `User` for the Home-scoped actor). IDs are UUIDv4 everywhere. Dates/times are ISO 8601 UTC on the wire. Errors use FastAPI's default `{"detail": "..."}` shape; validation errors use the standard Pydantic 422 body.
- **Schema changes:** Every schema change is an Alembic migration committed to the repo — never a manual change to any database. Each developer has their own local Docker database (AD-15), so whoever pulls a migration runs it before starting work.
- **Local running (AD-15):** `docker compose up` starts a local PostgreSQL database; one documented command applies the Alembic migrations and loads seed data; all configuration comes from environment variables with `.env.example` as the template. AI, push (Trinn 2) and Photo Evidence storage (Trinn 2) sit behind adapters with a mock/local implementation that is selected automatically when the key is missing. The automated test suite always runs offline against the mock adapters.
- **Deployment/infrastructure (optional hosted demo):** one Vercel project (`g04husly`) with the Vite frontend and FastAPI backend as Vercel Services on one domain (`/api/*` → backend); Neon Postgres via the Vercel integration, with a Neon branch per PR preview migrated in the build step and deleted when the PR closes; a private Vercel Blob store for Photo Evidence; Vercel Cron for the daily due-check; Google Gemini API for AI. This is an optional demo deployment of the same code, not a requirement for running the app, and Trinn 1 needs none of cron, push or Blob there (Story 1.7).
- **Secrets:** Gemini key, VAPID keys, DB URL, JWT signing key, `CRON_SECRET` and `BLOB_READ_WRITE_TOKEN` via environment variables only (Vercel project settings in the hosted demo), never committed.
- **Core entities (names/relationships only):** User, Membership (scoped to one Role per Home), Home, InviteLink (own validity state: token, target Role, used/expired/revoked, distinct from Membership), Task, TaskType (system-seeded catalog carrying `photo_evidence_eligible`), TaskInstance, MemberCompletion (attribution), PhotoEvidence (per-Task), NotificationCadenceSetting (Landlord Homes), PushSubscription (per User, one per device). `[ASSUMPTION carried from Architecture, confirm with team before building]`: invite link default policy is single-use + 7-day expiry, regenerable by whoever can invite. `[REVISED 2026-11-08]` — policy settled by the team on 2026-11-07 (Story 1.4, decision 1): single-use, valid 7 days; any Household Member or the Landlord can make a link, a Tenant cannot (server rejects with 403); "Lag ny lenke" leaves earlier unused links valid; no revoking in v1.
- **Explicitly deferred by Architecture (flag for sprint planning, not pre-decided):** observability/logging strategy (left to Vercel's runtime logs + basic logging); automated testing strategy (pytest/Vitest suggested, not binding — the one binding rule is that the suite runs offline against the mock adapters, AD-15); rate-limiting/abuse protection on AI endpoints (none beyond the one-service chokepoint + Gemini's own free-tier cap); internationalization infrastructure (not needed — Norwegian-only v1 per UX). `[REVISED 2026-11-08]` Two risks accepted in the Epic 1 retrospective (P3, R9; Eirik): (1) the row locks in `create_home`, `invites.accept`, `homes.add_member` and the migration lock in `alembic/env.py` are reasoned, not tested, because pytest runs on SQLite; no Postgres concurrency test job is built before Epic 2. (2) Login and registration have no rate limit or lockout, also on the hosted demo, where each attempt runs Argon2; the demo holds no real data and is a course project. Revisit both if the hosted demo gets real users.

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
UX-DR17: No in-app notification inbox (FR-10/FR-11/FR-12 stay push-only). A daily due/overdue notification about one task deep-links to its Task Detail and one about several tasks opens Task Overview; an FR-11 nudge opens its Task Detail; an FR-12 broadcast opens Task Overview. The notification text names the tasks.

**State patterns (each with its specified copy/treatment, not left generic)**
UX-DR18: Cold load (Task Overview, Landlord Portfolio Dashboard) — 3–4 skeleton placeholder cards/rows while data loads, distinct from the Empty state.
UX-DR19: Task due soon — due date in `warning` color, bold, plus the word "Snart forfall" (never color/weight alone).
UX-DR20: Task overdue — due date in `danger` color plus the word "Forfalt" (deliberately distinct wording from the Must badge's "Must" label).
UX-DR21: Task completed — checkbox filled, title strikethrough, due-date line replaced by a success-colored completion note ("Fullført i dag" / "Fullført av Peter").
UX-DR22: Empty task list — "Ingen oppgaver akkurat nå — nyt det! 🎉" (household) or "Ingen aktive oppgaver i dette hjemmet." (landlord Home Admin) — never an illustration with no text.
UX-DR23: Invalid or expired invite link — "Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra [utleier/husstandsmedlem]." — never a generic 404.
UX-DR24: Failed login — inline field-level error, not a full-page reload; message never confirms or denies whether an email/username exists.
UX-DR25: Duplicate registration attempt via invite link — if the invited email already has an account, offer "Logg inn i stedet" rather than a flat error. `[REVISED 2026-11-08]` The invite link carries no email (Story 1.4, team decision 2). "Logg inn i stedet" is shown when registration through the link hits an email that already has an account (409), and it keeps the invite.
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

FR-1: Epic 1 - Create a Home (Household or Landlord) + Story 1.9 (one creation rule, 2026-11-09)
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
FR-22: Epic 1 (Story 1.6 - local run with Docker, seed data and mock modes; README and `.env.example` from Story 1.1)
FR-23: Epic 1 (Story 1.8 - leave a Home, Landlord removes a Tenant; added 2026-11-08)
FR-24: Epic 2 (Story 2.6 - add and remove Tasks; added 2026-11-09)

Stage per FR: Trinn 1 = FR-1 to FR-9, FR-14, FR-17, FR-21 (shell), FR-22, FR-23, FR-24. Trinn 2 = FR-10 to FR-13, FR-15, FR-16, FR-18 to FR-20, FR-21 (dashboard behavior).

## Epic List

### Epic 1: Foundation — Accounts, Homes & Roles
Users can register and log in, create a Home (Household or Landlord), invite others via a scoped link, and have their Role (Household Member, Landlord, Tenant) correctly enforced server-side everywhere. This epic also establishes the responsive, installable app shell (design tokens as CSS custom properties per AD-13, PWA manifest + service worker + install prompt per AD-12, phone/tablet/desktop breakpoints per FR-21/UX-DR44) that every later epic's screens build on, plus the domain-service/permission-dependency layering (AD-1, AD-2, AD-3 scaffold), the same-origin JWT auth split (AD-7) and the optional hosted demo on Vercel (Story 1.7).
**FRs covered:** FR-1, FR-2, FR-3, FR-22, FR-23 (+ FR-21 at the shell level)
**Stage:** Trinn 1

### Epic 2: Task Management Core Loop
Household Members, Tenants, and Landlords can see a Must-first task list for their Home, (for Household Members/Landlords) adjust a task's Must/Should classification and Frequency inline, self-checkoff a task in one tap, see shared completion status update immediately with per-member attribution, and have the next occurrence auto-scheduled from the actual completion date. Includes the Task Setup step at Home creation (reviewing/accepting the app's recommended task list). Implements the single `complete_task_instance` domain function (AD-3) that Epic 4 (Photo Evidence) will later extend, and add or remove Tasks after setup (Story 2.6).
**FRs covered:** FR-4, FR-5, FR-6, FR-7, FR-8, FR-9, FR-17, FR-24
**Stage:** Trinn 1

### Epic 3: Notifications
Members receive a push notification when a task becomes due or overdue, with fairness-based targeting when one Member has fallen behind on a shared task; Landlords can send ad-hoc broadcast messages to their Tenants and configure how strictly Tenants are reminded. Implements the daily Vercel Cron-driven due-check endpoint (AD-8), the fairness-nudge rule (AD-9), and the direct/synchronous broadcast path (AD-14).
**FRs covered:** FR-10, FR-11, FR-12, FR-13
**Stage:** Trinn 2

### Epic 4: Photo Evidence
A Landlord can flag a specific Must task (restricted to system-eligible task types) as requiring Photo Evidence; a Tenant uploads a photo from their phone and the task auto-approves immediately, with the photo staying available for Landlord review and being auto-replaced on the next completion. Extends Epic 2's completion domain function and photo-eligibility gating (AD-5, AD-6).
**FRs covered:** FR-18, FR-19
**Stage:** Trinn 2

### Epic 5: AI Assistant
Any Member can tap "?" on a task for an immediate, disclaimer-carrying how-to answer, escalate to a full AI chat for follow-up questions, and a new Tenant receives an AI-generated onboarding guide tailored to their Home when they join. Implements the single server-mediated AI service (AD-4) wrapping all Gemini calls behind one structured response shape.
**FRs covered:** FR-14, FR-15, FR-16
**Stage:** FR-14 (Story 5.1) is Trinn 1; FR-15 and FR-16 (Stories 5.2, 5.3) are Trinn 2

### Epic 6: Landlord Portfolio Dashboard
A Landlord who owns more than one Home sees a single aggregated view of on-track/behind status across all their Homes and units, letting them triage without a site visit — including the dashboard's own tablet-and-up two-column (list + detail) responsive behavior.
**FRs covered:** FR-20 (+ FR-21 dashboard-specific behavior)
**Stage:** Trinn 2

## Epic 1: Foundation — Accounts, Homes & Roles

Users can register and log in, create a Home (Household or Landlord), invite others via a scoped link, and have their Role correctly enforced server-side everywhere — on top of a responsive, installable app shell with DESIGN.md's tokens wired in from the start.

`[ASSUMPTION carried from PRD Open Question 3 / EXPERIENCE.md's Foundation note, unresolved at the PRD level]`: v1 does not design a Home-switcher UI. A Landlord may own and switch between multiple Homes via the Portfolio Dashboard (Epic 6) — that mechanism is Landlord-specific and already scoped. A Household Member or Tenant is assumed to belong to at most one Home for the main self-service flow (Story 1.3); nothing technically prevents them from also accepting a second invite link (Story 1.4) into another Home, but no UI exists for switching between multiple simultaneous non-Landlord Memberships. If this turns out to matter for the team's actual usage, revisit before Epic 1 is built — it is a scope decision, not an oversight.

*Update 2026-11-07 (team decision 3, Story 1.4):* the assumption is now a rule enforced on the server in `domain/homes.add_member`. A user may be Household Member or Tenant in at most one Home; Landlord Memberships do not count, so a Landlord may also join one such Home. A second invite is refused with "Du er allerede med i «X». Du kan bare være med i ett hjem om gangen."

*Update 2026-11-09 (Sprint Change Proposal, Story 1.9):* creating a Home now follows the same limit: anyone may create Landlord Homes, and a Household Home only without another Household Member or Tenant Membership.

### Story 1.1: Project Scaffold, Design Tokens & Responsive App Shell

**Stage:** Trinn 1

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
**Then** a health-check endpoint responds 200, Alembic is wired for migrations against the local Docker PostgreSQL started by the repo's `docker-compose.yml`, and the source tree matches the committed layout (`backend/app/{routes,domain,permissions,models}`, `frontend/src/{api,components,routes,styles}`)

**Given** the scaffold
**When** the test commands are run
**Then** pytest (backend) and Vitest (frontend) are configured, each with one passing example test, and both run offline without any key — so every later story can add automated tests for its own logic from the start (AD-15)

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

**Given** the repository after this story
**When** a developer or reviewer opens it
**Then** a `README.md` and a `.env.example` exist at the repo root (no secrets), and every later story that changes how the app is set up or run updates them in the same pull request (FR-22, AD-15)

### Story 1.2: Account Registration & Login

**Stage:** Trinn 1

As a new user,
I want to register an account and log in,
So that I can access my Homes securely.

**Acceptance Criteria:**

**Given** a visitor with no account
**When** they submit a valid email + password
**Then** a User row is created and they receive a short-lived JWT access token in the response body (kept only in frontend memory) plus an httpOnly/Secure/SameSite=Lax refresh cookie scoped to `/api/auth/refresh` (AD-7)

**Given** a registered user
**When** they submit correct credentials
**Then** they receive a fresh access token + refresh cookie and land inside the app

**Given** a registered user
**When** they submit an incorrect password or unknown email
**Then** an inline field-level error displays without a full-page reload, and the message never reveals whether the email exists

**Given** an expired access token
**When** a request is made
**Then** the frontend calls `/api/auth/refresh` using the httpOnly cookie to get a new access token transparently, without forcing re-login

**Given** the frontend
**When** it calls the API locally (Vite proxy) or on Vercel (rewrite)
**Then** every call uses a relative `/api/...` path on the same origin, and no CORS configuration exists (AD-7, AD-15)

**Given** Safari on macOS and iOS
**When** a user logs in on local running and on the PR preview
**Then** the refresh cookie is set and `/api/auth/refresh` works; if Safari rejects the `Secure` cookie on `http://localhost`, the `Secure` flag is relaxed by an environment variable for local running only, never in the hosted demo

*Revised 2026-11-08:* as built, `Secure` is off for local running by default and on in the hosted demo (on Vercel, or with `AUTH_COOKIE_SECURE=true`), so Safari works on `http://localhost` without any setting (Story 1.2 spec, finding 9).

### Story 1.3: Create a Home (Household or Landlord)

**Stage:** Trinn 1

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

**Given** the seed command from Story 1.6
**When** this story is delivered
**Then** the seed data is extended with an example Household Home that the example users belong to (FR-22)

*Revised 2026-11-09 (Sprint Change Proposal, Story 1.9):* the AC "a Household Member/Tenant is not re-prompted to create another Home" and the rule "a Landlord may create more Landlord Homes only" are replaced by one rule: Landlord Homes always, Household Home only without another Household Member or Tenant Membership.

### Story 1.4: Invite Members via Scoped Link & Accept Invite

**Stage:** Trinn 1

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

*Revised 2026-11-08:* The invite link carries no email (Story 1.4, team decision 2). "Logg inn i stedet" is shown when registration through the link hits an email that already has an account (409), and it keeps the invite.

**Given** invite-link generation fails server-side
**When** the Member sees the result
**Then** an inline error with a retry affordance shows at the action — not a silent failure (UX-DR30)

*Implementation note 2026-11-07 (Story 1.4 spec):* invite generation is the first Home-scoped route, so `permissions/require_role.py` is built in this story instead of 1.5 (signature `require_role(*roles)`, reading `home_id` from the path); Story 1.5 reuses it. The invite control lives on a new page `/hjem/<id>/medlemmer` ("Medlemmer og invitasjon"), linked from the Home page, since the Task Overview header (Story 2.2) does not exist yet. The seed gains a Landlord (Kari) and a Tenant (Anders) who joins through an invite link.

### Story 1.5: View Home Members List & Enforce Role-Based Permissions

**Stage:** Trinn 1

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
**Then** `require_role(*allowed_roles)`, reading `home_id` from the path, loads the caller's Membership row for `(user_id, home_id)` and checks that row's Role — never a JWT claim, body, or query param (AD-2)

*Note 2026-11-07:* `require_role` itself was delivered early in Story 1.4 (first Home-scoped route); this story adds the members list to the existing Members & Invite page and applies `require_role` to its routes.

**Given** a user with a Membership in Home A but not Home B
**When** they call a Home B route
**Then** the request is rejected regardless of their Role in Home A

**Given** a Home with only Household Members
**When** inspected
**Then** it never also contains a Landlord/Tenant row, and vice versa


*Note 2026-11-08 (Sprint Change Proposal 2026-11-08):* this story's spec kept removing Members and leaving a Home out of scope ("Never: no removing Members"); that is superseded by Story 1.8 (FR-23).
### Story 1.6: Run Locally with Docker, Seed Data and Mock Modes

**Stage:** Trinn 1

As a developer or course reviewer,
I want to run the whole app on my own machine without the team's accounts or keys,
So that I can try it, test it and review it.

This story builds on Stories 1.1 (scaffold, `docker-compose.yml`, test setup) and 1.2 (users). It does not depend on later stories: the seed mechanism is extended by Stories 1.3 and 2.1 (example Home and tasks), and the AI mock provider is delivered with Story 5.1.

**Acceptance Criteria:**

**Given** a machine with Docker installed and the repository cloned
**When** the README's steps are followed (`docker compose up`, then one command for migrations and seed data)
**Then** a local PostgreSQL database is running with the schema applied and seed data loaded, including at least two example users whose credentials are listed in the README (FR-22, AD-15)

**Given** the seed mechanism
**When** a later story adds an entity that needs example data (Stories 1.3 and 2.1)
**Then** that story extends the same seed command, so one command always yields a ready-to-use example Home

**Given** `.env.example`
**When** inspected
**Then** it lists every environment variable the app reads, with placeholder values and no secrets, and `.env` is ignored by git

**Given** the automated test suite
**When** it is run without network access and without any key
**Then** it passes, using the mock adapters only

**Given** the README
**When** a reviewer reads it
**Then** it states the prerequisites (Docker), the exact start-up, seed and test commands, how mock mode is shown in the UI, and how to add real keys optionally — and the steps work on both macOS and Windows

**Given** the seed data
**When** it is loaded twice
**Then** it does not create duplicates (idempotent), so a reviewer can re-run it safely

> **Note 2026-11-01 (team decision, Story 1.6):** No mock-mode indicator is built in the UI yet. Trinn 1 calls no external service so far (AI arrives with Story 5.1, push and Blob in Trinn 2), so an indicator would show an empty list. The README says that nothing is mocked yet and that Story 5.1 marks AI answers as «demo-modus»; the UI indicator comes with Story 5.1, whose existing acceptance criterion ("the UI marks it as demo mode") already covers it. The acceptance criteria above are unchanged. The seed also refuses to run on Vercel or against a non-local database, so the example users never reach the hosted demo.

### Story 1.7: Hosted Demo on Vercel (Services + Neon)

**Stage:** Trinn 1 (optional hosted demo, AD-15). Built before Story 1.2, so that login can be tried on PR previews.

As a team member or course reviewer,
I want the frontend and the API deployed together on the course's Vercel project,
So that every PR can be tried online and the merged app is reachable at g04husly.vercel.app.

This story builds on Story 1.1. Local running (AD-15) stays the primary path and is unchanged apart from the `/api` proxy. Added by `sprint-change-proposal-2026-11-01.md`.

**Acceptance Criteria:**

**Given** `vercel.json` at the repo root with `frontend/` and `backend/` as Vercel Services, and the project's Root Directory set to the repo root
**When** `main` is deployed
**Then** `/` serves the Vite app (manifest and `/service-worker.js` included) and `/api/health` answers 200 from FastAPI on the same domain (AD-7)

**Given** Neon connected through the Vercel integration
**When** a deployment is built
**Then** `alembic upgrade head` runs in the build step against that deployment's `DATABASE_URL`, and a failed migration fails the build

**Given** a PR
**When** its preview is deployed
**Then** it uses its own Neon branch `preview/<git-branch>`, so its migrations never touch production

**Given** a PR is closed or merged
**When** cleanup runs
**Then** its Neon preview branch is deleted, so the free plan's 10-branch limit is never reached. If this is not possible on the free plan, the fallback is to migrate only on `main`, and the PR explains why

**Given** the Vite dev and preview servers
**When** the frontend calls `/api/...` locally
**Then** the call is proxied to the backend on port 8000, so local running is same-origin like the demo (AD-7)

**Given** the backend
**When** inspected
**Then** no CORS middleware is configured and `CORS_ORIGINS` is gone from the config and `.env.example` — this removes Story 1.1's CORS code (AD-7)

**Given** the backend running as a Vercel Function
**When** it connects to Neon
**Then** it uses Neon's pooled connection string, and the DB URL scheme is normalised for SQLAlchemy/psycopg in one place in the config

**Given** the repo
**When** inspected
**Then** no secret is committed, and the README describes the hosted demo: its URL, that it is optional, that only the project owner sees the Vercel and Neon dashboards, and how to roll back (tag `v0.1-for-vercel-hosting`, Root Directory `frontend`)

### Story 1.8: Leave a Home & Landlord Removes a Tenant

**Stage:** Trinn 1 · **Source:** Epic 1 retrospective (R2) and Sprint Change Proposal 2026-11-08 · **FR:** FR-23 · **AD:** AD-16, AD-2

As a Household Member or Tenant, I want to leave a Home I no longer belong to, and as a Landlord, I want to remove a Tenant who has moved out,
So that nobody is locked into the wrong Home and a Landlord's Home lists only current Tenants.

**Acceptance Criteria:**

**Given** a Household Member or Tenant on Members & Invite
**When** they choose «Forlat hjemmet» and confirm
**Then** their Membership is deleted, they land on the no-Home state with «Du har forlatt «X».», and they may create a Home or join another through an invite

**Given** the last Household Member of a Household Home
**When** they leave
**Then** the Home remains without Members and nothing else is deleted

**Given** a Landlord on Members & Invite
**When** they choose «Fjern» next to a Tenant and confirm
**Then** that Tenant's Membership is deleted and the list updates; the Landlord sees no leave action

**Given** a Household Member, a Tenant, or a Landlord targeting someone who is not a Tenant of that Home
**When** they call the remove route directly
**Then** the server answers 403 and nothing is deleted (AD-2); a Landlord calling the leave route also gets 403

**Given** a user removed while signed in
**When** their next Home-scoped request for that Home answers 403
**Then** the app refetches the Homes list and sends them to `/` — no error page and no retry loop

**Given** either action
**When** the first button is tapped
**Then** an inline confirmation with «Avbryt» appears; nothing is deleted until confirmed (UX: Leave / remove confirmation)

**Given** invite links created earlier by someone who has left
**When** they are opened
**Then** they stay valid until used or expired, as in Story 1.4 (a link belongs to the Home, not to its creator)

### Story 1.9: One Rule for Creating Homes

**Stage:** Trinn 1 · **Source:** issue #30, Epic 1 retrospective (R1), Sprint Change Proposal 2026-11-09 · **FR:** FR-1, FR-3 · **AD:** AD-1, AD-3

As a user who already belongs to a Home,
I want to create the other kind of Home when my situation calls for it,
So that a Landlord can have a private Household Home and a Household Member or Tenant can start renting out a unit, without needing an invite.

**Acceptance Criteria:**

**Given** a Landlord with no Household Member or Tenant Membership
**When** they open Create Home
**Then** both Household Home and Landlord Home are offered, and choosing Household Home makes them its Household Member (FR-1)

**Given** a Household Member or Tenant
**When** they open Create Home
**Then** only Landlord Home is offered, and creating one makes them its Landlord while their existing Membership is unchanged

**Given** a user who is already a Household Member or Tenant somewhere
**When** they call `POST /api/homes` with `type: household` directly
**Then** the server answers 409 with «Du er allerede med i «X». Du kan bare være med i ett hjem om gangen.», the same as joining (Story 1.4), and nothing is written

**Given** the creation rule and the joining rule
**When** their source is inspected
**Then** both read one domain statement of the one-Home limit in `domain/homes` (`allowed_types` and `join_blocker` share it), so they cannot drift apart again (AD-3)

**Given** any user who may still create a Home
**When** the Home page renders
**Then** «Opprett nytt hjem» is shown, and after creating, the user goes on to Task Setup (Story 2.1)

**Given** any created Home
**When** `fr3_violations` runs in the tests and CI
**Then** it is still empty: a Home never mixes Household Members with a Landlord or Tenants

**Given** the Story 1.3 and 1.4 test matrices
**When** this story is delivered
**Then** the row «Landlord creates Household» expects 201, a new row covers a Household Member creating a Landlord Home, and the README describes the rule where it explains creating a Home

## Epic 2: Task Management Core Loop

Household Members, Tenants, and Landlords can see a Must-first task list, adjust classification/Frequency where permitted, self-checkoff a task in one tap with shared status and attribution, and have the next occurrence auto-scheduled from the actual completion date.

### Story 2.1: Task Setup at Home Creation

**Stage:** Trinn 1

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

**Given** the recommended task list
**When** its source is inspected
**Then** it comes from a versioned, system-seeded task-type catalog in the repository (`TaskType`, AD-6) — one entry per task type with name, default Must/Should classification, recommended Frequency in days, and the `photo_evidence_eligible` flag — never hardcoded in a component or a route

**Given** the initial catalog
**When** it is reviewed in this story's pull request
**Then** it contains at least eight task types covering both classifications and at least two flagged `photo_evidence_eligible` (for example a drain), and the team has agreed the values; the starter list in the table below is a proposal to adjust, not a requirement `[ASSUMPTION: starter values, to be confirmed by the team in the PR]`

| Task type | Default | Frequency (days) | Photo-eligible |
|---|---|---|---|
| Deep-clean the bathroom (mold risk) | Must | 42 | No |
| Clean the drain (sluk) | Must | 30 | Yes |
| Descale the kettle | Should | 60 | No |
| Clean behind and under the fridge | Should | 90 | No |
| Clean the oven | Should | 90 | No |
| Vacuum and mop the floors | Should | 14 | No |
| Clean the extractor-fan filter | Must | 60 | Yes |
| Wash the shower grout | Should | 90 | No |

**Given** the seed command from Story 1.6
**When** Task Setup is delivered
**Then** the seed data is extended with an example Household Home that already has the recommended tasks, so a reviewer sees a populated Task Overview straight after seeding (FR-22)

**Note (2026-11-09, Story 2.1 spec, decisions by Eirik):** (1) Until Story 2.2 builds Task Overview, setup lands on `/`, which shows a minimal task list (name, Må/Bør, Frequency, next due date). (2) The catalog is a versioned Python module (`backend/app/domain/task_types.py`), not a table; a Task stores its catalog key and copies the name. (3) The eight starter entries in the table above are agreed as they stand. (4) The first instance is due on the setup date + Frequency; the seed sets both example Homes up as of an earlier date (28 and 40 days ago), so some tasks are due soon or overdue. (5) A task can be unticked in setup; custom tasks are not built now (`deferred-work.md`), but the model allows them later because a Task carries its own name. (6) Frequency is chosen from fixed intervals: 7, 14, 30, 42, 60, 90, 182 and 365 days («Hver uke» … «Hvert år»). Beyond the AC above, the seed also sets up the Landlord Home «Storgata 12», and setup runs once per Home (a second attempt gets 409). *Sprint Change Proposal 2026-11-09:* custom Tasks (decision 5) are planned in Story 2.6, and `has_tasks` keeps meaning "Task Setup has run" once Tasks can be archived.

### Story 2.2: Must-First Task Overview

**Stage:** Trinn 1

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

*Moved to Story 2.4 on 2026-11-10 (Story 2.2 spec, decision 6): 2.2 has no checkbox; the row alone links to Task Detail.*

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

**Given** a signed-in Member with a Home
**When** any signed-in page renders
**Then** a tab bar shows Task Overview and Settings/Profile, plus Portfolio for a Landlord who owns two or more Homes (EXPERIENCE.md)

*The Portfolio part moved to Story 6.1 on 2026-11-10 (Story 2.2 spec, decision 5); Story 2.2 builds Task Overview and Settings/Profile.*

*Added 2026-11-09 (Sprint Change Proposal):*

**Given** a user with more than one Home (for example a Landlord with their own Household Home, Story 1.9)
**When** they use the app
**Then** each Home has its own Task Overview at `/hjem/<id>`, a «Dine hjem» list lets them switch between their Homes, and `/` opens the most recently used Home. The Portfolio tab (Landlord with ≥2 Landlord Homes) is unchanged.

*The Portfolio tab moved to Story 6.1 on 2026-11-10 (Story 2.2 spec, decision 5).*

*Added 2026-11-10 (team decision, Eirik, during the Story 1.9 walkthrough):*

**Given** any page inside the app shell
**When** the user activates the «Husly» wordmark in the header
**Then** it is a link to `/`: a signed-in user lands on their Home (the same Home `/` opens, see the AC above), and a signed-out user is sent to sign-in by the existing route guard. It is a real link (keyboard-focusable, visible focus ring), not a click handler on text.

> **Note 2026-11-10:** Today «Husly» in `AppShell` is plain text, so pages such as Create Home, Members & Invite and Task Setup have no quick way back. Placed in Story 2.2 rather than a separate fix because 2.2 decides what `/` opens for a user with several Homes, which is where the link should go.

> **Note 2026-11-10 (team decisions, Story 2.2 spec, `spec-2-2-must-first-task-overview.md`):** The UI is Norwegian-only, so the badges read «Må»/«Bør» rather than "Must"/"Should". «Snart forfall» means due within 3 days (today up to today + 3); with 7, a weekly Task would always be due soon. The due state is computed on the server (`due_status`, `days_until_due`) so list and later push agree. The list always shows every Task, Must first; when nothing is overdue or due soon, the empty-state text shows above the list. The most recently used Home is kept per user on the device (`localStorage`), not on the server. Two ACs above moved: the checkbox/row focus-order AC moves to Story 2.4 (2.2 has no checkbox; the row opens a minimal read-only Task Detail that Story 2.3 extends), and the Portfolio tab moves to Story 6.1, which builds the Portfolio page. Settings/Profile (`/innstillinger`) holds «Dine hjem» and «Logg ut», and Create Home got «Logg ut» for a user without a Home.

> **Note 2026-11-07 (team decision, Story 1.3):** The tab bar was deferred from Stories 1.1 and 1.2 to 1.3, and has now been split out of 1.3 too, since after 1.3 only a placeholder Home page and sign-out exist. It belongs here because Task Overview is its first real content. Until then, Story 1.3 gives Landlords a plain link to create another Home.

### Story 2.3: Adjust Task Classification & Frequency

**Stage:** Trinn 1

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

> **Note 2026-11-11 (team decisions, Story 2.3 spec, `spec-2-3-adjust-task-classification-frequency.md`, issue #40):** The two fields are saved with a «Lagre endringer» button instead of on change ("directly editable inline" still holds: same page, no admin screen); only fields that differ from the server's current value are sent, and with no difference nothing is sent and «Ingen endringer å lagre.» is announced. "Immediately reflected to all Members" means on their next refetch (window focus, «Oppdater» or navigation), since there is no real-time layer (AD-10). A failed save shows its inline error and «Prøv igjen» at the form, under both fields, not at each field. Decision 1: a new Frequency also moves the open instance's due date to `due_on − old Frequency + new Frequency` (same start point, new interval), so it may become overdue at once; a classification-only change leaves the date alone. Story 2.5's reschedule then counts from the completion date with the stored Frequency.

### Story 2.4: Self-Checkoff Completion with Shared Status & Attribution

**Stage:** Trinn 1

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

*Moved from Story 2.2 on 2026-11-10 (team decision 6 in the Story 2.2 spec; 2.2 has no checkbox):*

**Given** a task card
**When** the checkbox and the row are both present
**Then** they are two independently focusable tap targets in that order in the tab sequence (checkbox first), with the row tap navigating to Task Detail

*Added 2026-11-08 (Sprint Change Proposal, AD-16):*

**Given** a completion recorded by a user who has since left the Home
**When** any Member views it
**Then** it is attributed to «Tidligere medlem» and the completion itself is kept

*Settled 2026-11-11 in the Story 2.4 spec (team decisions, Eirik):*

- A completed card shows the Task's latest completion while the open instance's due state is «later»; once it is due soon or overdue, the due line and an empty checkbox return (decision 1).
- Copy: «Fullført i dag» / «Fullført i går» / «Fullført 3. november» (year when not this year), plus « av Peter» for another current Member and « av tidligere medlem» for a completer without a Membership in this Home; one's own completion never has a name (decision 4).
- No undo: a completed checkbox is inert (decision 3).
- A tick made offline is sent when the connection returns while the app stays open; a reload or closing the app while offline loses it (decision 5, stated in README).
- **Deviation:** Task Detail shows the completion note read-only; completing from Task Detail (EXPERIENCE.md) moves to Epic 4, where Photo Evidence lands on Detail (decision 6).
- **Deviation:** Story 2.5 is built and closed together with 2.4 (decision 2): `complete_task_instance` also creates the next instance. 2.5's acceptance criteria are covered by named tests in `backend/tests/test_tasks.py` (marked "2.5").

### Story 2.5: Auto-Reschedule on Completion

**Stage:** Trinn 1

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

*Built with Story 2.4 on 2026-11-11 (Story 2.4 spec, decision 2).* Each criterion is covered by a test in `backend/tests/test_tasks.py`: `test_complete_records_who_and_when_and_adds_the_next_instance` (N days from the completion date), `test_late_completion_counts_from_the_completion_date` (2 days late, a full 30 days), `test_completion_on_setup_day_gives_the_next_instance_the_same_date`, and `test_a_retry_double_tap_or_second_member_changes_nothing` (idempotent). The photo-upload path (AD-3) calls the same function in Epic 4.

### Story 2.6: Add and Remove Tasks

**Stage:** Trinn 1 · **Source:** issue #31, Sprint Change Proposal 2026-11-09 · **FR:** FR-24, FR-4, FR-8 · **AD:** AD-2, AD-3, AD-6, AD-16 · **Builds on:** 2.2 (Task Overview), 2.3 (Task Detail), 2.4 (completion history)

As a Household Member or Landlord,
I want to add tasks my Home needs and remove the ones it no longer needs,
So that the task list keeps matching my Home after the first setup.

*Decisions 2026-11-12 (Eirik, Story 2.6 spec; no acceptance criterion below changes):* Add Task is one page (a radio list of the catalog types the Home lacks plus «Egen oppgave»), «Legg til oppgave» sits in the Task Overview header, the overview shows «La til «X».» and «Fjernet «X».» once through the one-time notice, and adding before Task Setup has run answers 409. The same flag, `can_adjust_tasks`, covers add and archive. Adjusting or completing an archived Task is 404, archiving it again is 204.

**Acceptance Criteria:**

**Given** a Household Member or Landlord on Task Overview
**When** they choose «Legg til oppgave»
**Then** Add Task offers the catalog task types the Home has no active Task for, each with its recommended Må/Bør and Frequency to adjust, and a custom Task with name, Må/Bør and Frequency (FR-24)

**Given** a catalog task type or a custom Task is saved
**When** the user lands back on Task Overview
**Then** the new Task is listed in Must-first order with its first instance due on today + Frequency, like Task Setup (Story 2.1)

**Given** a custom Task
**When** it is saved
**Then** it must have a name of 1–100 characters (trimmed) that no other active Task in the Home has (case-insensitive), a Må/Bør classification and a Frequency from the fixed list, or the server answers 422 with a Norwegian message shown at the field (FR-4, FR-8)

**Given** a custom Task
**When** a Landlord later tries to require Photo Evidence on it (Story 4.1)
**Then** the server rejects it, since only catalog types flagged `photo_evidence_eligible` qualify (AD-6)

**Given** a Household Member or Landlord on Task Detail
**When** they choose «Fjern oppgaven» and confirm inline
**Then** the Task is archived: it disappears from Task Overview for every Member, its instances and completions stay, and the user lands on Task Overview with «Fjernet «X».» (UX: Remove Task confirmation, Task removed)

**Given** a catalog task type whose Task was archived
**When** it is added again
**Then** it becomes a new Task with a new first due date; the archived Task and its history are unchanged

**Given** a repeated archive of the same Task (double tap, second tab)
**When** the request arrives
**Then** nothing changes and the user is not shown an error

**Given** a Home whose every Task is archived
**When** a Member opens Task Overview
**Then** it shows the No active Tasks state, and Task Setup is not offered again (`has_tasks` means setup has run)

**Given** a Tenant
**When** they view Task Overview or Task Detail, or call the add or archive routes directly
**Then** they see neither «Legg til oppgave» nor «Fjern oppgaven», and the server answers 403 (AD-2; the route walk in `test_permissions.py` covers the new routes)

**Given** adding or archiving fails server-side
**When** the user sees the result
**Then** an inline error with a retry affordance shows at the action (UX-DR30)

**Given** this story is delivered
**When** the README is read
**Then** it describes how to add a custom Task and remove a Task, and `deferred-work.md`'s custom-task entry has its outcome

## Epic 3: Notifications

Members receive a push notification when a task becomes due or overdue, with fairness-based targeting when one Member has fallen behind; Landlords can send ad-hoc broadcasts and configure how strictly Tenants are reminded.

### Story 3.1: Push Notification Permission & Device Registration

**Stage:** Trinn 2

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

**Stage:** Trinn 2

As a Member with a task due or overdue,
I want to be notified by push without having to check the app myself,
So that I never silently miss a task.

**Acceptance Criteria:**

**Given** a dedicated `GET /api/internal/run-due-check` endpoint
**When** it is called
**Then** it scans for task instances that are due or overdue and sends each relevant Member one push notification covering all of their due and overdue tasks (FR-10)

**Given** Vercel Cron calling this endpoint once a day (`0 6 * * *` UTC) with `Authorization: Bearer <CRON_SECRET>`
**When** it fires
**Then** the due/overdue scan runs without an in-process scheduler, and a request without the correct secret is rejected (AD-8)

**Given** the endpoint is called twice in quick succession (concurrent or overlapping triggers)
**When** both calls scan the same due/overdue window
**Then** no Member receives a duplicate notification for the same task instance and day (Vercel may deliver one cron event twice)

**Given** a Member receives a due/overdue push notification
**When** they tap it
**Then** a notification about one task opens that task's Task Detail, and one about several tasks opens Task Overview — no in-app notification inbox exists (UX-DR17)

**Given** no VAPID keys are configured (local running)
**When** the due-check endpoint is called by hand or by a script
**Then** the mock push sender records the notifications it would have sent instead of delivering them, so the due/overdue logic can be run and tested without external accounts (FR-22, AD-15)

*Added 2026-11-08 (Sprint Change Proposal, AD-16):*

**Given** a user who has left a Home
**When** the due-check runs
**Then** they receive no notification for that Home

### Story 3.3: Fairness-Based Targeted Notification

**Stage:** Trinn 2

As a Member who already did a shared recurring task multiple times,
I want the reminder to go to whoever hasn't done it, not to everyone,
So that completion feels fair rather than me nagging my housemates.

**Acceptance Criteria:**

**Given** a recurring shared task where Member A completed the last 3 instances and Member B completed 0 of those 3
**When** the due-check job runs
**Then** a targeted nudge notification is sent to Member B specifically, not broadcast to the whole Home (FR-11, AD-9)

**Given** a recurring shared task in a Home with only one current Member, or with fewer than three completed instances
**When** the due-check job runs
**Then** the fairness nudge does not fire (PRD FR-11: at least two current Members and three completed instances)

**Given** a task instance that is already completed
**When** the due-check job runs
**Then** no fairness nudge is sent for it — the nudge only fires while the instance is open and due or overdue, and at most once per task instance (SM-15)

**Given** a recurring shared task where no Member has completed any of the last 3 instances
**When** the due-check job runs
**Then** the fairness nudge does not fire — the regular due/overdue notification still applies instead

**Given** Martin (UJ-3) receives a fairness-targeted nudge
**When** he reads it
**Then** the copy is indistinguishable in tone from a normal due/overdue reminder — no "you're the only one" framing

*Added 2026-11-08 (Sprint Change Proposal, AD-16):*

**Given** a Member who has left
**When** fairness is computed
**Then** they are neither counted nor targeted

### Story 3.4: Landlord Ad-Hoc Broadcast Message

**Stage:** Trinn 2

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

*Added 2026-11-08 (Sprint Change Proposal, AD-16):*

**Given** a removed Tenant
**When** the Landlord broadcasts
**Then** the recipient count and recipients include current Tenants only

### Story 3.5: Landlord-Controlled Notification Cadence

**Stage:** Trinn 2

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

**Given** the cadence options
**When** they are shown to the Landlord
**Then** they are whole-day intervals (for example daily, every second day, weekly), since reminders come from the daily due-check (FR-13, AD-8)

**Given** a Tenant
**When** they attempt to change their Home's notification cadence
**Then** the request is rejected server-side — cadence is Landlord-only

**Given** a cadence save fails server-side
**When** the Landlord sees the result
**Then** an inline error with a retry affordance shows at the action — not a silent failure (UX-DR30)

## Epic 4: Photo Evidence

A Landlord can flag a specific Must task (restricted to system-eligible task types) as requiring Photo Evidence; a Tenant uploads a photo and the task auto-approves immediately, with the photo staying available for Landlord review and being auto-replaced on the next completion.

### Story 4.1: Landlord Requires Photo Evidence on Eligible Must Tasks

**Stage:** Trinn 2

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

**Stage:** Trinn 2

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

**Given** no `BLOB_READ_WRITE_TOKEN` is configured (local running)
**When** a photo is uploaded
**Then** it is stored through the local filesystem adapter under the same fixed per-task key, so Photo Evidence can be run and tested without external accounts (FR-22, AD-15)

### Story 4.3: Landlord Reviews Evidence & Auto-Replacing Photo Storage

**Stage:** Trinn 2

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

**Given** a stored photo
**When** the Landlord views it
**Then** it is served through a backend route that runs `require_role` first (streamed, or a short-lived signed URL if private Blob storage supports it); no permanent Blob URL ever reaches the browser (AD-5, NFR5)

**Given** a Tenant's task history and Photo Evidence
**When** visibility is checked
**Then** it is visible to that Tenant's own Landlord but never to other Tenants or other Landlords outside that Home (NFR6)

*Added 2026-11-08 (Sprint Change Proposal, AD-16):*

**Given** evidence uploaded by a Tenant who has since been removed
**When** the Landlord reviews it
**Then** it shows «Tidligere medlem» as uploader and stays reviewable

## Epic 5: AI Assistant

Any Member can tap "?" on a task for an immediate, disclaimer-carrying how-to answer, escalate to a full AI chat, and a new Tenant receives an AI-generated onboarding guide tailored to their Home when they join.

### Story 5.1: Contextual Quick-Answer ("?")

**Stage:** Trinn 1

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

**Given** no AI API key is configured
**When** a Member taps "?"
**Then** the mock provider returns a canned, task-specific answer in the same structure with the disclaimer, and the UI marks it as demo mode — the feature can be run and tested without any external account (FR-22, AD-15)

*Added 2026-11-12 (Sprint Change Proposal, teacher's PRD feedback; FR-14, AD-4, SM-7):*

**Given** the AI call fails or takes longer than 10 seconds
**When** the popover is open
**Then** it shows an error message (`status: "error"`) and a retry action, and the task can still be completed; the timeout is a constant, not a literal in the route

**Given** a user has made 20 AI calls today (quick answers and chat together)
**When** they tap "?" again
**Then** the popover says plainly that the daily limit is reached and when it resets; the limit counts mock answers too and is stored per user and day in a new table `ai_usage` (Alembic migration), so it is testable offline

**Given** any call to the AI provider
**When** the request is built
**Then** it contains only the task's name, its catalog type and the user's own question — no user names, e-mail addresses or Home names — and a test asserts the payload

**Given** the "?" popover
**When** it shows an answer
**Then** a short line next to the disclaimer says that the question is sent to an external AI service (Google Gemini)

**Given** the backend AI service
**When** it is built in this story
**Then** it sits behind a provider interface with a Gemini provider and a mock provider, the real Gemini provider is used only when `GEMINI_API_KEY` is set, and the automated tests always use the mock provider (AD-4, AD-15)

### Story 5.2: Escalate to Full AI Chat

**Stage:** Trinn 2

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
**Then** it follows the same timeout (10 seconds), daily limit (20 calls per user, shared with the quick-answer) and call-content rules as Story 5.1 (FR-15)

**Given** AI Chat
**When** it calls the backend
**Then** it uses the same shared AI service (AD-4) as the quick-answer — not a separate implementation

### Story 5.3: AI-Generated Onboarding Guide for New Tenants

**Stage:** Trinn 2

As a new Tenant joining a Home,
I want a short guide tailored to this specific Home,
So that I understand how the app and my obligations work without asking my Landlord to explain everything.

**Acceptance Criteria:**

**Given** a Landlord provisions a Home and invites Tenants
**When** the onboarding guide is generated
**Then** it is generated once per Home at provisioning time and persisted — not regenerated on every view (FR-16, AD-4)

**Given** a new Tenant accepts an invite
**When** they first open Task Overview
**Then** the guide surfaces as a one-time dismissible card at the top of the list — naming the Home and listing its active Must tasks with their frequencies, so two Homes with different tasks never get the same text

**Given** the Tenant dismisses the card
**When** they want to see it again later
**Then** it remains reachable from Settings

**Given** the guide generation
**When** it runs
**Then** it goes through the same single backend AI service (AD-4) as the other AI surfaces, with the disclaimer applied consistently if the guide contains how-to content

## Epic 6: Landlord Portfolio Dashboard

A Landlord who owns more than one Home sees a single aggregated view of on-track/behind status across all their Homes and units, letting them triage without a site visit.

### Story 6.1: Landlord Portfolio Dashboard

**Stage:** Trinn 2

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

*Moved from Story 2.2 on 2026-11-10 (team decision 5 in the Story 2.2 spec; the tab has nothing to open before this story):*

**Given** a Landlord with two or more Landlord Homes
**When** any signed-in page renders
**Then** the tab bar from Story 2.2 also shows a Portfolio tab that opens this dashboard

**Given** the Portfolio Dashboard
**When** the Landlord pulls down to refresh
**Then** it refetches aggregated status — pull-to-refresh is supported on this surface (UX-DR36)
