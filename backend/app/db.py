"""Database engine (Story 1.7). One engine per URL, built from Settings.database_url."""

from collections.abc import Iterator
from functools import lru_cache

from fastapi import Request
from sqlalchemy import Engine
from sqlmodel import Session, create_engine


@lru_cache
def get_engine(url: str) -> Engine:
    return create_engine(
        url,
        # Neon scales to zero and drops idle connections; check before handing one out.
        pool_pre_ping=True,
        # Neon's pooled URL goes through PgBouncer in transaction mode, where a prepared
        # statement can land on another server connection and fail on reuse. Kept until
        # verified unnecessary (Story 1.2 runs repeated queries through the pooler).
        connect_args={
            "prepare_threshold": None,
            # Fail fast with 503 instead of hanging until the function times out.
            "connect_timeout": 10,
        },
    )


def get_session(request: Request) -> Iterator[Session]:
    """One session per request on the app's engine. Tests override this dependency."""
    with Session(get_engine(request.app.state.settings.database_url)) as session:
        yield session
