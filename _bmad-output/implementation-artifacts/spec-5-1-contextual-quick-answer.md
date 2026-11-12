---
title: 'Story 5.1: Contextual Quick-Answer ("?")'
type: 'feature'
created: '2026-11-12'
status: 'done'
baseline_commit: '4da112683331af861592601507b9a77c6cc190f0'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
  - '{project-root}/_bmad/custom/review-conventions.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Member who does not know how to do a task step has nowhere to ask. Story 5.1 adds "?" on Task Detail, backed by one backend AI service with a Gemini provider and a mock provider, a 10-second timeout, a 20-calls-per-user-per-day limit and a minimal provider payload (FR-14, FR-22, NFR4, AD-4, AD-15, UX-DR48, SM-7).

**Approach:** `app/ai/` holds the provider interface, the two providers and `answer_question`, the one function every AI surface will call (5.2 and 5.3 reuse it). One Home-scoped route returns `{status, answer, disclaimer, demo}`. A new table `ai_usage` counts calls per user and UTC day. «?» on Task Detail opens an inline popover.

**Decisions (mine; each can be overridden at the checkpoint):**
1. **Question:** tapping «?» asks at once with a default question («Hvordan gjør jeg «X»?», built by the service); the popover also has an optional field «Spør om noe annet» (max 300 characters) that asks again with the user's own question.
2. **Where:** Task Detail only (UX: Quick-answer popover), for every Role, including Tenants.
3. **Route:** `POST /api/homes/{home_id}/tasks/{task_id}/answer`, body `{question?: string}`, behind `AnyMember`. The `test_permissions.py` walk covers it. An unknown, foreign or archived Task is 404.
4. **Counting (confirmed by Eirik):** every call that reaches the provider counts, failures and timeouts too (the quota is spent either way), so retries after an error also use up the 20; a refused call (limit reached) does not. Mock answers count (FR-14). README says this plainly.
5. **Limit answer:** HTTP 429 with `{detail, resets_at}`. `resets_at` is the next UTC midnight; the popover shows it with `Intl.DateTimeFormat` («Du kan spørre igjen 13.11.2026 kl. 01:00.»). The browser's clock is never read.
6. **Demo marker:** the response has an additive `demo: boolean` (true for the mock provider); AD-4 is updated to say so.

## Boundaries & Constraints

**Always:**
- React never calls Gemini. `answer_question(session, user_id, task_name, task_type, question) -> AiAnswer` is the only entry; it never raises into the route: any provider exception, bad provider output or timeout becomes `status: "error"`.
- `AiAnswer = {status: "ok"|"low_confidence"|"error", answer: str, disclaimer: str, demo: bool}`. `DISCLAIMER` is one constant in `app/ai/`, set on every response including `error`; it is never part of `answer`. It names the chemical caution.
- Constants, not literals: `AI_TIMEOUT_SECONDS = 10`, `AI_DAILY_LIMIT = 20`. The provider call runs in a worker thread with `future.result(timeout=AI_TIMEOUT_SECONDS)`; the Gemini `httpx` client uses the same timeout. The executor is module-level (or shut down with `wait=False`), never a `with ThreadPoolExecutor` block, whose exit waits for the provider and would defeat the bound; a test uses a provider that sleeps past the (patched) constant and asserts `status: "error"` comes back in time. The database session is committed (usage counted) before the call starts.
- The provider interface takes an `AiRequest(task_name, task_type, question)` and nothing else, so user names, e-mail addresses and Home names cannot reach it. `task_type` is the catalog key or `None` for a custom Task. A test asserts the exact JSON body the Gemini provider sends (with `httpx.MockTransport`) contains none of the user's name, e-mail or the Home's name.
- Provider choice: `GEMINI_API_KEY` set → Gemini, otherwise mock. Read through `config.py` (`_env`, empty = unset), never on import. `GEMINI_MODEL` is optional with a default constant. Automated tests always use the mock; the suite's network guard stays on.
- Gemini provider: REST `generateContent` with the key in the `x-goog-api-key` header (never in the URL or logs), a Norwegian-only system instruction (never mix languages, short, step by step, mention caution with chemicals), JSON output `{confidence: "ok"|"low", answer}`. The user's question goes only in the user content, never in the system instruction, so free text cannot override «only Norwegian» or «short»; a test asserts it. A provider exception becomes `error` without logging the request, URL or headers, so the key never reaches logs or messages; a test asserts it. «low» → `low_confidence`.
- Mock provider: a canned answer per catalog type (all eight) and one generic answer for a custom Task, in Norwegian, with `demo: true`. It does not read the question, so the demo marker also says so («Demo-svar … svarer ikke på selve spørsmålet»).
- `ai_usage(user_id FK users, day date, count int)` with PK `(user_id, day)` and `CHECK count >= 0`, via a hand-written Alembic revision after `d7a3b5c9e2f1`. The increment is one conditional `UPDATE … WHERE count < limit`; when it touches no row, an `INSERT` creates the day's row, and an `IntegrityError` from a race retries the `UPDATE` once. No `SELECT` then `UPDATE`. Days come from `app/clock.py` (UTC).
- Frontend: no `fetch` or server data in `useState`; a hook over the generated client (`useAskTask`, a mutation, since every call counts and must not be cached or retried automatically). The answer is kept while the popover is closed, so reopening does not spend a call. Skeleton line (not a spinner) with `aria-live="polite"`; the arriving answer is announced the same way. «?» is a button with an accessible name naming the Task and its state (expanded/collapsed), never hover-only. A failed or slow call shows «Usikker på svaret her — spør gjerne på nytt» for `low_confidence` and a plain error text plus «Prøv igjen» for `error` or a network failure; completing the Task is never touched. The disclaimer and the line «Spørsmålet sendes til en ekstern KI-tjeneste (Google Gemini).» are shown with every answer; in demo mode the marker reads «Demo-svar: ingen KI-nøkkel er satt, så svaret er ferdigskrevet og svarer ikke på selve spørsmålet. Med nøkkel sendes spørsmålet til en ekstern KI-tjeneste (Google Gemini).» A 403 shows nothing inline (global handler). A 404 refetches the tasks (the Task guard routes).
- `.env.example` and `README.md` (mock mode, how to set `GEMINI_API_KEY`, the limit) are updated in this PR. `epics.md` (Story 5.1 note on the decisions), the architecture's AD-4 (the `demo` field, the 429 body, failures count) and `sprint-status.yaml` follow the code.

**Never:** the full chat, «Ask more» or any 5.2/5.3 UI; the onboarding guide; streaming; storing questions or answers; a per-Home or per-Role limit; reading the browser's clock; sending anything but name, type and the question; a real Gemini call in any test or in CI; adding an AI SDK dependency (plain `httpx`, moved from dev to runtime dependencies at the same pin).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error handling |
|---|---|---|---|
| First tap, no key | «?» on «Rens sluket», no question | 200 `{status: "ok", demo: true}`, canned drain answer, disclaimer in its own field; usage count 1 | N/A |
| Own question | «Spør om noe annet»: «Hva med kalk?» | the provider got that question; a default question is built only when none is sent or it is blank | N/A |
| Custom Task | Task without `task_type` | generic mock answer; `task_type` is `None` in the request | N/A |
| Chemical question | «Hvilket middel egner seg på fliser?» | still answered, disclaimer shown | never scoped out |
| Low confidence | Gemini says `low` | `status: "low_confidence"`, disclaimer shown, popover says «Usikker på svaret her …» | N/A |
| Provider failure | HTTP error, bad JSON, empty answer | 200 `status: "error"`, disclaimer; count was spent | popover: error text + «Prøv igjen» |
| Timeout | provider takes over 10 s (test patches the constant) | 200 `status: "error"` within the limit, never a 500 | as above; retry possible |
| Limit | 21st call of the UTC day (mock too) | 429 `{detail, resets_at}`; provider not called; count stays 20 | popover shows the plain message with the reset time |
| New day | calls yesterday | count restarts at the new date | N/A |
| Two calls at once | both at count 19 | exactly one succeeds past 20, never 21 | the loser gets 429 |
| Question too long | 301 characters | 422 | shown at the field |
| Tenant | Anders asks | 200, same as others | N/A |
| Not a Member / other Home | any | 403 / 404 | global handler / refetch |
| Archived Task | stale popover | 404 «Fant ikke oppgaven.» | tasks refetch, guard routes |
| Payload | Gemini request body | contains only name, type, question and the instruction | test asserts |
| Failed answer mid-task | UJ-1: error shown | the Task can still be ticked | not blocking |

</frozen-after-approval>

## Code Map

- `backend/app/ai/{__init__,service,providers,mock_answers}.py` -- new; `AiRequest`, `AiAnswer`, `DISCLAIMER`, constants, `answer_question`, `select_provider`, `GeminiProvider`, `MockProvider`.
- `backend/app/models/ai_usage.py`, `models/__init__.py` -- the table; `backend/alembic/versions/` -- revision after `d7a3b5c9e2f1`; `.github/workflows/ci.yml` probes `alembic check` already.
- `backend/app/domain/ai_usage.py` -- `try_count_call(session, user_id, day) -> bool` and `next_reset(day)`; domain layer like `domain/tasks` (AD-3), the service only orchestrates.
- `backend/app/config.py` -- `get_gemini_api_key()`, `get_gemini_model()`; `.env.example`, `backend/tests/test_env_example.py` (stays green).
- `backend/app/routes/tasks.py` (or a new `routes/ai.py` if cleaner), `main.py` -- the route with `responses` for 403, 404 and 429 so the client types them; `AnyMember`.
- `backend/tests/test_ai_*.py`, `test_permissions.py`, `test_config.py` -- every matrix row; concurrency on SQLite where possible, the SQL logic otherwise.
- `backend/pyproject.toml`, `uv.lock` -- `httpx` to runtime dependencies.
- `frontend/openapi.json`, `src/api/schema.d.ts` -- regenerate (`uv run python -m app.export_openapi`, `npm run gen:api`).
- `frontend/src/api/{tasks or ai}.ts`, `queries.ts`, `src/test-utils/fakeApi.ts` -- `askTask`, `useAskTask`, messages, fake handler.
- `frontend/src/routes/TaskDetail.tsx`, `.css`, `.test.tsx` (or a `QuickAnswer.tsx` component) -- the «?» button and popover.
- `README.md`, `epics.md`, `ARCHITECTURE-SPINE.md` (AD-4), `sprint-status.yaml`, `docs/ki-logg/korrigeringer.md` if the review finds KI errors.

## Tasks & Acceptance

**Execution:**
- [x] `backend/app/models/ai_usage.py` + migration -- the table and its backstops
- [x] `backend/app/domain/ai_usage.py` -- atomic count and reset time
- [x] `backend/app/ai/*` + `config.py` + `.env.example` -- providers, service, constants
- [x] route + `main.py` + `backend/tests/*` -- the endpoint and every matrix row
- [x] `pyproject.toml`, `uv.lock`, `frontend/openapi.json`, `src/api/*`, `fakeApi.ts` -- client
- [x] `TaskDetail` «?» popover and tests -- UI, a11y, failure paths
- [x] `README.md`, `epics.md`, AD-4, `sprint-status.yaml` -- same PR

**Acceptance Criteria:**
- Given Peter on Task Detail without an AI key, when he taps «?», then a popover opens inline with a skeleton line, then a task-specific canned answer, the disclaimer and the external-service line, marked as demo; he can still tick the Task.
- Given 20 answers today, when he taps «?» again, then the popover says the limit is reached and when it resets, and no call reaches the provider.
- Given the provider fails or exceeds 10 seconds, when the popover is open, then it shows the error and «Prøv igjen» and the Task stays completable.
- Given the full test suite and CI, then no test calls Gemini and the payload test proves only name, type and question are sent.
- Given a screen reader, when «?» is used, then the button, the loading state, the answer and the error are announced with the Task's name.

## Implementation Notes

- Migration `a8c2f4d6b1e3`. Ran upgrade, `alembic check` (clean), `downgrade -1` and upgrade against a throwaway database `husly_scratch_51` in the Docker container (dropped afterwards; `husly` untouched). Race check on Postgres 18: 40 calls from 30 threads for one user and day gave exactly 20 successes and a stored count of 20.
- The limit constant lives in `domain/ai_usage` (the domain must not import `app.ai`); `ai.service.AI_DAILY_LIMIT` re-exports it. `AI_TIMEOUT_SECONDS` lives in `ai/providers.py` so the Gemini client and the service deadline share it; `ai.service` imports it, and tests patch it there.
- `tasks.active_task` is new in `domain/tasks`: the one lookup of an active Task by Home and id for the route.
- The Gemini provider is only tested over `httpx.MockTransport`; no real call was made (no key), and the default model `gemini-2.5-flash` is not verified against a live key.
- `conftest.mock_ai` (autouse) removes `GEMINI_API_KEY` and `GEMINI_MODEL`, so a developer's shell can never make a test call Gemini; the existing network guard backs that up.
- Frontend: the popover panel uses `hidden`, so its live region is removed from the accessibility tree while closed. The answer arrives later and is announced; the skeleton text of the opening moment may not be. `useAskTask` is a mutation: reopening keeps `data`, and only an idle mutation asks.
- Task Detail's tab order now has «Spør KI» between the title and the fields; the Tenant tab-order test was updated for that.

## Spec Change Log

## Review Triage Log

Code review 2026-11-12 (Blind Hunter B, Edge Case Hunter E, Verification Gap V; about 38 findings, verified against the code by the orchestrator):

| Finding | Verdict | Route / action |
|---|---|---|
| Pool of four threads: hung calls queue later ones, which time out unseen and still cost a count (B, E) | medium | patch: a daemon thread per call, with a test of eight hung calls and a quick one |
| Retry branch after a lost first-call race not pinned: the existing test never reached a successful retry (V) | medium | patch: new test where the retried update counts |
| Home-name check in the payload test vacuous: no Home existed (E) | medium | patch: route-level test with a Home named «Hemmelig Borettslag» and the Gemini provider on a mock transport |
| `get_gemini_model` and the key untested (B, V) | low | patch: `test_config.py` cases and a URL check |
| 403 branch of the popover untested (V) | low | patch: one test |
| `select_provider()` after counting could cost a call on a 500 (E) | low | patch: moved before counting, with a test |
| Reset text differs from decision 5 (year missing) (B, E) | low | patch: `dateStyle: 'short'`, «13.11.2026 kl. 01:00» |
| Unused `logger`, `calls_today` used only by tests, `getattr(..., "rowcount", 0)`, stale test path in the model docstring, tautological constant test (B, E) | low | patch: removed or fixed (`cast` to `CursorResult`) |
| Design Note: the leftover thread ends at the `httpx` timeout (B) | low | patch: the note now says the timeout is per phase |
| PRD-drift: counting of failed calls, UTC day and reset time, 300 characters, default question, Tenants, demo marker, stored counts (B, E, V) | medium | patch to text: FR-14, FR-22, §9 and one Revision log row; `epics.md` note rewritten as behaviour; AD-4's two sentences reconciled |
| `QuickAnswer` shows the previous Task's answer after a route change (B, E) | false | `TaskLoader` renders `<Detail key={task.id}>`, which remounts the popover |
| Cap the answer length; map a blocked answer to its own message (E) | low, rejected | the fix adds a limit and a status; a blocked answer already becomes `error` with retry |
| `ERROR_TEXT` never shown; retry cost not stated in the UI; no `Retry-After`; no client timeout; empty field gives no message (B) | low, rejected | `answer` must stay a string in the structure; the cost is in README and PRD; the server's deadline bounds the wait; each fix adds UI for a rare case |
| 403/404 popover empty for a moment (E) | low, rejected | the spec says a 403 shows nothing inline; a 404 refetches and the guard leaves the page |
| Live region inside a `hidden` panel; `role="alert"` inside a polite region (B) | maybe-false | defer: needs a screen reader (`deferred-work.md`) |
| No SQLite concurrency test; the Postgres race run has no automated trace (B) | low, rejected | the guarantee is one conditional `UPDATE`, run by hand on Postgres (Implementation Notes) |
| README and `.env.example` silent on the hosted demo without a key (B) | low | patch: one README sentence |

## Design Notes

The service is synchronous because the routes are; the 10-second bound is a daemon thread per call that the service waits on for at most the constant, so a hung provider cannot hold the request past it and hung calls never queue later ones (a first version used a pool of four, which could). The leftover thread ends when the provider's own `httpx` timeout does; that timeout is per phase (connect, read, write), not a total, so a trickling response can outlive the deadline for a while. Counting before calling means a crash mid-call still spends the call: the safe side for a free-tier quota. Limit text lives in the route as a constant next to `resets_at`; the frontend never builds Norwegian sentences from numbers it computed itself.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check .` -- all pass
- `cd frontend && npm test -- --run && npm run lint && npm run build` -- all pass
- `alembic upgrade head` / `downgrade -1` / `upgrade head` / `alembic check` against a throwaway Postgres database (not `husly`) -- all pass

**Manual checks:**
- Chrome smoke on a throwaway DB: «?» with no key shows the demo answer; asking 20 times then a 21st shows the limit message; the real Gemini call is not run (no key) and that is said in the PR.
