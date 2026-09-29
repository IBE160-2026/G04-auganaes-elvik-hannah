---
name: Husly
description: "Placeholder name — team to rename. Household task app spanning private homes and landlord-tenant relationships. 'Sbanken, not DNB': friendly, colorful, and a little playful, but never childish — with an underlying professional polish."
colors:
  primary: '#6E62CC'
  secondary: '#B67F98'
  accent: '#5B96B1'
  surface-base: '#FAF8FF'
  surface-raised: '#FFFFFF'
  ink-primary: '#2A2640'
  ink-secondary: '#6B6480'
  success: '#267F59'
  warning: '#9E641F'
  danger: '#C9404B'
  must-badge: '#B94A6E'
  must-badge-ink: '#FFFFFF'
  should-badge: '#5D6BBE'
  should-badge-ink: '#FFFFFF'
  focus-ring: '#6E62CC'
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 1.5rem
    fontWeight: 700
    lineHeight: 1.2
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 1.125rem
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 0.9375rem
    fontWeight: 500
    lineHeight: 1.45
  meta:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 0.78125rem
    fontWeight: 500
    lineHeight: 1.4
  badge:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 0.625rem
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: 0.03em
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
    typography: '{typography.badge}'
  badge-should:
    background: '{colors.should-badge}'
    color: '{colors.should-badge-ink}'
    radius: '{rounded.full}'
    typography: '{typography.badge}'
  portfolio-row:
    background: '{colors.surface-raised}'
    radius: '{rounded.sm}'
    padding: '{spacing.3}'
  status-tag:
    background: 'must-badge | should-badge pattern — see Components'
    radius: '{rounded.full}'
    typography: '{typography.badge}'
  invite-link-control:
    background: '{colors.surface-raised}'
    border: '1px solid {colors.accent}'
    radius: '{rounded.sm}'
    padding: '{spacing.3}'
  broadcast-composer:
    background: '{colors.surface-raised}'
    radius: '{rounded.md}'
    padding: '{spacing.4}'
    accent: '{colors.accent}'
  frequency-must-toggle:
    editable:
      background: '{colors.surface-raised}'
      border: '1px solid {colors.ink-secondary}'
    locked:
      background: '{colors.surface-base}'
      border: '1px dashed {colors.ink-secondary}'
      icon: 'lock, {colors.ink-secondary}'
    radius: '{rounded.sm}'
  focus-outline:
    color: '{colors.focus-ring}'
    width: 2px
    offset: 2px
---

## Brand & Style

Husly (placeholder name) sits closer to Sbanken than DNB — a deliberate reference the team named directly. That means: modern, colorful, a little playful, never stiff or corporate-cold, but always professional enough to trust with something as unglamorous as chore schedules and rental maintenance. Color and emoji are used with a light hand, not as decoration for its own sake.

The product has two registers sharing one visual system. The **household mode** (Mari, Peter, Sara checking off chores together) leans into the full warmth of the palette — pink and lavender carry real weight, copy is casual, the app can feel a bit fun. The **landlord/portfolio mode** (Johan managing several buildings) pulls back: more neutral surface, tighter information density, restrained accent use, calmer copy. Both modes draw from the same token set — nothing is re-themed; the shift, confirmed with the team, is one of proportion, copy register, and accent restraint, not a different brand or a separate landlord theme.

**Mode is not Role.** "Household mode" / "landlord-portfolio mode" above is a visual-and-copy register — it tracks which *surface* someone is looking at. "Role" (Household Member / Landlord / Tenant, per PRD §2 Glossary) is a permissions concept — it tracks what someone is *allowed to do*. A Landlord viewing their own Portfolio Dashboard is in landlord-portfolio mode; that same Landlord's Tenants, viewing their own Task Overview, are in household mode by register even though their Role is Tenant, not Household Member. The two axes are independent.

No dark mode in v1 — the team confirmed light-only is sufficient for this round.

## Colors

Several tones below were darkened or deepened from their initial exploration shades to clear WCAG contrast floors; final ratios are noted per color.

- **Lavender (`{colors.primary}`, #6E62CC)** — the primary voice. Used for primary buttons, active states, focus rings, and the household mode's dominant chrome. Airy and calm rather than loud. Darkened from initial exploration to clear WCAG AA (4.9:1 on white).
- **Blush Mauve (`{colors.secondary}`, #B67F98)** — secondary accent with real presence: toggles, selected-tab underlines, household-mode illustration moments. Deepened to clear the 3:1 UI-component contrast floor when used as a functional boundary, not just decoration.
- **Muted Teal (`{colors.accent}`, #5B96B1)** — the quiet link back to the "banking-clean" register; used sparingly, mostly in the landlord/portfolio mode where a cooler, calmer accent reads more professional than lavender or mauve would. Deepened to clear the 3:1 functional-UI floor.
- **Surface Base (`{colors.surface-base}`, #FAF8FF)** — the app's canvas; a near-white with the faintest lavender warmth, not clinical white.
- **Surface Raised (`{colors.surface-raised}`, #FFFFFF)** — cards, task rows, portfolio rows sit on true white to lift off the base.
- **Ink Primary / Ink Secondary (#2A2640 / #6B6480)** — near-black-lavender for primary text, a muted lavender-grey for secondary/meta text (due dates, helper copy). Both already clear AA with wide margin (13.7:1 / 5.3:1+) — untouched.
- **Success (#267F59)**, **Warning/Due-soon (#9E641F)**, **Danger/Overdue (#C9404B)** — the only saturated, purely functional colors in the system, never decorative. All three darkened to clear 4.5:1+ against both surface tones with margin (the originals ran as low as 2.76:1).
- **Must-badge (#B94A6E)** and **Should-badge (#5D6BBE)** — the app's most important recurring visual distinction (per PRD FR-6, Must always sorts first). Must reads warm/urgent-adjacent (rose-burgundy family) without colliding with true Danger red at a glance; Should reads cool/calm (indigo-blue family). Darkened to clear 4.6:1+ (the originals were 3.3:1 / 3.64:1).
- **Focus ring (`{colors.focus-ring}`, same as primary)** — the visible-focus indicator required on every interactive element (WCAG 2.4.7), 2px outline with 2px offset, verified ≥4.3:1 against both surface tones.

Avoid: stacking Must-badge against Danger red in the same view without enough separation (spacing or grouping) — the two are close enough in family that adjacency can read as a single alarm rather than two distinct signals; both states additionally carry a text label ("Must" / "Forfalt") so color is never the sole signal (see EXPERIENCE.md Accessibility Floor). Avoid full-saturation fills for large surfaces — every chromatic color here works as an accent, badge, or 2px focus ring, never as a background wash.

## Typography

System font stack throughout — the team explicitly asked for "the same font as iPhone Reminders," which resolves to San Francisco on Apple devices via `-apple-system` / `BlinkMacSystemFont`, with Segoe UI / Roboto as the non-Apple equivalent. No custom webfont; this is a deliberate choice for familiarity (task apps should feel like they belong on the device) and to keep the 3-person team from managing font-loading performance.

Sizes are specified in `rem`, not `px`, against a 16px root — this is required so the type scale honors the browser/OS text-size setting (WCAG 1.4.4, resize to 200%) rather than staying fixed.

- **`display`** (1.5rem / 700) — screen-level headers, for example "Dagens oppgaver."
- **`title`** (1.125rem / 700) — card, dialog, and section headers.
- **`body`** (0.9375rem / 500) — every task title, button label, and primary content; weight 500 rather than 400 so text holds up at a glance on mobile.
- **`meta`** (0.78125rem / 500) — due dates, timestamps, and helper text.
- **`badge`** (0.625rem / 700, uppercase-tracked) — Must/Should badge text only. Called out as its own role because it's too small to claim the WCAG large-text exemption, so badge colors were darkened to clear 4.5:1 outright (see Colors).

## Layout & Spacing

Scale: 4 / 8 / 12 / 16 / 24 / 32 / 48px (`{spacing.1}`–`{spacing.7}`). Household mode favors the larger end of the scale — generous card padding (`{spacing.4}`), breathing room between task rows — reinforcing the "playful, not cramped" register. Landlord/portfolio mode tightens toward the smaller end — denser rows, smaller gaps — because Johan is scanning many units at once and density communicates "professional tool," not "consumer app."

Mobile-first single column; tablet/desktop introduce a secondary column only where FR-21's responsive requirement calls for it — for example, the portfolio dashboard gains a side list + detail split at wider viewports (see `EXPERIENCE.md.Responsive & Platform` for the committed breakpoint values). No more than one modal layer deep. At 400% zoom / 320 CSS px width, every surface reflows to a single column with no horizontal scroll — the `rem`-based type scale and the mobile-first single-column default are what make this achievable without a separate zoomed layout.

## Elevation & Depth

Minimal elevation. Cards and rows are distinguished from the canvas by the `surface-base` → `surface-raised` tone shift (per Colors), not by heavy shadow. A single soft, low-opacity shadow (`0 2px 6px rgba(0,0,0,.05)`, as prototyped in the color exploration) is enough to lift a card without adding visual noise. Reserve any stronger elevation for transient surfaces only — a modal or the AI chat panel over its background. All transitions (popover open/close, the AI-pending skeleton, optimistic-update state changes) must respect `prefers-reduced-motion` — replace the animated transition with an instant state change when the preference is set, never remove the resulting state itself.

## Shapes

Rounded, soft corners throughout, per the team's explicit direction ("Sbanken-aktig"). `{rounded.sm}` (8px) for inputs, small controls, and the invite-link and frequency/must-toggle containers. `{rounded.md}` (14px) for cards, task rows, and dialogs — the default corner. `{rounded.lg}` (20px) for larger surfaces and sheets. `{rounded.full}` (pill) for badges (Must/Should, portfolio status tags) and primary buttons — the pill shape is the strongest "friendly, not corporate" signal in the system and should stay reserved for those roles so it keeps its meaning.

## Components

→ Composition reference: `mockups/task-overview.html`, `mockups/task-detail.html`, `mockups/portfolio-dashboard.html`. EXPERIENCE.md wins on conflict with any mock.

- **Primary button** — `{colors.primary}` fill, white text (4.9:1), `{rounded.full}` pill shape. Used for the one dominant action per screen (for example, "Fullfør oppgave," "Send invitasjon"). States: default, pressed (8% darker overlay), disabled (`{colors.ink-secondary}` background, no pill outline change), and a text-only "Sender…" label swap for in-flight submission — never a spinner alone, without an accompanying text label.
- **Task card** — `{colors.surface-raised}`, `{rounded.md}`, checkbox + title (`body`) + Must/Should badge inline + due date (`meta`) below. Completed state: checkbox filled, title strikethrough, due date recolors to `{colors.success}` with completion label. Checkbox and row are two independent tap/focus targets, in that order in the reading/tab sequence.
- **Must/Should badge** and **status tag** (Portfolio row's overdue/on-track indicator) — pill (`{rounded.full}`), `{typography.badge}`, always carry a text label (never an icon or color alone) — "Must"/"Should" on the badge, "Forsinket"/"Alt i orden" on the portfolio status tag.
- **Portfolio row** (landlord mode) — tighter padding than task card, `{rounded.sm}`, building name (`body`) + unit count and status (`meta`) + the status tag described above.
- **Quick-answer popover** — anchored to the task's "?" affordance, `{colors.surface-raised}`, `{rounded.md}`, includes the always-visible AI disclaimer (per PRD FR-14) in `meta` weight beneath the answer text. Loading state is an inline skeleton line, not a spinner; the arriving answer is announced via `aria-live="polite"` (see EXPERIENCE.md Accessibility Floor).
- **Photo evidence upload** — appears only on Must tasks flagged by a Landlord (FR-18); camera/upload affordance in `{colors.accent}` (now 3.3:1, clears the 3:1 UI-component floor), confirms upload with a `{colors.success}` state, never blocks on approval per FR-19.
- **Invite link control** — `{colors.surface-raised}` with a `{colors.accent}` border, `{rounded.sm}`. Renders only for roles permitted to invite (any Household Member or a Landlord); for a Tenant, this control is absent from the layout entirely, not present-and-disabled.
- **Broadcast composer** — `{colors.surface-raised}`, `{rounded.md}`, free-form text field with an `{colors.accent}` send action; confirms with recipient count ("Sendt til N leietakere") on success.
- **Frequency/Must toggle** — two visual states, not one: *editable* (white surface, solid `{colors.ink-secondary}` border — Household Member or Landlord) and *locked* (`{colors.surface-base}` fill, dashed border, a visible lock glyph in `{colors.ink-secondary}` plus the "Satt av utleier" label — Tenant view only). The locked state stays focusable (not `disabled`) so its label is reachable by assistive tech — see EXPERIENCE.md Accessibility Floor for the ARIA technique.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Reserve `{rounded.full}` pills for badges, status tags, and primary buttons only | Use pill shapes for every container — it dilutes the signal |
| Keep landlord/portfolio views denser and cooler-toned within the same palette | Introduce a visually separate "professional theme" — one token set, two moods |
| Use Must/Should badges and the overdue/status-tag state consistently with a text label every time | Rely on color alone to distinguish Must from Should, or due-soon from overdue |
| Use system font weights (500/700) and `rem` sizing to keep text legible and zoom-honoring | Introduce a custom webfont, a fixed-`px` type scale, or additional weights |
| Keep chromatic color (mauve, lavender, teal) to accents, badges, and primary actions | Use saturated color as a large background wash |
| Show the 2px `{colors.focus-ring}` outline on every interactive element, including split targets like the task-card checkbox | Suppress the focus outline for aesthetic reasons |
| Respect `prefers-reduced-motion` for every transition and loading skeleton | Ship motion as the only cue that a state changed |
