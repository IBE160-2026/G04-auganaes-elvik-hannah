---
title: "Architecture Spine Review — Husly (rubric pass)"
reviewed: ARCHITECTURE-SPINE.md (architecture-prosjektoppgave-ibe160-2026-10-04)
reviewed_against: .memlog.md (same folder), PRD prd-prosjektoppgave-ibe160-2026-09-29
date: 2026-10-04
reviewer: Claude (sub-agent review pass)
scale_note: "3-person, 13-week academic project — severities calibrated down from production/enterprise norms."
---

# Verdict

The spine is substantively solid — all 13 ADs are testable, every FR-1…FR-21 is mapped, and no structural dimension at this altitude is left silently undecided — but it ships one real contradiction between AD-1 and AD-2 (how a Home-scoped Role gets resolved per-request) that would let two developers build incompatible auth, plus a handful of medium-severity gaps worth a fix pass before story-writing starts.

# Critical

### C-1: AD-2's Rule contradicts AD-1's data model — Role can't actually "be read from the JWT"

- **Where:** AD-1 (`Role lives on Membership, not on the User account`) vs. AD-2 (`Server-side permission enforcement through one dependency`)
- **What's wrong:** AD-1 deliberately makes Role a property of the User↔Home **Membership** row — one User can hold a different Role in each Home (that's the whole point: it resolves PRD Open Question 3, dual-role-across-Homes). AD-2's Rule, as written, says `require_role(...)` "reads the Role from the verified JWT." Those two can't both be true as stated: a JWT issued at login time can encode at most one static Role claim, which only works if a User has exactly one Role — the thing AD-1 just abolished. Two implementations are equally "compliant" with the current wording and are incompatible with each other:
  1. One developer bakes "current Home's role" into the JWT at login, re-minting a token whenever the user switches Home context.
  2. Another developer has `require_role` ignore any role claim in the JWT and instead look up `Membership(user_id, home_id)` from the DB on every request, using only `home_id` from the route path.
  These have different revocation semantics (stale JWT vs. always-fresh DB read) and different route signatures (whether `home_id` is required). Worse, as literally written, AD-2 never checks that the Membership row's `home_id` matches the resource being accessed at all — only that *some* Role claim satisfies the check. That's a cross-Home data-isolation gap: a Tenant of Home A with a stale/replayed token could pass a Landlord-Home-B route's role check if the dependency only compares role strings and never re-verifies "is this User actually a Member of *this* Home."
- **Why it matters here:** This is the single enforcement point every protected route in the system depends on (binds "all authenticated routes" per AD-7, and FR-3/5/8/13's server-side-enforcement NFR). Getting it wrong is both a correctness bug (three developers each guessing) and a real privacy leak across Homes/Tenants, which the PRD's Privprivacy Constraints section treats as a hard requirement ("should not be visible to other Tenants or other Landlords outside the relevant Home").
- **Fix suggestion:** Rewrite AD-2's Rule to make the lookup explicit: the JWT carries only verified **identity** (`user_id`), never a Role claim. `require_role(role, ...)` takes the Home-scoping identifier from the route (e.g. a `home_id` path param or the task/resource's owning `home_id` resolved first), queries `Membership` for `(user_id, home_id)`, and 404s/403s if no Membership row exists for that Home at all before checking whether its Role satisfies the required tier. This one rewrite fixes both the AD-1/AD-2 contradiction and the missing cross-Home isolation check, and is still a one-paragraph rule — no added complexity for the team.

# High

### H-1: FR-12's "ad-hoc" broadcast is mapped only to the cron-gated due-check path, which would silently add up to 14 minutes of latency to an action the PRD and UX treat as immediate

- **Where:** Capability → Architecture Map, row "Notifications (FR-10–13) | `backend/app/notifications` | AD-8, AD-9"; AD-8 itself.
- **What's wrong:** AD-8's Rule is explicit that `POST /internal/run-due-check`, fired only by the external cron every 10–14 minutes, "is the only thing that triggers it" (the due/overdue scan). FR-12 is a Landlord composing and sending a message *right now* ("ad-hoc reminder message... Johan sends a targeted reminder message straight to that Home's Tenants" — PRD UJ-2). Nothing in the spine says FR-12 has its own immediate send path distinct from AD-8's scan loop. Lumping FR-10–13 together in the Capability Map under the same two ADs reads as "all four of these go through the cron job," which is correct for FR-10/FR-11 (due-check-driven) and wrong for FR-12 (user-initiated, should fire on click). Two developers could reasonably diverge here: one wires a `POST /homes/{id}/broadcast` endpoint that calls the push service directly and returns immediately; another — reading the Capability Map literally — queues the message for the next due-check tick, introducing a latency bug that contradicts "ad-hoc."
- **Fix suggestion:** Split the Capability Map row, or add a one-line clause to AD-8 (or a new short AD) stating FR-12's broadcast endpoint calls the push-sending function directly and synchronously on the Landlord's request, independent of the due-check cron; AD-8 only governs FR-10/FR-11's scan-triggered sends.

# Medium

### M-1: No migration/schema-change strategy for the single shared dev database — a whole dimension left silent, not even flagged as Deferred

- **Where:** "Structural Seed → Deployment & environments" section; absent from the "Deferred" list entirely.
- **What's wrong:** The spine (and memlog, decision at line 24) commit to one shared Supabase project for all three developers for the whole 13 weeks, and the memlog explicitly logs "all three developers share one dev database" as an accepted risk. But nothing says *how* schema changes reach that shared database — no Alembic/migration tool decision, not even a one-line "manual `CREATE`/`ALTER`, discuss in standup before changing a table" convention. This is exactly the kind of dimension the checklist flags: silent, at initiative altitude, and a classic way for 3 independently-working developers to diverge incompatibly (two people alter the same table differently the same week, or one developer's local model drifts from the shared DB's actual schema). Compare to how carefully AD-5/AD-6 govern Photo Evidence or how carefully the Deferred section calls out testing/observability as consciously left open — this dimension isn't even acknowledged as a gap.
- **Fix suggestion:** Either add a minimal AD ("SQLModel's `create_all`/Alembic autogenerate is run by whoever changes a model, before pulling; no manual `ALTER` against the shared Supabase instance") or add it to Deferred with an explicit interim convention (e.g., "coordinate schema changes in the team chat before applying — acceptable given shared single environment and 3-person scale"). Either is fine at this altitude; silence is the actual problem.

### M-2: FR-16's AI-generated onboarding guide — persisted artifact or regenerated each view is undecided

- **Where:** Capability → Architecture Map, "AI Assistant (FR-14–16) | `backend/app/ai` | AD-4"; AD-4 itself; Core entities ERD (no onboarding-guide entity).
- **What's wrong:** AD-4 fixes the response-state contract (`ok`/`low_confidence`/`error`) and the disclaimer-injection point for the quick-answer and chat paths, but says nothing about FR-16's guide specifically, and the ERD has no entity to hold a generated guide. That leaves open whether the guide is generated once (at invite-provisioning time, per UJ-2) and stored for repeat access, or regenerated via a fresh Gemini call every time a Tenant opens it. These diverge in real, visible ways: regeneration risks the guide's wording changing between views (odd for an onboarding document a Tenant might re-read) and burns Gemini's free-tier daily request cap (already a named constraint elsewhere in the spine) on every re-read, not just once per Home.
- **Fix suggestion:** One sentence in AD-4 or a new short AD: "the onboarding guide is generated once when the Landlord provisions the Home/sends the invite, persisted (e.g. a text column on `Home` or its own `OnboardingGuide` row), and served from storage thereafter — never regenerated per view."

### M-3: AD-7's cross-origin cookie strategy is enforceable only alongside a CORS policy the spine never states

- **Where:** AD-7 — Auth: in-memory access token + httpOnly refresh cookie.
- **What's wrong:** AD-7 correctly identifies that Vercel (frontend) and Render (backend) are cross-origin and chooses `SameSite=None` + `Secure` cookies to cope. But a `SameSite=None` cookie only survives the browser's credentialed-request rules if the backend's CORS config echoes back the *specific* frontend origin and sets `allow_credentials=True` — a wildcard `allow_origins=["*"]` (FastAPI's/Starlette's easy default) silently breaks the whole mechanism (the browser drops the cookie). The spine states the cookie strategy but not the CORS configuration it depends on, leaving room for exactly the kind of per-developer guess AD-7 otherwise closes off everywhere else.
- **Fix suggestion:** Add one clause to AD-7: "CORS is configured with an explicit allow-list of the deployed frontend origin(s) and `allow_credentials=True`; never a wildcard origin." Trivial to state, easy to get wrong without it.

### M-4: Stack table's SQLModel/SQLAlchemy pin claim may already be stale

- **Where:** Stack table — `SQLModel | latest (pins SQLAlchemy ~1.4.41 internally — known, accepted limitation)`.
- **What's wrong:** Per the checklist's "plausibly current" check (not a re-verification request): SQLModel's long-standing SQLAlchemy-1.4 pin has been a widely tracked issue, and SQLModel has been moving toward SQLAlchemy 2.0 compatibility over the past couple of release cycles. Given the document's own Oct-2026 vantage point, asserting the ~1.4.41 pin as current fact (rather than "verify at kickoff") risks being wrong by the time the team actually `pip install`s it, and the "known, accepted limitation" framing may no longer apply.
- **Fix suggestion:** Soften to "verify SQLModel's SQLAlchemy version pin at project kickoff — historically pinned to ~1.4.x; treat 2.0 compatibility as a pleasant surprise, not an assumption," or just re-check before the team's first `pip install`.

# Low

### L-1: Stack table mixes pinned and unpinned versions inconsistently

- **Where:** Stack table.
- **What's wrong:** `FastAPI` and `React` are pinned to specific minor versions; `SQLModel`, `pywebpush`, `google-genai`, `TypeScript`, `Vite`, `TanStack Query`, and `Node.js` all say "latest." Over a 13-week build, "latest" resolved at different calendar weeks by different team members (before a lockfile exists) can quietly diverge. Low stakes since `package-lock.json`/`uv.lock` fixes this in practice once committed, but worth a one-line note.
- **Fix suggestion:** Add a sentence: "whoever runs the first `npm install`/`pip install` commits the lockfile immediately; everyone else installs from it, not from `latest` again."

### L-2: Capability Map's FR-8–9 → AD-3 mapping is loosely worded

- **Where:** Capability → Architecture Map, "Frequency & Scheduling (FR-8–9) | `backend/app/domain` | AD-3"
- **What's wrong:** AD-3's actual Rule is specifically about one function owning task-*completion* state (and FR-9's reschedule-on-completion, which it does explicitly name). FR-8 (recommending/setting a task's Frequency — an edit operation, not a completion event) isn't really governed by AD-3's stated divergence-prevention; it's a different code path (an update endpoint on the Task, not on TaskInstance completion). Not a functional gap — FR-8 just doesn't need its own AD, since it's ordinary role-gated field-editing already covered by AD-2 — but the mapping row implies a connection to AD-3 that doesn't hold for FR-8.
- **Fix suggestion:** Split the row, or note that FR-8 is governed by AD-2 (role-gated edit) and FR-9 specifically by AD-3.

---

# Checklist Coverage Summary

| Checklist item | Verdict |
| --- | --- |
| Fixes real divergence points, misses none | Mostly — misses the AD-1/AD-2 Role-resolution mechanics (C-1) and FR-12's immediate-vs-cron send path (H-1) |
| Every AD's Rule enforceable and prevents its divergence | 12 of 13 hold up; AD-2 does not as currently worded (C-1) |
| Nothing under Deferred risks incompatible divergence | Pass — all 5 Deferred items are genuinely safe to leave open at this scale |
| Named tech plausibly current | Mostly pass; SQLModel/SQLAlchemy pin claim worth re-checking (M-4) |
| Capability Map covers FR-1 through FR-21 | Pass, all 21 FRs mapped (FR-8 mapping is loose, L-2) |
| Every structural dimension decided/deferred/open, none silent | One real silence: schema-migration strategy for the shared dev DB (M-1) |
