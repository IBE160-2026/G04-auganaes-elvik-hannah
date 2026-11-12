"""create ai_usage (Story 5.1, FR-14, AD-4)

Written by hand like the earlier revisions. One row per user and UTC day with the number of AI
calls made, which the daily limit reads. The downgrade drops the table (the counts are
disposable).

Revision ID: a8c2f4d6b1e3
Revises: d7a3b5c9e2f1
Create Date: 2026-11-12 21:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a8c2f4d6b1e3"
down_revision: str | Sequence[str] | None = "d7a3b5c9e2f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_usage",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.CheckConstraint("count >= 0", name="ck_ai_usage_count"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_ai_usage_user_id_users"),
        sa.PrimaryKeyConstraint("user_id", "day", name="pk_ai_usage"),
    )


def downgrade() -> None:
    op.drop_table("ai_usage")
