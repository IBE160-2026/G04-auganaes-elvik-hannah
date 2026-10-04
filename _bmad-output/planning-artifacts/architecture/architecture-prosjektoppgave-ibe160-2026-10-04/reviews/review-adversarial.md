---
title: "Adversarial Review — ARCHITECTURE-SPINE.md (Husly)"
status: final
created: 2026-10-04
reviews: _bmad-output/planning-artifacts/architecture/architecture-prosjektoppgave-ibe160-2026-10-04/ARCHITECTURE-SPINE.md
against: _bmad-output/planning-artifacts/prds/prd-prosjektoppgave-ibe160-2026-09-29/prd.md
---

# Adversarial Review — Husly Architecture Spine

## Verdict

The spine closes the obvious single-path gaps (one completion function, one AI gateway, one storage key, one PWA shell) but leaves several **boundary interactions** between ADs unresolved; in at least two cases a developer following an AD to the letter builds something that is actively incompatible with what another AD (or the Core Entities diagram) tells a different developer to build, and both of those land squarely on the core loop (role/permission correctness, and the Photo Evidence trust mechanic) rather than on an edge case.

---

## Critical

### C-1. Photo Evidence: Task-keyed storage vs. TaskInstance-shaped data model

**Two units built as:**
- Dev A builds the domain-layer photo-upload path inside `complete_task_instance` (AD-3 + AD-5), writing every uploaded photo to the fixed key `tasks/{task_id}/evidence.jpg`, exactly as AD-5 prescribes ("no code path appends a new key per upload").
- Dev B builds the Landlord's photo-review surface (FR-19: "the Landlord can retrieve the current photo for a task instance after the fact"), modeling `PhotoEvidence` per the Core Entities diagram's cardinality `TASK_INSTANCE ||--o| PHOTO_EVIDENCE: "may require"` — i.e., one `PhotoEvidence` record per instance, each presumably carrying a pointer to "its" photo.

**Diverge because:** AD-5's overwrite key is keyed by `task_id`, not `task_instance_id`. The *first* time the recurring task is completed with a photo, instance N's `PhotoEvidence` row and the blob agree. The moment the *next* occurrence (instance N+1) is completed with a new photo, the blob at `tasks/{task_id}/evidence.jpg` is silently overwritten — but Dev B's instance-N `PhotoEvidence` row, built per the ER diagram's per-instance cardinality, still exists and still resolves to that same storage key. Any Landlord who looks at instance N's "evidence" after that point sees instance N+1's photo, not what was actually uploaded for N. Nothing in AD-5 or AD-3 says whether completing a new instance should (a) insert a new `PhotoEvidence` row, (b) update the existing Home/Task-level row, or (c) invalidate stale per-instance rows — so whichever dev builds the review query first picks a behavior the other dev's upload path doesn't actually guarantee.

**Why it matters at this scale:** This is the PRD's own words — "Photo Evidence is deliberately last [to cut], since it's the most distinctive Landlord-Tenant trust mechanism named in the brief's differentiation case" (PRD Open Question 1) — and FR-19's testable consequence ("Landlord can retrieve the current photo for a task instance") breaks for any task with more than one completed-with-photo occurrence, which is the normal case for a recurring Must task within 13 weeks of use/demo.

**Fix:** Add a Rule to AD-5 (or a new AD) stating explicitly: `PhotoEvidence` is a property of the *current* instance only — either (a) there is no durable per-instance `PhotoEvidence` row at all, only a `Task.current_evidence_key` + `uploaded_at`/`uploaded_by` pointer that the Landlord-review query reads, and the ER diagram's `TASK_INSTANCE ||--o| PHOTO_EVIDENCE` relation is corrected to `TASK ||--o| PHOTO_EVIDENCE`; or (b) storage keys are actually instance-scoped (`task_instances/{instance_id}/evidence.jpg`) and AD-5 is restated that way, with an explicit note that only the *most recent* instance's key is retained/linked (matching FR-19's "no accumulating photo history"). Pick one and make the ER diagram and AD-5 agree.

---

### C-2. Role resolution across multiple Homes: JWT-embedded vs. per-request DB lookup

**Two units built as:**
- Dev A builds the auth/login domain service (AD-7): issues the short-lived JWT access token at login, and — because AD-2 says `require_role(...)` "reads the Role from the verified JWT" — embeds `role` as a single top-level JWT claim, computed from (for example) the user's first/most-recent Membership at login time.
- Dev B builds a Homes/Membership route, e.g. `PATCH /homes/{home_id}/tasks/{task_id}/classification` (FR-5), and declares `require_role("household_member_or_landlord")` on it per AD-2, trusting that the dependency resolves the Role *for `home_id`* — which, per AD-1, is a Membership-scoped field, not an account-wide one.

**Diverge because:** AD-1 explicitly rules out Role living on the User account ("One User row can have many Membership rows, each with its own Role scoped to one Home"), but AD-2's rule — "reads the Role from the verified JWT" — reads naturally as a single static claim, which is only coherent if Role *is* account-wide. Nothing in AD-2 says the dependency takes `home_id` as a parameter, cross-references it against the JWT's (necessarily multi-entry, e.g. `{home_id: role}`) claims, or re-reads Membership from the DB per request. If Dev A ships a single flat `role` claim (the natural reading of AD-2's literal words) and a user who is a Household Member in Home A is also a Tenant in Home B, Dev B's route for Home B silently authorizes using Home A's role, or vice versa — exactly the cross-Home privilege confusion AD-1 says it exists to prevent. This also silently breaks PRD Open Question 3 ("can a Landlord also be a Household Member of a separate personal Home"), which AD-1 claims to resolve but AD-2 doesn't actually carry through.

**Why it matters at this scale:** This is the Cross-Cutting NFR "Permission enforcement" and the core Tenant-lock mechanic (FR-3, FR-5, FR-8, FR-13) — a Tenant able to act as a Household Member (or vice versa) in a different Home because of how the JWT was shaped breaks the product's "structural positioning claim" (PRD §4.2) in the course demo itself, not in a rare edge case.

**Fix:** Extend AD-2's Rule to state explicitly how `require_role` is parameterized and scoped: e.g. "`require_role(home_id, allowed_roles)` takes the Home from the route path, looks up the caller's Membership for that Home fresh from the database (or from a JWT claim shaped as `{home_id: role}` refreshed on every login/`/refresh` call), and 403s if no Membership exists for that Home" — and add a note on what happens when a Landlord changes/revokes a Tenant's Role mid-session (does the existing access token stay valid until its short TTL expires, acceptable per AD-7, or does revocation need an explicit invalidation path?).

---

## High

### H-1. Cross-origin refresh cookie vs. the one generated API client's default credentials behavior

**Two units built as:**
- Dev A builds the `/refresh` endpoint and login response per AD-7, setting the refresh token as `httpOnly; Secure; SameSite=None` — correct for the Vercel/Render cross-domain split AD-7 itself calls out.
- Dev B generates the frontend's single OpenAPI client (per AD-11's Consistency Convention: "Frontend API types generated from the backend's OpenAPI schema... never hand-written") and wires it into TanStack Query hooks, using whatever the generator's default fetch wrapper does.

**Diverge because:** `SameSite=None` cookies are only sent cross-origin if the *client's* request explicitly opts in (`credentials: "include"` on `fetch`, or the generated client's equivalent config) **and** the backend's CORS middleware echoes a specific allowed origin with `Access-Control-Allow-Credentials: true` (a wildcard `*` origin silently breaks it). Typical `openapi-typescript`-generated fetch clients default to omitting credentials unless explicitly configured. AD-7 and AD-11 are each individually satisfied — the cookie is set correctly, and the one shared client is used everywhere — yet if Dev B never flips the credentials flag (because neither AD mentions it), every `/refresh` call silently fails to send the cookie, and sessions die the moment the short-lived access token expires. No AD assigns ownership of this cross-cutting wiring.

**Why it matters at this scale:** Breaks session refresh for 100% of users after the access-token TTL, i.e. the entire authenticated app, not an edge case — but it's a one-line fix once named, hence High rather than Critical.

**Fix:** Add a line to AD-7 (or AD-11's Consistency Convention row) naming the two concrete settings this requires: generated client configured with `credentials: "include"` globally, and backend CORS configured with the exact Vercel origin + `allow_credentials=True` (never `*`).

### H-2. Optimistic-update "feel" is pinned for the checkbox mutation but not the photo-upload mutation

**Two units built as:**
- Dev A builds the Tenant-facing photo-upload flow for FR-19, and — reading AD-11's instruction that the checkbox mutation (FR-17) uses "instant UI flip, quiet retry/rollback on failure" as the house style for completion mutations generally — makes the photo-upload mutation optimistic too: the UI flips to "complete" the instant a photo is selected, before the upload/auto-approval round-trip finishes.
- Dev B builds the Landlord's review view consuming the same completion state, assuming (reasonably, since a photo upload can fail on size/format/network in ways a checkbox toggle cannot) that photo-upload completion is pessimistic — UI only shows "complete" after the server confirms auto-approval, matching a distinct "uploading evidence" state.

**Diverge because:** AD-11's Rule names the checkbox-completion mutation specifically ("The checkbox-completion mutation (FR-17) specifically uses... optimistic-update pattern") and gives no instruction for the photo-upload mutation either way. Each dev's choice is individually defensible and AD-11-compliant by omission. If Dev A's optimistic version ships, a failed upload leaves a window where the Tenant's device says "done" while the Landlord's device (per AD-10, only refetching on focus — no push-to-open-screen) shows nothing, directly contradicting FR-19's "Landlord can retrieve the current photo" and undermining the trust mechanic the PRD calls out as the product's most distinctive feature.

**Fix:** Extend AD-11's Rule to state the photo-upload mutation explicitly: pessimistic by design (UI waits for server confirmation before flipping to "complete"), given it's a slower, more failure-prone operation than the checkbox toggle — one sentence closes this.

### H-3. AI response envelope: where does the disclaimer actually live?

**Two units built as:**
- Dev A builds the backend AI service (AD-4), which "injects the disclaimer text from a single shared constant" — implemented as string-concatenation into the `answer` field returned in the `ok` state (e.g. `answer: "<AI text>\n\n⚠ AI can be wrong..."`).
- Dev B builds the frontend quick-answer component ("?" affordance, FR-14) and the chat component (FR-15), each expecting a *separate* `disclaimer` field in the response envelope so it can be styled as a persistent caption per DESIGN.md's tokens (AD-13) rather than inline AI-generated text, and rendered only "at least once per session" for chat per FR-15's actual wording.

**Diverge because:** AD-4's rule only commits to a *single shared constant as the source of the text* and three named states (`ok`/`low_confidence`/`error`); it never pins the field-level shape of the payload. If the backend bakes the disclaimer into the answer text and the frontend expects a separate field to render as styled UI chrome, the frontend either double-renders the disclaimer (duplicated inside the AI's own text, uncontrollably styled) or — more likely, if a dev trusts the separate-field assumption without checking — never renders anything, because the field it reads doesn't exist. That silently violates FR-14's testable consequence ("every AI-generated answer displays a visible disclaimer") for exactly the chemical-safety case the PRD flags as the one place accuracy actually matters.

**Fix:** Add one sentence to AD-4 pinning the response shape, e.g.: `{status: "ok" | "low_confidence" | "error", answer?: string, disclaimer?: string, error?: string}` — disclaimer always a separate field, never concatenated into `answer`.

---

## Medium

### M-1. "Task types" is an AD-6 concept with no corresponding entity in the Core Entities diagram

**Two units built as:**
- Dev A builds the Task-creation domain service (FR-4) and, needing somewhere to read `photo_evidence_eligible` from, adds it as a column directly on the `Task` row, set once at creation from a hardcoded lookup keyed by the task's name/category — since the Core Entities ER diagram has no `TASK_TYPE` entity to reference.
- Dev B builds the AD-6 eligibility check in the Photo-Evidence-requirement endpoint (FR-18), reading AD-6's wording — "Task types carry a system-seeded `photo_evidence_eligible` flag" — as implying one canonical lookup table, and writes the check as a join against a `TaskType` table keyed by a type code.

**Diverge because:** The spine's Core Entities diagram only lists `TASK`, with no `TASK_TYPE`/catalog entity at all, so AD-6's "Task types carry a flag" has no modeled home. Whichever dev's interpretation ships first, the other's code either can't compile against the schema or silently reads a flag that was set by a different, inconsistent code path (e.g. the AI-generated onboarding guide's auto-created tasks (FR-16) vs. manually created tasks (FR-4) computing eligibility differently if there's no single source of truth). Worst case: a privacy-sensitive task type (e.g. something bedroom-adjacent) ends up `photo_evidence_eligible = true` on one creation path and `false` on another, which is exactly the Privacy Constraints violation AD-6 exists to prevent.

**Fix:** Add `TASK_TYPE` (or equivalent catalog) to the Core Entities diagram with `TASK }o--|| TASK_TYPE`, and state in AD-6 that every Task-creation path (manual, AI-onboarding-generated) resolves its `photo_evidence_eligible` value by FK to that one table, never by copying/recomputing the flag per Task row.

### M-2. `complete_task_instance`'s idempotency contract under concurrent calls is unspecified

**Two units built as:**
- Dev A builds the checkbox endpoint (FR-17) calling `complete_task_instance`, and — to keep AD-11's optimistic-update UX feeling smooth when two Household Members tap "complete" within the same race window — makes the domain function's "already complete" case a silent no-op success (so a second caller's optimistic UI doesn't need an error path).
- Dev B builds the photo-upload endpoint (FR-19) calling the same `complete_task_instance`, and treats "already complete" as a 409 rejection (a photo shouldn't attach to an instance someone already checked off via FR-17 moments earlier), surfacing a hard error to the Tenant.

**Diverge because:** AD-3 only commits to *shared logic* ("neither duplicates its logic") inside one function, not to a *shared contract* for what that function does when called twice on the same instance. Since both callers are "compliant" by routing through the one function, the actual behavior on the race path depends on whichever caller's pre/post-condition check runs first in that shared function's implementation — meaning the two devs effectively have to negotiate this out-of-band, and whoever writes `complete_task_instance` first bakes in a choice the AD never made for them. This also leaves FR-11's fairness count ambiguous: does a race produce two `MEMBER_COMPLETION` rows for one instance (inflating both members' completion counts) or one (attributing to whichever request wins)?

**Fix:** Add one line to AD-3's Rule: calling `complete_task_instance` on an already-complete instance is idempotent — returns the existing completion state (HTTP 200) rather than erroring, and does not create a second `MEMBER_COMPLETION` row for the same instance.

---

## Low

### L-1. Due-check cron endpoint has no stated de-duplication guard

**Two units built as:**
- Dev A builds `/internal/run-due-check` (AD-8) assuming the 10–14 minute external cron cadence guarantees non-overlapping invocations, so no locking/dedup is added.
- Dev B builds the push-notification sender it calls, assuming the caller already guarantees single-flight execution, so it also adds no "already notified this cycle" guard.

**Diverge because:** AD-8 says the cron "is the only thing that triggers it" but doesn't require the endpoint to be safe against *overlapping* triggers (a slow Render cold-start response can cause cron-job.org to retry, or a long-running scan can still be executing when the next scheduled ping arrives). Neither dev is wrong per AD-8's literal text, but together they produce duplicate push notifications on a cold start — annoying, not core-loop-breaking.

**Fix:** Add a sentence to AD-8: the endpoint must no-op (not re-send) for any task instance already notified within the current due/overdue window, independent of how many times it's invoked.

### L-2. AD-12's "once per Member" install prompt has no stated storage tier

**Two units built as:**
- Dev A (frontend) implements "shown once per Member after first login" via a `localStorage` flag set after the prompt is dismissed — the obvious, zero-backend-work reading of "single shared component."
- Dev B, building anything that later assumes server-tracked onboarding state (e.g. a Landlord-facing "which Tenants have installed the PWA" view, or just a test asserting the rule), expects a `Member.install_prompt_shown_at`-style server field implied by AD-12's literal wording ("once per Member," not "once per device").

**Diverge because:** AD-12 states the rule at the Member level but the natural zero-friction implementation is device-level (`localStorage`), so a Member logging in on a second device/browser sees the prompt again — a harmless but literal violation of the stated rule, and a landmine for anyone building against the Member-level reading later.

**Fix:** Either relax AD-12's wording to "once per device" (matching the cheap implementation, and accurate for a PWA install prompt anyway — install state is inherently per-device), or explicitly commit to a server-side `Member` flag if "once per Member" is actually required.
