"""create due_notifications (Story 3.2, FR-10, AD-8)

Written by hand like the earlier revisions: plain sa types and every constraint named. One row
per Member, task instance and UTC day that the due-check has claimed. The downgrade drops the
table; the only loss is that a run the same day could send again.

Revision ID: b9d3e7a1c5f4
Revises: e5b7c9d1f3a2
Create Date: 2026-11-13 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b9d3e7a1c5f4"
down_revision: str | Sequence[str] | None = "e5b7c9d1f3a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "due_notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_instance_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_instance_id"],
            ["task_instances.id"],
            name="fk_due_notifications_task_instance_id_task_instances",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_due_notifications_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_due_notifications"),
        sa.UniqueConstraint(
            "task_instance_id", "user_id", "day", name="uq_due_notifications_instance_user_day"
        ),
    )


def downgrade() -> None:
    op.drop_table("due_notifications")
