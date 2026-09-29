# Accessibility Review — DESIGN.md / EXPERIENCE.md

Reviewed as a WCAG 2.1 AA pre-build check. Contrast ratios below are computed from the declared hex values using the standard WCAG relative-luminance formula (not estimated). "Load-bearing" = the pairing actually occurs in a component or state defined in the spec, not a hypothetical.

Severity counts: **1 critical, 4 high, 7 medium, 3 low** (15 findings).

---

## Critical

1. **Dynamic type / zoom / reflow is entirely unaddressed.** DESIGN.md's typography scale is defined only in fixed px (24/18/15/12.5px) and nothing in either file mentions WCAG 1.4.4 (resize text to 200%) or 1.4.10 (reflow at 400% zoom / 320 CSS px width, no horizontal scroll). This is a whole success criterion left silent, not just under-specified — a developer building strictly from this spec has no reason to test it and will likely ship fixed layouts (pill buttons, badges, portfolio-row density) that clip or truncate under zoom.
   - **Location:** DESIGN.md `typography` tokens; no counterpart anywhere in EXPERIENCE.md's Responsive & Platform section.
   - **Fix:** Specify the type scale in `rem`, state a requirement that the app reflows to single-column with no horizontal scrolling at 320 CSS px, and add a line to Responsive & Platform committing to 200%/400% zoom testing, especially for the Must/Should badge and primary-button pill shapes which have fixed padding.

## High

2. **Success color (`#2F9E6E`) as text fails AA contrast.** Used as due-date/completion-note text color on both surfaces: on `surface-raised` (`#FFFFFF`) contrast is **3.37:1**; on `surface-base` (`#FAF8FF`) it's **3.20:1**. Both fail the 4.5:1 AA minimum for normal text (this is small `meta`-weight text, not large text).
   - **Location:** DESIGN.md Colors ("Success"), Components ("Task card... due date recolors to `{colors.success}`"); EXPERIENCE.md State Patterns, "Task completed" row.
   - **Fix:** Darken success (target something in the ~`#1E7F58` range to clear 4.5:1 with margin) or re-verify against the actual final shade with a contrast tool before implementation.

3. **Warning color (`#D98A2B`) as due-soon text fails badly.** On white it's **2.76:1** — below even the 3:1 large-text floor, let alone 4.5:1 for the small `meta` text this is used for.
   - **Location:** DESIGN.md Colors ("Warning/Due-soon"); EXPERIENCE.md State Patterns, "Task due soon" row.
   - **Fix:** Darken warning substantially (e.g. toward `#A6660A`) and re-check; this is the worst-performing color in the palette for its actual use.

4. **Must-badge and Should-badge text fail AA, and badge typography is unspecified so no large-text exemption can be claimed.** White text on `must-badge` (`#E85D8A`) is **3.30:1**; white text on `should-badge` (`#6E7FE0`) is **3.64:1**. Both fail 4.5:1. DESIGN.md's `components.badge-must` / `badge-should` tokens define background/color/radius but never a font size or weight, so there's no basis in the spec to argue these qualify as "large text" (3:1 threshold) — this is the single most load-bearing visual element in the app per FR-6.
   - **Location:** DESIGN.md `colors.must-badge`/`should-badge`, `components.badge-must`/`badge-should`.
   - **Fix:** Darken both badge fills to clear 4.5:1 against white text, or explicitly define badge text as bold at ≥18.66px and accept the 3:1 rule deliberately (with the ratios above, should-badge would then pass at 3.64:1 but must-badge at 3.30:1 would still fail even that).

5. **Danger color (`#D64550`) is borderline-failing where it matters most.** As overdue-date text and as white-text-on-danger status tags, contrast is **4.35:1** — just under the 4.5:1 AA threshold for normal text.
   - **Location:** DESIGN.md Colors ("Danger/Overdue"); EXPERIENCE.md State Patterns "Task overdue" row; Component Patterns "Portfolio row" status tag.
   - **Fix:** Darken slightly (e.g. `#C7303D`-ish) to clear 4.5:1 with real margin rather than shipping a value this close to the line, since it's a functional signal (overdue Must tasks) that must remain legible.

## Medium

6. **Primary button text is under 4.5:1.** White text on `{colors.primary}` (`#7B6EE3`) is **4.05:1**. The button label uses `body` (15px/500), and 500-weight does not meet WCAG's bold definition for the large-text exemption, so this needs 4.5:1 and doesn't reach it.
   - **Location:** DESIGN.md `components.button-primary`, `colors.primary`.
   - **Fix:** Darken primary slightly or verify final production shade meets 4.5:1; this is the "Fullfør oppgave" / "Send invitasjon" button, i.e. the one dominant action per screen.

7. **Accent and Secondary fail the 3:1 UI-component minimum where used functionally.** `{colors.accent}` (`#6FB8D9`) against white is **2.20:1**; `{colors.secondary}` (`#F0A8C9`) against white is **1.88:1**. Both are used for functional (non-decorative) UI: accent for the photo-evidence camera/upload affordance, secondary for toggles and selected-tab underlines. WCAG 1.4.11 requires 3:1 for UI component boundaries/states against adjacent color(s).
   - **Location:** DESIGN.md Colors ("Sky Accent", "Blush Pink"); Components "Photo evidence upload control."
   - **Fix:** Darken these when used as functional boundaries, or pair with a non-color cue (outline, icon shape, underline thickness change) so the 3:1 rule isn't the sole differentiator.

8. **Due-soon state is color(+weight)-only, inconsistent with the spec's own stated rule.** EXPERIENCE.md's Accessibility Floor explicitly says Must/Should and overdue are never color-only (overdue adds the literal word "Forfalt"), but the "Task due soon" row states: *"No badge — due-soon is a text-color signal only."* Bold weight is the only non-color addition — it is not a text label, and bold-weight-only is a weak signal for low-vision users who may not perceive weight differences as reliably as an explicit word.
   - **Location:** EXPERIENCE.md State Patterns table, "Task due soon" row — directly inconsistent with the "Task overdue" row two lines below it and with the Accessibility Floor's stated rule.
   - **Fix:** Add a short text cue analogous to "Forfalt" (e.g. "Snart forfall" / "Frist om 2 dager") so due-soon matches the same non-color-only bar the spec sets for every other state.

9. **Locked-field ARIA technique is unspecified, risking a silent contradiction of the stated intent.** EXPERIENCE.md correctly distinguishes "locked-but-visible" (Tenant view of Landlord-set Must/Frequency, with a "Satt av utleier" label) from "entirely absent" (Tenant's invite control) — good design intent. But it never specifies the accessibility API mechanism for the locked case. If a developer implements this with the native `disabled` attribute (the obvious default), the control becomes unfocusable and its label/reason typically goes unannounced by screen readers — silently defeating the explicit goal that it be "announced as read-only with the reason, not simply skipped."
   - **Location:** EXPERIENCE.md Component Patterns, "Frequency/Must toggle" row; Accessibility Floor, "Locked fields" row.
   - **Fix:** Specify the technique explicitly — e.g. keep the control focusable with `aria-readonly="true"` and `aria-describedby` pointing at the "Satt av utleier" text (not native `disabled`) — and require screen-reader verification, not just visual QA, since the visual and AT experience can diverge here.

10. **Portfolio-row status tag risks being color-only.** DESIGN.md describes it as "`{colors.danger}` if overdue Must tasks exist, `{colors.success}` if all clear" with no stated requirement that the tag itself carry text or an icon — distinct from the row's own subtitle copy (e.g. "Bygg A — 1 forsinket must-oppgave" in UJ-2's narrative, which is prose, not confirmed to be part of the tag component).
    - **Location:** DESIGN.md Components, "Portfolio row"; EXPERIENCE.md Component Patterns, "Portfolio row."
    - **Fix:** Require the tag itself (not just adjacent row text) to carry a short label or icon, consistent with the Must/Should-badge and overdue precedent set elsewhere in the same spec.

11. **Screen-reader labeling is demonstrated for one component, not specified systematically.** The Accessibility Floor gives a single worked example (checkbox: "Merk 'Vask bad' som fullført") plus a general assertion that "every interactive element... carries an accessible label." Left unspecified: the "?" popover's role/live-region behavior (does the skeleton-loading state and the arriving answer get announced?), the AI Chat message stream (new-message announcements), alt text for uploaded evidence photos, the broadcast composer's send-confirmation announcement, and the task-card-row-vs-checkbox split target (two independently focusable/interactive regions in one row — order and roles unstated).
    - **Location:** EXPERIENCE.md Accessibility Floor; Component Patterns table generally.
    - **Fix:** Add a short labeling/role table, one row per interactive component, mirroring the checkbox example — with explicit `aria-live` guidance for the "?" popover's loading/answer states and the AI Chat stream.

12. **No visible focus indicator is specified anywhere.** The Accessibility Floor addresses focus *order* but never a focus-*visible* style — no color, thickness, or contrast requirement, and no token for it exists in DESIGN.md's color or component definitions. This is required by WCAG 2.4.7 and is not something a developer can infer from what's given.
    - **Location:** DESIGN.md Colors/Components (absent); EXPERIENCE.md Accessibility Floor.
    - **Fix:** Add a focus-indicator token (e.g. a 2px outline verified at ≥3:1 contrast against both `surface-base` and `surface-raised`) and state it must apply to every interactive element, including the checkbox and row as separate focus stops.

## Low

13. **No `lang` attribute / bilingual-content guidance.** All copy examples are Norwegian; the spec never states whether the product is Norwegian-only in v1 or whether any English content (e.g. an AI-generated answer that could plausibly mix languages) can appear, which matters for WCAG 3.1.1/3.1.2.
    - **Location:** EXPERIENCE.md Voice and Tone.
    - **Fix:** State explicitly that v1 UI is Norwegian-only, or add `lang` handling guidance if mixed-language content is possible via the AI features.

14. **No `prefers-reduced-motion` guidance.** The skeleton-loading state, popover open/close, and optimistic-update transitions imply motion with no statement on respecting the reduced-motion preference.
    - **Location:** DESIGN.md Elevation & Depth; EXPERIENCE.md State Patterns, "AI answer pending" row.
    - **Fix:** Add a one-line rule to honor `prefers-reduced-motion` for transitions and the loading skeleton.

15. **Alt text convention for uploaded evidence photos is unaddressed.** The photo-evidence flow (FR-18/19) doesn't state how an uploaded image is exposed to screen-reader users reviewing it later (e.g. a Landlord checking evidence after the fact).
    - **Location:** DESIGN.md Components, "Photo evidence upload control"; EXPERIENCE.md State Patterns, "Photo evidence uploaded" row.
    - **Fix:** Require an accessible-description convention for evidence photos (e.g. "Bildebevis lastet opp av [navn], [dato]") rather than leaving it to whatever the file input's default naming produces.

---

### Contrast ratios computed (for reference)

| Pair | Ratio | AA normal text (4.5:1) | AA large text / UI (3:1) |
|---|---|---|---|
| ink-primary `#2A2640` on surface-base `#FAF8FF` | 13.74:1 | Pass | Pass |
| ink-primary on surface-raised `#FFFFFF` | 14.48:1 | Pass | Pass |
| ink-secondary `#6B6480` on surface-base | 5.29:1 | Pass | Pass |
| ink-secondary on surface-raised | 5.58:1 | Pass | Pass |
| success `#2F9E6E` on surface-raised | 3.37:1 | **Fail** | Pass |
| success on surface-base | 3.20:1 | **Fail** | Pass |
| warning `#D98A2B` on surface-raised | 2.76:1 | **Fail** | **Fail** |
| danger `#D64550` on surface-raised | 4.35:1 | **Fail (borderline)** | Pass |
| white on must-badge `#E85D8A` | 3.30:1 | **Fail** | Pass |
| white on should-badge `#6E7FE0` | 3.64:1 | **Fail** | Pass |
| white on primary `#7B6EE3` (button) | 4.05:1 | **Fail (borderline)** | Pass |
| accent `#6FB8D9` on surface-raised | 2.20:1 | n/a (UI element) | **Fail** |
| secondary `#F0A8C9` on surface-raised | 1.88:1 | n/a (UI element) | **Fail** |
