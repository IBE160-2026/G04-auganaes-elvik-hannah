"""A single-use link that lets someone join one Home (Story 1.4, FR-2, AD-1).

Separate from Membership: the link carries the Role a joiner will get, decided by the Home type
in domain/homes.py, never by the person who made the link. Only the SHA-256 hash of the token
is stored, so the database alone cannot be used to join a Home.
"""

import uuid
from datetime import datetime

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

from app.models.user import utc_now

# Hex SHA-256.
TOKEN_HASH_LENGTH = 64


class InviteLink(SQLModel, table=True):
    __tablename__ = "invite_links"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_invite_links"),
        ForeignKeyConstraint(["home_id"], ["homes.id"], name="fk_invite_links_home_id_homes"),
        ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], name="fk_invite_links_created_by_user_id_users"
        ),
        ForeignKeyConstraint(
            ["used_by_user_id"], ["users.id"], name="fk_invite_links_used_by_user_id_users"
        ),
        UniqueConstraint("token_hash", name="uq_invite_links_token_hash"),
        Index("ix_invite_links_home_id", "home_id"),
        # A link never makes a Landlord. Alembic check ignores CHECK constraints;
        # tests/test_invites.py and CI cover this one.
        CheckConstraint("role IN ('household_member', 'tenant')", name="ck_invite_links_role"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    home_id: uuid.UUID
    role: str = Field(max_length=20)
    token_hash: str = Field(max_length=TOKEN_HASH_LENGTH)
    created_by_user_id: uuid.UUID
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    used_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    used_by_user_id: uuid.UUID | None = None
