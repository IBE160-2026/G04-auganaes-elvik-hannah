"""Shared fixtures (Story 1.2): an in-memory SQLite database, so tests need no Docker."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  (registers the tables on the metadata)
from app.config import Settings
from app.db import get_session
from app.main import create_app

TEST_SECRET = "test-secret-som-er-minst-32-byte-lang"


@pytest.fixture
def engine() -> Iterator[Engine]:
    # One shared connection, so every session sees the same in-memory database.
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
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
