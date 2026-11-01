"""Settings read from environment variables (AD-15). See .env.example."""

import os
from dataclasses import dataclass

DEFAULT_DATABASE_URL = "postgresql+psycopg://husly:husly@localhost:5433/husly"
SQLALCHEMY_SCHEME = "postgresql+psycopg://"
# Neon and the Vercel integration hand out plain libpq URLs; SQLAlchemy needs the driver named.
LIBPQ_SCHEMES = ("postgresql://", "postgres://")


@dataclass(frozen=True)
class Settings:
    database_url: str


def normalize_database_url(url: str) -> str:
    """Give a libpq URL the psycopg driver scheme (Story 1.7).

    Only the scheme prefix is swapped. The rest is left as is, so %-encoded passwords and
    query parameters such as sslmode and channel_binding survive. Other schemes pass through.
    """
    for scheme in LIBPQ_SCHEMES:
        if url.startswith(scheme):
            return SQLALCHEMY_SCHEME + url[len(scheme) :]
    return url


def _env(name: str) -> str | None:
    """An environment variable, with an empty string counted as unset."""
    return os.environ.get(name) or None


def get_database_url() -> str:
    """The pooled URL the app uses. On Vercel a missing URL is an error, never localhost."""
    url = _env("DATABASE_URL")
    if url is None:
        if _env("VERCEL"):
            raise RuntimeError(
                "DATABASE_URL mangler på Vercel. Koble Neon-integrasjonen til prosjektet "
                "(Storage → Neon) slik at DATABASE_URL blir satt."
            )
        return DEFAULT_DATABASE_URL
    return normalize_database_url(url)


def get_migration_url() -> str:
    """The direct (unpooled) URL for Alembic when set, otherwise the app's URL."""
    unpooled = _env("DATABASE_URL_UNPOOLED")
    if unpooled is not None:
        return normalize_database_url(unpooled)
    return get_database_url()


def get_settings() -> Settings:
    return Settings(database_url=get_database_url())
