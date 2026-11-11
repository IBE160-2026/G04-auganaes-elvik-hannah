---
title: 'Story 2.2: Must-first Task Overview, tab bar and Home switching'
type: 'feature'
created: '2026-11-10'
status: 'done'
route: 'dispatch'
baseline_commit: '789db4448e7e0973a1a13884dee748c4efc86c6a'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md'
  - '{project-root}/_bmad/custom/review-conventions.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `/` is the Story 1.3/2.1 placeholder page: it shows only the newest Home, a plain task list without due states, and the only «Logg ut». A user with two Homes cannot reach the second one's tasks, there is no tab bar, and «Husly» in the header is plain text (issue #37; FR-6, FR-21, UX-DR19/20/36/41).

**Approach:** One Task Overview per Home at `/hjem/<id>` (Must first, due states with words, skeleton, empty state, pull-to-refresh), `/` opening the most recently used Home, a tab bar on every signed-in page with a Home, a Settings/Profile page, and the wordmark as a link to `/`. The server decides each Task's due state, so the rule is tested in one place.

## Boundaries & Constraints

**Always:**
- Due state is computed in `domain/tasks` from `due_on` and the UTC date from `app/clock.py`: `overdue` (before today), `due_soon` (today up to the threshold), `later`. Sent as `TaskOut.due_status`; the frontend only renders it.
- Badge text is «Må»/«Bør» (Norwegian-only UI, as Story 2.1), never colour alone; due soon = warning colour, bold, «Snart forfall»; overdue = danger colour, «Forfalt».
- Focus order follows reading order: Must before Should, top to bottom. Every link/button has a visible focus ring and ≥44×44 tap target; skeleton respects `prefers-reduced-motion`. Only `var(--…)` tokens.
- All server data through TanStack Query hooks; guards route from the server's Homes list (foreign or unknown `homeId` → `/`, Home without Tasks → Task Setup for whoever may set it up, Tenant text otherwise); the global 403 handler keeps working (no inline error on 403).
- `/hjem/<id>/medlemmer` and Task Setup keep working; «Tilbake til hjemmet» goes to that Home's `/hjem/<id>`.

**Never:**
- No new Home-scoped API route outside `/api/homes/{home_id}/…`; no migration unless a decision below requires one.
- No completion (Story 2.4), no editing on Task Detail (2.3), no Add/Archive Task (2.6), no push-permission row (3.1), no gamification.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Must first | Should overdue, Must due in 20 days | Must row above Should row | N/A |
| Due states | due yesterday / today / today+threshold / today+threshold+1 | overdue / due_soon / due_soon / later | N/A |
| Cold load | tasks request pending | 3–4 skeleton rows, no empty text | N/A |
| Load fails | tasks GET 500 | inline error + «Prøv igjen»; header, tab bar still there | 403 → global handler, no inline error |
| `/` with 2 Homes | last used = B | redirect (replace) to `/hjem/B` | last used gone → fallback Home |
| Foreign id | `/hjem/<not mine>` | redirect to `/` | N/A |
| No Home | signed in, 0 Homes | `/` → Create Home, no tab bar | N/A |
| Wordmark | any page | real `<a href="/">` | signed out → sign-in via guard (an open invite's token is not kept; accepted) |
| Nothing due | every Task `later` | empty-state text above the full list | N/A |
| Task Detail | `/hjem/<id>/oppgaver/<taskId>` | Home guards as the overview; tasks pending → «Laster …»; loaded without that id → `/hjem/<id>` | 500 → inline error + «Prøv igjen»; 403 → global handler |
| Accept invite | Kari (last used «Storgata 12») joins a Household Home | lands on `/hjem/<joined>`, which becomes last used | N/A |
| Leave Home | leave the last used Home | lands on the fallback Home's overview with «Du har forlatt «X».» announced once | 0 Homes → Create Home with the notice |
| Setup done / 409 | Task Setup for Home B, success or 409 | `/hjem/B` (guard and success both), never `pickHome` | N/A |
| Tab bar hidden | signed out, sign-in/register, Homes pending or failed, 0 Homes | no tab bar | N/A |

## Decisions (team, 2026-11-10, all recommended options)

1. **«Snart forfall» = due within 3 days** (`DUE_SOON_DAYS = 3`: today … today+3). With 7, a weekly Task would always be due soon.
2. **The list always shows every Task, Must first.** When no Task is overdue or due soon, «Ingen oppgaver akkurat nå — nyt det! 🎉» (Household Home) or «Ingen aktive oppgaver i dette hjemmet.» (Landlord Home) shows above the list. No «Senere» split (it would break FR-6).
3. **Most recently used Home in `localStorage`, per user** (key includes the user id; read/write in try/catch). Visiting `/hjem/<id>` records it. `/` picks: stored id if still in the Homes list, else `lived_in_home_id`, else the first Home. No migration; per device.
4. **`/innstillinger` (Settings/Profile)** shows name and e-mail, «Dine hjem» (each Home: open its overview, «Medlemmer», «Sett opp oppgaver» when `can_set_up_tasks && !has_tasks`), «Opprett nytt hjem» when `allowed_types` is non-empty, and «Logg ut». The Task Overview header shows the Home name, «Medlemmer og invitasjon», and «Bytt hjem» (link to «Dine hjem» on Settings) when the user has ≥2 Homes.
5. **No Portfolio tab in 2.2.** Story 6.1 (Trinn 2) adds it with the Portfolio page; noted in `epics.md`.
6. **Row → minimal read-only Task Detail** at `/hjem/<id>/oppgaver/<taskId>` (name, badge, Frequency, due text, back link), read from the Home's tasks query; Story 2.3 extends it. **No checkbox in 2.2**: the checkbox and its focus-order AC move to Story 2.4 (noted in `epics.md`).
7. **«Logg ut» on Create Home**, so a user without a Home can sign out (closes the open item from Story 1.8).

Settled after the spec review (orchestrator, shown to the team at Checkpoint 1):

8. **Due text from the server's day count.** `TaskOut` also carries `days_until_due` (from the same UTC today as `due_status`), so «i dag / i morgen / om N dager» and «Forfalt» never disagree with the status.
9. **Pull-to-refresh has an accessible twin:** a small «Oppdater» button in the overview header; both refetch and announce «Oppdatert» in an `aria-live="polite"` region; the list area has `overscroll-behavior-y: contain`; no pull animation under `prefers-reduced-motion`.
10. **Empty-state wording by role:** the caller's `role === 'landlord'` gets «Ingen aktive oppgaver i dette hjemmet.», everyone else the household text.
11. **Header content:** Home name (h1), the caller's Role, «Medlemmer og invitasjon», «Bytt hjem» (≥2 Homes), «Oppdater». The «Velkommen hjem» lead and the Type/Role fact list are dropped; «Dine hjem» rows on Settings show each Home's Role.
12. **Last used is recorded only after the overview's guards pass** (Home found and has Tasks or is shown with the Tenant text). A stored id no longer in the list is ignored by `pickHome` and overwritten on the next visit. Invite accept and Task Setup navigate straight to `/hjem/<id>`.
13. **Tab bar:** rendered only with a session and a loaded Homes list with ≥1 Home. «Oppgaver» links to `/hjem/<current Home from the URL, else pickHome>` and is `aria-current="page"` on every `/hjem/:id/…` path; «Innstillinger» on `/innstillinger`.
14. **Focus after navigation:** each new page's `h1` gets focus (`tabIndex={-1}`) on mount; «Bytt hjem» targets `/innstillinger#dine-hjem`.

</frozen-after-approval>

## Code Map

- `backend/app/domain/tasks.py:144` -- `tasks_of` already sorts Must → `due_on` → name → id; add `DueStatus`, `DUE_SOON_DAYS = 3`, `due_status(due_on, today)`.
- `backend/app/routes/tasks.py:53-80` -- `TaskOut`/`tasks_out`: add `due_status`, `days_until_due` (one `utc_now().date()` per request).
- `backend/tests/test_seed.py:135` -- asserts a 7-day window; switch to `due_status == "due_soon"`. Seed (28/40 days back) gives one due-soon row per Home at +2 days; fine for a fresh local seed.
- `frontend/src/routes/HomePage.tsx` -- becomes the `/` redirector; its guards and `PendingNotice` (line 43, Story 1.8 leave notice) move to the overview.
- `frontend/src/routes/MembersPage.tsx:30-56` -- guard pattern to copy; «Tilbake til hjemmet» → `/hjem/<id>`.
- `frontend/src/routes/InvitePage.tsx:122`, `TaskSetup.tsx:126` + its `has_tasks` guard, `api/queries.ts` (`useSetUpTasks`/`useAcceptInvite` comments) -- navigate to `/hjem/<id>`, not `/`.
- `frontend/src/components/AppShell.tsx` + `AppShell.test.tsx` -- wordmark → `Link`; tests must wrap in Router + QueryClient. `App.tsx:86-91`: `AppShell` wraps `SessionGate`, so `TabBar` reads session/Homes defensively (decision 13).
- `frontend/src/App.test.tsx:52-55` -- asserts «Velkommen hjem» and empty storage; keep the token guard as "no key except the last-Home key".
- `frontend/src/api/tasks.ts:53` -- `formatDueOn` (local date parts); due text uses `days_until_due`, not the browser date.
- `frontend/src/components/Badge.tsx`, `PendingNotice.tsx` -- reuse; `tokens.test.ts` limits `--radius-full` to `Badge*.css`/`PrimaryButton.css`.
- `frontend/src/test-utils/fakeApi.ts` -- task fixtures get `due_status`/`days_until_due`; `HomePage`, `App`, `CreateHome`, `TaskSetup`, `MembersPage`, `InvitePage` tests expect `/` content today.
- `frontend/openapi.json`, `src/api/schema.d.ts` -- regenerate.

## Tasks & Acceptance

**Execution:**
- [x] `sprint-status.yaml` -- `2-2-…` to `in-progress`; `review` when the PR opens.
- [x] `backend/app/domain/tasks.py`, `routes/tasks.py` -- due status, day count, fields.
- [x] `backend/tests/test_tasks.py`, `test_tasks_routes.py`, `test_seed.py` -- boundaries −1/0/3/4 days, Must-first with an overdue Should, fields in GET and setup POST, seed has a due-soon row.
- [x] `frontend/openapi.json`, `src/api/schema.d.ts` -- regenerate.
- [x] `frontend/src/api/tasks.ts` -- due text from status + day count («Forfalt — frist var 26. september», «Snart forfall — i dag / i morgen / om N dager», «Neste gang: 9. desember»).
- [x] `frontend/src/api/lastHome.ts` (new) -- decisions 3, 12: per-user read/write in try/catch, `pickHome`.
- [x] `frontend/src/routes/TaskOverview.tsx` + `.css` (new) -- `/hjem/:homeId`: guards, `PendingNotice`, header (decision 11), skeleton (3–4 rows), empty text (2, 10), rows as links, error/retry, pull-to-refresh + «Oppdater» (9), focus (14), records last used (12).
- [x] `frontend/src/routes/TaskDetail.tsx` + `.css` (new) -- decision 6, matrix row "Task Detail".
- [x] `frontend/src/routes/HomePage.tsx` -- `/` only redirects (`replace`) to `/hjem/<pickHome>` or `/nytt-hjem`.
- [x] `frontend/src/components/TabBar.tsx` + `.css` (new), `AppShell.tsx/.css` -- decision 13; wordmark link.
- [x] `frontend/src/routes/Settings.tsx` + `.css` (new), `App.tsx` -- decision 4 (`id="dine-hjem"`); routes `/hjem/:homeId`, `/hjem/:homeId/oppgaver/:taskId`, `/innstillinger`.
- [x] `frontend/src/routes/MembersPage.tsx`, `TaskSetup.tsx`, `InvitePage.tsx`, `CreateHome.tsx`, `api/queries.ts` -- `/hjem/<id>` targets (decision 12); «Logg ut» on Create Home (7).
- [x] `frontend/src/**/*.test.tsx`, `test-utils/fakeApi.ts` -- every matrix row and AC; `pickHome` (stored gone, `lived_in_home_id` null, throwing storage); due text −1/0/1/3; pull via touch events; `aria-current` per path.
- [x] `_bmad-output/planning-artifacts/epics.md` -- Story 2.2 note (Må/Bør, 3 days, moved ACs); checkbox AC added to Story 2.4, Portfolio tab to Story 6.1.
- [x] `README.md` -- "Prøv oppgaveoversikten": Mari (overdue/due soon), Kari creates a Household Home and switches.

**Acceptance Criteria** (with the matrix; together they cover every epics.md 2.2 AC except the two moved by decisions 5 and 6):
- Given the seed, when Mari signs in, then `/` opens `/hjem/<her Home>` with every Må row above every Bør row, badges reading «Må»/«Bør», and at least one «Forfalt» (danger colour) and one «Snart forfall» (warning colour, bold) row.
- Given Kari creates a Household Home, when she opens «Storgata 12» from «Dine hjem», reloads and goes to `/`, then `/` opens «Storgata 12».
- Given a keyboard user on the overview, when they tab, then focus goes header → rows top to bottom (Må before Bør) → tab bar, each with a visible focus ring.
- Given the overview while tasks load, when the data is pending, then 3–4 skeleton rows show and no empty text.
- Given a pull from the top or «Oppdater», when released/activated, then the tasks refetch and «Oppdatert» is announced.
- Given any signed-in page with a Home, when it renders, then the tab bar and the «Husly» link to `/` are present and keyboard-reachable.
- Given a user with no Home on Create Home, when they activate «Logg ut», then they are signed out.

## Design Notes

- **Server-side due state:** CLAUDE.md asks for tests of due-date logic; one domain function, one UTC "today", no browser-clock drift between list and later push (Epic 3).
- **Must-first is already in `tasks_of`;** the frontend must not re-sort.
- **Last used Home on the device, not the server (decision 3):** no migration, and a wrong guess costs one tap on «Bytt hjem».

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all pass
- `cd frontend && npm test -- --run && npm run lint && npm run build` -- expected: all pass

**Manual checks:**
- Chrome smoke on a throwaway DB (not `husly`): Mari's overview, Kari creating a second Home and switching, accept an invite while having a Home, leave the last used Home, wordmark, tab bar at 320px width.

## Implementation Notes

- `TabBar` reads the Homes through `useLoadedHomes()` (`enabled: false`): an observer that fetched would mount before the page's own and load the list twice. Consequence: on a cold `/invitasjon/<token>` (which loads no Homes) there is no tab bar until the list is cached (decision 13).
- A Tenant opening Task Setup goes to `/hjem/<id>`, not `/` (the spec named only the `has_tasks` case).
- A failed «Oppdater»/pull announces «Vi fikk ikke oppdatert oppgavene.» and keeps the list.
- The overview header is a `<div>`, so the page keeps one banner landmark.
- `overscroll-behavior-y: contain` is set on `document.documentElement` while the task list is mounted (review fix), not on the list.
- `test-setup.ts` clears `localStorage` after each test; due-text tests freeze `Date` at 2026-11-10.
- Chrome smoke on a throwaway DB `husly_smoke22` (backend :8001, Vite :5174, removed afterwards): Mari's overview, due states, tab bar, Settings. Not done by hand then: 320px width, Kari's second Home, invite accept, leaving the last used Home (covered by tests).
- Manual checks 2026-11-11 on a throwaway DB `husly_smoke` (backend :8001, Vite :5174, removed afterwards), all passed:
  - 320px: the window would not shrink, so `/`, `/hjem/<id>`, `/innstillinger` and the Members page were loaded in a 320px iframe; no element extends past 320px.
  - Kari creates a second Home («Karis leilighet», Household), sets up Tasks, gets «Bytt hjem», switches via «Dine hjem»; `/`, the wordmark and the «Oppgaver» tab all open the last used Home.
  - Kari leaves the last used Home: lands on «Storgata 12» with «Du har forlatt «Karis leilighet».», shown once (gone after reload); «Bytt hjem» disappears.
  - Kari (last used «Storgata 12») accepts an invite to «Mari og Jonas sitt hjem»: lands on `/hjem/<joined>`, which becomes last used (`/` opens it).

## Spec Change Log

## Review Triage Log

Spec review 2026-11-10 (one adversarial reviewer; 18 findings, all verified against the code by the orchestrator, all taken in):

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | Invite accept navigates to `/`, which now opens the last used Home (`InvitePage.tsx:122`) | high | decision 12, matrix row, task |
| 2 | `App.test.tsx:55` asserts empty storage; last-Home key breaks it | high | Code Map: keep token guard, allow that key |
| 3 | Story 1.8 leave notice lost when `HomePage` only redirects | high | `PendingNotice` on overview; matrix row |
| 4 | Task Detail redirects while tasks are pending; no error/403 behaviour | high | matrix row "Task Detail" |
| 5 | Browser date vs UTC status disagree around midnight | medium | decision 8 (`days_until_due`) |
| 6 | Seed Kari has one Home; AC not reproducible | medium | AC/README: Kari creates a Household Home |
| 7 | `test_seed.py:135` checks 7 days, not due_soon | medium | test via `due_status`; fresh local seed is enough |
| 8 | `aria-current` for «Oppgaver» undefined | medium | decision 13 |
| 9 | Pull-to-refresh has no keyboard alternative or announcement | medium | decision 9 |
| 10 | Tab bar vs `AppShell.test` without Router/QueryClient; hidden states unspecified | medium | decision 13, matrix row, Code Map |
| 11 | Focus after navigation unspecified | medium | decision 14 |
| 12 | Too few ACs to cover epics.md | medium | ACs added; mapping stated |
| 13 | Task Setup success/409 go to `/` | medium | decision 12, matrix row |
| 14 | Empty text by Home type vs role | low | decision 10 (role) |
| 15 | Dropped Home page content not stated | low | decision 11 |
| 16 | Wordmark drops invite token for signed-out user | low | accepted, noted in matrix |
| 17 | `lastHome` record/clear rules incomplete | low | decision 12; `pickHome` tests |
| 18 | Manual checks miss invite and leave flows | low | Verification updated |

Code review 2026-11-10 (Blind Hunter, Edge Case Hunter, Verification Gap; 31 findings incl. duplicates, verified against the code by the orchestrator):

| Finding | Verdict | Route / action |
|---|---|---|
| `overscroll-behavior-y: contain` on a non-scrolling section; native pull-to-reload can fire too; CSS comment claims otherwise (B, E×2) | medium | patch: set on `document.documentElement` while the list is mounted |
| Deleted "background Homes refetch fails keeps page" test not replaced on the overview (V) | medium | patch: test on `/hjem/<id>` |
| Due-text tests assert year-less dates from 2026 fixtures; break when the browser year differs (B) | medium | patch: freeze Date in those test files |
| Moved ACs still unmarked in Story 2.2 in `epics.md` (B) | medium | patch: mark in place as moved |
| `atTop` rule of pull-to-refresh untested (V) | low | patch: test with stubbed scrollTop |
| Seed comment still says "due within a week" (V, B) | low | patch |
| Kiritimati test name over-claims (B) | low | patch: narrow name |
| Route test hardcodes the threshold; `== 3` repeated per case (B) | low | patch |
| README step 1 «om 2 dager» only true on seed day (E) | low | patch: wording |
| Double tap on Create Home «Logg ut» sends two requests (E) | low | patch: ignore while pending |
| Route test compares its own `utc_now()` with the server's; midnight race (B) | low | rejected: milliseconds at 00:00 UTC, same as accepted in 2.1 |
| «Logg ut» on Create Home shows also for users with Homes (B) | low | rejected: harmless duplicate of Settings; decision 7 only requires it for users without a Home |
| «Dine hjem» does not mark the current Home (B) | low | rejected: a new UX element; the overview h1 names the Home |
| Tenant waiting view has no «Oppdater» (B) | low | rejected: refetch on focus covers it; adding a refresh path is new scope |
| Settings profile empty while `/me` loads or fails (B, E) | false | `useMe` has `initialData: session.user`, so name and e-mail are there from the first render |
| Emoji in the household empty text is read aloud (B) | low | rejected: team-approved UX copy (EXPERIENCE.md) |
| Negative assertions after fixed 20 ms waits (B) | low | rejected: the absence is checked after the observable pending state; rewriting the waits is more than a direct fix |
| `aria-current="page"` on «Oppgaver» on Members/Setup (B) | low | rejected: decision 13 sets it on every `/hjem/:id/…` path |
| «Oppgaver» marked current for an unknown Home id (E) | false | the page redirects to `/` on the same render cycle; the state is never stable |
| Clicking «Innstillinger» on `/innstillinger#dine-hjem` does not move focus (E) | low | rejected: rare; focus stays where the user is |
| `dueText` with an unknown `due_status` (E) | false | the type is the generated union and frontend and API deploy together; TS enforces exhaustiveness |
| Tab bar on a cold `/invitasjon/<token>` depends on cache (E) | low | rejected: decision 13 shows it only with a loaded Homes list; the invite page loads none |
