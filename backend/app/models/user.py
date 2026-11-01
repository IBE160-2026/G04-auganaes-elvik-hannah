"""The account row (Story 1.2, FR-1). A Role never lives here; it belongs on Membership (AD-2)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

EMAIL_MAX_LENGTH = 320
NAME_MAX_LENGTH = 50


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    # "user" is a reserved word in Postgres.
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # Stored stripped and lowercased (domain/accounts.py), so the constraint is case-insensitive.
    email: str = Field(max_length=EMAIL_MAX_LENGTH)
    name: str = Field(max_length=NAME_MAX_LENGTH)
    password_hash: str
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
