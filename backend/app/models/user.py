"""The account row (Story 1.2, FR-1). A Role never lives here; it belongs on Membership (AD-2)."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.clock import utc_now

EMAIL_MAX_LENGTH = 320
NAME_MAX_LENGTH = 50


class User(SQLModel, table=True):
    # "user" is a reserved word in Postgres.
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        # The database itself keeps e-mail addresses lowercase (deferred from Story 1.2), so a write
        # that bypasses accounts.normalize_email cannot make `Ola@…` beside `ola@…`.
        CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # Stored stripped and lowercased (domain/accounts.py), so the constraint is case-insensitive.
    email: str = Field(max_length=EMAIL_MAX_LENGTH)
    name: str = Field(max_length=NAME_MAX_LENGTH)
    password_hash: str
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    # Story 1.10 (FR-25, AD-17): set when the account is deleted. The row stays, anonymised, so
    # history that references the User keeps working.
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
