"""A Landlord Home's onboarding guide introduction (Story 5.3, FR-16, AD-4).

One row per Home: the introduction the AI service wrote once when the Home's Tasks were set up
(or the fixed fallback text when it could not). Only the introduction is stored; the Home's name
and its Must tasks are read live when the guide is shown, so a later change to the Tasks never
leaves a stale guide.
"""

import uuid
from datetime import datetime
from typing import Literal, get_args

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKeyConstraint, PrimaryKeyConstraint
from sqlmodel import Field, SQLModel

from app.clock import utc_now

GuideSource = Literal["ai", "demo", "fallback"]
GUIDE_SOURCES: tuple[GuideSource, ...] = get_args(GuideSource)
INTRO_MAX_LENGTH = 2000


class OnboardingGuide(SQLModel, table=True):
    __tablename__ = "onboarding_guides"
    __table_args__ = (
        PrimaryKeyConstraint("home_id", name="pk_onboarding_guides"),
        ForeignKeyConstraint(["home_id"], ["homes.id"], name="fk_onboarding_guides_home_id_homes"),
        # Alembic check ignores CHECK constraints; tests/test_onboarding.py covers this one.
        CheckConstraint("source IN ('ai', 'demo', 'fallback')", name="ck_onboarding_guides_source"),
    )

    home_id: uuid.UUID
    intro: str = Field(max_length=INTRO_MAX_LENGTH)
    # ai: Gemini wrote it. demo: the mock did (no key). fallback: the fixed text.
    source: str = Field(max_length=10)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
