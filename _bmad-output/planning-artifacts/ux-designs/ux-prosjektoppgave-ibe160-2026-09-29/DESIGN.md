---
name: Husly
description: "Placeholder name — team to rename. Household task app spanning private homes and landlord-tenant relationships. 'Sbanken, not DNB': friendly, colorful, and a little playful, but never childish — with an underlying professional polish."
colors:
  primary: '#7B6EE3'
  secondary: '#F0A8C9'
  accent: '#6FB8D9'
  surface-base: '#FAF8FF'
  surface-raised: '#FFFFFF'
  ink-primary: '#2A2640'
  ink-secondary: '#6B6480'
  success: '#2F9E6E'
  warning: '#D98A2B'
  danger: '#D64550'
  must-badge: '#E85D8A'
  must-badge-ink: '#FFFFFF'
  should-badge: '#6E7FE0'
  should-badge-ink: '#FFFFFF'
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 1.2
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 18px
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 15px
    fontWeight: 500
    lineHeight: 1.45
  meta:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 12.5px
    fontWeight: 500
    lineHeight: 1.4
rounded:
  sm: 8px
  md: 14px
  lg: 20px
  full: 9999px
  DEFAULT: 14px
spacing:
  '1': 4px
  '2': 8px
  '3': 12px
  '4': 16px
  '5': 24px
  '6': 32px
  '7': 48px
components:
  button-primary:
    background: '{colors.primary}'
    color: '#FFFFFF'
    radius: '{rounded.full}'
    fontWeight: '{typography.body.fontWeight}'
  task-card:
    background: '{colors.surface-raised}'
    radius: '{rounded.md}'
    padding: '{spacing.4}'
  badge-must:
    background: '{colors.must-badge}'
    color: '{colors.must-badge-ink}'
    radius: '{rounded.full}'
  badge-should:
    background: '{colors.should-badge}'
    color: '{colors.should-badge-ink}'
    radius: '{rounded.full}'
  portfolio-row:
    background: '{colors.surface-raised}'
    radius: '{rounded.sm}'
    padding: '{spacing.3}'
---

## Brand & Style

Husly (placeholder name) sits closer to Sbanken than DNB — a deliberate reference the team named directly. That means: modern, colorful, a little playful, never stiff or corporate-cold, but always professional enough to trust with something as unglamorous as chore schedules and rental maintenance. Color and emoji are used with a light hand, not as decoration for its own sake.

The product has two registers sharing one visual system. The **household mode** (Mari, Peter, Sara checking off chores together) leans into the full warmth of the palette — pink and lavender carry real weight, copy is casual, the app can feel a bit fun. The **landlord/portfolio mode** (Johan managing several buildings) pulls back: more neutral surface, tighter information density, restrained accent use, calmer copy. Both modes draw from the same token set — nothing is re-themed — the shift is one of *proportion and tone*, not a different brand. `[ASSUMPTION: the household/landlord tonal split is expressed through density, copy register, and accent restraint rather than a separate color scheme, since the selected palette (Lavender Air) was chosen as one unified light theme, not the dual-register variant explored alongside it. Flag if a visually distinct landlord theme is wanted instead.]`

No dark mode in v1 — the team confirmed light-only is sufficient for this round.

## Colors

- **Lavender (`{colors.primary}`, #7B6EE3)** — the primary voice. Used for primary buttons, active states, and the household mode's dominant chrome. Airy and calm rather than loud.
- **Blush Pink (`{colors.secondary}`, #F0A8C9)** — secondary accent with real presence, not a decoration. Appears in household-mode illustration/accent moments and lighter-weight UI (toggles, selected-tab underlines).
- **Sky Accent (`{colors.accent}`, #6FB8D9)** — the quiet link back to the "banking-clean" register; used sparingly, mostly in the landlord/portfolio mode where a cooler, calmer accent reads more professional than lavender or pink would.
- **Surface Base (`{colors.surface-base}`, #FAF8FF)** — the app's canvas; a near-white with the faintest lavender warmth, not clinical white.
- **Surface Raised (`{colors.surface-raised}`, #FFFFFF)** — cards, task rows, portfolio rows sit on true white to lift off the base.
- **Ink Primary / Ink Secondary (#2A2640 / #6B6480)** — near-black-lavender for primary text, a muted lavender-grey for secondary/meta text (due dates, helper copy).
- **Success (#2F9E6E)**, **Warning/Due-soon (#D98A2B)**, **Danger/Overdue (#D64550)** — the only saturated, purely functional colors in the system. Never used decoratively.
- **Must-badge (#E85D8A)** and **Should-badge (#6E7FE0)** — the app's most important recurring visual distinction (per PRD FR-6, Must always sorts first). Must reads warm/urgent-adjacent (pink-red family) without colliding with true Danger red; Should reads cool/calm (blue-lavender family).

Avoid: stacking Must-badge pink directly against Danger red in the same view without enough separation (spacing or grouping) — the two are close enough in hue that adjacency reads as a single alarm rather than two distinct signals. Avoid full-saturation fills for large surfaces — every chromatic color here works as an accent or badge, never as a background wash.

## Typography

System font stack throughout — the team explicitly asked for "the same font as iPhone Reminders," which resolves to San Francisco on Apple devices via `-apple-system` / `BlinkMacSystemFont`, with Segoe UI / Roboto as the non-Apple equivalent. No custom webfont; this is a deliberate choice for familiarity (task apps should feel like they belong on the device) and to keep the 3-person team from managing font-loading performance.

`display` (24px/700) is reserved for screen-level headers (e.g. "Dagens oppgaver"). `title` (18px/700) names cards, dialogs, and section headers. `body` (15px/500) is every task title, button label, and primary content — weight 500 rather than 400 so text holds up at a glance on mobile. `meta` (12.5px/500) is due dates, timestamps, and helper text.

## Layout & Spacing

Scale: 4 / 8 / 12 / 16 / 24 / 32 / 48px (`{spacing.1}`–`{spacing.7}`). Household mode favors the larger end of the scale — generous card padding (`{spacing.4}`), breathing room between task rows — reinforcing the "playful, not cramped" register. Landlord/portfolio mode tightens toward the smaller end — denser rows, smaller gaps — because Johan is scanning many units at once and density communicates "professional tool," not "consumer app."

Mobile-first single column; tablet/desktop introduce a secondary column only where FR-21's responsive requirement calls for it (e.g. portfolio dashboard gains a side list + detail split at wider viewports). No more than one modal layer deep.

## Elevation & Depth

Minimal elevation. Cards and rows distinguish from the canvas by the `surface-base` → `surface-raised` tone shift (per Colors), not by heavy shadow. A single soft, low-opacity shadow (`0 2px 6px rgba(0,0,0,.05)`, as prototyped in the color exploration) is enough to lift a card without adding visual noise. Reserve any stronger elevation for transient surfaces only — a modal or the AI chat panel over its background.

## Shapes

Rounded, soft corners throughout, per the team's explicit direction ("Sbanken-aktig"). `{rounded.sm}` (8px) for inputs and small controls. `{rounded.md}` (14px) for cards, task rows, and dialogs — the default corner. `{rounded.lg}` (20px) for larger surfaces and sheets. `{rounded.full}` (pill) for badges (Must/Should) and primary buttons — the pill shape is the strongest "friendly, not corporate" signal in the system and should stay reserved for those two roles so it keeps its meaning.

## Components

- **Primary button** — `{colors.primary}` fill, white text, `{rounded.full}` pill shape. Used for the one dominant action per screen (e.g. "Fullfør oppgave," "Send invitasjon").
- **Task card** — `{colors.surface-raised}`, `{rounded.md}`, checkbox + title (`body`) + Must/Should badge inline + due date (`meta`) below. Completed state: checkbox filled, title strikethrough, due date recolors to `{colors.success}` with completion label.
- **Must/Should badge** — pill (`{rounded.full}`), `{colors.must-badge}` or `{colors.should-badge}` fill, white text, always rendered inline with the task title per FR-6's must-first ordering.
- **Portfolio row** (landlord mode) — tighter padding than task card, `{rounded.sm}`, building name (`body`) + unit count and status (`meta`) + a compact status tag (`{colors.danger}` if overdue Must tasks exist, `{colors.success}` if all clear).
- **AI quick-answer popover** — anchored to the task's "?" affordance, `{colors.surface-raised}`, `{rounded.md}`, includes the always-visible AI disclaimer (per PRD FR-14) in `meta` weight beneath the answer text.
- **Photo evidence upload control** — appears only on Must tasks flagged by a Landlord (FR-18); camera/upload affordance in `{colors.accent}`, confirms upload with a `{colors.success}` state, never blocks on approval per FR-19.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Reserve `{rounded.full}` pills for badges and primary buttons only | Use pill shapes for every container — it dilutes the signal |
| Keep landlord/portfolio views denser and cooler-toned within the same palette | Introduce a visually separate "professional theme" — one token set, two moods |
| Use Must/Should badges consistently, always inline with the task title | Rely on color alone to distinguish Must from Should — pair with the badge label text too |
| Use system font weights (500/700) to keep small text legible | Introduce a custom webfont or additional weights |
| Keep chromatic color (pink, lavender, accent blue) to accents, badges, and primary actions | Use saturated color as a large background wash |
