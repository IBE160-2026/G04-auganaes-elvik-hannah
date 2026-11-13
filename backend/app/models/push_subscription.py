"""One browser's Web Push subscription, per User and device (Story 3.1, FR-10, AD-8, AD-12).

A device is identified by its `endpoint`, which the push service makes unique and unguessable, so
it is the unique key. A second device of the same User is a second row, never an overwrite.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    UniqueConstraint,
)
from sqlmodel import Field, SQLModel

from app.clock import utc_now

ENDPOINT_MAX_LENGTH = 2048
KEY_MAX_LENGTH = 256


class PushSubscription(SQLModel, table=True):
    __tablename__ = "push_subscriptions"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_push_subscriptions"),
        ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_push_subscriptions_user_id_users"),
        UniqueConstraint("endpoint", name="uq_push_subscriptions_endpoint"),
        Index("ix_push_subscriptions_user_id", "user_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    endpoint: str = Field(max_length=ENDPOINT_MAX_LENGTH)
    p256dh: str = Field(max_length=KEY_MAX_LENGTH)
    auth: str = Field(max_length=KEY_MAX_LENGTH)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
