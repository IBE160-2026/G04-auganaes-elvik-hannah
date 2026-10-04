---
name: 'Husly'
type: review
lens: 'Technology version & reality-check verification (web-researched vs. training-data asserted)'
target: ARCHITECTURE-SPINE.md
reviewed: '2026-10-04'
---

# Review — Version & Reality-Check Verification

## Overall Verdict

Most of the stack is correctly pinned and several claims are explicitly (and correctly) web-verified, but one committed technical caveat — SQLModel's SQLAlchemy 1.4 pin — is stale by roughly two years and was evidently asserted from training data rather than checked, and two live free-tier defaults (Render's monthly instance-hour cap, Supabase's 7-day auto-pause) that materially affect AD-8's design were never surfaced at all.

## Findings

### HIGH

**H1 — SQLModel's "pins SQLAlchemy ~1.4.41" caveat is obsolete; SQLModel has required SQLAlchemy 2.0 since mid-2024.**
- **Checked:** SQLModel's official release notes (`https://sqlmodel.tiangolo.com/release-notes/`) and GitHub discussion `fastapi/sqlmodel#547`.
- **Found:** SQLModel dropped its SQLAlchemy 1.4 dependency back at v0.0.19 (June 2024), moving its minimum requirement to SQLAlchemy 2.0.14. The current release as of this review is **v0.0.47** (2026-09-23), which tracks SQLAlchemy 2.0.5x (changelog shows routine bumps, e.g. "Bump sqlalchemy from 2.0.51 to 2.0.52"). There is no SQLAlchemy-1.4 pin in any SQLModel release in roughly the last two years.
- **Verdict — does not hold up, needs correction.** The Stack table's line `SQLModel | latest (pins SQLAlchemy ~1.4.41 internally — known, accepted limitation)` describes a real constraint from SQLModel's early life (circa 2022–2023) that was resolved over two years ago. This reads as a training-data assertion, not a web-verified one — unlike the adjacent FastAPI and google-genai rows, which carry explicit "(web-verified ...)" / "(supersedes deprecated ...)" annotations that do check out. Recommended fix: change the row to `SQLModel | latest (SQLAlchemy 2.0.x; no 1.4 pin since v0.0.19, June 2024)` or simply drop the parenthetical. No downstream AD depends on the 1.4 behavior, so this is a documentation correction, not a design change — but it's exactly the kind of claim the course project should not ship uncorrected since it's wrong and was clearly flagged as a "known limitation" when it isn't one anymore.

### MEDIUM

**M1 — AD-8's cron-ping cadence is close to exhausting Render's free-tier monthly instance-hour budget; this tradeoff isn't surfaced.**
- **Checked:** Render's own free-tier docs and multiple 2026 secondary sources on the 750-free-instance-hour/workspace/month allowance.
- **Found:** Render free web services spin down after 15 minutes idle (confirmed accurate, see M2/below) and grant **750 free instance-hours per workspace per month**. A calendar month has ~720–744 hours. Pinging every 10–14 minutes around the clock, as AD-8 prescribes, keeps the backend essentially always-on for the whole month — consuming nearly the entire 750-hour budget on this one service. If the workspace runs any other free-tier Render service in parallel (even briefly, e.g. a teammate's preview deploy), the combined hours can exceed 750, and Render suspends **all** free web services in that workspace for the rest of the month.
- **Verdict — AD-8's chosen mechanism is still sound, but the spine asserts it without checking this specific margin.** This doesn't invalidate the decision (the `[ASSUMPTION]` already flags it as "acceptable risk ... reversible to paid tier"), but the specific risk of *running out of hours mid-month and losing the whole service*, as distinct from "the ping pattern itself is unsupported," was not identified. Worth a one-line addition to AD-8's assumption: keep the workspace to a single free Render service, or the always-on ping could trip the 750-hour cap.

**M2 — Supabase's free-tier project auto-pause (7 days of inactivity) is a live default of a named dependency that is never mentioned anywhere in the spine.**
- **Checked:** Supabase's official docs, "Project Pausing" (`supabase.com/docs/guides/platform/free-project-pausing`).
- **Found:** Supabase pauses free-plan projects after 7 days with no API calls, DB connections, or dashboard logins. A paused project is restorable from the dashboard (data retained, one-year restore window), but the app is down until someone manually resumes it. Any request — including a scheduled health-check hit — counts as activity and prevents the pause.
- **Verdict — a real gap, but likely incidentally already covered, undocumented.** AD-8's due-check job runs every 10–14 minutes and, per AD-9, queries the DB to scan for due/overdue instances — so in practice it should also keep Supabase from pausing, as a side effect nobody designed for. The spine should say this explicitly (e.g., "the AD-8 cron ping also prevents Supabase's 7-day free-tier pause, since the due-check always touches the DB") rather than leaving it to chance — if a future refactor makes the due-check short-circuit before touching the DB when nothing is due, the team could lose this side benefit silently and the project would pause over a multi-week gap (e.g., over a reading week with no logins).

### LOW

**L1 — FastAPI's "web-verified current, Oct 2026" version is already one release behind.**
- **Checked:** PyPI release history for FastAPI.
- **Found:** Latest is **0.142.2** (2026-09-30); the spine's pinned `0.141.x` was current roughly two months earlier (0.141.1, July 2026).
- **Verdict — minor, expected churn, not a real problem.** FastAPI ships frequent point releases; pinning "latest" at install time resolves this automatically. Flagging only because the row explicitly claims to be "web-verified current" as of the document's own Oct 2026 date, and a newer patch already existed by then — the verification was done slightly before, or without, the most current check.

**L2 — React is pinned at "19.2" while 19.3.0 is the current minor as of September 2026.**
- **Checked:** React release notes/changelog sources.
- **Found:** React 19.2 (Oct 2025) is still fully supported and fine to build on; 19.3.0 shipped Sept 9, 2026 with no breaking changes relevant here.
- **Verdict — not wrong, just not the newest minor.** No action needed beyond optionally writing "19.2+" to signal the team isn't required to stay pinned to that exact minor.

**L3 — Calling Vite the "official CRA replacement" slightly overstates its status, and it's now several majors ahead of what most 2024-era references describe.**
- **Checked:** Vite's own release blog.
- **Found:** Vite is the de facto community-standard Create React App successor (CRA itself was archived/deprecated by the React team, who now point to frameworks or Vite-based scaffolds), not an "official" React-team product. Current major is **Vite 8** (March 2026), which switched its default bundler to the Rust-based Rolldown — a materially different engine from the Vite 4/5 era.
- **Verdict — wording nitpick, no functional risk.** Pinning "latest" via `npm create vite@latest` will correctly pull v8 with no spine changes needed; just note the "official" framing is informal usage, and if any team member scaffolds from an old tutorial pinned to Vite ≤5, double check plugin compatibility with Rolldown.

## Confirmed Accurate (no correction needed)

- **Render free-tier 15-minute idle spin-down** (AD-8): confirmed current and accurate via Render's own docs — free services spin down after 15 min idle, cold start ~30–60s on next request.
- **External-cron-ping workaround is genuinely unsupported/not guaranteed**, exactly as the spine's `[ASSUMPTION]` already states — Render's documented supported fix is the paid tier; the cron-ping pattern is a widely used but explicitly unofficial community workaround. cron-job.org itself remains a live, free, unlimited-job service as of 2026.
- **google-genai SDK naming and status** (Stack table, AD-4): correct. `google-generativeai` was deprecated Nov 30, 2025 and its repo archived Dec 16, 2025; `google-genai` reached GA in May 2025 and is the actively maintained official package (`pip install google-genai`). The spine's framing is accurate and appears genuinely web-checked.
- **pywebpush**: actively maintained, latest release 2.5.0 (Aug 29, 2026); "latest" pin is safe.
- **TanStack Query v5**: still the current major as of Sept 2026 (patch releases ongoing); "latest (v5)" pin is accurate.
- **AD-12's iOS 16.4+ Web Push / home-screen-install requirement**: still accurate in 2026; correctly already marked "web-verified" in the source document.

## Not independently re-checked (lower risk, judgment call)

TypeScript "latest stable," Node.js "current LTS," and Vercel's static-hosting defaults were not separately web-verified in this pass — these are evergreen "ecosystem latest" pins with negligible risk of being wrong in a way that would affect the architecture, since no specific version or deprecated-API claim is made about them.
