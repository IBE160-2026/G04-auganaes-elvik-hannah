---
name: Husly
status: final
sources:
  - _bmad-output/planning-artifacts/prds/prd-prosjektoppgave-ibe160-2026-09-29/prd.md
  - _bmad-output/planning-artifacts/briefs/brief-prosjektoppgave-ibe160-2026-09-12/brief.md
updated: 2026-10-04
---

# Husly (placeholder name) — Experience Spine

## Foundation

`DESIGN.md` is the visual identity reference; this spine is the behavior. Responsive single web app — phone, tablet, and desktop (PRD FR-21) — no native app in v1. No UI system named; the team's stack is a Python backend with a React (JavaScript) frontend. No dark mode in v1 (DESIGN.md).

Three Roles read the same surfaces differently throughout, per PRD §2 Glossary: **Household Member** (single, samboer, kollektiv — full read/write on their Home), **Landlord** (elevated, multi-Home), and **Tenant** (locked-down, single Home). Every surface below states which roles reach it and how permissions change what they see.

`[NOTE FOR UX]` PRD Open Question 3 (can one account hold both a Landlord Role in one Home and a Household Member Role in another?) is unresolved at the PRD level. This spine assumes single-role-per-account as the simpler v1 case and does not design a Home-switcher for a dual-role account. If PRD OQ3 resolves toward allowing dual roles, this Foundation and the IA below need a revisit — flagged here rather than silently designed around.

## Information Architecture

| Surface | Reached from | Roles | Purpose |
|---|---|---|---|
| Sign in / Register | App open (cold), or an invite link | All | Authenticate, or register via invite link and land inside the linked Home |
| Create Home | Post-auth, no Home yet | Household Member, Landlord | Choose Household Home or Landlord Home, then a short Task Setup step: review the app's recommended Must/Should task list (PRD FR-4) and accept or adjust before landing on Task Overview — applies to both Home types, not just Landlord setup |
| Task Overview | Tab bar / home screen | Household Member, Tenant, Landlord (per-Home) | Must-first task list for one Home (PRD FR-6); primary landing surface |
| Task Detail | Task Overview row tap | Household Member, Tenant, Landlord | Full task info, "?" quick-answer, mark complete, photo evidence upload where required. For Household Members, the Must/Should classification and Frequency are directly editable inline here (PRD FR-5, FR-8) — no separate admin screen needed for this lighter-weight peer role. For Tenants, the same fields render locked (see Frequency/Must toggle, Component Patterns). |
| AI Chat | Task Detail "?" → "Ask more" | Household Member, Tenant, Landlord | Full conversational follow-up (PRD FR-15) |
| Members & Invite | Task Overview header | Household Member (any), Landlord only | Generate invite link, view member list. Tenants cannot reach the invite action (PRD FR-2). |
| Landlord Portfolio Dashboard | Tab bar (Landlord only, ≥2 Homes) | Landlord | Aggregated status across all owned Homes (PRD FR-20) |
| Landlord Home Admin | Portfolio row tap, or single-Home settings | Landlord | Bulk Must/Should, Frequency, and Photo Evidence requirement management across a Home's tasks, notification cadence, compose broadcast message (PRD FR-5, FR-8, FR-13, FR-18) — the Landlord's heavier equivalent of the inline editing Household Members get on Task Detail |
| Settings / Profile | Tab bar | All | Account, notification permission status, sign out |

No in-app notification inbox in v1 — a push notification deep-links straight to Task Detail (confirmed with the team; PRD FR-10/FR-11/FR-12 stay push-only).

`[NOTE FOR UX]` PRD FR-18's Photo Evidence eligibility restriction (which task types may require a photo) is itself an open `[ASSUMPTION]` in the PRD — whether it's enforced via a curated system allowlist or left to Landlord judgment is undecided (PRD §Privacy Constraints). This spine's Landlord Home Admin currently exposes an unconstrained per-task toggle; if the PRD resolves toward a system allowlist, Landlord Home Admin needs a corresponding "eligible task types only" constraint added to the toggle's available options.

A first-time Tenant's Task Overview visit surfaces the AI-generated onboarding guide (PRD FR-16) as a one-time dismissible card at the top of the list — not a separate surface, so it doesn't compete with the IA above, but reachable again later from Settings if dismissed.

→ Composition reference: `mockups/task-overview.html`, `mockups/task-detail.html`, `mockups/portfolio-dashboard.html`. These three illustrate the Task Overview, Task Detail (including the Quick-answer popover and Photo Evidence states), and Landlord Portfolio Dashboard surfaces. Spine (this file and DESIGN.md) wins on conflict with any mock.

## Voice and Tone

Microcopy only. Brand voice and aesthetic posture live in `DESIGN.md.Brand & Style`. The household/landlord tonal split from DESIGN.md carries into copy directly: household copy is warm and a little playful; landlord copy is neutral and information-first. All copy is Norwegian-only in v1 — no `lang` mixing is expected, including AI-generated answers, which the AI Assistant is instructed to return in Norwegian; if the AI ever mixes languages in a response, that response inherits the page's declared `lang` rather than being marked separately.

| Do (Household) | Don't (Household) |
|---|---|
| "Bra jobba — badet er ferdig! 🎉" | "Achievement unlocked: Bathroom Master" |
| "Peter tok denne i dag." | "✓ Task completed by user Peter" |
| "Usikker på noe? Trykk ? for hjelp." | "Need assistance? Click here!!!" |

| Do (Landlord) | Don't (Landlord) |
|---|---|
| "Bygg A — 1 forsinket must-oppgave." | "Bygg A: 🚨 UH OH! Something's overdue!" |
| "Sendt til 4 leietakere." | "Your message has been successfully dispatched." |
| "Kreve bildebevis for denne oppgaven?" | "Enable photo verification mode" |

Shared rule both registers respect: never frame a missed task as a failure or shame the person who didn't do it — the product's own differentiation (PRD §4.5) is replacing gamification/shame mechanics with help, not adding guilt.

## Component Patterns

Behavioral. Visual specs live in `DESIGN.md.Components`. Names below match `DESIGN.md.Components` verbatim so the two files string-match component by component.

| Component | Use | Behavioral rules |
|---|---|---|
| Primary button | Any surface, one per screen | Default / pressed / disabled / in-flight ("Sender…" text swap, no spinner-only state) — see DESIGN.md for visual states. Disabled state still carries an accessible reason via `aria-describedby` when the disable condition is non-obvious, for example a required field unfilled. |
| Task card | Task Overview list → `mockups/task-overview.html` | Tap anywhere → Task Detail. Checkbox is a distinct tap/focus target from the row (checkbox = quick self-checkoff per FR-17; row tap = detail) — two independently focusable regions, checkbox first in tab order, row second. Must tasks always render above Should tasks (FR-6); within each tier, sort order is by due date. |
| Must/Should badge | Task card, Task Detail | Always renders inline with the task title — the label text ("Must"/"Should") is the signal; color is reinforcement only, never the sole cue. |
| Quick-answer popover | Task Detail → `mockups/task-detail.html` | Tap "?" opens an inline popover, not a full navigation — answer plus disclaimer (FR-14) render without leaving Task Detail. Loading state is a skeleton line announced via `aria-live="polite"`; the arriving answer is announced the same way. A second tap ("Ask more") pushes into AI Chat (FR-15), carrying the task as context. |
| Photo evidence upload | Task Detail, Must tasks flagged by Landlord only | Only rendered when FR-18 applies to this task, via camera or file picker; upload auto-approves the task (FR-19) — no spinner-then-wait state, the UI treats upload and completion as one action. Every uploaded photo requires an accessible description on save, for example "Bildebevis lastet opp av Martin, 29. sep" — not left to the file input's default filename. |
| Invite link control | Members & Invite | Renders only for roles permitted to invite (any Household Member or a Landlord); for a Tenant, the control is absent from the layout entirely — not present-and-disabled, since a disabled-but-visible control here would misrepresent that Tenants can never gain this ability, unlike the Frequency/Must toggle's locked state which represents a per-field, not per-role, restriction. |
| Portfolio row | Landlord Portfolio Dashboard → `mockups/portfolio-dashboard.html` | Tap → Landlord Home Admin for that Home. Status tag carries a text label ("Forsinket" / "Alt i orden"), never color alone — danger tag if any Must task is overdue in that Home, success tag if fully on-track. |
| Broadcast composer | Landlord Home Admin | Free-form message (FR-12); confirms recipient count before sending ("Sendt til N leietakere") rather than naming individuals, keeping the action feeling like one message, not N separate ones. Send-confirmation is announced via `aria-live="polite"` for screen-reader users, not shown only as a visual toast. |
| Frequency/Must toggle | Task Detail (Household Member, editable inline) and Landlord Home Admin (Landlord, editable in bulk) | Two visual states per DESIGN.md: *editable* for Household Members and Landlords, *locked* for Tenants. The locked state stays focusable — implemented with `aria-readonly="true"` and `aria-describedby` pointing at the "Satt av utleier" text, never the native `disabled` attribute, so the reason is announced rather than the control simply going silent for assistive-tech users. |

## State Patterns

| State | Surface | Treatment |
|---|---|---|
| Cold load | Task Overview, Landlord Portfolio Dashboard | Skeleton rows (3-4 placeholder cards/rows) while data loads — distinct from the Empty state below, which only renders once loading has completed and genuinely found nothing. |
| Task due soon | Task card, Task Detail | Due date renders in `{colors.warning}`, bold weight, **and** the word "Snart forfall" — matching the same non-color-only bar set for the overdue state below, rather than relying on color and weight alone. |
| Task overdue | Task card, Task Detail | Due date renders in `{colors.danger}` **and** carries the word "Forfalt" — deliberately distinct in wording from the Must badge's "Must" label so the two signals don't blur into one "everything is red" read (see DESIGN.md Do's and Don'ts). |
| Task completed | Task card | Checkbox filled, title strikethrough, due-date line replaced with completion note in `{colors.success}` ("Fullført i dag" / "Fullført av Peter"). |
| Empty task list | Task Overview | "Ingen oppgaver akkurat nå — nyt det! 🎉" (household) or "Ingen aktive oppgaver i dette hjemmet." (landlord Home Admin view) — never an empty illustration with no text, since the state itself is good news and should say so. |
| Invalid or expired invite link | Sign in / Register | "Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra [utleier/husstandsmedlem]." Never a generic 404; the message names who to ask, since the recipient has no other path back in. |
| Failed login | Sign in / Register | Inline field-level error, not a full-page reload; message never confirms or denies whether an email/username exists (standard auth-enumeration guard). |
| Duplicate registration attempt via invite link | Sign in / Register | If the invited email already has an account, offer "Logg inn i stedet" rather than showing a flat error. |
| Tenant views a locked field | Task Detail (as seen by Tenant) | Rendered read-only with visible lock affordance + "Satt av utleier" label, using `aria-readonly` (see Component Patterns), never a disabled-looking grayed control with no explanation. |
| AI answer pending | Task Detail "?" popover | Short inline loading state (skeleton line, `aria-live="polite"`), not a full-screen spinner — the popover shouldn't feel heavier than the question. |
| AI cannot answer / low confidence | "?" popover, AI Chat | Says so plainly ("Usikker på svaret her — spør gjerne på nytt eller sjekk med noen andre") rather than guessing silently; the disclaimer (FR-14) is always visible regardless of confidence. |
| Photo evidence uploaded | Task Detail | Immediate auto-approve confirmation ("Lastet opp — oppgaven er fullført") — never a "pending landlord review" state, since FR-19 is explicit that review happens after the fact, not before completion. |
| Form submission failure (invite generation, cadence/toggle save, broadcast send) | Members & Invite, Landlord Home Admin | Inline error at the field or action, with a retry affordance — distinct from the generic offline row below, since this is a server-side rejection, not a connectivity gap. |
| No push permission granted | Settings, and once contextually on first due task | Settings row shows current permission status plainly; if denied, Task Overview shows a single dismissible inline note (not a modal) explaining that reminders won't arrive — never a repeating nag. |
| Offline / network error | Any surface with a pending optimistic action (for example, a checkbox tap) | Local optimistic update where safe, with a quiet retry — no blocking error modal for a transient network blip. |

## Interaction Primitives

- Tap to act throughout; the checkbox on a Task card is the one primitive that completes a task directly without opening Task Detail.
- "?" is always a tap-to-reveal inline popover, never a hover-only affordance (this is a touch-first responsive app).
- Long-press is unused/reserved — no custom long-press menus, to keep the interaction model simple for a 13-week build.
- Pull-to-refresh on Task Overview and Landlord Portfolio Dashboard only.
- **Banned:** no gamification mechanics — see Inspiration & Anti-patterns, "Rejected — points/streaks/leaderboards."

## Accessibility Floor

Behavioral. Visual contrast lives in `DESIGN.md` — all functional colors (primary, success, warning, danger, must-badge, should-badge) were darkened during this spine's review specifically to clear WCAG AA 4.5:1 text contrast; accent and secondary clear the 3:1 UI-component floor for their functional (non-decorative) uses.

- **Zoom and reflow (WCAG 1.4.4 / 1.4.10):** honored via the `rem`-based type scale and single-column reflow at 320 CSS px / 400% zoom — see Responsive & Platform for the full commitment.
- Must/Should distinction and due-soon/overdue status are never color-only: badges and status tags always carry their text label, and both due-soon ("Snart forfall") and overdue ("Forfalt") carry the word alongside the color change (see State Patterns, Component Patterns).
- Locked fields use `aria-readonly="true"` + `aria-describedby` (never native `disabled`) so the "Satt av utleier" reason is announced, not silently skipped — see Component Patterns, Frequency/Must toggle.
- Every interactive element carries an accessible label describing both the action and current state: the checkbox ("Merk 'Vask bad' som fullført"), the quick-answer popover and AI Chat message stream (both `aria-live="polite"` on new content), the broadcast composer's send confirmation, and uploaded photo evidence (an accessible description on save, for example "Bildebevis lastet opp av Martin, 29. sep" — never a raw filename).
- Visible focus indicator required on every interactive element, including the task-card checkbox and row as separate focus stops: the 2px `{colors.focus-ring}` outline (DESIGN.md), verified ≥4.3:1 against both surface tones. Never suppressed for aesthetic reasons.
- `prefers-reduced-motion` is honored for every transition and loading skeleton (DESIGN.md Elevation & Depth) — the resulting state still appears, just without the animated transition.
- Tap targets ≥ 44×44px throughout.
- Focus order on every surface follows visual reading order: task list top-to-bottom, Must tasks before Should tasks (matching FR-6's visual order exactly, so keyboard/screen-reader users experience the same priority that sighted users see).

## Inspiration & Anti-patterns

- **Lifted from iOS Reminders:** the simple, single-tap checkbox-to-complete pattern.
- **Rejected — points/streaks/leaderboards (Sweepy, OurHome, Tody):** the PRD explicitly positions Husly's AI assistant as the alternative to gamification-driven completion; introducing streak mechanics later would contradict the product's own differentiation claim.
- **Rejected — a blocking "pending landlord approval" state for photo evidence:** FR-19 auto-approves on upload by design; a review-gate UI would misrepresent how the feature actually works and slow Tenants down for no product reason.

## Responsive & Platform

Mobile-first. Committed breakpoints: **phone** up to 599px, **tablet** 600–1023px, **desktop** 1024px and above. The frontend framework (React, confirmed 2026-10-04) does not impose its own breakpoint convention, so these device-width-based values stand as the team decision — no further revisit pending. Task Overview and Task Detail are single-column at every width — the core loop should never require a wider screen to use comfortably. The Landlord Portfolio Dashboard is the one surface that meaningfully gains a second column, at the tablet breakpoint and above: a building list alongside the selected building's detail, rather than list-then-navigate, since Landlords are more likely to be on a laptop scanning a portfolio than mid-task on a phone.

At 320 CSS px width / 400% browser zoom, every surface — including the two-column Dashboard — collapses to single-column with no horizontal scroll.

## Key Flows

### UJ-1 — Mari and Peter close the loop on a shared home without talking about it

1. Peter receives a push notification (floor + bathroom due).
2. Tap opens Task Detail directly for the bathroom task.
3. Peter taps "?", sees the tile-vs-mirror cleaner answer plus the AI disclaimer, inline — no navigation away.
4. He completes both tasks via Task Overview checkboxes.
5. App recalculates next due dates silently (no confirmation dialog needed — FR-9 is automatic).
6. Later, Mari opens Task Overview and both tasks already show completed state ("Fullført av Peter").
7. **Climax:** Mari sees the completed state the instant she opens the app — no refresh, no digging, the relief is immediate.

Failure: if the "?" answer fails to load (network or AI error), the popover shows "Usikker på svaret her — spør gjerne på nytt" (State Patterns, "AI cannot answer") rather than an infinite skeleton; Peter can still complete the task without an answer.

### UJ-2 — Johan manages a property portfolio without visiting every unit

1. Johan opens the app to the Landlord Portfolio Dashboard (his default landing surface, since he owns ≥2 Homes).
2. Scans portfolio rows; one shows a danger tag ("Forsinket") for the kollektiv behind on cleaning.
3. Taps into that Home's Landlord Home Admin, opens the broadcast composer, sends a reminder.
4. Separately, from the Dashboard he starts "Create Home" for a new unit and generates an invite link; the AI-generated onboarding guide is queued to send once a Tenant accepts.
5. He reviews the app's suggested Must tasks during that Home's Task Setup step and adjusts two.
6. **Climax:** the Dashboard's danger tag for the lagging Home clears once Tenants act on his message — the portfolio view itself becomes his confirmation, no separate report needed.

Failure: if the Dashboard is cold-loading when Johan opens it, skeleton rows render for each known Home (State Patterns, "Cold load") rather than a blank screen; if the broadcast send fails server-side, the composer shows an inline retry rather than silently discarding his message (State Patterns, "Form submission failure").

### UJ-3 — Martin gets a task-specific nudge, not a group scolding

1. Martin receives a push notification targeted only to him (FR-11 — others already completed this recurring task).
2. Tap opens Task Detail; Must tasks are visibly first, further down in his overview.
3. He completes the cleaning, and because this task requires Photo Evidence, the upload control renders.
4. He photographs the cleaned drain and uploads from his phone.
5. Task immediately shows completed — no pending/review state.
6. **Climax:** Martin never sees an accusatory "you're the only one" message anywhere in the UI — the targeting is invisible to him; he just gets a normal reminder, same tone as everyone else's.

Failure: if the photo upload itself fails (bad connection), the upload control shows a retry, not a silent failure that leaves the task looking incomplete for an unclear reason.

### UJ-4 — Sara keeps her own place on track, solo

1. Sara opens Task Overview for her one-person Household Home.
2. Must tasks first, Should tasks after — identical structure to UJ-1, but every task is hers alone; no second name ever appears next to a completion.
3. She uses "?" the same way Peter does when unsure how to do something.
4. **Climax:** the empty-state and completed-state copy never references anyone else ("Fullført i dag," not "Fullført av deg") — the experience quietly holds up for a household of one without feeling like a stripped-down version of the shared-home experience.

Failure: same as UJ-1's "?"-answer failure path — the single-person context doesn't change how AI failure is handled.
