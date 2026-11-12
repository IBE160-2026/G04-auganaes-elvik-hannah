# Sprint Change Proposal — 2026-11-12

**Trigger:** The teacher's formative feedback on the PRD (`prds/prd-prosjektoppgave-ibe160-2026-09-29/tilbakemelding-prd.md`, commit `f76b547`, 2026-11-12), plus `architecture/technology.md` (`235a598`) as a reference.
**Mode:** Incremental, coaching path. All six proposals approved by Eirik on 2026-11-12. Hannah and Steffen were unavailable and can object in the PR.
**Scope:** Moderate. PRD, `epics.md` and the architecture spine change; no completed story is invalidated and no code is changed by this proposal.

## 1. Issue Summary

The teacher rates the PRD as strong, but names four things that must be settled now: the Trinn 2 cut line is still "pending team validation" (Q1) while the PRD is `status: final`; some consequences are too vague to become tests (FR-4, FR-11, FR-16, Q4); AI failure, cost and data sent to the external service are not described (FR-14/15); and rules that SM-5/SM-6 test are missing from FR-2/FR-3. Mechanical findings: wrong FR count in §0, missing glossary terms, an outdated Photo Evidence assumption, revision history and code inside requirements, unnumbered sections, and no privacy statement for user accounts. A further finding came from checking the feedback against the code: the app has no "unit type" (FR-16).

`technology.md` describes another project (Railway, Supabase, Caddy) and does not change our stack (Vercel is the only hosting). What it confirms or adds: mock fallback without keys (already AD-15) and rate limiting on AI routes (new, Proposal 3).

## 2. Impact Analysis

- **Epics/stories:** No done or in-review story is affected (1.1–2.5). Story 3.3 gets the concrete FR-11 rule; Stories 5.1, 5.2 and 5.3 get acceptance criteria for AI failure, limit and data; the Trinn 2 delivery table is split into Must and If time permits.
- **PRD:** §0, §2, §3.3, §4 (FR-1, FR-2, FR-3, FR-4, FR-8, FR-11, FR-14, FR-15, FR-16, FR-19, FR-22, FR-23, FR-24), §5, §6, §7 (SM-7, SM-9, new SM-15), §8 (Q1, Q3, Q4), Assumptions, Privacy, NFRs, front matter.
- **Architecture:** AD-4 (timeout, daily limit, data minimisation, new table `ai_usage`); the deferred item on AI rate limiting is removed; the Photo Evidence allowlist decision is recorded.
- **UX:** Not affected beyond one sentence next to the AI disclaimer (Story 5.1).
- **Technical:** Nothing now. Later: `ai_usage` table with an Alembic migration (Story 5.1); the FR-11 threshold becomes a constant in `domain/` (AD-9 already counts the last 3 completed instances, so the rule fits the data model).

## 3. Recommended Approach

**Direct Adjustment.** Update PRD, epics and architecture in place; do not regenerate them. Effort: about half a day of document work. Risk: low. Timeline: no impact on Story 2.6; the cut line gives Trinn 2 a clear order, which is the main schedule risk the teacher names.

## 4. Detailed Change Proposals

### P1 — Decide the Trinn 2 cut line (PRD §8 Q1, §6, §9, UJ-1..4)
- Q1 becomes `RESOLVED 2026-11-12`. **Must:** FR-10, FR-12, FR-13, FR-18/19. **If time permits, cut from the bottom up:** FR-20 (first), FR-16, FR-11, FR-15 (last).
- §6 Trinn 2 is split into those two groups. `[NOTE FOR PM]` is reduced to a pointer; the matching Assumptions Index line is removed.
- Each UJ gets one line on what works in Trinn 1 (UJ-1 without push, UJ-2 without portfolio/broadcast/guide, UJ-3 without targeted reminder and photo, UJ-4 all but push).
- *Rationale:* high severity; the deadline is mid-December. FR-13 is Must because it shares the due-check with FR-10. Photo Evidence stays Must: it is the most distinctive Landlord–Tenant mechanism.

### P2 — Make vague consequences testable (FR-4, FR-11/Q4, FR-16)
- **FR-4:** add "Given 'Rens sluket' the recommendation is Must; given 'Avkalk vannkokeren' it is Should" (both exist in `task_types.py`).
- **FR-11/Q4:** "Given a recurring shared task in a Home with at least two current Members and at least three completed instances: while the task is open and due or overdue, if Member B has none of the last 3 completions, B receives a targeted reminder and no other Member receives one from this rule. At most one per task instance." The number 3 is a constant in `domain/`. Q4 is resolved. (Decision: the reminder fires only while the task is open, so it is a targeted variant of FR-10, not a nag after A has finished.)
- **FR-16:** "unit type" does not exist in the app. The guide is "tailored to that Home: it names the Home and lists its active Must tasks with their frequencies, so two Homes never get the same text." No new data model.

### P3 — AI failure, cost and data (FR-14, FR-15, AD-4, Story 5.1/5.2)
- **FR-14:** a call that fails or takes more than 10 seconds shows an error (`status: "error"`) and can be retried, and the task view and completion keep working; only the task's name, its catalog type and the user's own question are sent (no names, e-mails or Home names); at most 20 AI calls per user per day (quick answers and chat together), also for the mock provider so it is testable offline; the UI says the question goes to an external AI service (Google Gemini).
- **FR-15:** the same rules apply to the chat.
- **AD-4:** timeout and daily limit become rules; table `ai_usage` (user, day, count) with a migration in Story 5.1; the deferred item "Rate-limiting/abuse protection on the AI endpoints" is replaced by a reference to AD-4. The numbers 10 and 20 are constants, adjustable without changing the PRD.
- **Story 5.1:** new acceptance criteria for timeout, daily limit and call payload. **Story 5.2:** refers to the same rules.

### P4 — Clean requirements, history in a log (FR-1, FR-3, FR-8, FR-22, FR-23, FR-24, Q3, header)
- Remove `[REVISED …]`/`[ADDED …]` tags, function names (`domain/homes.fr3_violations`), HTTP code 409, file paths, story numbers and "decisions by" from the requirement text. FR-8 states the fixed intervals (7, 14, 30, 42, 60, 90, 182, 365 days). FR-22 names no environment variables (they stay in AD-15, README and `.env.example`).
- The four existing revision blocks become one **Revision log**: one line per change with date, FRs and a link to the proposal. Today's revision is added.
- `epics.md` FR inventory is updated to match, so PRD and epics do not drift apart.

### P5 — Requirements and success metrics say the same (FR-2, FR-3, SM-7, SM-9, SM-15)
- **FR-2:** "An invite link is valid for 7 days and can be used once. An expired or already used link shows a clear message and links nobody to the Home."
- **FR-3:** "A user cannot read or change data in a Home they are not a current Member of: every Home-scoped request is rejected server-side."
- **SM-9** is split into SM-9a (broadcast), SM-9b (no duplicate due notification), SM-9c (Photo Evidence only on eligible types), SM-9d (portfolio lists Homes with overdue Must tasks). Letters, not new numbers, because SM-10 to SM-14 exist.
- **SM-15** (Trinn 2) tests the FR-11 rule; **SM-7** is extended with timeout, daily limit and payload.

### P6 — Mechanical findings and account privacy
- §0: "FR-1 through FR-24", with a note that FR-23 and FR-24 were added later and keep their numbers because stories and code refer to them.
- Glossary: add Household Home, Landlord Home, Task Setup, Portfolio Dashboard and Trinn 1/Trinn 2; remove "unit type".
- Photo Evidence: the allowlist decision is recorded as made: `photo_evidence_eligible` in the task catalog, not editable by anyone, never on custom tasks (FR-24). The assumption in Privacy Constraints and §9 is updated.
- Remove "the product's own support staff" (FR-19, Privacy): access is the Home's Landlord only.
- "Notification reliability" becomes testable: each due-check run records per Member whether a notification was sent; failed sends are logged; delivery is promised no further than the daily batch (Open Question 2).
- Number the trailing sections: §9 Privacy Constraints, §10 Cross-Cutting NFRs, §11 Assumptions Index. `status: final` stays (Q1 and Q4 are closed); `updated: 2026-11-12`.
- **Account privacy (new Privacy Constraint):** the account stores e-mail, display name and a password hash; other Members of a Home see only the display name, never the e-mail; the only data shared with an external service is the minimal AI call (FR-14).
- **Account deletion** is not built in this course version. It is something the team aims to add: the user row would be anonymised (AD-16 already shows past activity as «Tidligere medlem»), and the Landlord case (FR-3 requires exactly one Landlord, FR-23 forbids a Landlord leaving) is an open product decision. Recorded in §5 as deferred, with an estimate of about one day.

## 5. Implementation Handoff

- **Scope: Moderate.** Documents only; implemented in this session by the Developer agent after approval.
- **Artifacts changed:** `prd.md`, `epics.md`, `ARCHITECTURE-SPINE.md`, `sprint-status.yaml` (note only), this proposal, `docs/ki-logg/korrigeringer.md` (the `unit type` finding: KI-generated FR-16 text referred to a concept the app does not have).
- **Success criteria:** PRD has no open questions and no code or story numbers in requirement text; every FR named by the teacher has a consequence that can be written as a test; `epics.md` FR inventory equals the PRD; Stories 3.3, 5.1, 5.2 and 5.3 carry the new criteria.
- **Teacher's reflection questions** are answered in `docs/ki-logg/` (question 2: what we carried from the code back into the requirements, and how we checked the text matches what was built).
- **Next:** Story 2.6 continues after PR #44 is merged. Hannah and Steffen review this proposal in the PR.
