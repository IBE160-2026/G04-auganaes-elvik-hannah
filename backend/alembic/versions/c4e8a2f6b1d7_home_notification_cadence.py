"""homes.notification_cadence_days (Story 3.5, FR-13, AD-8)

Written by hand after the model change: one NOT NULL column with server default 1 (today's
behaviour: a reminder every day), so existing Homes need no backfill, and a named CHECK for the
three options. Whole days only, since reminders come from the daily due-check.

Revision ID: c4e8a2f6b1d7
Revises: b9d3e7a1c5f4
Create Date: 2026-11-19 21:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4e8a2f6b1d7"
down_revision: str | Sequence[str] | None = "b9d3e7a1c5f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("homes") as batch:
        batch.add_column(
            sa.Column("notification_cadence_days", sa.Integer(), server_default="1", nullable=False)
        )
        batch.create_check_constraint(
            "ck_homes_notification_cadence_days", "notification_cadence_days IN (1, 2, 7)"
        )


def downgrade() -> None:
    with op.batch_alter_table("homes") as batch:
        batch.drop_constraint("ck_homes_notification_cadence_days", type_="check")
        batch.drop_column("notification_cadence_days")
