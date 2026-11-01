"""Story 1.1/1.7 (FR-22, AD-15): database URL from the environment, normalised in one place."""

import pytest

from app.config import (
    DEFAULT_DATABASE_URL,
    get_database_url,
    get_migration_url,
    get_settings,
    normalize_database_url,
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("DATABASE_URL", "DATABASE_URL_UNPOOLED", "VERCEL"):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "postgresql://u:p@h/db?sslmode=require&channel_binding=require",
            "postgresql+psycopg://u:p@h/db?sslmode=require&channel_binding=require",
        ),
        ("postgres://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("postgresql://u:p%40ss@h/db", "postgresql+psycopg://u:p%40ss@h/db"),
        ("postgresql+asyncpg://u:p@h/db", "postgresql+asyncpg://u:p@h/db"),
        ("mysql://u:p@h/db", "mysql://u:p@h/db"),
    ],
)
def test_normalize_database_url(raw: str, expected: str) -> None:
    assert normalize_database_url(raw) == expected


def test_reads_and_normalises_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@db.test:5432/x")

    assert get_settings().database_url == "postgresql+psycopg://u:p@db.test:5432/x"


@pytest.mark.parametrize("value", [None, ""])
def test_local_default_matches_docker_compose(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is not None:
        monkeypatch.setenv("DATABASE_URL", value)

    assert get_database_url() == DEFAULT_DATABASE_URL
    assert "@localhost:5433/husly" in DEFAULT_DATABASE_URL


@pytest.mark.parametrize("value", [None, ""])
def test_vercel_without_database_url_is_an_error(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    monkeypatch.setenv("VERCEL", "1")
    if value is not None:
        monkeypatch.setenv("DATABASE_URL", value)

    with pytest.raises(RuntimeError, match="Neon"):
        get_settings()


def test_vercel_with_database_url_uses_it(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@neon.test/db?sslmode=require")

    assert get_database_url() == "postgresql+psycopg://u:p@neon.test/db?sslmode=require"


def test_migration_url_prefers_unpooled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@pooler.test/db")
    monkeypatch.setenv("DATABASE_URL_UNPOOLED", "postgresql://u:p@direct.test/db")

    assert get_migration_url() == "postgresql+psycopg://u:p@direct.test/db"


@pytest.mark.parametrize("unpooled", [None, ""])
def test_migration_url_falls_back_to_database_url(
    monkeypatch: pytest.MonkeyPatch, unpooled: str | None
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@pooler.test/db")
    if unpooled is not None:
        monkeypatch.setenv("DATABASE_URL_UNPOOLED", unpooled)

    assert get_migration_url() == "postgresql+psycopg://u:p@pooler.test/db"


def test_migration_url_on_vercel_without_any_url_is_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VERCEL", "1")

    with pytest.raises(RuntimeError):
        get_migration_url()
