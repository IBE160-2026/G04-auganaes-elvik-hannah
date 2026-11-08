---
title: 'Story 1.5: View Home Members List & Enforce Role-Based Permissions'
type: 'feature'
created: '2026-11-08'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '8cdbafafc0a05c258fb292d3fe9507514de94c97'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Members & Invite page (`/hjem/<id>/medlemmer`, Story 1.4) shows only the invite control, so nobody can see who else is in their Home. The Role rules (AD-2, FR-3, SM-6) are enforced on one route only, and nothing proves that every Home-scoped route goes through `require_role` or that a Home never mixes Household Members with a Landlord or Tenants.

**Approach:** Add a Home-scoped `GET /api/homes/{home_id}/members` behind `require_role` (all three Roles), and show the list on the existing Members & Invite page above the invite control. Add tests that pin the Role rules: cross-Home rejection, Tenant without the invite control, every `{home_id}` route guarded, and the no-mixing invariant over every write path.

**Decisions (team, 2026-11-08):**
1. Each row shows name and Role, plus "(deg)" for the caller. No email leaves the server, so a Tenant cannot collect other Tenants' emails.
2. FR-3's "never mixed" rule stays enforced by the domain (`_CREATOR_ROLE`, `_JOINER_ROLE`) and is proven by tests over every write path, plus a CI SQL query on the seeded database. No migration in this story.
3. Spec size (~2000 tokens) accepted; not split.

## Boundaries & Constraints

**Always:**
- Any Member of the Home may read the list (`require_role("household_member", "landlord", "tenant")`); a non-member, an unknown Home and a malformed id behave as in 1.4 (403 with `FORBIDDEN`, 422 for a bad UUID). The Role comes from the Membership row, never the JWT, body or query (AD-2).
- The list is built in `domain/homes` by `members_of(session, home_id)` (the route has only the Membership from `require_role`); the route stays thin. Order: Landlord first, then by `Membership.created_at`, then `Membership.id`. Creator-first holds only up to the clock resolution (~15.6 ms on Windows), so ordering tests pin `created_at` with `set_joined_at`.
- `require_role`'s `home_id` becomes an explicit `Path()` parameter, so a route without `{home_id}` in its path can never read it from the query (AD-2).
- FR-3 invariant, one predicate used by pytest and CI: a `household` Home has only `household_member` rows; a `landlord` Home has exactly one `landlord` and otherwise only `tenant`. The only `Membership(` constructors are in `domain/homes.create_home` and `add_member`; register-with-invite and `invites.accept` reach them through `add_member`.
- Role labels reuse `ROLE_LABELS` in `frontend/src/api/homes.ts`. The caller's own row is marked "(deg)".
- The page keeps 1.4's guards (loading, `HomesLoadError`, redirect only when the loaded Homes list lacks the id). The list lives in a child component rendered only after the Home is found (like `InviteControl`), so a foreign or mistyped id is never fetched. It has its own loading text (no `role="status"`, which the Homes loading already uses) and an inline error `MEMBER_MESSAGES.loadFailed = "Vi fikk ikke hentet medlemmene."` with a retry button labelled `aria-label="Prøv å hente medlemmene igjen"` (UX-DR30); a failed members load never hides the invite control.
- Freshness: the list refetches on mount and window focus (React Query defaults); no polling. Rows are keyed on `user_id`, since two Members can share a name.
- Norwegian copy, design tokens only, mobile-first, 44×44 tap targets.

**Never:**
- No removing Members, no leaving a Home, no changing Roles, no revoking links (reconcile-prd #5 stays a scope note).
- No Home switcher, no tab bar (Story 2.2).
- No Role in the JWT, body or query; no client-side Role check that decides access.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Household list | Mari (household_member of H) | 200, Mari and Jonas with Role `household_member`, Mari first | N/A |
| Landlord list | Kari (landlord of L) | 200, Kari (`landlord`) first, then Anders (`tenant`) | N/A |
| Tenant list | Anders (tenant of L) | 200, same list; page shows the list and no invite control | N/A |
| Outsider | Member of H calls L's members route | nothing returned | 403, same body as unknown Home |
| Unknown Home | random UUID | nothing returned | 403 |
| Bad id | `not-a-uuid` | nothing returned | 422 |
| Signed out | no Bearer | nothing returned | 401 |
| Landlord also Household Member | test fixture only (not the seed): Kari is landlord of L and household_member of H | each Home's list shows her Role in that Home | N/A |
| Members load fails | 5xx / network | inline error at the list with "Prøv igjen"; invite control still usable | never silent |
| Single Member | new Home, only the creator | list with one row, "(deg)" | N/A |
| Same names | two Members both named "Ola" | two rows, only the caller's has "(deg)" | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/permissions/require_role.py` -- reuse; only change: `home_id: Annotated[uuid.UUID, Path()]`. The returned closure has `__qualname__ == "require_role.<locals>.dependency"`; the route walk matches on that. `permissions/__init__.py` docstring still says "Filled in Story 1.5" (fix).
- `backend/app/routes/invites.py` -- pattern for a Home-scoped route: `Annotated[Membership, Depends(require_role(...))]`, 403 declared in `responses=`, `ErrorOut` from `routes/homes.py`.
- `backend/app/routes/homes.py` -- add the members route and `MemberOut`/`MembersOut` here (prefix `/homes`); update the module docstring, which says require_role is not needed here.
- `backend/app/domain/homes.py` -- `_CREATOR_ROLE`, `_JOINER_ROLE`, `homes_for` (ordering style), `add_member`, `create_home`; add the members read function.
- `backend/app/models/{membership,user,home}.py` -- `Role`, `ROLES`; `User.name`.
- `backend/tests/conftest.py`, `test_homes.py` (`set_joined_at`), `test_homes_routes.py`, `test_invites_routes.py` -- `make_client`, sign-in helpers, 403/422 assertions.
- `backend/app/seed/`, `tests/test_seed.py`, `.github/workflows/ci.yml` (seed counts ~line 91, CHECK step ~line 97) -- seeded Homes for the invariant query; seed data, counts and README seed table stay unchanged.
- `frontend/src/routes/MembersPage.tsx` + `.css`, `MembersPage.test.tsx` -- add the list section above `InviteControl`; keep the Tenant note. Existing tests use `findByRole('alert')`, `getByRole('button', {name: 'Prøv igjen'})` and `getByRole('status')`; they must keep passing unchanged.
- `frontend/src/api/homes.ts` (`ROLE_LABELS`, `HOME_MESSAGES` pattern, types from `schema.d.ts`), `api/queries.ts` (`homesKey` keyed on user), `test-utils/fakeApi.ts` (unknown routes answer 404; `signedInWith` must add `GET /api/homes/<id>/members` for each Home it gets, so existing tests see a list, not an error).
- `_bmad-output/planning-artifacts/architecture/*/ARCHITECTURE-SPINE.md` lines 35, 60, 225 and `epics.md` lines 110 and 125 -- still show `require_role(home_id, allowed_roles)` and the invite policy as an unconfirmed assumption. Keep each original sentence and append a dated `[REVISED 2026-11-08]` note, in the style of ARCHITECTURE-SPINE line 152.
- Not to touch: `alembic/env.py` and `alembic/versions/` (no migration, decision 2), `vercel.json`, `service-worker.ts`, refresh-token code, invite token handling.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 1-5 to `in-progress` now, `review` when the PR opens
- [x] `backend/app/domain/homes.py`, `permissions/require_role.py` -- `members_of(session, home_id) -> list[HomeMember]` (user id, name, Role narrowed as in `homes_for`, joined at), ordered as in Boundaries; `Path()` on `home_id`
- [x] `backend/app/routes/homes.py`, `permissions/__init__.py` -- `GET /api/homes/{home_id}/members` → `MembersOut {members: [MemberOut {user_id, name, role, is_you}]}`, 403 declared; docstrings updated
- [x] `backend/tests/test_homes.py`, `test_homes_routes.py` -- every matrix row; ordering with pinned `created_at`; the FR-3 predicate after `create_home`, `add_member` for both Home types, the dual-Role Landlord, register with `invite_token`, and accept into a Landlord Home
- [x] `backend/tests/test_permissions.py` -- walks `app.routes` and each `route.dependant` tree recursively: (a) every path with `{home_id}` has a `require_role` dependency; (b) every route with a `require_role` dependency has `{home_id}` in its path; (c) no route under `/api/homes/{...}/` uses another placeholder name for the Home; (d) no route has a query or body parameter named `home_id`; at least 2 routes are found, so the walk never passes vacuously. Cross-Home sweep: a Member of A calls every `{home_id}` route for B, with every other path parameter filled by a random UUID and no body, and gets exactly 403. `/api/invites/{token}` routes are out of scope (token-scoped)
- [x] `.github/workflows/ci.yml` -- after seeding, a SQL query joining `homes.type` finds no Home that breaks the FR-3 predicate
- [x] `frontend/openapi.json`, `src/api/schema.d.ts`, `src/api/homes.ts`, `src/api/queries.ts` -- regenerate; `fetchMembers`, `useMembers(homeId)` keyed on `['members', homeId, userId]`; `MEMBER_MESSAGES`
- [x] `frontend/src/routes/MembersPage.tsx` + `.css` -- section "Medlemmer" with a list of name, Role label and "(deg)"; own loading and inline error with retry
- [x] `frontend/src/routes/MembersPage.test.tsx`, `test-utils/fakeApi.ts` -- `signedInWith` serves members; list for Member/Landlord/Tenant, Tenant has the list and no invite control, "(deg)", same names, members error with retry while the invite control still works, no members request for a Home not in the list
- [x] `README.md` -- extend step 4 (~line 97): Anders sees Kari (Utleier) and himself (Leietaker, deg) and no invite button; mention the new CI invariant check in the CI paragraph (~line 136)
- [x] `ARCHITECTURE-SPINE.md`, `epics.md` -- delivered `require_role(*roles)` signature; invite policy marked settled (2026-11-07), with a dated note, not a rewrite
- [x] `docs/ki-logg/korrigeringer.md` -- corrections found in review
- [ ] After merge (status commit on main): 1-5 `done` in `sprint-status.yaml`, Story 1.5 done in `epic-1-context.md`, CLAUDE.md status, KI-logg README row

**Acceptance Criteria:**
- Given a clean clone and the seed, when Anders signs in and opens Members & Invite for «Storgata 12», then he sees Kari (Utleier) and himself (Leietaker, "(deg)") and no invite control.
- Given Mari signed in, when she calls `GET /api/homes/<Storgata 12>/members` in `/docs`, then the answer is 403.
- Given a new route with `{home_id}` added without `require_role`, when the test suite runs, then `test_permissions.py` fails.

## Implementation Notes

- **Route walk does not use `app.routes` directly.** FastAPI 0.162 includes routers lazily: `app.routes` holds `_IncludedRouter` wrappers, not `APIRoute`s, so a walk over it found 0 routes (the "at least 2 routes" guard caught it). The walk uses `fastapi.routing.iter_route_contexts(app.routes)`, the same walk the OpenAPI schema uses, which gives each route's full path and dependant tree. A meta-test builds a throwaway app with a `{home_id}` route without `require_role` and checks that the walk flags it (AC 3).
- **The FR-3 predicate** is `domain/homes.fr3_violations(session)`, one SQL query joining `homes.type`, used by pytest and by the new CI step "Ingen hjem blander roller (FR-3)". It also flags a Home with an unknown type. It returns `uuid.UUID`s; SQLite gives the id back as hex text and Postgres as a UUID, which the first draft compared as strings and got wrong on SQLite.
- **"Only two `Membership(` constructors"** is a source-scan test (`test_only_create_home_and_add_member_construct_a_membership`), so a new write path that builds a Membership outside `create_home`/`add_member` fails the suite.
- **Members load error** uses `role="alert"` plus a secondary-styled button (visible "Prøv igjen", `aria-label="Prøv å hente medlemmene igjen"`), since `PrimaryButton` takes no `aria-label` and the invite control keeps the page's one primary action.
- **Orchestrator fix after the code-review patches:** the visually hidden separator first used `width: 1px; height: 1px`, which `src/styles/tokens.test.ts` rejects as literal lengths; removed, since `position: absolute` with `clip-path: inset(50%)` already hides it.

## Spec Change Log

## Review Triage Log

Spec review 2026-11-08 (one adversarial reviewer; 18 findings, verified against the code by the orchestrator):

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | `fakeApi` answers 404 for unknown routes, so every existing Members test gets a second alert/"Prøv igjen"/status | high | `signedInWith` serves members; distinct retry label; no second `role="status"` |
| 2 | A top-level `useMembers` fetches a foreign id before the redirect | medium | list in a child component after the Home is found |
| 3 | `require_role` reads `home_id` from the query on a route without `{home_id}` | high | `Path()`; reverse direction in the route walk |
| 4 | Route walk cannot match the closure by identity; could pass vacuously | medium | `__qualname__` match; at least 2 routes |
| 5 | Other placeholder names or a body/query `home_id` slip past the walk | medium | checks (c) and (d) |
| 6 | Cross-Home sweep gets 422/404 on future routes with bodies/params | medium | random UUIDs, no body, exactly 403; invite routes out of scope |
| 7 | "Creator first" flaky on Windows clock ticks | medium | pin `created_at` with `set_joined_at` |
| 8 | Invariant ignores `Home.type` (zero Landlords, Tenant in Household Home) | medium | one FR-3 predicate joining `homes.type` |
| 9 | Register-with-invite and accept not named as write paths | low | named; route-level invariant checks |
| 10 | Dual-Role row could be read as seed data | low | fixture only; seed unchanged |
| 11 | `useAcceptInvite` invalidation of members is a no-op for the joiner | low | dropped; refetch on mount/focus is the freshness model |
| 12 | epics.md line 110 also has the old signature; edits could rewrite | low | lines 110/125; dated `[REVISED]` append |
| 13 | README step duplicates step 4; CI paragraph not updated | low | extend step 4; CI paragraph |
| 14 | Members load-error copy undefined | low | `MEMBER_MESSAGES.loadFailed` |
| 15 | Same-name Members; React key on name | low | matrix row; `key={user_id}` |
| 16 | `members_of(session, home)` but the route has only `home_id`; role typed `str` | low | `members_of(session, home_id)`, narrowed Role |
| 17 | Verification `cd frontend` from inside `backend/` | low | run from repo root |
| 18 | No post-merge status task | low | task added |

Code review 2026-11-08 (Blind Hunter, Edge Case Hunter, Verification Gap; 22 findings, verified against the code by the orchestrator):

| Finding | Verdict | Route / action |
|---|---|---|
| Route walk only covers `{home_id}` paths; a future `/api/tasks/{task_id}` without `require_role` passes, and the docstring promises otherwise (B) | medium | patch: every placeholder route has `home_id` or is on an allowlist (`/api/invites/{token}`) |
| Check (d) ignores header and cookie params (B, E) | low | patch: header/cookie params checked too |
| Check (d) does not recurse into `Optional[Model]`/Union or nested body models (B, E) | low | rejected: no such body exists; recursion adds branches for an unlikely route shape |
| `__qualname__` match breaks if `require_role` is renamed (B) | false | a rename makes `test_every_home_id_route_uses_require_role` fail loudly on both existing routes |
| Tie-break test repeats the same query 5 times (B) | low | patch: loop removed |
| Constructor scan misses `model_validate`/`insert(Membership)`/raw SQL; comments can trip it; docstring overclaims (B, E) | low | patch: claim softened to what the test guards; AST scan rejected as extra machinery for an unlikely bypass |
| Name and Role read as one word ("Ola (deg)Husstandsmedlem") by screen readers and copy-paste (B) | low | patch: visually hidden ", " |
| `memberRows()` breaks once the page has a second list (B) | low | patch: scoped to the "Medlemmer" region |
| Mermaid `%%` revision note does not render (B) | low | patch: note under the diagram |
| README has no step showing the list from a Household Member's side (B) | low | patch: clause in step 1 |
| 403 on the members load gives a retry that never succeeds (B, E) | low | rejected: needs a Member removed from a Home, which v1 has no action for (Never: no removing Members); the fix adds a branch |
| Background refetch failure keeps a stale list without an error (E) | low | rejected: same deliberate pattern as the Homes list (1.4: "a failed background refetch keeps the cached data") |
| Empty Household Home passes the FR-3 check (B) | low | rejected: `create_home` always adds the creator; FR-3 does not call an empty Home mixed |
| Cross-Home sweep has no caller with zero Memberships (B) | low | rejected: same `membership is None` branch as the other-Home caller; covered by the unknown-Home and outsider rows |
| `MembersList` and `InviteControl` share `key={home.id}` (E) | false | keys only need to be unique within an array of children; these are static siblings, and no React warning appears in the test run |
| `test_permissions.py` builds the app at import time (B) | low | rejected: `create_app` takes explicit `Settings` and opens no connection; no harm named |
| KI errors not in `korrigeringer.md` (B) | false | added when the story is presented (step 5), as in 1.3 and 1.4 |
| Spec checklist item for `sprint-status.yaml` unticked (B) | false | the task also covers `review` when the PR opens; ticked then |
| User id in `membersKey` untested (V) | low | defer: needs a session change without sign-out; shared gap with `homesKey`/`inviteKey`; deferred-work entry |
| Probe of checks (b), (c), (d) (V, other) | false | not a defect; the probe confirmed each guard fails |
| FR-3 query only proven to find violations on SQLite (V, other) | false | not a defect; the reviewer named no way Postgres differs (plain varchar + CHECK) |

## Design Notes

- **Route walk instead of a list of routes:** the "every Home-scoped route" AC is about routes that do not exist yet (Epics 2–6). A test that inspects `app.routes` and each route's dependant tree catches a forgotten `require_role` without anyone remembering to add a test.
- **Two directions in the route walk:** `{home_id}` without `require_role` is a missing check; `require_role` without `{home_id}` would read `home_id` from the query (AD-2). `Path()` makes the second fail at request time; the test catches both before then.
- **`is_you` from the server:** the frontend knows its own user id, but computing it on the server keeps the list self-contained and the test fixtures simple.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- all pass
- `cd backend && uv run python -m app.seed && uv run python -m app.seed` -- exit 0 both times
- From the repo root: `(cd backend && uv run python -m app.export_openapi) && cd frontend && npm run gen:api && git diff --exit-code src/api/schema.d.ts && npm test -- --run && npm run lint && npm run build` -- all pass, no diff
