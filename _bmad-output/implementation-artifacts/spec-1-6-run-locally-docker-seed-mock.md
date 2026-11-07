---
title: 'Story 1.6: Run Locally with Docker, Seed Data and Mock Modes'
type: 'feature'
created: '2026-11-01'
status: 'done'
baseline_commit: '2ebb0424f376e1910aeca9ba555f1b4a62423140'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A reviewer can start the database and the app today, but has to run migrations by hand and register a user before seeing anything. There is no seed data, and no check that `.env.example` and the "offline, no keys" promise stay true (Story 1.6, issue #12, FR-22, AD-15).

**Approach:** Add one command, `uv run python -m app.seed`, run from `backend/`. It applies the Alembic migrations, then runs an ordered list of seed steps. The first step creates example users through `accounts.register`, and Stories 1.3 and 2.1 add their own steps to the same list. Tests keep `.env.example`, `.gitignore` and offline testing honest. The README's local-run section is rewritten around the new command.

**Decisions (team, 2026-11-01):**
- Example users (password `husly-demo` for both): **Mari Nordmann** `mari@example.com` and **Jonas Berg** `jonas@example.com`. Stories 1.3–1.5 add a Landlord and a Tenant by extending the same seed step.
- **No mock indicator in the UI yet.** Trinn 1 so far calls no external service (AI arrives with 5.1; push and Blob in Trinn 2), so there is nothing to mock or show. The README says so, and says that 5.1 marks AI answers as «demo-modus». The deviation from the AC is recorded as a note under Story 1.6 in `epics.md` and in the PR. An indicator that would show an empty list is not built.
- **The seed writes only to a local database.** It refuses when `VERCEL` is set, or when the host of `get_database_url()` or `get_migration_url()` is not `localhost`, `127.0.0.1` or `::1`. It refuses before connecting: exit ≠ 0, nothing written. Users with publicly known passwords therefore never reach g04husly.vercel.app or a Neon branch, also not from a laptop with a copied Neon URL in `.env` (spec review finding 1). On the demo a reviewer registers their own account.

## Boundaries & Constraints

**Always:**
- Users are created only through `domain/accounts.register`, so emails are normalised and hashed exactly like real registrations. `EmailTaken` means the user is already there, and the step skips it.
- The seed is idempotent. Running it twice gives the same rows and exit 0, and it never deletes or overwrites data.
- Migrations run in-process through `alembic.command.upgrade`, with `Config(Path(__file__).resolve().parents[2] / "alembic.ini")`, so `env.py`'s migration URL and advisory lock are reused unchanged. Alembic's `fileConfig` replaces logging, so seed output uses `print()`, never `logging`. Alembic's own INFO lines stay in the output (accepted).
- `sqlalchemy.exc.OperationalError` is caught around both the upgrade and the steps. It ends with a Norwegian hint to run `docker compose up -d --wait`, and exit 1.
- Steps are plain functions `(Session) -> None`, listed in order in one `STEPS` tuple. A later step that needs earlier rows (e.g. 1.3 needs Mari) looks them up by natural key, i.e. the normalised email.
- The seed prints one Norwegian line per created or existing row.
- Tests run with no keys, and Python-level non-loopback socket connects fail (the guard is described in Tasks). Postgres is never reached in tests anyway: the fixtures use SQLite and a dummy URL.
- Commands work in zsh and Git Bash.

**Never:** a second seed entry point or shell script; raw SQL inserts of users; resetting or truncating tables; a Docker image for backend/frontend; env vars in `.env.example` that the app does not read yet (5.1 adds `GEMINI_API_KEY`); committed secrets or `.env`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error handling |
|---|---|---|---|
| Fresh DB | empty Postgres | migrations applied, 2 users created, exit 0 | — |
| Rerun | seed already run | "finnes allerede" per user, no new rows, exit 0 | — |
| Partial | one example user already registered via `register` with other input casing | that user skipped, the other created | `EmailTaken` → skip |
| DB down | Docker not started | exit 1 with the hint | `OperationalError` caught |
| On Vercel | `VERCEL` set | exit ≠ 0, Norwegian message | refused before upgrade/connect |
| Remote DB | `DATABASE_URL` or `DATABASE_URL_UNPOOLED` with a non-local host | exit ≠ 0, message names the host | refused before upgrade/connect |

</frozen-after-approval>

## Code Map

- `backend/app/domain/accounts.py` -- `register(session, *, email, name, password)`, `EmailTaken`, `normalize_email`. Reuse as is. `register` rolls back on a duplicate, so the shared session stays usable.
- `backend/app/config.py` -- `get_database_url()`, `get_migration_url()`, `_env()`. Env names read: `DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `JWT_SECRET`, `AUTH_COOKIE_SECURE`, `VERCEL` (set by the platform).
- `backend/app/db.py` -- `get_engine(url)` has psycopg-only `connect_args`. `run()` takes an injectable session factory and `upgrade` callable, so tests never call `get_engine` with SQLite.
- `backend/alembic/env.py` -- `fileConfig` (line 21–22), `get_migration_url()`, advisory lock. Do not touch it.
- `backend/tests/conftest.py` -- SQLite `engine`/`session` fixtures; the socket guard goes here (autouse).
- `.env.example` -- the four keys exist; add one comment that `VERCEL` is set by the platform.
- `.github/workflows/ci.yml` -- migrations job (line 73): `alembic upgrade head` becomes the seed. The `alembic_version` check stays right after it.
- `README.md` -- "2. Backend" (line 50–58), "4. Første innlogging" (line 72–80), folder tree.
- `_bmad-output/implementation-artifacts/deferred-work.md` -- the lowercase-email entry (last one).
- `_bmad-output/planning-artifacts/epics.md` -- Story 1.6 (line 458).
- Not to touch: `alembic/env.py`, frontend code, `vercel.json`.

## Tasks & Acceptance

**Execution:**
- [x] `backend/app/seed/__init__.py` -- `STEPS` and `run(*, upgrade=..., session_factory=...) -> int`: the local-only guard, then upgrade, then the steps in one session, catching `OperationalError`. `__main__.py` holds only `raise SystemExit(run())`.
- [x] `backend/app/seed/users.py` -- `EXAMPLE_USERS` (emails already lowercase) + `seed_users(session)`.
- [x] `backend/tests/test_seed.py` -- every matrix row. Steps run on the SQLite session; `run()` gets fakes. DB down: the fake `upgrade` raises `OperationalError` → exit 1 and the hint. Vercel and remote: neither fake is called. Also test `STEPS` order and the user count after two runs.
- [x] `backend/tests/conftest.py` -- autouse guard patching `socket.socket.connect` and `connect_ex`. It allows non-INET families, the host `"localhost"`, and any `ipaddress.ip_address(host).is_loopback` (2- and 4-tuples); everything else raises. It is tested so that `("192.0.2.1", 80)` fails and `socket.socketpair()` works (needed by asyncio on Windows).
- [x] `backend/tests/test_env_example.py` -- use `ast` to collect the `_env(...)` arguments in `app/`; a non-literal argument fails. Each must be an uncommented `^NAME=` key in `.env.example` (path via `Path(__file__).resolve().parents[2]`) or be in `PLATFORM_SET = {"VERCEL"}`. Reverse: every key is read. Also: `git check-ignore -q .env` succeeds (skipped if git is missing).
- [x] `.env.example` -- `VERCEL` comment.
- [x] `.github/workflows/ci.yml` -- seed, `alembic_version` check, seed again, then assert `count(*) FROM users` = 2; then the existing downgrade/upgrade and `alembic check`.
- [x] `README.md` -- step 2 runs the seed (from `backend/`); a table of the example users replaces line 80. Registration stays as the alternative. Add a "Mock-modus og ekte nøkler" section (nothing mocked yet; 5.1 shows «demo-modus»; real keys go in `.env` with `--env-file`; the seed only writes to a local DB). Add `seed/` to the tree.
- [x] `deferred-work.md` -- outcome: the seed uses `register`. Raw-SQL writes stay open until the DB enforces lowercase.
- [x] `_bmad-output/planning-artifacts/epics.md` -- a dated note under Story 1.6: the UI mock indicator comes with Story 5.1 (team decision 2026-11-01). The ACs are unchanged.

**Acceptance Criteria:**
- Given a clean clone with Docker running and no `.env`, when the README is followed on macOS, then a reviewer logs in as `mari@example.com` / `husly-demo`. Steffen repeats this in Git Bash on Windows before the merge.
- Given CI, when the PR runs, then the seed runs twice against Postgres 18 with 2 users, and pytest passes on Ubuntu and Windows.

## Implementation Notes

Implemented 2026-11-01 (bmad-build, by a subagent from this spec; diff checked against the spec by the orchestrator).

- **Guard, beyond the spec:** it also refuses `?host=`/`?hostaddr=` in the URL (libpq would use those instead of the URL's host), and URLs that cannot be parsed or have no host. Refusal exits 2, a DB that is down exits 1.
- **`.gitignore` test** skips when `.git` is missing (zip download) as well as when git is missing.
- **Verified locally** against Docker Postgres 18 (existing volume kept): seed twice, exit 0, second run "finnes allerede"; `authenticate` works with `husly-demo` for both users, also as `Jonas@Example.com`; `VERCEL=1` and a Neon-host `DATABASE_URL` → exit 2 naming the host; DB stopped → exit 1 with the hint. The CI count snippet ran locally (4 users there, because Eirik's own users are in that volume; CI starts empty).
- `uv run pytest`: 125 passed, none skipped; ruff clean.
- **Not verified here:** browser login on `localhost:5173`, Steffen's Git Bash run, and CI on GitHub (the Windows socket guard and the Postgres seed job).

## Spec Change Log

## Review Triage Log

Spec review 2026-11-01 (one adversarial reviewer, checked against code; all 15 accepted and applied):

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | The Vercel guard misses a laptop `.env` with a Neon URL | high | local-host guard (Decisions) + matrix row |
| 2 | `run()` untestable on SQLite (`get_engine` connect_args) | high | injectable `upgrade`/session factory |
| 3 | Which `OperationalError`, where | medium | `sqlalchemy.exc`, around upgrade and steps |
| 4 | `fileConfig` silences loggers, Alembic INFO lines mixed in | medium | `print()`; INFO lines accepted, `env.py` untouched |
| 5 | Socket guard vs Windows `socketpair`, IPv6, AF_UNIX, `"localhost"` | medium | guard specified exactly + tests |
| 6 | Guard cannot see libpq/DNS | medium | wording narrowed to Python-level |
| 7 | `.env.example` substring match fragile | medium | regex keys, `PLATFORM_SET`, both directions |
| 8 | "Kommer senere" block = unread keys | medium | dropped; 5.1 adds its key |
| 9 | "Exit 0 twice" doesn't prove idempotency | medium | CI count assert |
| 10 | AC "`.env` ignored" unguarded | medium | `git check-ignore` test |
| 11 | How later steps find users | low | look up by normalised email |
| 12 | "Any cwd" misleading | low | run from `backend/`; ini via `Path(__file__)` |
| 13 | Partial row casing contradicts write path | low | row reworded; deferred note |
| 14 | `run()`/`STEPS` location ambiguous | low | `__init__.py`; `__main__` one line |
| 15 | README registration flow | low | kept as alternative |

Code review 2026-11-01 (Blind Hunter, Edge Case Hunter, Verification Gap; 20 findings, verified against the code and with `make_url`/`ipaddress` in the backend venv):

| Finding | Verdict | Route / action |
|---|---|---|
| Every `OperationalError` shown as "start Docker" (wrong password, missing DB) (ECH, BH) | medium | patch: print `exc.orig` under the hint + test |
| Multi-host URL `remote:5432,localhost` → `ValueError` traceback in the guard (VG) | low | patch: catch `ValueError` too (verified it raises) |
| `hostaddr`, unparseable-URL and no-host branches untested (VG) | medium | patch: tests |
| Real DB-down path only tested with fakes (VG) | medium | patch: CI step on a closed port (manual run here: exit 1 + hint) |
| CI hardcodes `n == 2`, connection never closed (BH) | low | patch: `len(EXAMPLE_USERS)`, `with` |
| Refusal exit 2 vs DB-down 1 not pinned (BH) | low | patch: assert `== 2`, document codes |
| README "Ekte nøkler" asks for keys that do not exist (BH) | low | patch: name the three overridable keys |
| Epics note doesn't say where the indicator obligation lives (BH) | low | patch: Story 5.1's existing AC already says "the UI marks it as demo mode" (epics.md line 1035); note points to it |
| `PGHOST`/`PGHOSTADDR`/`PGSERVICE` env can redirect libpq past the URL check (ECH, BH, VG) | low | rejected: nothing in the README flow sets them, and the fix adds new guards; the guard already documents it checks the URL |
| Local Unix socket, `?host=localhost`, `127.0.0.2` refused (ECH, BH) | low | rejected: safe loud failure; the documented URL is `localhost:5433` |
| `EmailTaken` masks other `IntegrityError`s (ECH) | false | `users` has only the PK (UUIDv4), `uq_users_email` and NOT NULLs; the fixed seed data cannot violate the others |
| `::ffff:127.0.0.1` not loopback on 3.12 (ECH) | false | `ipaddress.ip_address('::ffff:127.0.0.1').is_loopback` is `True` in the backend venv |
| Other loopback hostnames (`ip6-localhost`) blocked by the guard (ECH) | low | rejected: no test connects by hostname; failing loudly is the intended behaviour |
| `os.environ`/`alembic/` reads escape the `.env.example` test (ECH, BH) | low | rejected: only `config._env` reads env today (grep); an extra check adds surface for a hypothetical |
| `.env.example` values not checked for secrets (BH) | low | rejected: all values are empty or the local Docker default, checked by hand |
| Windows / Git Bash not verified; cp1252 output (BH) | low | rejected as code finding: the AC already requires Steffen's Git Bash run before merge; the output's characters (æøå, «») all exist in cp1252 |
| `run()` closes the fixture session (BH) | false | SQLAlchemy `Session.close()` leaves the session reusable by design; tests rely on documented behaviour |
| KI-logg, korrigeringer, sprint-status missing from diff (BH) | false | added with the commit and PR (step 5), not part of the code diff |

## Design Notes

- **Migrations inside the seed command** satisfy "one command for migrations and seed", and keep a reviewer from forgetting `alembic upgrade head`. `uv run alembic upgrade head` still works on its own.
- **No DB-backed test harness** in this story: the seed logic runs on SQLite, and the real Postgres path is covered by CI. The deferred R6 check on `env.py` therefore stays deferred.

## Verification

**Commands:**
- `cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .` -- pass
- `docker compose up -d --wait && cd backend && uv run python -m app.seed && uv run python -m app.seed` -- both exit 0, second reports "finnes allerede" (keeps Eirik's local data; a clean-volume run only with his OK)
- `docker compose stop && cd backend && uv run python -m app.seed` -- exit 1 with the hint

**Manual checks:**
- Log in at `http://localhost:5173` as both example users.
