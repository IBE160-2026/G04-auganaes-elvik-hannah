---
title: 'Story 1.9: One Rule for Creating Homes'
type: 'feature'
created: '2026-11-10'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The creation rule (Story 1.3) and the joining rule (Story 1.4) disagree: a Landlord can never create their own Household Home, and a Household Member or Tenant can never create a Landlord Home (issue #30, retro R1).

**Approach:** One domain statement of the one-Home limit in `domain/homes` ("the Home where the user is Household Member or Tenant, if any"), read by both `allowed_types` and `join_blocker`. Landlord Home is always allowed; Household Home only when that statement finds nothing. A refused Household create answers 409 with the joining message naming the Home. No migration; seed data unchanged.

## Boundaries & Constraints

**Always:** Rule lives only in `domain/homes`; frontend offers exactly `allowed_types` and never derives it. `fr3_violations` stays `[]` after every create. A refused create writes nothing (existing user-row lock and rollback stay). The 409 text is built by one function shared with invites (`in_other_home_message`). Norwegian copy only.

**Decision (2026-11-10, Eirik):** A second Household Home (e.g. a cabin) stays out of scope; it is a possible later version, like the Trinn 2 AI extensions, tracked in issue #34. So the one-Home limit must live in exactly one function (`lived_in_home`): `role != "landlord"` (or `!== 'landlord'`) as a membership filter appears nowhere else in backend or frontend, so loosening it later is a one-place change.

**Decision 1 (2026-11-10):** Until Story 2.2, `/` keeps showing the newest Home (`homes_for` order unchanged); Story 2.2 brings «Dine hjem» and `/hjem/<id>`. Accepted consequence: after creating a second Home, `/` redirects to its Task Setup until that Home has Tasks, and the other Home's tasks are not on `/` until 2.2.

**Decision 2 (2026-11-10):** Create Home title is «Opprett hjemmet ditt» for a first Home, «Opprett nytt hjem» when both types are offered, «Opprett ny utleiebolig» when only Landlord Home is. A user with `lived_in_home_id` set also sees the lead «Du blir utleier for den nye boligen. Medlemskapet ditt i «X» endres ikke.» (X = that Home's name) in place of the first-Home lead; others with Homes get no lead. Type descriptions unchanged.

**Never:** No change to `join_blocker`'s results, `require_role`, `fr3_violations`, Alembic, `vercel.json`, Home switching (Story 2.2) or the InvitePage copy. No new endpoint.

## I/O & Edge-Case Matrix

| Scenario | State | `allowed_types`, `lived_in_home_id` / `POST /api/homes` |
|---|---|---|
| No Membership | — | both, null; either type 201 |
| Landlord only | Landlord of «Storgata 12» | both, null; household 201 → Household Member of it |
| Landlord + own household | Landlord, Household Member of «Karis» | `["landlord"]`, Karis; household 409 «Du er allerede med i «Karis». Du kan bare være med i ett hjem om gangen.» |
| Landlord + Tenant elsewhere | Landlord, Tenant of «Hybel» | `["landlord"]`, Hybel; household 409 naming «Hybel» |
| Household Member | Member of «Mari og Jonas sitt hjem» | `["landlord"]`, that Home; landlord 201 → Landlord, old Membership unchanged; household 409 naming it |
| Tenant | Tenant of «Storgata 12» | `["landlord"]`, Storgata 12; landlord 201; household 409 naming it |
| Left then create | Household Member left their Home (1.8) | both, null |
| Invite to own Home | Household Member opens invite to the Home they live in | `AlreadyMember`, not `InOtherHome` (order kept) |
| Join after create | Landlord created own household, opens another household invite | `InOtherHome` as today |
| Double submit (landlord) | two parallel landlord creates | both succeed (never refused); UI guards with pending button and `replace` as today |

</frozen-after-approval>

## Code Map

- `backend/app/domain/homes.py` -- `allowed_types` (:104), `join_blocker` (:143; keep `AlreadyMember` check first, then `lived_in_home`), `HomeCreationNotAllowed` (replace `allowed` with `home`), `create_home` (:118, lock + rollback reused); module docstring :8-9 and `allowed_types` docstring state the old rule.
- `backend/app/routes/homes.py` -- `LANDLORD_ONLY`, `ALREADY_IN_HOME` (:31-36) → delete; 409 mapping :115-117 (drop the `if exc.allowed` branch); 409 description :108 → "Household Home refused: the caller already lives in another Home"; `HomesOut` comment :68.
- `backend/app/routes/invites.py:37-42` -- `already_member_message`, `in_other_home_message`; invites already imports routes/homes (:19), so move both to a new `backend/app/routes/messages.py` that both import (no cycle).
- `backend/app/seed/homes.py` -- `_seed_household` :41 → `"household" not in allowed_types`; `_seed_landlord` :66-71 branch can no longer trigger → remove; `HOME_TYPES` import :12 then unused. Seed data unchanged.
- Backend tests: `test_homes.py` (:56, :68, :82-112; `exc.value.allowed` at :89, :98), `test_homes_routes.py` (:23 imports, :86-128, :171, exact-dict `HomesOut` at :161, :394 — grep `{"homes":`), `test_seed.py:285-302` (Kari in a Household → now gets «Storgata 12», Anders joins, 8 tasks; rename and rewrite) plus a row "Mari Landlord elsewhere → household created", `test_invites.py:310`/`test_invites_routes.py:277` stay valid.
- `frontend/src/routes/CreateHome.tsx` -- title :93, lead :95-97; keep the `allowed.length === 0` guard (:46: placeholders and fixtures can still be empty) with a rewritten comment; 409 comment :78-79.
- `frontend/src/api/queries.ts` -- placeholders in `useCreateHome` :176-180 and `useAcceptInvite` :215-218: keep `old?.allowed_types ?? []` and `old?.lived_in_home_id ?? null` until the refetch; never hard-code a type. Fix the comments.
- `frontend/src/routes/HomePage.tsx` -- header comment :1-3; `canCreate = allowed_types.length > 0` unchanged.
- Frontend tests: `HomePage.test.tsx:89-120`, `CreateHome.test.tsx:84-161`, `test-utils/fakeApi.ts:59-60,109` (`homesResponse`/`signedInWith` need `lived_in_home_id`).
- `README.md:89` (step 4, old rule) and `:103` (joining; keep consistent).

## Tasks & Acceptance

**Execution:**
- [ ] `sprint-status.yaml` -- 1-9 → `in-progress`, `review` when the PR opens
- [ ] `backend/app/domain/homes.py` -- `lived_in_home(session, user) -> Home | None`; `join_blocker` and `allowed_types` use it; `HomeCreationNotAllowed(home)`; docstrings
- [ ] `backend/app/routes/messages.py`, `routes/homes.py`, `routes/invites.py` -- shared messages; 409 via `in_other_home_message(exc.home.name)`; `HomesOut.lived_in_home_id: uuid | None`
- [ ] `backend/app/seed/homes.py` -- per Code Map
- [ ] `backend/tests/*` -- every matrix row; `fr3_violations` `[]` after each create; source test (AST/inspect): `allowed_types` and `join_blocker` call `lived_in_home`, and `!= "landlord"` occurs only in it
- [ ] `frontend/openapi.json`, `src/api/schema.d.ts` -- `cd backend && uv run python -m app.export_openapi`, then `cd frontend && npm run gen:api`
- [ ] `frontend/src/routes/CreateHome.tsx`, `HomePage.tsx`, `api/queries.ts`, `fakeApi.ts`, tests -- decision 2 copy (each title case, lead with X), placeholders, frontend matrix rows
- [ ] `README.md` -- step 4 new rule; :103 consistent
- [ ] `docs/ki-logg/korrigeringer.md` -- corrections found in review

**Acceptance Criteria:**
- Given the seed, when Kari opens «Opprett nytt hjem», then both types are offered, and choosing Husstand makes her its Household Member and goes on to Task Setup.
- Given the seed, when Jonas opens «Opprett nytt hjem», then only Utleiebolig is offered with the lead naming «Mari og Jonas sitt hjem», and after creating it his Membership there is unchanged.
- Given the full test suite and `fr3_violations` in CI, when they run, then all pass with no Home mixing Roles.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Spec review 2026-11-10 (one adversarial reviewer; 15 findings, verified against the code by the orchestrator):

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | `['landlord']` placeholder and "canCreate true for everyone" copy the rule into the frontend | high | keep `old` values; `canCreate` unchanged |
| 2 | CreateHome empty guard is not dead (`useAcceptInvite` placeholder, fixtures) | high | keep guard, rewrite comment |
| 3 | New `lived_in_home_id` breaks both placeholders and fakeApi types | high | named in Code Map |
| 4 | Exact-dict `HomesOut` assertions at test_homes_routes :161, :394 | medium | Code Map |
| 5 | Regen needs `app.export_openapi` before `gen:api` | medium | task fixed |
| 6 | `/` forces Task Setup of the new Home; other Home's tasks hidden | medium | accepted consequence written into decision 1 |
| 7 | test_seed Kari test flips entirely; unused `HOME_TYPES` | medium | Code Map |
| 8 | Source test ambiguous ("landlord" used legitimately elsewhere) | medium | exact assertion stated |
| 9 | `join_blocker` order (AlreadyMember first) unpinned | medium | matrix row |
| 10 | Exception shape contradictory | low | `home` only |
| 11 | Moving the message risks a circular import | low | new `routes/messages.py` |
| 12 | Stale copy/comments (409 description, comments) | low | Code Map |
| 13 | Lead per title case, InvitePage duplicate | low | decision 2 and Never |
| 14 | Missing rows: Landlord+Tenant, landlord double submit, `lived_in_home_id` | low | matrix |
| 15 | Line refs off; README :103 | low | fixed |

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all green
- `cd frontend && npm run lint && npm run build && npx vitest run` -- expected: all green

**Manual checks:**
- Local app with the seed: Kari creates a Household Home; Jonas creates a Landlord Home and sees the lead; Jonas trying household via API gets the 409 naming his Home.
