# Spine Pair Review — Husly (household task app)

## Overall verdict

The spine pair is source-extractable: every frontmatter token and `{path.to.token}` reference resolves, all four PRD user journeys have named Key Flows, `sources` frontmatter in both files points at real files, and UJ/FR names carry over verbatim. It is a genuinely strong first draft, not a thin one — the domain-specific decisions (Must/Should badge logic, locked-field treatment, photo-evidence auto-approve, no-shame copy) are committed and specific, not hand-waved. The real gaps are narrower: three EXPERIENCE.md components have no visual counterpart in DESIGN.md, the Sign in/Register surface (the entry point for the whole invite loop) has zero defined states, the two primary landing surfaces lack a cold-load state, and the one pixel-level decision this document was explicitly handed (breakpoints, per PRD FR-21) gets deferred again instead of committed. None of these break the contract outright, but a downstream consumer building from this spine would hit real gaps in those spots.

## 1. Flow coverage — adequate
Checked: every PRD UJ (UJ-1 through UJ-4) against EXPERIENCE.md Key Flows for a named protagonist, numbered steps, and a climax beat.

All four PRD journeys (UJ-1 Mari/Peter, UJ-2 Johan, UJ-3 Martin, UJ-4 Sara) have a corresponding Key Flow with a named protagonist, numbered steps, and an explicit **Climax:** beat. No UJ is missing.

### Findings
- **medium** None of the four Key Flows carries an inline failure-path annotation (contrast the spec's own Quill example, which appends a `Failure: …` and/or `Empty state: …` line after each flow). Husly's flows end cleanly at the climax even though real failure modes exist and are specified elsewhere (State Patterns: "AI cannot answer / low confidence," "Offline / network error," "No push permission granted") (EXPERIENCE.md, Key Flows section, all four flows). *Fix:* add a one-line failure/edge annotation per flow, pointing at the relevant State Patterns row — e.g. UJ-1's flow should note what happens if the "?" answer fails to load before Peter completes the task.

## 2. Token completeness — strong
Checked: every YAML frontmatter token in DESIGN.md and every `{path.to.token}` reference in both files' prose against that frontmatter.

All 14 color tokens carry hex values (no missing hex, which would have been critical). All four typography roles (display/title/body/meta) have complete `fontFamily`/`fontSize`/`fontWeight`/`lineHeight`. `rounded` (sm/md/lg/full/DEFAULT) and `spacing` (1–7) are fully populated. Every `{colors.*}`, `{spacing.*}`, `{rounded.*}`, and `{typography.body.fontWeight}` reference in DESIGN.md's prose and component tokens resolves. EXPERIENCE.md's own token references (`{colors.warning}`, `{colors.danger}`, `{colors.success}`) all resolve to DESIGN.md frontmatter by name.

### Findings
None.

## 3. Component coverage — thin
Checked: every component name appearing anywhere in either file against a matching row in DESIGN.md.Components and EXPERIENCE.md.Component Patterns.

DESIGN.md.Components lists 6 components; EXPERIENCE.md.Component Patterns lists 8. Four names match cleanly (Task card, Must/Should badge, Portfolio row, and — modulo naming, see below — the photo-evidence and quick-answer components).

### Findings
- **high** Three components with full behavioral rows in EXPERIENCE.md.Component Patterns — Invite link control, Broadcast composer, Frequency/Must toggle — have no matching row in DESIGN.md.Components, so they carry zero visual spec (color, sizing, corner radius, typography, or the visible "lock" affordance state explicitly called out for the toggle) (DESIGN.md Components section vs. EXPERIENCE.md Component Patterns rows 5, 7, 8). *Fix:* add three DESIGN.md.Components rows, particularly for the Frequency/Must toggle's locked-vs-editable visual states, which EXPERIENCE.md treats as meaningful ("the lock is visible, not hidden").
- **medium** DESIGN.md's "Primary button" has no corresponding row in EXPERIENCE.md.Component Patterns — no behavioral rules exist anywhere for disabled, loading/submitting, or multi-instance-on-one-screen states for the app's one dominant action pattern. *Fix:* add a Primary button row to Component Patterns.
- **low** Component names drift between spines for what is clearly the same component: DESIGN.md's "AI quick-answer popover" vs. EXPERIENCE.md's "\"?\" quick-answer affordance"; DESIGN.md's "Photo evidence upload control" vs. EXPERIENCE.md's "Photo evidence upload." *Fix:* standardize names verbatim across both files so a downstream consumer can string-match components with confidence (see also §7).

## 4. State coverage — adequate
Checked: every IA surface in EXPERIENCE.md against the expected state set (empty, cold-load, focus, error, offline, permission-denied) versus what State Patterns actually covers.

The domain-specific states are genuinely well covered: due-soon/overdue/completed on Task card and Task Detail, empty task list (with register-appropriate copy for household vs. landlord), locked-field treatment for Tenants, AI pending/low-confidence, photo-evidence auto-approve, push-permission-denied, and generic offline/optimistic-update behavior. That's 10 specified states, all with concrete, non-vague treatment.

### Findings
- **high** Sign in/Register — the entry point for the entire invite-and-onboarding loop (FR-2) — has no rows in State Patterns at all: no invalid/expired/already-used invite link, no failed-login, no duplicate-registration-attempt state. This is the one surface every new Member and every invited Tenant must pass through. *Fix:* add State Patterns rows for invalid/expired invite link and auth failure.
- **medium** Neither primary landing surface — Task Overview nor Landlord Portfolio Dashboard — has a defined cold-load/skeleton state. Task Overview's only load-adjacent row is "Empty task list" (zero tasks after load), not "tasks not yet loaded"; contrast Quill's explicit "Cold open" row for its equivalent landing surface. *Fix:* add a cold-load row for both.
- **low** Members & Invite and Landlord Home Admin have no explicit rows for action-submission failure (invite-link generation fails, cadence/toggle save fails). This may be intended to fall under the generic "Offline / network error: Any surface with pending action" row, but that row's wording ("local optimistic update … quiet retry," modeled on a checkbox tap) doesn't obviously extend to form-submission failures. *Fix:* either broaden that row's language or add explicit rows for these two surfaces.

## 5. Visual reference coverage
`imports/` exists and is empty. No `mockups/` or `wireframes/` directory exists yet. This is expected at this planning stage, and EXPERIENCE.md's IA section says so directly and accurately ("Composition reference: none yet — see Finalize for key-screen mocks"). No finding.

## 6. Bloat & overspecification — strong
Checked: whether prose restates PRD content without adding UX-specific value, and whether any section is padded relative to what it decides.

No section reads as filler. FR/UJ citations are load-bearing (they justify a specific visual or behavioral choice) rather than decorative. The household/landlord tonal-register discussion in DESIGN.md's Brand & Style is repeated in EXPERIENCE.md's Voice and Tone, but each instance adds a different layer (visual proportion vs. microcopy examples), so it reads as reinforcement, not duplication.

### Findings
None of consequence.

## 7. Inheritance discipline — adequate
Checked: sources frontmatter resolution, UJ/FR name fidelity to PRD, glossary-term consistency, component-name consistency, and EXPERIENCE.md token references resolving to DESIGN.md by name.

Both `sources` entries in EXPERIENCE.md's frontmatter resolve to real files (`prd.md` and `brief.md` both exist on disk at the cited paths). All four UJ headings in Key Flows match PRD UJ titles verbatim (modulo trailing punctuation). FR citations throughout (FR-1, FR-2, FR-5, FR-6, FR-8 through FR-15, FR-17 through FR-19, FR-21) match PRD FR content on spot-check. EXPERIENCE.md's `{colors.*}` references all resolve to DESIGN.md tokens by name.

### Findings
- **medium** PRD FR-21 explicitly delegates one concrete decision to this document: "this PRD sets the requirement, UX sets the pixels." EXPERIENCE.md's Responsive & Platform section punts it again — `Exact breakpoint pixel values are left open — [NOTE FOR UX] pick concrete breakpoints when the frontend framework is chosen` — so the one load-bearing decision this spine was explicitly assigned to make remains uncommitted, and downstream (architecture, story-dev) has no numbers to build against (EXPERIENCE.md, Responsive & Platform). *Fix:* commit provisional breakpoint values now (revisable later once the frontend framework is chosen) rather than leaving an open `[NOTE FOR UX]` inside the document that was supposed to resolve it.
- **low** DESIGN.md's "household mode" / "landlord-portfolio mode" language (a visual tone-register concept) sits close enough to PRD's Role glossary (Household Member / Landlord / Tenant) that a downstream reader skimming both files could conflate "mode" with "Role." They're not the same axis — mode is about visual proportion and copy register, Role is about permissions — but nothing in either file says so explicitly. *Fix:* one clarifying sentence in DESIGN.md's Brand & Style noting mode ≠ Role.
- **low** Component-name drift noted in §3 (AI quick-answer popover / "?" quick-answer affordance; Photo evidence upload control / Photo evidence upload) is also an inheritance-discipline issue — cross-referenced here, not double-counted.

## 8. Shape fit — strong
Checked: DESIGN.md section order against the canonical 8-section order; EXPERIENCE.md required-default sections; triggered-optional sections (Inspiration/Responsive) present since triggered.

DESIGN.md carries all 8 canonical sections in locked order: Brand & Style → Colors → Typography → Layout & Spacing → Elevation & Depth → Shapes → Components → Do's and Don'ts. EXPERIENCE.md carries every required default (Foundation, IA, Voice and Tone, Component Patterns, State Patterns, Interaction Primitives, Accessibility Floor, Key Flows) plus both correctly-triggered optional sections: Inspiration & Anti-patterns (reference products are named — Sbanken, iOS Reminders, Sweepy/OurHome/Tody) and Responsive & Platform (genuinely multi-surface per FR-21), both in the expected position before Key Flows.

### Findings
None.

## Mechanical notes

- **Sources frontmatter:** both entries resolve — `prd.md` and `brief.md` exist at the cited paths.
- **UJ names:** verbatim match to PRD across all four Key Flows headings.
- **FR references:** spot-checked FR-1, FR-2, FR-5, FR-6, FR-8/9, FR-10–15, FR-17–19, FR-21 — all consistent with PRD content, no misattributions found.
- **Broken cross-refs:** none found. Every `{colors.*}`, `{spacing.*}`, `{rounded.*}`, `{typography.*}` reference in both files resolves to a DESIGN.md frontmatter token.
- **Component-name inconsistencies (2 pairs):** "AI quick-answer popover" (DESIGN.md) vs. "\"?\" quick-answer affordance" (EXPERIENCE.md); "Photo evidence upload control" (DESIGN.md) vs. "Photo evidence upload" (EXPERIENCE.md).
- **Component-coverage gaps:** DESIGN.md.Components missing rows for Invite link control, Broadcast composer, Frequency/Must toggle. EXPERIENCE.md.Component Patterns missing a row for Primary button.
- **Frontmatter completeness:** DESIGN.md — all color/typography/rounded/spacing tokens fully populated, no missing hex values. EXPERIENCE.md — `name`, `status`, `sources`, `updated` all present and valid.
