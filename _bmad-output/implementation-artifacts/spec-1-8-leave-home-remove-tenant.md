---
title: 'Story 1.8: Leave a Home & Landlord Removes a Tenant'
type: 'feature'
created: '2026-11-08'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'cb5ed9027c5f8c58614f92096cdd7c420b3de42e'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nobody can leave a Home or be removed. Because a Household Member or Tenant may belong to only one Home (Story 1.4, decision 3), a user who accepts the wrong invite is locked in for good and can only be freed in the database (Epic 1 retrospective R2; issue #25).

**Approach:** Implement FR-23 and AD-16 as planned in `sprint-change-proposal-2026-11-08.md`: a Household Member or Tenant can leave from Members & Invite; a Landlord can remove a Tenant there. Both delete only the Membership row, behind `require_role`, with an inline confirmation. A user who loses access while signed in is sent to `/` on the next 403.

**Decisions (Eirik, 2026-11-08, Sprint Change Proposal §2):** (1) Household Members and Tenants can only leave themselves; a Household Member cannot remove another. (2) A Landlord can remove Tenants but cannot leave their own Landlord Home. (3) When the last Household Member leaves, the Home remains without Members; nothing is deleted. (4) Leaving or removal deletes the Membership row only; history shows «Tidligere medlem» (from Epic 2). (5) A user who has left may create a Home or join another through an invite. (6) Invite links created earlier by someone who has left stay valid. (7) Leave and remove stay in one story (split check).

## Boundaries & Constraints

**Always:**
- Who may do what is decided on the server from the caller's Membership row (AD-2). `DELETE /api/homes/{home_id}/members/me` uses `require_role("household_member", "tenant")`; `DELETE /api/homes/{home_id}/members/{user_id}` uses `require_role("landlord")` and the target must be a Tenant of that Home. Every refusal (wrong Role, no Membership, unknown Home, target not a Tenant here, target is the caller) is the same 403 with `FORBIDDEN`; a malformed id is 422; signed out is 401. Success is 204. Register `/members/me` before `/members/{user_id}` (a test that a Household Member's and a Tenant's `DELETE …/members/me` return 204 guards the order). Because `require_role` runs before the endpoint's own `user_id` is validated, a malformed `user_id` gives 422 only for the Landlord of that Home; others get 403.
- Mutations go through `domain/homes`: `leave(session, membership)` and `remove_tenant(session, landlord_membership, user_id)`, where both Membership arguments are what `require_role` returns. Each deletes with `delete(Membership).where(...)` and commits, so a repeated or racing call deletes nothing else and raises nothing; nothing else is written or deleted, and no migration is added (AD-16). `remove_tenant` decides with `can_remove(caller_role, target_role)`, so the Tenant rule exists once.
- The rules live once in `domain/homes` and reach the frontend as server fields, like `can_invite` in 1.4: `HomeOut.can_leave` and `MemberOut.can_remove`. The frontend never re-derives them from Roles. `can_leave` is set wherever `HomeOut` is returned (list, create, accept); `can_remove` is false on the caller's own row.
- Frontend reuses `ApiError`/`toApiError` (`api/errors.ts`), the hooks pattern in `api/queries.ts` (AD-7) and `tests/helpers.py`. `leaveHome`/`removeMember` check `response.ok`, not `data`: openapi-fetch returns `data: undefined` for a 204.
- **Inline confirmation** (EXPERIENCE.md "Leave / remove confirmation"): the first button reveals an explanation, a confirm button in `--color-danger` with its text label, and «Avbryt». Leave text: «Du mister tilgangen til «X». Oppgavene du har gjort, blir stående.» with «Ja, forlat hjemmet»; remove: «Ja, fjern <navn>». Focus moves to the confirm button, and back to the first button on «Avbryt». A failure other than 403 shows an inline error with «Prøv igjen» (UX-DR30), which keeps focus; a 403 shows no inline error and only refreshes (below). Nothing is deleted until confirmed.
- **After leaving:** the mutation stores the notice «Du har forlatt «X».» under a query-cache key (e.g. `['notice', userId]`), then refetches the Homes query (`await refetchQueries`); it does not navigate or write a placeholder into the Homes cache. The existing guards then route from the server's answer: the Members page sends the user to `/`, and `/` to `/nytt-hjem` if no Homes remain, with the server's `allowed_types`. `HomePage` and `CreateHome` render the notice in a persistent `<p aria-live="polite">` (no `role="status"`, which the loading text already uses) and clear it once shown, so it survives the redirects but not a reload.
- **After removing:** the members query is invalidated; «<navn> er fjernet.» is announced in a persistent `aria-live="polite"` paragraph, and focus moves to the «Medlemmer» heading (`tabIndex={-1}`), since the removed row and its button are gone.
- **Removed while signed in, or a target already gone:** one global handler in `createQueryClient`, on both `QueryCache` and `MutationCache` `onError`: if `error instanceof ApiError && error.status === 403`, call `invalidateQueries({ queryKey: ['homes'] })` and `invalidateQueries({ queryKey: ['members'] })` (prefix match; the client has no user id). The Members page then sees the Home missing and redirects to `/` (existing guard), or a Landlord's list drops a Tenant who already left. No new retry, no error page, no loop: the members request is made once per refetch. It covers future Home-scoped routes too.
- Norwegian copy, design tokens only, mobile-first, 44×44 tap targets, `aria-label`s that name the person («Fjern Anders Johnsen»).

- **A used link and a leaver:** in `domain/invites`, "used by this viewer" counts as `already_member` (preview) or `AlreadyMember` (accept) only while the viewer still has a Membership in that Home; otherwise a used link is invalid (preview `invalid`, accept 410), like a link used by someone else.

**Never:**
- No deleting Homes, Users or invite links; no revoking links; no transfer of a Landlord Home; no Household Member removing another; no Landlord leave.
- No `left_at`/soft delete, no migration, no change to `fr3_violations`, the seed or hosting.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Household leave | Jonas leaves Mari's Home | 204; Membership gone; Mari's list shows only Mari; Jonas has no Homes, `allowed_types` both | N/A |
| Last member leaves | sole Household Member leaves | 204; Home row stays with no Members; `fr3_violations` `[]` | N/A |
| Tenant leaves | Anders leaves Storgata 12 | 204; Kari's list shows only Kari | N/A |
| Landlord also Household Member leaves the Household | Kari in Mari's Home | 204; Kari keeps Storgata 12 and lands on `/` with the notice | N/A |
| Landlord tries to leave | Kari, `members/me` on Storgata 12 | nothing deleted | 403 |
| Landlord removes Tenant | Kari removes Anders | 204; Anders has no Homes | N/A |
| Remove non-Tenant | Kari targets herself, or a user not in the Home, or a Tenant of another Home | nothing deleted | 403 |
| Non-Landlord removes | Mari removes Jonas; Anders removes Kari | nothing deleted | 403 |
| Outsider / unknown Home | Member of A on B, or random UUID | nothing deleted | 403, same body |
| Bad ids / signed out | Landlord with `user_id` `not-a-uuid`; anyone with `home_id` `not-a-uuid`; no Bearer | nothing deleted | 422; 422; 401 |
| Rejoin | Jonas, after leaving, opens a new link to Mari's Home | joins again as Household Member | N/A |
| Leaver opens own used link | Jonas reopens the link he once joined with | invalid-link message, no join button | accept → 410 |
| Create own Home after leaving | Jonas leaves, then creates «Jonas sin hybel» | 201; he is its Household Member | N/A |
| Who sees what | Landlord; Household Member; Tenant on Members & Invite | Landlord: «Fjern» on Tenants only, no leave; Household Member: leave, no «Fjern»; Tenant: leave, no «Fjern» | N/A |
| Repeated / racing delete | leave twice; leave while being removed | second call deletes nothing and does not error (domain); route gives 403 once the Membership is gone | N/A |
| Target already gone | Kari removes Anders after Anders left | 403; Kari's members list refreshes without Anders | no inline error |
| Old link by leaver | Jonas made a link, then left; Per opens it | valid; Per joins | N/A |
| Removed while signed in | Anders on Members & Invite when Kari removes him; the members refetch (window focus, no reload) | 403 → Homes and members refetched → `/` → `/nytt-hjem`; `GET …/members` called once | no error page, no loop |
| Leave/remove fails | 5xx / network | inline error with «Prøv igjen», focus stays; still a Member | never silent |
| Cancel | «Avbryt» | nothing sent; focus back on the first button | N/A |

</frozen-after-approval>

## Code Map

- `backend/app/domain/homes.py` -- `INVITER_ROLES`/`can_invite` (pattern for `can_leave(role)`, `can_remove(caller_role, target_role)`), `members_of`, `add_member`, `join_blocker`, `fr3_violations`; add `leave`, `remove_tenant`, `NotATenant`.
- `backend/app/permissions/require_role.py` -- `require_role(*roles)`, `FORBIDDEN`; reuse unchanged.
- `backend/app/routes/homes.py` -- `AnyMember`, `MemberOut`, `MembersOut`, `HomeOut`/`home_out`, `list_members`, `ErrorOut`; add the two DELETE routes and `can_leave`/`can_remove`.
- `backend/app/domain/invites.py:116-122,147-149` -- `used_by_viewer` in `preview` and the `used_by_user_id == user.id` check in `accept`; both must also require a current Membership.
- `backend/tests/helpers.py` (`new_user`, `sign_up`, `register_via_api`, `auth_for`, `count`), `test_homes.py`, `test_homes_routes.py` (`household`/`rental` fixtures, `join`, `invite_link`, `rows`; the exact `MemberOut` key-set assertion near line 241 must gain `can_remove`), `test_clock.py:56-63` (builds `HomeOut` without `can_leave`), `test_invites.py`/`test_invites_routes.py` (used-by-viewer cases), `test_permissions.py` (route walk and cross-Home sweep pick up the new routes automatically; the sweep fills `user_id` with a random UUID).
- `frontend/src/api/homes.ts` (`fetchMembers`, `HOME_MESSAGES`, `MEMBER_MESSAGES`; every function uses `if (!data) throw`, which is wrong for 204), `api/errors.ts`, `api/queries.ts` (`createQueryClient` with no user id, `homesKey`, `membersKey`), `routes/MembersPage.tsx:30-32` (redirect guard when the Home is missing), `routes/CreateHome.tsx:43-44` (redirect when `allowed_types` is empty), `routes/MembersPage.tsx` + `.css` (`MembersList`, `InviteControl`, `members-page__secondary`), `routes/HomePage.tsx`, `routes/CreateHome.tsx`, `test-utils/fakeApi.ts` (`signedInWith`, `olaAs`, `membersPath`, `OLAS_HOME`).
- `frontend/src/styles/tokens.css` -- `--color-danger`.
- `HomePage.test.tsx:35`, `MembersPage.test.tsx:125` -- use `getByRole('status')` for the loading text; the new notices must not add a second `role="status"`.
- `backend/app/seed/homes.py:48-56,74-92` -- re-running the seed re-adds Jonas to Mari's Home and Anders to Storgata 12 (deletes nothing).
- Not to touch: `alembic/`, `app/seed/`, `vercel.json`, `fr3_violations`, `require_role.py`.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 1-8 to `in-progress` now, `review` when the PR opens
- [x] `backend/app/domain/homes.py` -- `can_leave`, `can_remove`, `leave`, `remove_tenant` (raises `NotATenant` when `can_remove` is false or the target has no Membership here) -- FR-23, AD-16
- [x] `backend/app/domain/invites.py` -- used-by-viewer requires a current Membership (preview and accept)
- [x] `backend/app/routes/homes.py` -- the two DELETE routes (204, 403 declared), `HomeOut.can_leave`, `MemberOut.can_remove`
- [x] `backend/tests/test_homes.py`, `test_homes_routes.py`, `test_invites*.py`, `test_clock.py` -- every matrix row on the backend side; `fr3_violations` `[]` after each leave/remove; old link by a leaver still accepted; rejoin; `can_leave` on list, create and accept responses; `can_remove` false on own row; both `members/me` calls 204 (route order)
- [x] `frontend/openapi.json`, `src/api/schema.d.ts` -- regenerate
- [x] `frontend/src/api/homes.ts`, `api/queries.ts` -- `leaveHome`, `removeMember` (check `response.ok`), `useLeaveHome` (notice key, then refetch Homes), `useRemoveMember`, messages (`leaveFailed`, `removeFailed`, notices); 403 handler in `createQueryClient`
- [x] `frontend/src/components/ConfirmAction.tsx` + `.css` -- the inline confirmation, used by both actions
- [x] `frontend/src/routes/MembersPage.tsx` + `.css`, `HomePage.tsx`, `CreateHome.tsx` -- «Forlat hjemmet» section when `home.can_leave`; «Fjern» on rows with `can_remove`; left notice on both destinations
- [x] `frontend/src/test-utils/fakeApi.ts`, `**/*.test.tsx` -- `can_leave`/`can_remove` in fixtures; every matrix row on the frontend side, asserting `document.activeElement` on confirm, cancel, failure and after remove; a 204 fake response; the removed-while-signed-in redirect without reload and with one members call; the leave notice surviving the redirect to `/nytt-hjem`
- [x] `README.md` -- "prøv å forlate et hjem" steps (Jonas leaves, Kari removes Anders); undo by re-running `uv run python -m app.seed`, which puts both back and deletes nothing
- [x] `docs/ki-logg/korrigeringer.md` -- corrections found in review

**Acceptance Criteria:**
- Given the seed, when Jonas signs in and leaves «Mari og Jonas sitt hjem», then he lands on Create Home with «Du har forlatt «Mari og Jonas sitt hjem».», and Mari's members list shows only her.
- Given the seed, when Kari removes Anders while Anders has Members & Invite open, and Anders switches away from that tab and back (the tab becomes visible again; TanStack Query 5 refetches on `visibilitychange`, not on window focus), then he lands on Create Home without an error page.
- Given the route walk in `test_permissions.py`, when the suite runs, then both new routes are found and pass every check without editing that file.

## Implementation Notes

Implementation 2026-11-08 (dev agent), choices the spec left open:

- `domain/homes.is_member(session, home_id, user_id)` is the "still has a Membership" check used by `invites.preview`/`accept`.
- `leave` also refuses a Role that `can_leave` rejects (`ValueError`), so the Landlord rule holds in the domain and not only behind `require_role`.
- The global 403 handler leaves out the query that failed (`predicate: query !== failed`). Without that, a members query that answers 403 invalidates itself and refetches in a loop until the Homes refetch redirects (verified: the test runs out of memory without the predicate). Mutations have no failing query, so every members list refetches.
- The notice is read by `useNotice` in a `setTimeout` after mount (lint forbids `setState` directly in an effect, and the empty live region is then in the DOM before the text). It renders through `components/PendingNotice.tsx`, mounted only where the page is shown, so a redirect never consumes it.
- Remove explanation text (not given by the spec): «<navn> mister tilgangen til «X».» After a 403 on remove, focus also moves to the «Medlemmer» heading, since the row disappears on the refetch.
- In a failed state the confirm button reads «Prøv igjen» (same element, so focus stays).

Code review fixes 2026-11-08:

- Each Tenant row owns its `useRemoveMember` (`RemoveControl`) and reports back through `mutateAsync`, so «Avbryt» on one row can no longer reset another row's pending remove.
- A 403 on leave or remove folds the confirmation back to the first button (`ConfirmAction` passes `close` to `onConfirm`), so no second DELETE can be sent during the refetch.
- `remove_tenant` raises `NotATenant` when the DELETE's `rowcount` is 0 (the Tenant left between the SELECT and the DELETE), so the route never answers 204 for a delete that did not happen.
- The leave route uses `require_role(*sorted(homes.LEAVER_ROLES))`. A source-scan test keeps `delete(Membership` to `leave` and `remove_tenant`, and the route walk now names both new paths.
- The matrix row "Removed while signed in" says "window focus". TanStack Query 5 refetches on `visibilitychange`, so the AC and README say "switch to another tab and back". The test already dispatches `visibilitychange`.

## Spec Change Log

## Review Triage Log

Spec review 2026-11-08 (one adversarial reviewer; 18 findings, verified against the code by the orchestrator):

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | openapi-fetch gives `data: undefined` on 204; `if (!data) throw` would fail a successful delete | high | check `response.ok`; 204 test |
| 2 | Cache-first leave bounces between `/nytt-hjem` and `/` (stale `allowed_types: []`) and loses the notice | high | no placeholder; refetch Homes, let guards route |
| 3 | Notice in navigation state is dropped by the Members page guard | high | notice under a query-cache key |
| 4 | A leaver reopening their own used link is offered «bli med», then refused | high | used-by-viewer requires a current Membership; matrix row |
| 5 | Removed-while-signed-in AC reloads, so the 403 handler never runs | medium | AC and test without reload, one members call |
| 6 | Global handler cannot name `homesKey(userId)` | medium | prefix `['homes']` on both caches |
| 7 | Remove of a Tenant who already left leaves Kari's list stale | medium | handler also invalidates `['members']`; matrix row |
| 8 | Racing delete on a loaded ORM object warns or fails | medium | `delete(...).where(...)`; repeated-delete test |
| 9 | 422 for a bad `user_id` only for the Landlord | medium | matrix row says who gets 422 |
| 10 | `test_clock.py` and the exact `MemberOut` key-set assertion break; `can_leave` also on create/accept | medium | Code Map and tasks |
| 11 | Focus after remove/failure unspecified | medium | heading focus after remove; tests assert `activeElement` |
| 12 | Inline error on a 403 clashes with the redirect | medium | 403 shows no inline error |
| 13 | New live regions break `getByRole('status')` tests | low | `aria-live` paragraph without `role="status"` |
| 14 | Notice in history state returns on reload | low | resolved by the cache key |
| 15 | Tenant rule written twice | low | `remove_tenant` uses `can_remove`; parameters named |
| 16 | UI absence per Role and create-after-leave not in the matrix | low | rows added |
| 17 | README undo: re-running the seed already restores Jonas and Anders | low | README task changed |
| 18 | Route order unguarded | low | 204 test for both `members/me` callers |

Code review 2026-11-08 (Blind Hunter, Edge Case Hunter, Verification Gap; 15 findings, verified against the code by the orchestrator). First run with `_bmad/custom/review-conventions.md`: no reviewer filed KI-logg, `korrigeringer.md` or sprint-status as a finding.

| Finding | Verdict | Route / action |
|---|---|---|
| One remove mutation shared by all Tenant rows; cancelling or confirming another row drops the first row's notice and focus (B, E) | medium | patch: one mutation per row; two-Tenant test |
| After a 403 on remove/leave the confirmation stays open and can fire again (B) | low | patch: close on 403 |
| Double-submit guard in `ConfirmAction` untested (V, B) | low | patch: test with a pending DELETE |
| "Notice shown once" untested (B) | low | patch: test |
| `remove_tenant` answers 204 if the Tenant left between SELECT and DELETE (E) | low | patch: `rowcount == 0` → `NotATenant` |
| Leave route hard-codes the Roles beside `LEAVER_ROLES` (B) | low | patch: `require_role(*sorted(LEAVER_ROLES))` |
| No guard for where Memberships are deleted (B) | low | patch: source-scan test |
| Route walk's anchor set misses the new routes (B) | low | patch |
| README step relies on window focus; TanStack Query 5 refetches on `visibilitychange` (B) | low | patch: switch tab and back |
| Leave succeeds but the Homes refetch fails: user stays, notice lingers (E, B) | low | rejected: needs a network failure right after a successful DELETE; the next Homes load routes correctly and shows the notice once, so nothing is lost |
| Last Household Member leaves; an old link still lets someone join the empty Home (E, B) | false | decisions 3 and 6 (Eirik) keep the Home and the links; joining it is the intended outcome of a valid link |
| A removed Tenant gets no explanation (B) | low | rejected: EXPERIENCE.md "Removed while signed in" defines a silent redirect; a notice would need a new UX decision |
| Verification gap: everything else traced is covered (V) | false | not a defect |

## Design Notes

- **Server fields instead of Role checks in the UI:** `can_invite` set the pattern; `can_leave`/`can_remove` keep the Tenant/Landlord rules in one place, so a later rule change (e.g. allowing a Landlord to hand over a Home) touches only `domain/homes`.
- **Global 403 handler:** a removed Tenant's next request can come from any Home-scoped query (Members today, Task Overview in Epic 2). Invalidating Homes once and letting the existing guards redirect avoids a handler per page.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- all pass
- From the repo root: `(cd backend && uv run python -m app.export_openapi) && cd frontend && npm run gen:api && git diff --exit-code src/api/schema.d.ts && npm test -- --run && npm run lint && npm run build` -- all pass, no diff after regenerating
