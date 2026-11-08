"""User↔Home join with the Member's Role in that Home (Story 1.3, AD-1, AD-2).

The Role lives here and never on User: one user can be Landlord in one Home and Household
Member in another.
"""

import uuid
from datetime import datetime
from typing import Literal, get_args

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    UniqueConstraint,
)
from sqlmodel import Field, SQLModel

from app.clock import utc_now

Role = Literal["household_member", "landlord", "tenant"]
ROLES: tuple[Role, ...] = get_args(Role)


class Membership(SQLModel, table=True):
    __tablename__ = "memberships"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_memberships"),
        ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_memberships_user_id_users"),
        ForeignKeyConstraint(["home_id"], ["homes.id"], name="fk_memberships_home_id_homes"),
        UniqueConstraint("user_id", "home_id", name="uq_memberships_user_id_home_id"),
        Index("ix_memberships_home_id", "home_id"),
        # Alembic check ignores CHECK constraints; tests/test_homes.py covers this one.
        CheckConstraint(
            "role IN ('household_member', 'landlord', 'tenant')", name="ck_memberships_role"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    home_id: uuid.UUID
    role: str = Field(max_length=20)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
