"""Story 1.7: /api/health/db reports only up or down, with no database needed in tests."""

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.config import Settings
from app.db import get_engine
from app.main import create_app
from app.routes.health import app_engine

SECRET_URL = "postgresql+psycopg://u:hemmelig@db.test/husly"


class FakeConnection:
    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, statement: object) -> None:
        self.statement = str(statement)


class FakeEngine:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.connection = FakeConnection()

    def connect(self) -> FakeConnection:
        if self.fail:
            raise OperationalError("SELECT 1", {}, Exception(f"could not reach {SECRET_URL}"))
        return self.connection


@pytest.fixture(autouse=True)
def clear_engine_cache() -> Iterator[None]:
    get_engine.cache_clear()
    yield
    get_engine.cache_clear()


def client_with(engine: FakeEngine) -> TestClient:
    app = create_app(Settings(database_url=SECRET_URL))
    app.dependency_overrides[app_engine] = lambda: engine
    return TestClient(app)


def test_db_up_returns_ok() -> None:
    engine = FakeEngine()

    response = client_with(engine).get("/api/health/db")

    assert response.status_code == 200
    assert response.json() == {"database": "ok"}
    assert engine.connection.statement == "SELECT 1"


def test_db_down_returns_503_with_fixed_text(caplog: pytest.LogCaptureFixture) -> None:
    response = client_with(FakeEngine(fail=True)).get("/api/health/db")

    assert response.status_code == 503
    assert response.json() == {"detail": "Databasen svarer ikke"}
    assert "hemmelig" not in response.text
    assert "Databasesjekk feilet" in caplog.text


def test_engine_uses_pre_ping_and_pooler_safe_connect_args(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr("app.db.create_engine", lambda url, **kwargs: calls.append(kwargs))

    get_engine(SECRET_URL)

    assert calls[0]["pool_pre_ping"] is True
    assert calls[0]["connect_args"] == {"prepare_threshold": None, "connect_timeout": 10}


def test_app_engine_is_built_from_settings() -> None:
    app = create_app(Settings(database_url=SECRET_URL))

    engine = app_engine(SimpleNamespace(app=app))  # type: ignore[arg-type]

    assert engine.url.render_as_string(hide_password=False) == SECRET_URL
    assert engine is get_engine(SECRET_URL)
