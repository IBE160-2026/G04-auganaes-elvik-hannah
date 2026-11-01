---
title: "Sprint Change Proposal: Vercel as the only supported hosting"
date: 2026-11-01
status: approved
trigger: "Teacher's message of 2026-11-01: all group repos are connected to Vercel, which is the only hosting the course supports"
scope: moderate
rollback: tag v0.1-for-vercel-hosting (main after Story 1.1, commit 71164b2)
---

# Sprint Change Proposal — 2026-11-01

## 1. Issue summary

**Trigger.** On 2026-11-01 the teacher connected every group repo in the IBE160-2026 organisation to Vercel and wrote that Vercel is the only hosting the course supports. Other hosting has to be arranged and paid for by the group, with no help if it breaks. The teacher also names Supabase and Neon as examples of services whose keys go into Vercel's environment variables, so an external database is allowed. Only the hosting of the app itself is restricted.

**When.** Story 1.1 had just been merged (PR #4) and was live as a static frontend on <https://g04husly.vercel.app>. Story 1.2 (login, issue #5) had a branch but no code. This is the last cheap moment for the change: 1.2 is the first story where the frontend talks to the backend, and its auth design depended on the old hosting.

**Problem.** The optional hosted demo in the architecture used four services: Vercel for the static frontend, Render for FastAPI, Supabase for Postgres and Storage, and cron-job.org for the due-check. Render is now ruled out, which affects four decisions:

1. **AD-7 (auth)** assumed frontend and backend on different domains, so it needed a `SameSite=None` cookie and credentialed CORS.
2. **AD-8 (due-check)** needed a cron call every 10–14 minutes. Vercel Cron on the free Hobby plan runs at most once a day, with up to 59 minutes' delay ([Vercel Cron limits](https://vercel.com/docs/cron-jobs/usage-and-pricing)).
3. **AD-5 (Photo Evidence)** stored photos in Supabase Storage.
4. **Database:** Supabase had been chosen partly because the cron ping kept its free project from pausing.

**Evidence.** The teacher's message (pasted into the session of 2026-11-01, see `docs/ki-logg/okter/2026-11-01_eirik_a9ebc4c9.md`), the working Vercel project `g04husly`, and Vercel's documentation for [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi), [Services](https://vercel.com/docs/services), [Services routing](https://vercel.com/docs/services/routing), [Cron](https://vercel.com/docs/cron-jobs/usage-and-pricing) and [Blob](https://vercel.com/docs/vercel-blob/usage-and-pricing), all checked on 2026-11-01.

## 2. Impact analysis

**Epics.**
- **Epic 1** is affected: Story 1.2's auth criteria change, and a new Story 1.7 is added.
- **Epic 3** (Trinn 2) is affected: the due-check becomes a daily batch.
- **Epic 4** (Trinn 2) is affected: photo storage moves to Vercel Blob.
- **Epics 2, 5 and 6** are not affected.
- No epic is removed or renumbered. Stories: 23 + 1 = 24.

**New story.** Story 1.7, *Hosted Demo on Vercel (Services + Neon)*, is built before Story 1.2. Without it, nobody owns getting the backend online, and the login on 1.2's PR preview would reach no backend.

**Artifacts changed (one commit each):**

| Artifact | Change | Commit |
|---|---|---|
| PRD | Open Question 2 resolved as a daily morning batch; FR-10 made testable (one notification per day covering all due tasks); FR-13 cadence limited to whole-day intervals | `9dee99b` |
| Architecture spine | Hosted demo becomes one Vercel project with Vercel Services; Neon replaces Supabase (branch per preview); AD-5 uses a private Vercel Blob served only through the backend; AD-7 same-origin; AD-8 daily Vercel Cron; AD-15 adapter list; Stack, conventions, source tree, deployment diagram; memlog | `433c0e7` |
| UX (EXPERIENCE.md) | Deep-link rule split: one task opens Task Detail, several open Task Overview; FR-11 opens Task Detail, FR-12 opens Task Overview | `973c81d` |
| Epics | New Story 1.7; Story 1.2 same-origin plus a Safari check; Story 3.2 daily cron and deep-link rule; Story 3.5 whole-day cadence; Stories 4.2 and 4.3 Vercel Blob via the backend; UX-DR17; Additional Requirements | `a920d00` |
| `sprint-status.yaml` | `1-7-hosted-demo-on-vercel-services-neon: backlog`; recommended order 1-7, then 1-2, then 1-6 | `4e01320` |
| `epic-1-context.md` | Story 1.7 listed; Auth rewritten to the new AD-7; Stack and mock-adapter lines updated (the build agent reads this file) | `595a281` |
| Product brief | Hosting line in the constraints | `461bce7` |
| DESIGN.md | No change | — |

**Technical impact.**
- The Vercel project's Root Directory moves from `frontend` to the repo root, with a `vercel.json` that declares the services.
- The CORS middleware, `CORS_ORIGINS` and their tests from Story 1.1 become dead code and are removed in Story 1.7.
- The Vite dev and preview servers get an `/api` proxy, so local running is same-origin like the demo.
- Local running with Docker (AD-15) is otherwise unchanged and is still how a reviewer runs the app.

## 3. Recommended approach

**Direct adjustment.** No code is rolled back and no scope is cut. One story is added and four architecture decisions are revised before they are implemented.

- **Rollback of this change:** the tag `v0.1-for-vercel-hosting` marks `main` before the change. The PR is merged with a merge commit, so `git revert -m 1 <merge>` undoes it. In Vercel, the Root Directory must also be set back to `frontend`.
- **Effort:** low for the planning documents (done); small for Story 1.7.
- **Risk:** low to medium. Vercel Services is in beta, and Story 1.7 runs first precisely to find out early whether it works with our layout.
- **Timeline:** neutral. The four services become one project and one external database, which answers the teacher's earlier point about too much hosting infrastructure.

### Decisions made with the team

| Question | Decision | Why |
|---|---|---|
| Where FastAPI runs in the demo | Vercel Services in the same project as the frontend | The only supported hosting. One domain, one project, as the teacher asked ("ett prosjekt per gruppe"). |
| Database for the demo | Neon via the Vercel integration | Both Neon and Supabase connect to Vercel equally easily. Supabase's free project pauses after 7 days idle and needs a manual restart, so a reviewer opening the demo weeks after delivery could find it down. Neon wakes on the next query. We only use plain Postgres, so switching later only means a new `DATABASE_URL`. |
| Migrations on previews | (a) A Neon branch per PR preview, migrated in the build step and deleted when the PR closes | An unmerged migration never touches production. The free plan allows 10 branches, so the cleanup is required. Fallback if the cleanup is not possible on the free plan: migrate only on `main` and explain why in the 1.7 PR. |
| Photo Evidence storage | Private Vercel Blob, always served through a `require_role`-checked backend route | A permanent Blob URL can be shared and would keep working for a Tenant who moved out; with a fixed overwritten key it would even show the new Tenant's photos. Checking the Role on every view is the only way to meet NFR5. Story 4.3 chooses between streaming the photo and a short-lived signed URL. |
| Notification timing (PRD OQ-2) | Daily morning batch, one notification per Member covering all due and overdue tasks | Vercel Cron on Hobby allows one run a day. Tasks have due dates, not due times, UJ-1 already says the notification arrives "earlier in the day", and one daily message works against notification fatigue (SM-C1). |
| Auth (AD-7) | Same origin everywhere, `SameSite=Lax` refresh cookie, no CORS | With one domain, cross-site cookies and CORS are no longer needed. That avoids Safari's strict third-party cookie rules and makes local running behave like the demo. |

## 4. Detailed change proposals

Each proposal was presented in old → new form and approved one at a time (incremental mode). The exact text is in the commits in section 2.

| # | Proposal | Outcome |
|---|---|---|
| 1 | PRD: revision note, FR-10, FR-13, Open Question 2 | Approved |
| 2 | Architecture AD-7, same origin | Approved; CORS removal assigned to Story 1.7 |
| 3 | Architecture: AD-5, AD-8, AD-15, diagrams, deployment, Stack, conventions | Approved after the team asked why photos must go through the backend; AD-5 now leaves the choice between streaming and a signed URL to Story 4.3 |
| 4 | EXPERIENCE.md deep-link rule | Approved, with the matching Story 3.2 change |
| 5 | Epics: Story 1.7, 1.2, 3.2, 3.5, 4.2, 4.3, summaries | Approved; the fallback for Neon branch cleanup is acceptable if the PR explains it |
| 6 | Brief and `epic-1-context.md` | Approved (follows from 1–5) |

**Checked against upstream sources.**
- **UJ-1:** "push notification earlier in the day" and a single notification for two tasks match the daily batch.
- **FR-12** broadcasts stay immediate (AD-14).
- **FR-13** was the one thing the daily batch would have broken (an hourly cadence could never work), so it was tightened.
- **A stale file:** `epic-1-context.md` still described the old AD-7 and lacked Story 1.7. It was found by searching the whole repo for the old services, and it would have made the build agent implement the old auth in Story 1.2.

## 5. Implementation handoff

**Scope classification: moderate.** The backlog gets one new story and a new order. Code is touched only by the stories that follow.

| Role | Responsibility |
|---|---|
| Eirik (Vercel project owner) | When Story 1.7 is built: connect Neon under Storage in the Vercel project, set Root Directory to the repo root, add `CRON_SECRET` later (Trinn 2) and, if the cleanup uses a GitHub Action, add `NEON_API_KEY` as a repo secret. Only the owner can see the Vercel and Neon dashboards. |
| Developer (`bmad-build`) | Build Story 1.7, then Story 1.2 against the new AD-7, then Story 1.6. |
| Whole team | Story 1.2 issue #5 already mentions the AD-7 question; update it to point to this proposal. |

**Success criteria for this change.**
- PRD, architecture, UX, epics, `epic-1-context.md` and `sprint-status.yaml` agree on Vercel Services, Neon, Vercel Blob, the daily cron and same-origin auth. A search for Render, Supabase, cron-job.org, `SameSite=None` and `CORS_ORIGINS` outside the history finds only Story 1.1's code, which Story 1.7 removes.
- After Story 1.7: `/api/health` answers 200 on <https://g04husly.vercel.app>, and a PR preview uses its own Neon branch.
- Local running from the README still works with Docker alone, without any Vercel or Neon account.

**Not decided here.**
- Whether private Vercel Blob offers signed URLs, and the exact Python keyword for overwriting. This is checked in Story 4.3, which is Trinn 2.
- Whether Safari accepts the `Secure` cookie on `http://localhost`. This is checked in Story 1.2.
