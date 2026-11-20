"""onboarding_guides and memberships.onboarding_dismissed_at (Story 5.3, FR-16, AD-4)

Written by hand after the models: one introduction per Home (the primary key is the Home id) with
a CHECK on where it came from, and a nullable dismissal time on the Membership. No ondelete: Homes
are never deleted.

Revision ID: f1a3c5e7b9d2
Revises: c4e6a8b0d2f5
Create Date: 2026-11-20 23:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f1a3c5e7b9d2"
down_revision: str | Sequence[str] | None = "c4e6a8b0d2f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "onboarding_guides",
        sa.Column("home_id", sa.Uuid(), nullable=False),
        sa.Column("intro", sa.String(length=2000), nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("source IN ('ai', 'demo', 'fallback')", name="ck_onboarding_guides_source"),
        sa.ForeignKeyConstraint(["home_id"], ["homes.id"], name="fk_onboarding_guides_home_id_homes"),
        sa.PrimaryKeyConstraint("home_id", name="pk_onboarding_guides"),
    )
    op.add_column(
        "memberships",
        sa.Column("onboarding_dismissed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("memberships", "onboarding_dismissed_at")
    op.drop_table("onboarding_guides")
