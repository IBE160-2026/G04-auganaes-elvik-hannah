"""Story 1.1/1.7/1.2 (FR-22, AD-15, AD-7): settings from the environment, checked in one place."""

import pytest

from app.config import (
    DEFAULT_DATABASE_URL,
    DEFAULT_GEMINI_MODEL,
    DEV_JWT_SECRET,
    MIN_JWT_SECRET_BYTES,
    get_cookie_secure,
    get_database_url,
    get_gemini_api_key,
    get_gemini_model,
    get_jwt_secret,
    get_migration_url,
    get_settings,
    normalize_database_url,
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "DATABASE_URL",
        "DATABASE_URL_UNPOOLED",
        "VERCEL",
        "JWT_SECRET",
        "AUTH_COOKIE_SECURE",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
    ):
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


STRONG_SECRET = "s" * MIN_JWT_SECRET_BYTES


@pytest.mark.parametrize("value", [None, ""])
def test_local_jwt_secret_falls_back_to_dev_default_with_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, value: str | None
) -> None:
    if value is not None:
        monkeypatch.setenv("JWT_SECRET", value)

    assert get_jwt_secret() == DEV_JWT_SECRET
    assert len(DEV_JWT_SECRET.encode()) >= MIN_JWT_SECRET_BYTES
    assert "JWT_SECRET" in caplog.text


def test_short_local_jwt_secret_is_used_with_a_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("JWT_SECRET", "kort")

    assert get_jwt_secret() == "kort"
    assert "kortere enn" in caplog.text


def test_jwt_secret_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", STRONG_SECRET)

    assert get_jwt_secret() == STRONG_SECRET


@pytest.mark.parametrize("value", [None, "", "s" * (MIN_JWT_SECRET_BYTES - 1)])
def test_vercel_without_strong_jwt_secret_is_an_error(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@neon.test/db")
    if value is not None:
        monkeypatch.setenv("JWT_SECRET", value)

    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        get_settings()


def test_vercel_with_strong_jwt_secret_uses_it(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@neon.test/db")
    monkeypatch.setenv("JWT_SECRET", STRONG_SECRET)

    assert get_settings().jwt_secret == STRONG_SECRET


@pytest.mark.parametrize(
    ("vercel", "flag", "expected"),
    [
        (None, None, False),
        (None, "false", False),
        (None, "true", True),
        (None, "TRUE", True),
        ("1", None, True),
        ("1", "false", True),
    ],
)
def test_cookie_secure_only_on_vercel_or_opt_in(
    monkeypatch: pytest.MonkeyPatch, vercel: str | None, flag: str | None, expected: bool
) -> None:
    if vercel is not None:
        monkeypatch.setenv("VERCEL", vercel)
    if flag is not None:
        monkeypatch.setenv("AUTH_COOKIE_SECURE", flag)

    assert get_cookie_secure() is expected


def test_gemini_key_is_unset_when_missing_or_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    assert get_gemini_api_key() is None
    monkeypatch.setenv("GEMINI_API_KEY", "")
    assert get_gemini_api_key() is None
    monkeypatch.setenv("GEMINI_API_KEY", "hemmelig")
    assert get_gemini_api_key() == "hemmelig"


def test_gemini_model_defaults_and_can_be_overridden(monkeypatch: pytest.MonkeyPatch) -> None:
    assert get_gemini_model() == DEFAULT_GEMINI_MODEL != ""
    monkeypatch.setenv("GEMINI_MODEL", "")
    assert get_gemini_model() == DEFAULT_GEMINI_MODEL
    monkeypatch.setenv("GEMINI_MODEL", "annen-modell")
    assert get_gemini_model() == "annen-modell"
