---
title: 'Story 1.1: Project Scaffold, Design Tokens & Responsive App Shell'
type: 'feature'
created: '2026-10-25'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'e247caa5bf9d8c3aff1b84112f240913ccf642be'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-prosjektoppgave-ibe160-2026-09-29/DESIGN.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The repo has only planning docs. Every later story needs a runnable backend, frontend, local database, test setup and the shared visual shell before it can add features or tests (Story 1.1, FR-21, FR-22, AD-12, AD-13, AD-15).

**Approach:** Scaffold the committed source tree by hand (no generator): FastAPI + SQLModel + Alembic against PostgreSQL in Docker, and React 19 + TypeScript + Vite with DESIGN.md tokens as CSS custom properties, a responsive shell, a shared primary button, and an installable PWA shell. Built as one PR with one commit per milestone.

## Boundaries & Constraints

**Always:**
- Component files reference only `var(--...)` for color, spacing, radius, shadow, tap size and focus ring. Font sizes in `rem`, system font stack, weights 500/700.
- Mobile-first breakpoints written as `37.5em` (600px) and `64em` (1024px), since `var()` cannot be used in `@media`. No horizontal scroll at 320 CSS px / 400% zoom.
- 2px focus ring with 2px offset on every interactive element, never `outline: none`/`0`. Tap targets ≥44×44px. `prefers-reduced-motion: reduce` sets all durations to 0.
- `--radius-full` (pill) only in `PrimaryButton.css` and future badge/status-tag files.
- All UI copy in Norwegian; `<html lang="nb">`.
- Exact versions pinned; lockfiles `uv.lock` and `package-lock.json` committed. `postgres:17` to match Supabase.
- Tests run offline, without Docker or keys.
- Commands in README work in zsh and Git Bash.

**Never:**
- No auth, users, Homes or data models (Story 1.2+). No seed command (Story 1.6). No Web Push (Trinn 2). No offline caching in the service worker.
- No webfont, no dark mode, no CSS framework, no component library, no PWA plugin.
- No `fetch` in components; `src/api/` holds only `.gitkeep` until Story 1.2. No frontend env variables yet.
- No secrets or `.env` committed.

**Decisions (team, 2026-10-25):**
- Python dependencies are managed with `uv` (`pyproject.toml` + committed `uv.lock`, Python 3.12 fetched by uv). No `requirements.txt` fallback.
- The app keeps the placeholder name "Husly" in the header, `<title>` and `manifest.json` for now.
- The shell is minimal: header with app name and a placeholder start page with a short Norwegian welcome text and a `PrimaryButton` demo. No tab bar until there are pages to navigate to.
- Spec kept as one story above the 1600-token guideline; mitigated by one commit per milestone and checking off tasks.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Health check | `GET /api/health` | 200 `{"status": "ok"}` | N/A |
| Button in-flight | `pending` | Text "Sender…", `aria-busy="true"`, `aria-disabled="true"`, click ignored, stays focusable | N/A |
| Button disabled with reason | `disabled` + `disabledReason` | `aria-disabled="true"` (not native `disabled`), `ink-secondary` background, click ignored, `aria-describedby` → visible reason | N/A |
| Install prompt, first visit on mobile | no `localStorage` flag | prompt shown, flag written when shown | N/A |
| Install prompt, seen before | flag set | not shown | `localStorage` throws → show once this session, never crash |
| Install prompt, installed / desktop | `display-mode: standalone` or not mobile | not shown | N/A |

</frozen-after-approval>

## Code Map

- `README.md` -- exists (group, members, doc links). Extend; keep existing sections.
- `.gitignore` -- covers `node_modules`, `.venv`, `dist`, `.env*` (keeps `.env.example`). No change.
- `.gitattributes` -- LF everywhere; no change.
- `_bmad-output/planning-artifacts/ux-designs/ux-prosjektoppgave-ibe160-2026-09-29/DESIGN.md` -- token source (frontmatter): colors, typography, rounded, spacing, `focus-outline`, card shadow.
- `.../EXPERIENCE.md:14` -- says "React (JavaScript)"; correct to TypeScript per architecture Stack, with a dated note.
- `_bmad-output/planning-artifacts/architecture/.../ARCHITECTURE-SPINE.md` -- source tree, Stack, AD-12/13/15. Do not change.
- `scripts/ki-logg/` -- do not touch.

## Tasks & Acceptance

**Execution:**
- [x] `backend/pyproject.toml`, `backend/.python-version`, `backend/uv.lock` -- FastAPI (exact patch), SQLModel, Alembic, `psycopg[binary]`; dev: pytest, httpx, ruff; pytest `pythonpath = ["."]` -- AC 4, 5
- [x] `backend/app/{__init__,main,config}.py`, `backend/app/routes/{__init__,health}.py`, `backend/app/{domain,permissions,models}/__init__.py` -- app with `/api/health`; `config.py` reads `DATABASE_URL` (default `postgresql+psycopg://husly:husly@localhost:5433/husly`) and `CORS_ORIGINS` (comma-separated, default `http://localhost:5173,http://localhost:4173`), no wildcard -- AC 4
- [x] `backend/alembic.ini`, `backend/alembic/{env.py,script.py.mako}`, `backend/alembic/versions/.gitkeep` -- uses `DATABASE_URL` and `SQLModel.metadata`, no migrations yet -- AC 4
- [x] `backend/tests/test_health.py` -- 200 + body via `TestClient`; CORS allows a configured origin and rejects another -- AC 5
- [x] `docker-compose.yml` -- `postgres:17`, host port 5433, named volume, `pg_isready` healthcheck -- AC 4
- [x] `frontend/package.json` (`engines.node >=22`, scripts `dev`, `build`, `preview`, `test: vitest`, `lint`), `package-lock.json`, `.nvmrc` (24), `vite.config.ts`, `tsconfig*.json`, `eslint.config.js`, `index.html` (`lang="nb"`, viewport meta, manifest link), `src/main.tsx`, `src/App.tsx`, `src/test-setup.ts` (jest-dom, `matchMedia` mock), `src/{routes,api}/.gitkeep` -- AC 4, 5
- [x] `frontend/src/styles/tokens.css` -- every DESIGN.md token plus `--tap-min: 2.75rem`, `--focus-width`, `--focus-offset`, `--shadow-card` -- AD-13
- [x] `frontend/src/styles/global.css` -- 16px root, font stack, `:focus-visible` ring, reduced-motion override, `box-sizing`, `overflow-wrap`, no horizontal overflow -- AC 1, 7–10
- [x] `frontend/src/components/AppShell.tsx` + `.css` -- header + main, mobile-first `@media` at `37.5em`/`64em` -- AC 1, 2
- [x] `frontend/src/components/PrimaryButton.tsx` + `.css` + `.test.tsx` -- states per I/O matrix; pressed = 8% darker overlay -- AC 11
- [x] `frontend/public/manifest.json`, `frontend/public/icons/icon-{192,512}.png` (simple generated mark in `primary`), `src/service-worker.ts` + `tsconfig.sw.json` (`lib: webworker`), `src/registerServiceWorker.ts` -- SW built as its own Rollup input emitted as root `service-worker.js`; registered only when `import.meta.env.PROD` -- AC 3
- [x] `frontend/src/components/InstallPrompt.tsx` + `.test.tsx` -- Android/Chrome: `beforeinstallprompt`; iOS Safari: Norwegian instruction (Del → Legg til på Hjem-skjerm); flag stored on show; hidden when standalone/desktop -- AC 3
- [x] `frontend/src/styles/tokens.test.ts` -- scans `src/components/**/*.{css,tsx}`; fails on hex, `rgb(`/`hsl(`, named colors in color properties, literal px/rem/em in padding/margin/gap/radius/shadow/size, `outline: none|0`, and `--radius-full` outside allowed files; `@media` lines and `1px` borders exempt -- AC 6, 7, 9
- [x] `.env.example` -- `DATABASE_URL`, `CORS_ORIGINS` with comments -- AC 12
- [x] `README.md` -- prerequisites (Docker Desktop running, WSL2 on Windows; uv via official installer for macOS and `winget install astral-sh.uv` / PowerShell for Windows; Node 22+), `docker compose up -d --wait`, `uv sync`, `uv run alembic upgrade head`, start backend (`uv run fastapi dev`) and frontend (`npm ci`, `npm run dev`), PWA check via `npm run build && npm run preview`, tests, lint, ports, folder overview -- AC 12, FR-22
- [x] `EXPERIENCE.md` -- JavaScript → TypeScript, dated revision note -- plan consistency

**Acceptance Criteria:**
- Given a clean clone on macOS or Windows (Git Bash), when the README steps are followed, then the DB is healthy, `alembic upgrade head` exits 0, `/api/health` answers 200 and the app loads at `http://localhost:5173`.
- Given the backend and frontend test commands, when run without Docker, network or keys, then both pass.
- Given the app at 320px, 768px and 1280px width and at 400% zoom on a 1280px window, when inspected, then layout follows the breakpoints with no horizontal scroll.
- Given `npm run build && npm run preview` at `http://localhost:4173`, when DevTools → Application is opened, then the manifest is valid and `/service-worker.js` is activated with scope `/`.

## Implementation Notes

- **Versions (2026-10-25):** FastAPI pinned to `0.162.0` (team decision; first pinned to `0.149.0`, the newest 0.14x the architecture Stack names). Installed as `fastapi[standard]`, because `fastapi dev` needs `fastapi-cli`. TypeScript pinned to `6.0.3`, not 7.0: `typescript-eslint` 8.72 requires `typescript <6.1`. Node engines `^22.12.0 || ^24.0.0 || >=26.0.0` (Vitest's range). React/React DOM `19.3.1`, Vite `8.3.5`, Vitest `5.0.5`, PostgreSQL `postgres:17`.
- **Token test scope:** it scans every `src/**/*.{css,tsx}` outside `src/styles/` and skips `*.test.tsx`, so `App.tsx`/`App.css` are covered as well as `src/components/`. It also checks that `tokens.css` matches DESIGN.md's frontmatter values (colors, spacing, rounded, typography), so a copy error fails locally.
- **Extra tokens** beyond the listed ones: `--color-on-primary` (button text, from `components.button-primary`), `--overlay-pressed` (8% overlay), `--focus-color`, `--duration-fast`, `--layout-max-width`, `--font-weight-medium/bold`.
- **Extra files:** `InstallPrompt.css`, `App.css` (styles needed by those components); a skip link "Hopp til hovedinnhold" in `AppShell`.
- **Start page demo:** `PrimaryButton` is shown disabled with the reason "Innlogging kommer i neste versjon av appen.", since there is nothing to start yet.
- **`.env` loading:** the backend reads `os.environ` only. Defaults match `docker-compose.yml`, so no `.env` is needed; README shows `uv run --env-file ../.env` for overrides.
- **FastAPI bumped to `0.162.0` (team decision, 2026-10-25):** the 0.149.0 pin above read "latest 0.14x" literally; the team confirmed the intent was "latest". Architecture Stack table and memlog updated with a dated revision note.

## Spec Change Log

## Review Triage Log

| # | Finding (pre-approval spec review, 2026-10-25) | Verdict | Change |
|---|---|---|---|
| 1 | `var()` impossible in `@media`; px for tap/focus/shadow would fail token test | high | em breakpoints, new tokens, `@media` exempt |
| 2 | SW as Vite entry gets hashed name and `/assets/` scope; dev needs module SW; `tsc` needs webworker lib | high | root `service-worker.js`, own tsconfig, PROD-only registration, verify on :4173 |
| 3 | Native `disabled` removes focus, so `aria-describedby` reason is never announced | medium | `aria-disabled` + ignored click |
| 4 | Token test missed rgb/hsl, rem spacing, `outline: none`, pill restriction | medium | rules extended |
| 5 | Lockfiles, `--wait`, port clash, Windows uv install, Docker running, Node pin missing | medium | added to tasks/README |
| 6 | DB driver, `CORS_ORIGINS` format, Vite env dir unspecified | medium | psycopg, comma-separated, no frontend env yet |
| 7 | Empty folders not tracked; tests cannot import `app` | medium | `.gitkeep`, `__init__.py`, pytest `pythonpath` |
| 8 | "Once" only on dismiss; jsdom lacks `matchMedia` | low | flag on show, mock in test setup |
| 9 | 400% zoom unchecked; `lang`, viewport, icon sizes, test script unspecified | low | added |

| Layer | Finding (code review, iteration 0, 2026-10-25) | Verdict | Evidence / route |
|---|---|---|---|
| blind | Planning artifacts and KI-logg absent from review diff | false | Excluded on purpose: the workflow gives the spec only to the edge-case layer; nothing to fix in code |
| blind | `korrigeringer.md` and KI-logg README not updated | low | True, but they are written at PR time (step 05), not part of the code diff; done there |
| blind | UX `.memlog.md` has no event for the EXPERIENCE.md TS correction | low | Confirmed; one-line append → patch (orchestrator) |
| blind | Nothing committed yet | false | Commits are made per milestone in step 05 after review |
| blind | `engines.node >=22` too loose | medium | Confirmed: vitest 5.0.5 requires `^22.12.0 \|\| ^24.0.0 \|\| >=26.0.0`, vite 8 `>=22.12`; Node 22.0–22.11 or 23/25 would pass README check and fail → patch |
| blind | `postgres:17` is a floating tag | false | Architecture Stack pins the PostgreSQL *major* to match Supabase; spec says `postgres:17` |
| blind+edge | Token sync test: shadow only `toBeDefined`, focus vs hardcoded `2px`, font-family and badge letter-spacing unchecked | low | Confirmed at tokens.test.ts sync block; direct extra assertions → patch |
| blind+verif | `manifest.json`/`index.html` theme colors duplicate tokens unchecked | medium | Confirmed: componentFiles() scans only src css/tsx; drift on palette change → patch |
| blind+edge | Token checker misses negative lengths, numeric TSX style values, `font`/`letter-spacing`/`flex-basis` | medium | Confirmed: `LITERAL_LENGTH` prefix class `[^\w.-]` excludes `-`, so `margin: -12px` passes, contradicting the spec claim → patch |
| blind+verif | `get_settings()` env reading/defaults untested | medium | Confirmed: tests build `Settings` directly; port drift would pass → patch |
| blind | No allowed-origin preflight test | low | Confirmed; cookie auth in 1.2 depends on it; one test → patch |
| blind+edge | iOS prompt says "i Safari" to Chrome/Firefox iOS and in-app webviews | medium | Confirmed: detectPlatform() matches any iPhone UA; spec scopes instructions to iOS Safari; flag is burned → patch (show only on iOS Safari) |
| blind+edge | `installEvent.prompt()` rejection / double tap unhandled; `appinstalled` not handled | medium | Confirmed: install() awaits without catch and keeps the event, second `prompt()` throws InvalidStateError → patch |
| blind+verif | InstallPrompt branches untested: iPadOS, `navigator.standalone`, Android dismiss, Android without event | medium | Confirmed by grep of test file → patch |
| blind | SW emitted as ES chunk but registered as classic script | low | True only once the SW imports shared code (Trinn 2); today no imports. Direct comment in vite.config.ts → patch |
| blind | Maskable icon reuses the "any" icon | low | Mark likely cropped by Android launchers; direct deletion of the maskable entry → patch |
| blind+verif | AppShell skip link/landmarks untested | medium | Confirmed: no test renders AppShell → patch |
| blind | Responsive/zoom AC verified only manually, not recorded | low | Recorded in PR description (step 05); no code change |
| blind | README: no troubleshooting for ports/Docker, `test:run` script | low | Rejected: unlikely to hit on first run, `npm test -- --run` works in Git Bash |
| edge | Empty `CORS_ORIGINS` gives empty allow-list silently | low | Confirmed; one guard in parse_origins → patch |
| edge | Trailing slash in origin never matches | low | Confirmed; `rstrip('/')` → patch |
| edge+verif | `%` in `DATABASE_URL` breaks ConfigParser interpolation in env.py | low | Confirmed: `set_main_option` interpolates; escape `%%` → patch |
| edge | Invalid `CORS_ORIGINS` aborts migrations | low | Confirmed: env.py calls get_settings(); read only the DB URL there → patch |
| edge | Bad env breaks test collection on import of app.main | false | A loud failure on invalid config is correct behavior |
| edge | `beforeinstallprompt` may fire before the effect attaches | maybe-false | Would need Chrome timing traces; event normally fires after load, after mount. Rejected as at most low |
| edge | `registerServiceWorker` called after load never registers | false | Called from main.tsx module execution, which runs before the window load event |
| edge | Multi-line declarations escape length rules | low | Rejected: hex rule is line-based and still fires; fix needs a parser |
| edge | Hex-letter id selectors (`#add`) false positive | low | Rejected: a false positive fails loudly; components use classes |
| edge | `frontmatterGroup` empty → zero sync tests | low | Verified it yields cases today; one non-empty assertion → patch |
| edge | Claim: scan scope wider than spec (all of src) | false | Stricter than spec and recorded in Implementation Notes |
| verif | `registerServiceWorker` has no unit test | medium | Confirmed: no test imports it → patch; build-output check deferred |

## Design Notes

The token test is the one meaningful logic test in this story: it turns AD-13 from a convention into a check that fails locally when someone hardcodes `#6E62CC` or `12px` in a component. `tokens.css` and `global.css` are exempt because they define the tokens.

The service worker only installs and claims clients (no caching), so it cannot serve stale code. It is not registered in `npm run dev`, which avoids the dev-server module-worker and scope problems.

## Verification

**Commands:**
- `docker compose up -d --wait` -- expected: postgres healthy
- `cd backend && uv sync && uv run alembic upgrade head` -- expected: exits 0
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- expected: all pass
- `cd frontend && npm ci && npm test -- --run && npm run lint && npm run build` -- expected: all pass

**Manual checks (if no CLI):**
- DevTools responsive mode at 320/768/1280px and 400% zoom; Tab through shell (focus ring visible); emulate reduced motion; `npm run preview` → Application tab shows manifest and active service worker.
