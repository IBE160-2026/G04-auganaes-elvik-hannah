"""create fairness_nudges (Story 3.3, FR-11, AD-9)

One row per task instance, with the UTC day of the nudge, so a task instance gets at most one
fairness nudge. Constraints are named. No ondelete: instances are never deleted.

Revision ID: c4e6a8b0d2f5
Revises: e8a2c4d6f1b3
Create Date: 2026-11-20 21:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4e6a8b0d2f5"
down_revision: str | Sequence[str] | None = "e8a2c4d6f1b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fairness_nudges",
        sa.Column("task_instance_id", sa.Uuid(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_instance_id"],
            ["task_instances.id"],
            name="fk_fairness_nudges_task_instance_id_task_instances",
        ),
        sa.PrimaryKeyConstraint("task_instance_id", name="pk_fairness_nudges"),
    )


def downgrade() -> None:
    op.drop_table("fairness_nudges")
