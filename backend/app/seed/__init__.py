"""The seed command (Story 1.6, FR-22, AD-15): migrations, then example data.

Run from backend/: `uv run python -m app.seed`. It writes only to a local database, so users
with publicly known passwords never reach the hosted demo or a Neon branch. Idempotent: it
never deletes or overwrites rows. Story 1.3 added the example Home; Story 2.1 adds the Homes'
Tasks as a third step.

Output uses print(), because Alembic's fileConfig replaces the logging setup.
"""

import sys
from collections.abc import Callable
from pathlib import Path

from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError, OperationalError
from sqlmodel import Session

from alembic import command
from app.config import _env, get_database_url, get_migration_url
from app.db import get_engine
from app.seed.homes import seed_homes
from app.seed.tasks import seed_tasks
from app.seed.users import seed_users

Step = Callable[[Session], None]

# In order: a later step may look up rows from an earlier one by natural key (e.g. email).
STEPS: tuple[Step, ...] = (seed_users, seed_homes, seed_tasks)

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"

DB_DOWN_HINT = (
    "Får ikke kontakt med databasen. Start den fra rotmappen med `docker compose up -d --wait`, "
    "og kjør seed-kommandoen på nytt."
)


def _non_local_host(url: str) -> str | None:
    """The host if the URL points anywhere but this machine, otherwise None."""
    try:
        parsed = make_url(url)
    except (ArgumentError, ValueError):
        return "<ugyldig URL>"
    # libpq also accepts the host as a query parameter, which would override the one above.
    for key in ("host", "hostaddr"):
        if key in parsed.query:
            return f"{key}={parsed.query[key]}"
    host = (parsed.host or "").lower()
    return None if host in LOCAL_HOSTS else (host or "<ingen vert>")


def local_only_refusal() -> str | None:
    """Why the seed must not run here, or None when the database is local."""
    if _env("VERCEL"):
        return "Seed-kommandoen kjører bare lokalt, ikke på Vercel. Ingenting er skrevet."
    for name, get_url in (
        ("DATABASE_URL", get_database_url),
        ("DATABASE_URL_UNPOOLED", get_migration_url),
    ):
        host = _non_local_host(get_url())
        if host is not None:
            return (
                f"Seed-kommandoen skriver bare til en lokal database, men {name} peker til "
                f"{host}. Ingenting er skrevet."
            )
    return None


def _upgrade() -> None:
    command.upgrade(Config(str(ALEMBIC_INI)), "head")


def _session() -> Session:
    return Session(get_engine(get_database_url()))


def run(
    *,
    upgrade: Callable[[], None] = _upgrade,
    session_factory: Callable[[], Session] = _session,
) -> int:
    """Apply migrations, then every step in STEPS in one session. Returns the exit code.

    0: done. 1: the database could not be reached or refused the connection.
    2: refused before connecting (Vercel or a non-local database), nothing written.
    """
    refusal = local_only_refusal()
    if refusal is not None:
        print(refusal, file=sys.stderr)
        return 2
    try:
        upgrade()
        with session_factory() as session:
            for step in STEPS:
                step(session)
    except OperationalError as exc:
        print(DB_DOWN_HINT, file=sys.stderr)
        # The cause too, so a wrong password or a missing database is not hidden by the hint.
        print(f"Feilen var: {exc.orig or exc}", file=sys.stderr)
        return 1
    print("Seed-data er klare.")
    return 0
