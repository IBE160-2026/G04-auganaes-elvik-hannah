"""Story 1.1 (FR-22, AD-15): settings come from the environment with local defaults."""

import pytest

from app.config import get_database_url, get_settings, parse_origins


def test_reads_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@db.test:5432/x")
    monkeypatch.setenv("CORS_ORIGINS", "http://app.test")

    settings = get_settings()

    assert settings.database_url == "postgresql+psycopg://u:p@db.test:5432/x"
    assert settings.cors_origins == ["http://app.test"]


def test_defaults_match_docker_compose_and_vite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    settings = get_settings()

    assert settings.database_url == get_database_url()
    assert "@localhost:5433/" in settings.database_url
    assert settings.cors_origins == ["http://localhost:5173", "http://localhost:4173"]


def test_parse_origins_strips_trailing_slash() -> None:
    assert parse_origins("http://localhost:5173/, http://a.test") == [
        "http://localhost:5173",
        "http://a.test",
    ]


@pytest.mark.parametrize("raw", ["", " , ,", "/"])
def test_parse_origins_rejects_empty_list(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_origins(raw)
