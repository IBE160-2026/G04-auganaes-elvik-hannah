---
title: "Sprint Change Proposal: Response to teacher feedback on the product brief"
date: 2026-10-11
status: approved
trigger: _bmad-output/planning-artifacts/briefs/brief-prosjektoppgave-ibe160-2026-09-12/tilbakemelding-product-brief.md
scope: moderate
---

# Sprint Change Proposal — 2026-10-11

## 1. Issue summary

**Trigger.** The teacher's feedback on the product brief, dated 2026-10-06. No story had been implemented yet; this is a stakeholder-driven change found while the plan was still on paper, which is the cheapest time to make it.

**Problem.** Three issues, in the teacher's order of importance:

1. **Scope of v1 is too large.** Four segments, three roles, invitations, recommended frequencies, push with a Landlord channel, AI chat and responsive design, for three beginners in about 13 weeks. The teacher rated difficulty "Vanskelig" and time and scope a risk.
2. **Success criteria cannot be tested.** "The core loop needs to actually function end-to-end" is too general, and reviews, fewer conflicts and fewer deposit disputes cannot be measured within the course.
3. **The app cannot be run by a reviewer.** The architecture depended on one shared Supabase database, Render, Vercel, cron-job.org and Google Gemini, so a reviewer needs the team's accounts and keys. The teacher rated this "stor risiko".

**Smaller points.** Pick one primary user for v1; consider simplifying the three hosting platforms; justify that Photo Evidence and the portfolio dashboard entered the plan after the brief.

## 2. Impact analysis

**Epics.** No epic is removed or renumbered. Every story gets a Stage. Epic 5 is split between stages (quick-answer in Trinn 1; chat and onboarding guide in Trinn 2). One story is added (1.6).

**Stories.** 22 existing stories (the earlier count of 20 was a miscount) plus new Story 1.6 = 23. Acceptance criteria were added to Stories 1.1, 3.2, 4.2 and 5.1 for README/`.env.example` and mock modes.

**Artifacts changed (one commit each):**

| Artifact | Change | Commit |
|---|---|---|
| Product brief | Trinn 1/Trinn 2 split; eight testable success criteria; household as primary user for Trinn 1; local run in scope; reviews and conflict reduction moved to Vision; rationale for Photo Evidence and dashboard | `14ad20d` |
| PRD | MVP scope split by stage; new FR-22 (run locally without external accounts); success metrics replaced with testable SM-1…SM-9 traced to FRs; long-term signals marked; Open Question 1 partly resolved | `29615bf` |
| Architecture spine | New AD-15 (local Docker as primary path); AD-4 gets a provider interface with a mock; shared dev database replaced by one local database per developer; hosting made optional; Trinn 2 ADs tagged; AD-13 colour corrected to `#6E62CC` | `772755c` |
| Epics | Stage on every story and epic; Story 1.6; FR-22 and NFR7; AC additions; schema-change and deployment notes aligned with the architecture | `77ed396` |
| UX (DESIGN.md, EXPERIENCE.md) | No change | — |

**Technical impact.** Implementation will need `docker-compose.yml`, `.env.example`, a README, seed data and mock adapters (AI, later push and storage) from the first stories. All three developers get an isolated local database, which removes the old "announce schema changes to the other two" rule.

## 3. Recommended approach

**Direct adjustment, with a scope review (hybrid of options 1 and 3).** Nothing is cut: the scope is ordered into two stages so that Trinn 1 is a complete app even if Trinn 2 is not finished.

- **Rollback:** not viable and not needed; no code exists.
- **Effort:** medium (four planning documents and a new story). **Risk:** low.
- **Timeline:** improves it. The riskiest items (push, cron, Storage, chat, dashboard) move behind a stable core.

### Decisions made with the team

| Question | Decision | Why |
|---|---|---|
| Primary user for Trinn 1 | Household (kollektiv/samboer/single) | One primary user as the teacher asked. The Landlord–Tenant role model stays in Trinn 1 because it is the differentiator and the most testable rule set; Landlord oversight tools move to Trinn 2. |
| Local database | PostgreSQL in Docker | The course teaches Docker for working across machines; same database as production; gives each developer their own database. |
| AI in Trinn 1 | Quick-answer only (5.1) | Smallest piece that shows the AI feature. Chat is a small extension once the AI service exists, so it opens Trinn 2. Mock mode means no key is needed. |
| Hosting | Keep, but optional | Local Docker is the main path; the hosted setup is a demo deployment and Trinn 1 needs none of cron, push or Storage there. |

## 4. Detailed change proposals

Each proposal below was presented in old → new form and approved one document at a time (incremental mode). The exact text is in the commits listed in section 2; this table is the trace from feedback to change.

| Teacher's point | Where it is answered |
|---|---|
| Define a minimal core flow; split v1 | Brief §Scope; PRD §6; epics §Delivery stages and Stage tags |
| Testable success criteria | Brief §Success Criteria; PRD §7 (SM-1…SM-9) |
| Move reviews, conflict and deposit signals out | Brief §Vision; PRD SM-12…SM-14 marked long-term |
| Plan local running for the reviewer | PRD FR-22 and NFR; Architecture AD-15; Epics Story 1.6 and NFR7 |
| README and `.env.example` early | Epics Story 1.1 (new AC) and Story 1.6 |
| Mock mode for Gemini and push | Architecture AD-4/AD-15; Epics 3.2, 4.2, 5.1 (new AC) |
| One primary user | Brief §Who This Serves; PRD §3 |
| Justify Photo Evidence and dashboard | Brief §Scope; PRD §6 note for PM |
| Consider simplifying hosting | Architecture §Deployment (optional hosted demo) |
| Tests for meaningful logic | Brief criteria 1–6; PRD SM-1…SM-6; AD-15 (offline test suite) |

## 5. Implementation handoff

**Scope classification: moderate** — backlog reorganisation across four planning documents, no code.

| Role | Responsibility |
|---|---|
| PM (brief, PRD) | Done in this change. Keep Open Question 1 under review: whether Trinn 2 fits before mid-December. |
| Architect | Done in this change. Pin the PostgreSQL major version when `docker-compose.yml` is created. |
| PO / Developer | Run `bmad-sprint-planning` next, using the Stage tags to order the sprint. Start with Story 1.1 and Story 1.6 so that the README and local run exist from the first story. |

**Success criteria for this change.**
- Brief, PRD, architecture and epics agree on the stage split, FR-22 and AD-15.
- A reviewer can follow the README (once written) and run Trinn 1 with Docker alone.
- The eight Trinn 1 criteria are each covered by at least one automated test when Trinn 1 is done.

**Not done here.** `sprint-status.yaml` does not exist yet, so checklist item 6.4 does not apply; it is created by `bmad-sprint-planning`.

**Follow-ups noticed during the analysis.** The primary colour in AD-13 differed from DESIGN.md and epics (`#7B6EE3` vs `#6E62CC`); the architecture was corrected. The story count of 20 in CLAUDE.md was wrong (22 before, 23 now) and is corrected in the status section.

**Review fixes (PR #1, 2026-10-11).** Eirik's review from Mac found that replacing the old catch-all SM-1 left FR-1, FR-4 and FR-21 without a success criterion; they are now covered by brief criteria 3 and 5 and PRD SM-3 and SM-5, so every Trinn 1 FR is validated by a criterion. Remaining "FR-1 through FR-21" references in the architecture scope and `epics.md` were updated to FR-22, and the brief's stack line now says TypeScript, matching the architecture.
