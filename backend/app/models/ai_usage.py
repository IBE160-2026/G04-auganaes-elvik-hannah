"""How many AI calls a User has made on a UTC day (Story 5.1, FR-14, AD-4).

One row per user and day, counted by domain/ai_usage.try_count_call. Mock answers count too, so
the daily limit is testable offline. The row references the User, as all history does (AD-16).
"""

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, PrimaryKeyConstraint
from sqlmodel import Field, SQLModel


class AiUsage(SQLModel, table=True):
    __tablename__ = "ai_usage"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "day", name="pk_ai_usage"),
        ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_ai_usage_user_id_users"),
        # Alembic check ignores CHECK constraints; tests/test_ai.py covers this one.
        CheckConstraint("count >= 0", name="ck_ai_usage_count"),
    )

    user_id: uuid.UUID
    day: date
    count: int = Field(default=0)
