"""A real Postgres for the concurrency tests (Epic 1 retro P3, deferred-work.md).

SQLite ignores `FOR UPDATE`, so the row locks in the domain are not exercised by the normal suite.
These tests run only when `HUSLY_POSTGRES_TEST_URL` points at a Postgres server (the CI job
«Migreringer (Postgres 18)» sets it; locally they are skipped). Each test module gets its own
database, created and migrated here, so nothing of the seed or of another test is in the way.
"""

import os
import subprocess
import sys
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine, make_url
from sqlmodel import Session

URL_VARIABLE = "HUSLY_POSTGRES_TEST_URL"
ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get(URL_VARIABLE):
        return
    skip = pytest.mark.skip(reason=f"{URL_VARIABLE} is not set (a Postgres server is needed)")
    for item in items:
        if "tests/postgres" in str(item.path).replace("\\", "/"):
            item.add_marker(skip)


def _admin_url() -> URL:
    return make_url(os.environ[URL_VARIABLE])


def start_migration(database_url: URL) -> subprocess.Popen[str]:
    """`alembic upgrade head` against `database_url` in its own process, the way the deploy runs it.

    A process of its own, so two of them can run at once (the advisory-lock test) without sharing
    the environment of the test run.
    """
    env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL_UNPOOLED"}
    env["DATABASE_URL"] = database_url.render_as_string(hide_password=False)
    return subprocess.Popen(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ALEMBIC_INI.parent,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def migrate(database_url: URL) -> None:
    process = start_migration(database_url)
    output, _ = process.communicate(timeout=120)
    assert process.returncode == 0, output


def create_database() -> URL:
    """A new, empty database on the server, named for this run."""
    name = f"husly_conc_{uuid.uuid4().hex[:10]}"
    admin = create_engine(_admin_url(), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()
    return _admin_url().set(database=name)


def drop_database(url: URL) -> None:
    admin = create_engine(_admin_url(), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture(scope="module")
def pg_engine() -> Iterator[Engine]:
    url = create_database()
    migrate(url)
    engine = create_engine(url, pool_size=20, max_overflow=20)
    try:
        yield engine
    finally:
        engine.dispose()
        drop_database(url)


@pytest.fixture
def make_session(pg_engine: Engine) -> Callable[[], Session]:
    def factory() -> Session:
        return Session(pg_engine, expire_on_commit=True)

    return factory
