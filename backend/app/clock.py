"""One clock for the backend (Epic 1 retro, action 2, A3).

Timestamps are written in UTC. SQLite gives them back without a zone, so `as_utc` puts UTC
back on a naive value, and response models type their datetimes `UtcDatetime`, so every
datetime the API sends carries a zone, whatever the database or session time zone.
"""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator


def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(moment: datetime) -> datetime:
    """SQLite gives timestamps back without a zone; they were written in UTC."""
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


def to_utc(moment: datetime) -> datetime:
    """A naive value gains UTC; an aware one is converted to UTC."""
    return as_utc(moment).astimezone(UTC)


# Runs when the response model is constructed (FastAPI does not re-validate model instances),
# so build response models normally, never with model_construct.
UtcDatetime = Annotated[datetime, AfterValidator(to_utc)]
