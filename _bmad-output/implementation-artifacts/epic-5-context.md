# Epic 5 Context: AI Assistant

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Any Member can tap "?" on a task for an immediate how-to answer with a visible disclaimer, escalate to a full AI chat, and a new Tenant gets an AI-generated onboarding guide tailored to their Home. Only the quick-answer (5.1) is Trinn 1; the chat (5.2) and guide (5.3) are Trinn 2.

## Stories

- Story 5.1: Contextual Quick-Answer ("?") — Trinn 1
- Story 5.2: Escalate to Full AI Chat — Trinn 2
- Story 5.3: AI-Generated Onboarding Guide for New Tenants — Trinn 2

## Requirements & Constraints

- Every AI answer is Norwegian only and carries a disclaimer (AI can be wrong; caution with chemical products) in its own field, always visible, whatever the status. Chemical questions are never scoped out.
- Low confidence or error is said plainly ("Usikker på svaret her — spør gjerne på nytt eller sjekk med noen andre"); a failed answer never blocks completing the task.
- A call that fails or takes over 10 seconds gives `status: "error"` and a retry action.
- At most 20 AI calls per user per day, quick answers and chat together, mock answers included; beyond that the user is told plainly when it resets.
- Only the task's name, its catalog type and the user's own question go to the provider: no user names, e-mail addresses or Home names. The UI says the question goes to an external AI service (Google Gemini).
- With no `GEMINI_API_KEY` the app uses mock answers in the same structure and marks them as demo mode; tests always use the mock; the app must run without any team account or key.

## Technical Decisions

- One backend AI service wraps every AI call (quick-answer, chat, onboarding guide). React never calls Gemini. Behind a provider interface with a Gemini provider and a mock provider (selected when the key is unset). Code lives in `backend/app/ai/`.
- Response object `{status: "ok" | "low_confidence" | "error", answer, disclaimer}`; the disclaimer comes from one shared constant and is never concatenated into `answer`.
- The service never raises into the route: timeout/provider failure becomes `status: "error"`. Timeout (10 s) and limit (20) are constants.
- Daily usage is stored in a new table `ai_usage` (user, day, count) via an Alembic migration. Days are UTC through `app/clock.py`.
- Onboarding guide (5.3) is generated once per Home at provisioning and persisted, not on every view.

## UX & Interaction Patterns

- "?" opens an inline popover on Task Detail, not a navigation; loading is a skeleton line with `aria-live="polite"`, the answer is announced the same way. "Ask more" (5.2) pushes into AI Chat with the task as context.
- "?" is tap-to-reveal, never hover-only.

## Cross-Story Dependencies

- 5.2 and 5.3 reuse the service, limit and payload rules built in 5.1.
- 5.1 depends on Task Detail (Story 2.3) and the shared route dependencies in `routes/deps.py`.
