---
title: 'Story 5.2: Escalate to Full AI Chat'
type: 'feature'
created: '2026-11-20'
status: 'done'
baseline_commit: '83c8b002de33b4cf6d50987b5eb433927d428a45'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-5-1-contextual-quick-answer.md'
  - '{project-root}/_bmad/custom/review-conventions.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The «?» popover answers one question. A Member who needs a follow-up has nowhere to continue. Story 5.2 adds a full AI chat, opened from the popover with «Spør mer», that keeps the originating Task as context, shows the disclaimer, and follows the 5.1 rules for timeout, data and daily limit (FR-15, FR-14, NFR4, AD-4, UX-DR9, UX Accessibility Floor).

**Approach:** No new AI implementation: `answer_question` (AD-4) gets an optional `history`, and the existing route `POST /api/homes/{home_id}/tasks/{task_id}/answer` accepts it. A new page `/hjem/<id>/oppgaver/<taskId>/chat` holds the conversation in memory and sends the earlier turns with each message.

**Decisions (mine; Eirik confirms or overrides):**
1. **Stateless server.** Questions and answers are still never stored (5.1 «Never»). The browser keeps the conversation in memory and sends the completed turns with each message. A reload of the chat page keeps what was carried in router state, otherwise it starts empty.
2. **One route, not two.** `/answer` gets `history: [{role: "user"|"assistant", text}]` (default empty). History needs a non-blank `question` (422 otherwise). The service stays the only entry; the quick-answer is a chat with empty history.
3. **Task context comes from the path, not the client.** The route resolves the Task (404 if archived or foreign) and passes its name and catalog type; the provider puts them in the first user turn. History carries no Task data.
4. **History is bounded and validated.** At most 10 entries, strictly alternating, starting with `user` and ending with `assistant`; a user entry up to 300 characters, an assistant entry up to 2000. Anything else is 422. The client sends only completed turns (ok or low_confidence answers) and trims the oldest pairs past 10.
5. **Provider payload.** Still only the Task's name, its catalog type, the user's own questions and the AI's own earlier answers to them, plus the instruction. The history is the user's own words and the AI's replies, so no new kind of data leaves the app; FR-15 and FR-14 say so in words. Client-made `assistant` turns are accepted: they only steer that user's own chat, the system instruction stays separate, and the 20 per day limit still holds.
6. **Counting.** Every chat message is one call, counted before it is made, exactly as in 5.1. The quick-answer and the chat share the 20.
7. **«Spør mer»** is a button in the popover, visible once an answer (ok or low_confidence) is shown. It navigates to the chat and carries the exchange as router state. The popover's own field stays (FR-14 requires it).
8. **Mock follow-ups.** The mock answers a follow-up (non-empty history) with a canned text that names the Task and says it is a demo answer, so context retention is testable offline. First messages keep the 5.1 canned answers.
9. **Page.** Heading with the Task's name, a back link to the Task, the disclaimer and the external-service line always visible above the stream, a message stream (`role="log"`, `aria-live="polite"`), a skeleton line while waiting, an input (max 300) and «Send». A failed message stays shown with «Prøv igjen»; the limit message says when the count restarts. Guards as Task Detail (unknown Home to `/`, a Task gone from the list back to the overview). Every Role.

## Boundaries & Constraints

**Always:**
- `answer_question(..., history=())` is the one entry; it never raises into the route except `LimitReached`. `AiRequest` gains `history: tuple[ChatTurn, ...] = ()` (`ChatTurn(role, text)`) and nothing else. Task name and type go in the first user turn, the instruction stays out of user text and user text out of the instruction.
- History validation lives in the request model of the route (pydantic) and is tested; the provider never sees an unvalidated list. The default question is built only when no question and no history are sent.
- The Gemini body for a follow-up contains the instruction, the Task header, the history texts and the new question, and none of the user's name, e-mail or the Home's name (test with a Home named «Hemmelig Borettslag»).
- Frontend: no `fetch`; the conversation is local UI state in the page (messages are not server data), the call is the existing mutation `useAskTask` extended with `history`. The page never reads the browser's clock. The stream is a polite live region; the disclaimer is outside it and always shown (visible at least once per session).
- `README.md` mentions the chat and that each message counts; `epics.md` (5.2 note), `ARCHITECTURE-SPINE.md` (AD-4: `history`) and the PRD (FR-15 consequences, one Revision log row) follow the code; `sprint-status.yaml` and CLAUDE.md Status after merge.

**Never:** storing chats or history on the server; streaming; a separate AI implementation or route for the chat; a different limit, timeout or payload rule; Task data from the client; 5.3's onboarding guide; reading the browser's clock.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error handling |
|---|---|---|---|
| Open from popover | answer shown, tap «Spør mer» | chat page with that exchange in the stream, Task name as heading | N/A |
| Follow-up | question + 1 completed exchange | 200; provider got history and Task from the path; usage +1 | N/A |
| Mock follow-up | history non-empty, no key | demo text naming the Task | N/A |
| Direct link | no router state | empty stream, input ready | N/A |
| History without question | history set, blank question | 422 | N/A |
| Bad history | wrong order, ends with `user`, 11 entries, too long | 422 | N/A |
| Failed message | provider error / timeout | status `error`; message stays with «Prøv igjen»; count was spent; history excludes it | retry asks again |
| Limit | 21st call | 429 `{detail, resets_at}` shown in the stream; provider not called | as 5.1 |
| Archived Task | stale chat | 404; tasks refetch, guard routes to the overview | as 5.1 |
| Tenant | Anders chats | 200 | N/A |
| Disclaimer | any state incl. error and empty | visible outside the live region | N/A |
| Payload | Gemini body | only name, type, history, question, instruction | test asserts |

</frozen-after-approval>

## Code Map

- `backend/app/ai/providers.py` -- `ChatTurn`, `AiRequest.history`, `GeminiProvider.build_body` (contents from history), `MockProvider` follow-up; `ai/mock_answers.py` -- `follow_up_for(task_name)`; `ai/service.py` -- `answer_question(history=)`, history limits as constants; `ai/__init__.py` exports.
- `backend/app/routes/ai.py` -- `AskRequest.history` with a validator; pass to the service; `responses` unchanged.
- `backend/tests/test_ai.py`, `test_ai_routes.py` -- every matrix row; `test_permissions.py` unchanged (same route).
- `frontend/openapi.json`, `src/api/schema.d.ts` -- regenerate (`uv run python -m app.export_openapi`, `npm run gen:api`).
- `frontend/src/api/ai.ts` (`askTask` with `history`, `ChatTurn`, chat messages), `queries.ts` (`useAskTask` variables), `test-utils/fakeApi.ts` (`answerHandler` records history).
- `frontend/src/components/QuickAnswer.tsx` -- «Spør mer» navigating with state; `.css`, `.test.tsx`.
- `frontend/src/routes/TaskChat.tsx`, `.css`, `.test.tsx` -- new page; `App.tsx` -- route.
- Reuse: `useFocusOnMount`, `AI_MESSAGES`, `AiLimitError`, `TASK_MESSAGES`, `useTasksWithPending`. Do not change `domain/ai_usage` or the counting.

## Tasks & Acceptance

**Execution:**
- [x] `backend/app/ai/*` -- `ChatTurn`, history in request, Gemini contents, mock follow-up, service parameter
- [x] `backend/app/routes/ai.py` -- `history` field and validation
- [x] `backend/tests/*` -- matrix rows, payload test, validation, counting, mock follow-up
- [x] regenerate `frontend/openapi.json` and `schema.d.ts`; `api/ai.ts`, `queries.ts`, `fakeApi.ts`
- [x] `QuickAnswer` «Spør mer»; `TaskChat` page, route, tests (a11y, failure, limit, history sent, guards)
- [x] `README.md`, `epics.md`, AD-4, PRD FR-15 + Revision log, `.env.example` if needed

**Acceptance Criteria:**
- Given an answer in the popover, when Peter taps «Spør mer», then the chat opens with that exchange and the Task's name, and his next question is answered with the Task as context.
- Given any chat state, then the disclaimer is visible outside the live region, and new messages are announced via `aria-live="polite"`.
- Given 20 calls today (popover and chat together), when he sends a message, then the stream says when the count restarts and no call reaches the provider.
- Given a failed or slow call, then the message stays with «Prøv igjen», the count was spent and the failed turn is not sent as history.
- Given the test suite and CI, then no test calls Gemini and the payload test proves nothing but Task name, type, history, question and instruction is sent.

## Implementation Notes

- Built directly (no implementation subagent: the mandate names the three reviewers only). Epic 5 context was older than `epics.md`/PRD (PRD-drift rows from 5.1), so the sources were read directly; no recompile.
- Backend: `ChatTurn` and `AiRequest.history` (`providers.py`), `GeminiProvider.build_body` builds `contents` from history and puts the Task header on the first user turn only, `MockProvider` answers a follow-up with `mock_answers.follow_up_for`. The route validates `history` in pydantic (`AskRequest`, `HistoryEntry`); the service trusts it. `domain/ai_usage` and the counting are untouched.
- The 5.1 structural test `AiRequest._fields` now lists `history` (the one sanctioned addition).
- Frontend: `TaskChat` has its own small guard instead of sharing `TaskDetail`'s (that one carries Detail-specific UI); the history is built by `historyOf` and trimmed in whole pairs. «Spør mer» builds the default question text itself (`defaultQuestion`) for display and history; the server's default stays the source of the wording the provider sees for the first message.
- Guarded lines: `test_a_bad_history_is_422_and_spends_no_call` (11 parametrized cases) guards the validators in `routes/ai.py` and that no usage row is written; `test_the_history_and_the_task_reach_the_provider_and_the_task_comes_from_the_server` guards `ChatTurn` mapping and that `task_name`/`task_type` in the body are ignored; `test_the_gemini_body_is_the_history_then_the_question…` guards the header-on-first-turn and role mapping in `build_body`; `test_a_follow_up_counts_with_the_quick_answers…` guards that history calls pass through `try_count_call`; `drops the oldest pairs…` guards `historyOf`'s slice; `keeps the failed message… never sent as history` guards `onSuccess` appending only non-error answers; the disclaimer tests guard its place outside the `role="log"` region.
- Not verified: no real Gemini call (no key locally); a follow-up against real Gemini on Preview is a separate smoke test (`gemini-3.1-flash-lite`, thinking LOW, with history the prompt is longer but the 10 s deadline is unchanged).

## Spec Change Log

## Review Triage Log

Code review 2026-11-20 (Blind Hunter B, Edge Case Hunter E, Verification Gap V; about 32 findings, verified against the code):

| Finding | Verdict | Route / action |
|---|---|---|
| An AI answer over 2000 characters is sent back as history and gets 422 forever; each retry spends a call (B, E, V) | high | patch: `historyOf` cuts an earlier answer to 2000; frontend test |
| The disclaimer is missing in an empty chat or when the first message fails without an answer, against the matrix row «any state» (B, E) | medium | patch: `FALLBACK_DISCLAIMER` in the frontend, kept equal to the server's text by a backend test; tests for error, network and limit |
| PRD-drift: FR-15 said a reload ends the chat, but a reload keeps the carried exchange (B, E) | medium | patch to text: FR-15 reworded |
| PRD-drift: the 2000-character cut, the oldest exchanges dropped, the direct link, FR-14's «Only» (B, E, V) | medium | patch to text: FR-14 points to FR-15, FR-15 states them; Revision log row amended |
| A blank history text passes `min_length=1`; the history list is parsed before its length is checked (E) | low | patch: blank validator, `max_length` on the list |
| `eleven` case in `bad_histories` would still pass without the length check (B) | medium | patch: case removed, `twelve` named as the length guard |
| `does not send a blank message` could pass without the guard (B) | low | patch: waits 50 ms before asserting |
| `defaultQuestion` is a copy of the server's default and no test ties them (V) | low | patch: a fixed-string assertion on both sides |
| README: mock follow-up only after a first exchange; no manual test step (B) | low | patch: wording and the step |
| Forged `assistant` turns reach Gemini (B) | low, accepted | already Decision 5: they steer only that user's own chat, the system instruction stays separate, the 20 per day limit holds |
| Real Gemini is not called with history (B, V) | medium, not testable here | defer: smoke test on Preview (`deferred-work.md`), stated in the PR |
| No auto-scroll or maximum height on the stream (B) | low | defer (`deferred-work.md`) |
| A failed message leaves the transcript when another is sent (B) | low | defer (`deferred-work.md`) |
| 403 test asserts only absence; router state shape checked loosely; `askTask` nested ternary and comment width; README one long bullet (B, E) | low, rejected | router state is built by our own code; lint passes; README keeps its existing single-bullet form |

## Design Notes

History is validated at the route so the service and providers can trust it. Trimming happens in the browser (oldest pairs first) so alternation always holds; the server only rejects, never repairs.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check .` -- all pass
- `cd frontend && npm test -- --run && npm run lint && npm run build` -- all pass (vitest on Node 24, see README)

**Manual checks:**
- Chrome on a throwaway DB, no key: «?» → «Spør mer» → two follow-ups show the demo text naming the Task; 21st call shows the limit. Real Gemini on Preview is a separate smoke test.
