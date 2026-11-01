"""Settings read from environment variables (AD-15). See .env.example."""

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_DATABASE_URL = "postgresql+psycopg://husly:husly@localhost:5433/husly"
SQLALCHEMY_SCHEME = "postgresql+psycopg://"
# Neon and the Vercel integration hand out plain libpq URLs; SQLAlchemy needs the driver named.
LIBPQ_SCHEMES = ("postgresql://", "postgres://")

# Story 1.2: only for local running and tests. On Vercel JWT_SECRET must be set.
DEV_JWT_SECRET = "husly-lokal-utvikling-ikke-hemmelig-0123456789"
MIN_JWT_SECRET_BYTES = 32


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret: str = DEV_JWT_SECRET
    # Secure on the refresh cookie. Off locally so Safari keeps it on http://localhost.
    cookie_secure: bool = False


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


def get_jwt_secret() -> str:
    """The JWT signing key (Story 1.2, AD-7). On Vercel a missing or short key is an error."""
    secret = _env("JWT_SECRET")
    if _env("VERCEL"):
        if secret is None or len(secret.encode()) < MIN_JWT_SECRET_BYTES:
            raise RuntimeError(
                f"JWT_SECRET mangler eller er kortere enn {MIN_JWT_SECRET_BYTES} byte på Vercel. "
                "Sett den under Settings → Environment Variables (Production og Preview)."
            )
        return secret
    if secret is None:
        logger.warning("JWT_SECRET er ikke satt; bruker en fast nøkkel for lokal utvikling.")
        return DEV_JWT_SECRET
    if len(secret.encode()) < MIN_JWT_SECRET_BYTES:
        logger.warning(
            "JWT_SECRET er kortere enn %d byte; på Vercel stopper det oppstarten.",
            MIN_JWT_SECRET_BYTES,
        )
    return secret


def get_cookie_secure() -> bool:
    """Secure refresh cookie: always on Vercel, locally only with AUTH_COOKIE_SECURE=true."""
    if _env("VERCEL"):
        return True
    return (_env("AUTH_COOKIE_SECURE") or "").lower() == "true"


def get_settings() -> Settings:
    return Settings(
        database_url=get_database_url(),
        jwt_secret=get_jwt_secret(),
        cookie_secure=get_cookie_secure(),
    )
