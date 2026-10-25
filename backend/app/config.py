"""Settings read from environment variables (AD-15). See .env.example."""

import os
from dataclasses import dataclass

DEFAULT_DATABASE_URL = "postgresql+psycopg://husly:husly@localhost:5433/husly"
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://localhost:4173"


def parse_origins(raw: str) -> list[str]:
    """Split a comma-separated origin list. A wildcard is rejected (credentials are sent).

    A trailing "/" is stripped, since the browser's Origin header never has one.
    """
    origins = [origin.strip().rstrip("/") for origin in raw.split(",")]
    origins = [origin for origin in origins if origin]
    if "*" in origins:
        raise ValueError("CORS_ORIGINS må være eksakte origins, ikke '*'")
    if not origins:
        raise ValueError("CORS_ORIGINS må inneholde minst én origin")
    return origins


@dataclass(frozen=True)
class Settings:
    database_url: str
    cors_origins: list[str]


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_settings() -> Settings:
    return Settings(
        database_url=get_database_url(),
        cors_origins=parse_origins(os.environ.get("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)),
    )
