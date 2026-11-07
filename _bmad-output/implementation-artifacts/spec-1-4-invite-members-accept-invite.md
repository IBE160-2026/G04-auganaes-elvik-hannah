---
title: 'Story 1.4: Invite Members via Scoped Link & Accept Invite'
type: 'feature'
created: '2026-11-07'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A Home can only ever have its creator. Mari cannot bring Jonas in, and a Landlord cannot bring in Tenants, so every shared-household feature in Epics 2–6 has nobody to share with (FR-2, UJ-1, UJ-2, SM-5).

**Approach:** Add `InviteLink` (scoped to one Home, carrying the joiner Role from `domain/homes`). A Household Member or the Landlord generates a link on a new Members & Invite page; whoever opens it sees the Home and either registers (linked on completion), signs in, or joins with one tap. Invalid links show the UX-copy message, never a 404. The server enforces who may invite and who may join.

**Decisions (team, 2026-11-07):**
1. Link policy: single-use, 7-day expiry. "Lag ny lenke" makes another link; earlier unused links stay valid. No revoking in this story.
2. The link carries no email. "Logg inn i stedet" appears when registration through the link hits an existing email (Story 1.2's 409 handling), and it keeps the invite.
3. A user may be Household Member or Tenant in at most one Home. A Landlord may also join one such Home. A Member or Tenant who opens a link to another Home sees "Du er allerede med i «X». Du kan bare være med i ett hjem om gangen."; the server answers 409. Enforced in `domain/homes.add_member`, so the seed follows it too (closes the 1.3 deferred-work entry).
4. The invite control lives on a new page `/hjem/<id>/medlemmer` ("Medlemmer og invitasjon"). The Home page links to it for the shown Home, and Landlords per Home in their list. Story 1.5 adds the members list to the same page.
5. Seed: example Landlord Kari Hansen (`kari@example.com`) with a Landlord Home, and example Tenant Anders Johnsen (`anders@example.com`) who joined it through an invite link (domain functions, not raw inserts).

## Boundaries & Constraints

**Always:**
- Who may invite is decided on the server from the caller's Membership row in that Home (AD-2). Because the Role implies the Home type, the allowed Roles are one constant `INVITER_ROLES = {household_member, landlord}` in `domain/homes`, used by both the route check and `can_invite`; `tenant` and non-members get the same 403 (a malformed UUID gives FastAPI's 422). The link's Role is `_JOINER_ROLE[home.type]`, never the caller's choice, and joining goes through `domain/homes.add_member`.
- The first Home-scoped route lands here, so this story adds `permissions/require_role.py`: `require_role(*roles)` returns a dependency that reads the path parameter `home_id: uuid.UUID`, loads the caller's Membership from the database and returns it. Story 1.5 reuses it. Deviation from epics.md (which places it in 1.5); recorded in the PR.
- `HomeOut` gets `can_invite: bool` computed by the domain, so the frontend never re-implements the rule. For a Tenant the invite control is absent, not disabled.
- The raw token (`secrets.token_urlsafe(32)`) is returned once at creation; only its SHA-256 hash is stored. Token inputs are capped at 64 characters.
- Time: `create_invite`, `preview` and `accept` take an optional `now` (default `utc_now()`) so tests fix the clock; a naive datetime read back from SQLite is treated as UTC before comparing.
- Commit semantics: `accept` locks the invite row (`with_for_update`), checks it, sets `used_at`/`used_by_user_id`, then calls `add_member`, which does the single commit. `add_member` rolls back before raising `AlreadyMember` or `InOtherHome`, so a refused join leaves the link unused.
- `homes_for` orders by the caller's `Membership.created_at` (then `Home.id`), so `/` shows the Home the user most recently created or joined; the join cache write matches that order.
- An invalid link (unknown, expired or used) shows "Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra utleieren." (Landlord Home), "… fra et husstandsmedlem." (Household Home), or "… fra den som inviterte deg." (unknown token).
- Registering through a link creates the account and the Membership in one request (`RegisterResponse` = `AuthResponse` + `joined_home_id`, used only by `/register`; login and refresh are unchanged). Register with `?invitasjon=` sends the now signed-in user to `/invitasjon/<token>`, never straight to `/`; the invite page then shows `already_member` (link used by this viewer) or the invalid message. If the link became invalid in between, the account is still created.
- `SignIn` and `Register` carry `?invitasjon=` through every link between them ("Logg inn i stedet", "Opprett konto", "Logg inn") and on redirect; the token is accepted only if it matches `[A-Za-z0-9_-]{1,64}`, otherwise ignored.
- The 1.3 copy `ALREADY_IN_HOME` is reworded to match decision 3: "Du er allerede med i et hjem, og du kan bare være med i ett hjem om gangen."
- The full link is built in the frontend from `window.location.origin` + `/invitasjon/<token>`; no base-URL variable.
- Every mutation goes through `backend/app/domain/invites.py` and `domain/homes.py`; routes stay thin. Norwegian copy, design tokens only, mobile-first, 44×44 tap targets, inline error with retry at the generate action (UX-DR30).

**Never:**
- No email sending, no push, no members list (1.5), no removing Members, no leaving a Home, no revoking links.
- No Role in the JWT, body or query.
- No tab bar or Home switcher.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Generate, Household | `household_member` of H | 201 `{token, role: household_member, expires_at}` | N/A |
| Generate, Landlord | `landlord` of L | 201, `role: tenant` | N/A |
| Generate, Tenant | `tenant` of L, direct API call | nothing written | 403 |
| Generate, outsider | no Membership in H, or H does not exist | nothing written | 403, same body |
| Generate fails | 5xx / network | inline error at the button with "Prøv igjen" | never silent |
| Preview | `GET /api/invites/{token}` | valid: `{status: valid, home_name, home_type, role}`; else `{status: invalid, home_type or null}`. With a valid Bearer also `viewer: can_join / already_member / in_other_home` and `other_home_name` | 200; a present but invalid Bearer gives 401 so the client refreshes |
| Open, signed out | valid link | Home name and Role; "Opprett konto og bli med" and "Logg inn" | N/A |
| Register via link | new email + valid token | 201, signed in, Membership with link Role, `joined_home_id` set; invite page sees `already_member` → `/` | N/A |
| Register, link died | new email, link expired meanwhile | 201, account created, `joined_home_id: null`; invalid message | N/A |
| Register, email taken | existing email | 409 with "Logg inn i stedet" that keeps the invite | N/A |
| Sign in via link | `/logg-inn?invitasjon=<token>` | back on the invite page after sign-in | N/A |
| Join | signed in, `can_join` | "Bli med i «H»" → Membership, link marked used, lands on `/` | N/A |
| Already in H | `already_member` | "Du er allerede med i «H»" + link to `/` | accept → 409, link stays unused |
| In another Home | Member/Tenant elsewhere | decision 3 message, no join button | accept → 409, nothing written |
| Landlord joins | Landlord only, Household link | joins as `household_member`; still may create Landlord Homes | N/A |
| Landlord joins another Landlord | Landlord only, other Landlord's link | joins as `tenant` | N/A |
| Landlord, second join | Landlord already in one non-Landlord Home | `in_other_home` | accept → 409 |
| Landlord, own link | Landlord of L opens L's link | `already_member` | accept → 409 |
| Used by this viewer | link used by the signed-in user | `already_member`, not the invalid message | N/A |
| Invalid link | expired / used by someone else / unknown | the message above, no 404 | accept → 410 (410 wins over 409 for others) |
| Expired session on preview | Bearer expired, refresh fails | signed-out view after refetch without Bearer | never an error page |
| Seed rerun | Kari's Home and Anders's Membership exist | nothing new; "finnes allerede" | Anders in another Home: skipped with reason |

</frozen-after-approval>

## Code Map

- `backend/app/domain/homes.py` -- `_JOINER_ROLE`, `add_member` (gets the second-Home rule and a user-row lock like `create_home`), `AlreadyMember`, `MemberHome`, `homes_for`.
- `backend/app/routes/homes.py` -- route style, `ErrorOut`, `HomeOut`/`_out` (add `can_invite`; reuse as the accept response), `SessionDep`, 409 declared in `responses=`.
- `backend/app/models/{home,membership}.py`, `models/__init__.py` -- model pattern: UUIDv4, `utc_now`, named PK/FK/unique/CHECK; import new models in `__init__`.
- `backend/alembic/versions/cf10f98fe92a_create_homes_memberships.py` -- current head; autogenerate the new revision, replace `AutoString` with `sa.String`.
- `backend/app/routes/auth.py` -- `RegisterRequest`, `register`, `AuthResponse`. Keep cookie/token code untouched.
- `backend/app/domain/accounts.py` -- `register` commits on its own; the route calls it, then the invite domain.
- `backend/app/permissions/current_user.py` -- `CurrentUser`, `_bearer`, `_unauthorized`; `require_role` and the optional-viewer dependency build on these.
- `backend/app/seed/{users,homes,__init__}.py`, `tests/test_seed.py` -- `EXAMPLE_USERS` (its docstring promises the Landlord and Tenant), `STEPS`, "finnes allerede" counts.
- `backend/tests/conftest.py`, `test_homes_routes.py` -- SQLite fixtures, `make_client`, how tests sign in.
- `.github/workflows/ci.yml` -- seed idempotence counts (~line 91) and the migrated-CHECK step (~line 97).
- `frontend/src/App.tsx` -- routes; `/invitasjon/:token` is public, `/hjem/:homeId/medlemmer` behind `RequireAuth`. `SignIn`/`Register` redirect to `/` when signed in and must honour `?invitasjon=`.
- `frontend/src/routes/{Register,SignIn,HomePage}.tsx`, `api/{auth,homes,queries}.ts` -- `AuthError`, `useHomes`/`homesKey`, `useCreateHome` (the cache-first no-bounce pattern for joining).
- `frontend/src/components/{PrimaryButton,TextField}.tsx`, `routes/HomesLoadError.tsx`, `test-utils/fakeApi.ts` -- reuse.
- Not to touch: `alembic/env.py`, `vercel.json`, `service-worker.ts`, refresh-token code.

## Tasks & Acceptance

**Execution:**
- [ ] `sprint-status.yaml` -- 1-4 to `in-progress` now, `review` when the PR opens
- [ ] `backend/app/models/invite_link.py`, `models/__init__.py` -- `InviteLink` (`invite_links`): `home_id`, `role` (`ck_invite_links_role`: household_member, tenant), `token_hash` (unique), `created_by_user_id`, `created_at`, `expires_at`, `used_at`, `used_by_user_id`; named PK/FKs/unique, index on `home_id` -- AD-1
- [ ] `backend/alembic/versions/<rev>_create_invite_links.py` -- autogenerate, review, working downgrade
- [ ] `backend/app/domain/homes.py` -- `INVITER_ROLES`, `can_invite(role)`; `add_member` locks the user row, raises `AlreadyMember` or `InOtherHome(home)` (the user has any non-`landlord` Membership in another Home), rolling back before raising and committing otherwise; `homes_for` ordered by `Membership.created_at` desc, then `Home.id`
- [ ] `backend/app/domain/invites.py` -- `create_invite`, `preview` (viewer state incl. "used by this viewer" → `already_member`), `accept` (commit semantics above), `InviteInvalid`; 7-day constant; hash helper; optional `now`
- [ ] `backend/app/permissions/require_role.py` -- `require_role(*roles)` as above; 403 with one Norwegian detail for wrong Role, no Membership or unknown Home
- [ ] `backend/app/routes/invites.py`, `routes/homes.py`, `routes/auth.py`, `main.py` -- `POST /api/homes/{home_id}/invites` (201), `GET /api/invites/{token}` (optional Bearer; a present invalid Bearer → 401), `POST /api/invites/{token}/accept` (200 `HomeOut`; 409/410 declared); `HomeOut.can_invite`; reword `ALREADY_IN_HOME`; `RegisterRequest.invite_token` optional (max 64), `RegisterResponse` for `/register` only
- [ ] `backend/tests/test_invites.py`, `test_invites_routes.py`, `test_homes.py`, `test_homes_routes.py` -- every matrix row; expiry via `now`; "sequential second accept fails" (named so; parallel is reasoned only); refused join leaves the link unused; only the hash is stored; Tenant and outsider 403; `homes_for` order after a join; registration with a dead link still creates the account; update `ALREADY_IN_HOME` and any exact `HomeOut` assertions
- [ ] `backend/app/seed/users.py`, `seed/homes.py`, `tests/test_seed.py` -- append Kari and Anders after Mari and Jonas (index 0/1 stay); Kari's Landlord Home "Storgata 12" created unless it exists, skipped with a reason when `"landlord"` is not in her `allowed_types`; Anders checked by Membership first, and an invite is created only when he will be added; `InOtherHome`/`AlreadyMember` printed as a skip. New counts: 4 users, 2 Homes, 4 Memberships, 1 invite link; update every hard-coded count and the "finnes allerede" total; fresh, rerun and partial tests
- [ ] `.github/workflows/ci.yml` -- counts 4 users, 2 Homes, 4 Memberships, 1 invite link; an insert into `invite_links` with `role='landlord'` (selecting an existing Home and User) fails naming `ck_invite_links_role`
- [ ] `frontend/openapi.json`, `src/api/schema.d.ts`, `src/api/invites.ts`, `src/api/queries.ts` -- `useCreateInvite`, `useInvite(token)` keyed on token and `session?.user.id` (so a failed refresh refetches signed out), `useAcceptInvite` (writes the Home first into the homes cache, then navigates); register passes the token
- [ ] `frontend/src/test-utils/fakeApi.ts`, existing `*.test.tsx` -- add `can_invite` to `OLAS_HOME` and every `Home` fixture
- [ ] `frontend/src/routes/MembersPage.tsx` + `.css` -- `/hjem/:homeId/medlemmer`: "Laster …" while pending, `HomesLoadError` without data, `/` only when the loaded list lacks the id; invite control only when `can_invite`; link in a read-only field with "Kopier lenke", "Kan brukes én gang, gyldig til <dato>", and "Lag ny lenke"; Tenant sees "Det er utleieren som inviterer nye leietakere."
- [ ] `frontend/src/routes/InvitePage.tsx` + `.css`, `Register.tsx`, `SignIn.tsx`, `HomePage.tsx`, `App.tsx` -- every invite state in the matrix; `?invitasjon=` handling as above; Home page links "Medlemmer og invitasjon"
- [ ] `frontend/src/**/*.test.tsx` -- invite page states incl. expired session with failed refresh, register with the token (joined and dead link), sign-in and the links between them keep the token, a bad token is ignored, members page for Member/Landlord/Tenant (control absent) and loading/error, generate error with retry, join without bounce
- [ ] `README.md` -- Kari and Anders in the user table, "prøv invitasjon" steps, CI paragraph counts
- [ ] `_bmad-output/planning-artifacts/epics.md`, `implementation-artifacts/deferred-work.md` -- note `require_role` moved to 1.4 and the link policy confirmed; mark the 1.3 second-Home entry settled
- [ ] `docs/ki-logg/korrigeringer.md` -- corrections found in review

**Acceptance Criteria:**
- Given a clean clone and the seed, when signing in as Anders and calling `POST /api/homes/<Storgata 12>/invites` in `/docs`, then the answer is 403, and his Members page shows no invite control.
- Given Mari signed in locally, when she creates a link and opens it in a private window, then a new user can register through it and lands in «Mari og Jonas sitt hjem» as Husstandsmedlem; opening the same link again shows the invalid-link message.
- Given this PR's Vercel preview, when a Landlord creates a link and a second account joins through it, then the second account is Leietaker, and the migration ran on the preview's Neon branch.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Spec review 2026-11-07 (one adversarial reviewer; 19 findings, verified against the code by the orchestrator):

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | `Register` redirects to `/` as soon as `setSession` runs, so the dead-link view is unreachable | high | register with token → `/invitasjon/<token>`; `joined_home_id`; matrix rows |
| 2 | Commit order of `used_at` vs `add_member` undefined; rollback could release the lock | high | commit semantics in Boundaries |
| 3 | Aware vs naive datetimes from SQLite; no clock injection | high | optional `now`, naive treated as UTC |
| 4 | Landlord cases of decision 3 missing | medium | three matrix rows; `InOtherHome` defined |
| 5 | `ALREADY_IN_HOME` promises joining by invite, contradicts decision 3 | medium | reworded; tests updated |
| 6 | `homes_for` orders by Home, so a joined older Home is hidden | medium | order by Membership |
| 7 | Members page redirect while loading repeats 1.3 finding #2 | medium | loading/error guard |
| 8 | `can_invite` breaks `OLAS_HOME` and other fixtures | medium | task added |
| 9 | Hard-coded seed counts; `EXAMPLE_USERS[0]/[1]` indexing | medium | counts listed; append order |
| 10 | Seed skip rules for Kari/Anders; partial reruns leak invites | medium | skip rules; invite only when adding |
| 11 | `require_role(home_id, …)` signature cannot be a dependency; rule in two places | medium | `require_role(*roles)`, `INVITER_ROLES` |
| 12 | `joined_home_id` leaks into login/refresh; unbounded token input | medium | `RegisterResponse`; max 64 |
| 13 | Parallel-accept lock untestable on SQLite | medium | Design Note; sequential test named so |
| 14 | The user who just used the link is told it is invalid | low | used by viewer → `already_member` |
| 15 | Failed refresh on preview returns an error | low | query keyed on user; matrix row |
| 16 | Token in redirect unvalidated; "Opprett konto" link drops it | low | pattern check; all links keep it |
| 17 | Token in URL path ends up in logs | low | accepted, Design Note |
| 18 | CI bad-role check vague; `RequireAuth` loses deep link | low | `role='landlord'` insert; deep link accepted |
| 19 | `export_openapi` missing from Verification | low | added |

## Design Notes

- **One permission check for both Home types:** `household_member` exists only in Household Homes and `landlord` only in Landlord Homes, so `require_role(home_id, {"household_member", "landlord"})` expresses "any Household Member, or the Landlord" without looking at the Home type.
- **Optional viewer on the preview:** the invite page must show decision 3's message before the tap, without the frontend copying the rule. A present-but-expired Bearer answers 401 rather than being ignored, so the existing refresh middleware retries and the signed-in view is never mistaken for a signed-out one.
- **No `revoked_at`:** the architecture lists a revoked state, but decision 1 has no revoke action. Adding the column later is one migration.
- **Locks are reasoned, not tested:** the invite-row and user-row locks prevent a double accept and a parallel second join on Postgres. pytest runs on SQLite, which ignores `FOR UPDATE`, so only the sequential case is tested (same gap as the 1.3 deferred-work entry); noted in the PR.
- **Accepted:** the token is in the URL path, so it can appear in Vercel request logs and browser history; it is single-use and expires in 7 days. `RequireAuth` still sends a signed-out deep link to `/hjem/<id>/medlemmer` to `/` after sign-in; only the invite link keeps its target.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- all pass
- `cd backend && uv run python -m app.seed && uv run python -m app.seed` -- exit 0 both times, second run says "finnes allerede"
- Migration round trip against a throwaway database, never the local `husly`: create `husly_verify` in the db container, point `DATABASE_URL` and `DATABASE_URL_UNPOOLED` at it, `uv run alembic downgrade base && uv run alembic upgrade head && uv run alembic check`, then drop it -- exit 0
- `cd backend && uv run python -m app.export_openapi`, then `cd frontend && npm run gen:api && git diff --exit-code src/api/schema.d.ts && npm test -- --run && npm run lint && npm run build` -- all pass, no diff
