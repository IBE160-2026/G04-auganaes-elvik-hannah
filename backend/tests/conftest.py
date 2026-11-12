"""Shared fixtures (Story 1.2): an in-memory SQLite database, so tests need no Docker.

Story 1.6 (FR-22): an autouse guard makes every Python-level connect to a non-loopback
address fail, so the suite provably runs offline. libpq and DNS lookups are not covered.
"""

import ipaddress
import socket
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  (registers the tables on the metadata)
from app.config import Settings
from app.db import get_session
from app.main import create_app

TEST_SECRET = "test-secret-som-er-minst-32-byte-lang"

_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex


def _require_loopback(sock: socket.socket, address: object) -> None:
    # Non-INET families (AF_UNIX) and loopback stay allowed: asyncio's socketpair on Windows
    # connects to 127.0.0.1. IPv4 addresses are 2-tuples, IPv6 4-tuples.
    if sock.family not in (socket.AF_INET, socket.AF_INET6):
        return
    host = address[0] if isinstance(address, tuple) else address
    if host == "localhost":
        return
    try:
        if ipaddress.ip_address(host).is_loopback:
            return
    except ValueError:
        pass
    raise RuntimeError(f"Testene skal kjøre uten nett, men prøvde å koble til {address!r}")


def _guarded_connect(self: socket.socket, address: object) -> None:
    _require_loopback(self, address)
    return _real_connect(self, address)


def _guarded_connect_ex(self: socket.socket, address: object) -> int:
    _require_loopback(self, address)
    return _real_connect_ex(self, address)


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", _guarded_connect_ex)


@pytest.fixture(autouse=True)
def mock_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    """Story 5.1 (AD-15): the tests always use the mock AI provider, whatever the shell has set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)


@pytest.fixture
def engine() -> Iterator[Engine]:
    # One shared connection, so every session sees the same in-memory database.
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )

    # SQLite leaves foreign keys off unless asked (Story 1.3), unlike Postgres.
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection: object, _record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def make_client(engine: Engine, *, cookie_secure: bool = False) -> TestClient:
    app = create_app(
        Settings(
            database_url="postgresql+psycopg://unused",
            jwt_secret=TEST_SECRET,
            cookie_secure=cookie_secure,
        )
    )

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    # https, so the client also sends back cookies marked Secure.
    return TestClient(app, base_url="https://testserver")


@pytest.fixture
def client(engine: Engine) -> TestClient:
    return make_client(engine)
