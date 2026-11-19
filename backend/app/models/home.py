"""A Home: a Household Home or a Landlord Home (Story 1.3, FR-3, AD-1)."""

import uuid
from datetime import datetime
from typing import Literal, get_args

from sqlalchemy import CheckConstraint, Column, DateTime, Integer, PrimaryKeyConstraint
from sqlmodel import Field, SQLModel

from app.clock import utc_now

HOME_NAME_MAX_LENGTH = 60

# Story 3.5 (FR-13): how often a Home's Tenants are reminded about due Must tasks, in whole days.
CADENCE_OPTIONS: tuple[int, ...] = (1, 2, 7)
DEFAULT_CADENCE_DAYS = 1

HomeType = Literal["household", "landlord"]
HOME_TYPES: tuple[HomeType, ...] = get_args(HomeType)


class Home(SQLModel, table=True):
    __tablename__ = "homes"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_homes"),
        # Alembic check ignores CHECK constraints; tests/test_homes.py covers this one.
        CheckConstraint("type IN ('household', 'landlord')", name="ck_homes_type"),
        CheckConstraint(
            "notification_cadence_days IN (1, 2, 7)", name="ck_homes_notification_cadence_days"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str = Field(max_length=HOME_NAME_MAX_LENGTH)
    type: str = Field(max_length=20)
    notification_cadence_days: int = Field(
        default=DEFAULT_CADENCE_DAYS,
        sa_column=Column(Integer, nullable=False, server_default=str(DEFAULT_CADENCE_DAYS)),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
