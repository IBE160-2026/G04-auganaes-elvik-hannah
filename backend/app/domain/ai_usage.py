"""The daily limit on AI calls (Story 5.1, FR-14, AD-4).

A user may make AI_DAILY_LIMIT calls per UTC day, quick answers and chat together, mock answers
included. try_count_call is the one place that counts: a single conditional UPDATE, so two calls
at once can never both pass the last slot. A refused call is not counted.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, cast

from sqlalchemy import CursorResult, update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col

from app.models.ai_usage import AiUsage

AI_DAILY_LIMIT = 20


def _bump(session: Session, user_id: uuid.UUID, day: date, limit: int) -> bool:
    result = cast(
        "CursorResult[Any]",
        session.execute(
            update(AiUsage)
            .where(
                col(AiUsage.user_id) == user_id,
                col(AiUsage.day) == day,
                col(AiUsage.count) < limit,
            )
            .values(count=col(AiUsage.count) + 1)
        ),
    )
    return result.rowcount == 1


def try_count_call(
    session: Session, user_id: uuid.UUID, day: date, limit: int = AI_DAILY_LIMIT
) -> bool:
    """Counts one call for the user on this day. False, and nothing counted, at the limit."""
    if _bump(session, user_id, day, limit):
        session.commit()
        return True
    if session.get(AiUsage, (user_id, day)) is not None:
        session.rollback()
        return False
    # First call of the day. A parallel first call may have inserted the row meanwhile.
    try:
        session.add(AiUsage(user_id=user_id, day=day, count=1))
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
    counted = _bump(session, user_id, day, limit)
    if counted:
        session.commit()
    else:
        session.rollback()
    return counted


def next_reset(day: date) -> datetime:
    """When the count restarts: the next UTC midnight after this day."""
    return datetime.combine(day + timedelta(days=1), time.min, tzinfo=UTC)
