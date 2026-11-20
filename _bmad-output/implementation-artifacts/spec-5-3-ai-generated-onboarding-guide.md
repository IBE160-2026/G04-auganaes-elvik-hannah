---
title: 'Story 5.3: AI-Generated Onboarding Guide for New Tenants'
type: 'feature'
created: '2026-11-20'
status: 'in-progress'
baseline_commit: '340ca0a61c7d67aa9de7671602ca82d210d883d6'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-5-1-contextual-quick-answer.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-5-2-escalate-to-full-ai-chat.md'
  - '{project-root}/_bmad/custom/review-conventions.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Tenant who joins a Landlord's Home has no explanation of how Husly works or what is expected. Story 5.3 gives each Landlord Home a short onboarding guide, written once by the AI service when the Home's Tasks are set up, shown to a new Tenant as a one-time dismissible card on the Task Overview and kept reachable from Settings (FR-16, UJ-2, AD-4, UX Onboarding card).

**Approach:** The guide is two parts. The Home-specific part, the Home's name and its *current* active Must tasks with their frequencies, is built by the app from the database at every view, so it is always right and two Homes with different tasks never get the same text. The AI writes only a short general introduction about how the app works, once, and it is stored. The AI never sees the Home's name (FR-14 data rule). A new provider method behind the same provider interface and the same `app/ai` service writes it.

**Decisions (mine; Eirik confirms or overrides):**
1. **When:** generated in the request that sets up the Home's Tasks (Story 2.1), after the Tasks are committed, and only for Landlord Homes (only they have Tenants). The setup never fails because of the guide.
2. **What is stored:** one row per Home in `onboarding_guides` (`home_id` PK, `intro`, `source` `ai`|`demo`|`fallback`, `created_at`). Only the introduction is stored; name and Must list are never stored, so Tasks changed later (2.3, 2.6) cannot make the guide stale.
3. **Failure:** a provider error, a timeout, or the Landlord having used the 20 calls of the day gives the fixed Norwegian fallback introduction (`source: fallback`), stored all the same. There is no retry button (deferred). It still counts as one call when it reached the provider, like every call (FR-14).
4. **Counting:** the generation is one AI call counted against the setting-up user's 20 per UTC day, the same `try_count_call` and the same 10-second deadline as 5.1.
5. **Payload to the provider:** only the Must tasks' names, their catalog types and their frequencies in days, plus the instruction. No Home name, user names or e-mail. A test asserts the exact body.
6. **Homes set up before this story** have no stored row. They get the fallback introduction at view time, not stored and with no AI call.
7. **Who sees it:** `GET /api/homes/{home_id}/onboarding-guide` for a Tenant or the Landlord (403 for others, 404 if the Home has no Tasks). The card on the overview is for a Tenant who has not dismissed it. The Landlord sees the guide only from Settings, to know what Tenants read.
8. **Dismissal:** `POST /api/homes/{home_id}/onboarding-guide/dismiss`, Tenant only, idempotent, sets `memberships.onboarding_dismissed_at`. It is per Membership, so a Tenant who leaves and rejoins sees the card again (AD-16).
9. **Where to read again:** Settings, under «Dine hjem», has «Velkomstguide» for each Home where `can_view_guide` is true; it opens `/hjem/<id>/velkommen`, the same guide as a page.
10. **Disclaimer:** the guide carries the AI disclaimer in its own field (AD-4) whenever the introduction is AI-written or demo text, and the demo marker as in 5.1; the fallback text, which we wrote, has neither.
11. **Content rule for the AI:** it explains how Husly works (tasks, Må and Bør, ticking off, shared status, reminders, «Spør KI»), never how to clean, in Norwegian, at most 120 words. A test asserts the instruction says so.

## Boundaries & Constraints

**Always:**
- `generate_guide_intro(session, user_id, tasks) -> GuideIntro(text, source)` in `app/ai/service.py` is the only way the guide reaches a provider. It never raises into the route: limit reached, provider failure, bad output and timeout all give the fallback. Providers gain `write_guide(GuideRequest) -> str`; `GuideRequest` carries only `tuple[GuideTask(name, task_type, frequency_days)]`.
- The Gemini body for the guide has the guide instruction as the system instruction and the Must tasks as user content only, JSON output `{intro}`. The mock returns a canned introduction (`source: demo`) that does not read the tasks.
- `domain/onboarding.py` owns the rules: `GUIDE_ROLES`, `store_guide` (insert if missing, an existing row wins), `guide_for(session, membership)` (name, intro, source, current active Must tasks in the server's order, `dismissed`), `dismiss(session, membership)`. Routes only translate. Every new route with `{home_id}` goes through `require_role` (the `test_permissions.py` walk covers them).
- `HomeOut.can_view_guide` is decided by the domain (Tenant or Landlord, and the Home has Tasks); the frontend never re-implements it.
- Alembic revision after the current head `c4e6a8b0d2f5`: table `onboarding_guides`, column `memberships.onboarding_dismissed_at`, a CHECK on `source`; run against a throwaway database, never `husly`.
- Frontend: server data only through TanStack Query hooks; the card is a `section` with a heading naming the Home, the introduction, the Must list with frequencies in words (`FREQUENCY_LABELS`), the disclaimer and, in demo mode, the demo note, and a «Skjul» button. Dismissing removes the card at once and a failed dismissal shows it again. A 403 shows nothing (global handler). The card never blocks the task list.
- README and `.env.example` follow; `epics.md`, PRD FR-16 (+ Revision log row), AD-4 and the UX note follow the code; `sprint-status.yaml` and CLAUDE.md Status after merge.

**Never:** sending the Home name or any user data to the provider; storing the Must list or Home name in the guide; regenerating on view; a retry or edit UI; a guide for Household Homes; generating when a Tenant accepts an invite or opens the overview; reading the browser's clock.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error handling |
|---|---|---|---|
| Setup of a Landlord Home | Landlord sets up Tasks, mock provider | 201 as before; a row with `source: demo`; usage +1 | N/A |
| Setup of a Household Home | Household Member sets up | 201; no row, no AI call | N/A |
| Provider fails or times out | Setup | 201; row `fallback`; usage +1 | never a 500 |
| Landlord at 20 calls | Setup | 201; row `fallback`; provider not called; count stays 20 | N/A |
| Guide read | Tenant `GET` | Home name, intro, Must tasks with frequencies, `dismissed: false`, disclaimer | N/A |
| Tasks change later | Landlord adds a Må task, archives one | the next read lists the current Must tasks; intro unchanged | N/A |
| Two Homes | different Must tasks | different Must lists | N/A |
| Not regenerated | two reads | provider called once in total | N/A |
| Old Home, no row | read | fallback intro, no AI call, nothing stored | N/A |
| Roles | Household Member `GET` / Landlord `dismiss` | 403 | global handler |
| No Tasks yet | Landlord `GET` before setup | 404 | N/A |
| Dismiss | Tenant `POST` twice | 204 both; `dismissed: true`; other Tenants unaffected | N/A |
| Leave and rejoin | Tenant leaves, is invited again | `dismissed: false` | N/A |
| Disclaimer | `source` ai/demo vs fallback | disclaimer present vs absent | N/A |
| Payload | Gemini body | only Must names, types, frequencies, instruction; no Home name | test asserts |
| Card | Tenant opens overview | card at top; «Skjul» removes it; Settings still has «Velkomstguide» | N/A |
| Landlord | overview | no card; Settings has «Velkomstguide» | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/ai/providers.py` -- `GuideTask`, `GuideRequest`, `write_guide` on both providers, `GUIDE_INSTRUCTION`; `ai/mock_answers.py` -- `GUIDE_DEMO`; `ai/service.py` -- `GuideIntro`, `generate_guide_intro`, `GUIDE_FALLBACK`; `ai/__init__.py` exports.
- `backend/app/models/onboarding_guide.py`, `models/membership.py` (`onboarding_dismissed_at`), `models/__init__.py`; `backend/alembic/versions/` -- one revision.
- `backend/app/domain/onboarding.py` -- rules (reads `domain/tasks` rows; do not change `tasks.py` beyond what is needed).
- `backend/app/routes/onboarding.py`, `routes/tasks.py` (`set_up_tasks` calls the generation after the domain commit), `routes/homes.py` (`can_view_guide`), `main.py`.
- `backend/tests/test_onboarding*.py`, `test_ai.py` (guide provider tests), `test_permissions.py`, `test_homes*.py` (flag); `test_seed.py` / seed: the seed's landlord Home gets a guide row so the demo shows the card.
- `frontend/openapi.json`, `src/api/schema.d.ts`; `src/api/onboarding.ts`, `queries.ts`, `test-utils/fakeApi.ts`.
- `src/components/OnboardingGuide.tsx` (+ `.css`, `.test.tsx`), `routes/TaskOverview.tsx` (card for a Tenant), `routes/Settings.tsx` («Velkomstguide»), `routes/GuidePage.tsx`, `App.tsx`.
- Reuse: `try_count_call`, `_ask_within`, `FREQUENCY_LABELS`, `useFocusOnMount`, `PendingNotice` pattern. Do not change the 5.1/5.2 answer path or the counting.

## Tasks & Acceptance

**Execution:**
- [ ] model, migration, `domain/onboarding.py` -- table, column, rules
- [ ] `app/ai/*` -- guide provider method, instruction, mock, service function, fallback
- [ ] routes (`onboarding.py`, `set_up_tasks`, `can_view_guide`), seed -- the endpoints and the generation at setup
- [ ] `backend/tests/*` -- every matrix row, the payload test, permissions, migration check
- [ ] regenerate `openapi.json`/`schema.d.ts`; `api/onboarding.ts`, hooks, fake API
- [ ] `OnboardingGuide`, overview card, Settings link, guide page, tests (a11y, dismiss, failure)
- [ ] README, `epics.md`, PRD FR-16 + Revision log, AD-4, UX note

**Acceptance Criteria:**
- Given a Landlord sets up a Home's Tasks, when the request is done, then the Home has a stored guide introduction, written once, and the setup succeeded even if the AI failed.
- Given a new Tenant opens the Task Overview, then a dismissible card at the top names the Home and lists its current Must tasks with their frequencies; «Skjul» removes it and it stays gone, and «Velkomstguide» under Settings shows it again.
- Given two Homes with different Must tasks, then their guides never show the same text.
- Given the guide is generated, then it goes through the same AI service, the same limit and deadline and the same provider interface as 5.1/5.2, and nothing but Must task names, types and frequencies reaches the provider.
- Given the full test suite and CI, then no test calls Gemini.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

Splitting the guide into a stored AI introduction and a live Home-specific part keeps the requirement testable (the Must list is exact, whatever the model writes) and the privacy rule intact (the Home name never leaves). It also means a stored guide can never contradict the Home's current tasks. The cost is that the «AI-generated» part is small; that is deliberate for a free-tier quota.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check .` -- all pass
- `cd frontend && npm test -- --run && npm run lint && npm run build` -- all pass (Node 24)
- `alembic upgrade head` / `downgrade -1` / `upgrade head` / `alembic check` against a throwaway Postgres database -- if Docker runs; otherwise the CI migration job is the first run

**Manual checks:**
- Landlord Home on a throwaway DB, no key: set up Tasks, invite a Tenant, the Tenant sees the card with the demo marker, dismisses it and finds it under Settings.
