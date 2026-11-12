"""task instance completion (Story 2.4, FR-7, FR-9, AD-3)

Written by hand like the earlier revisions. A TaskInstance gains completed_at and
completed_by_user_id (both null while open, both set when completed), and the unique
(task_id, due_on) is replaced by a partial unique index: at most one open instance per Task.
Two instances of a Task may now share a date (a completed one and the next open one).

The downgrade deletes every completed instance, since the old unique (task_id, due_on) cannot
hold once completions exist. It is for throwaway databases only, never the local husly or Neon.

Revision ID: c4e1d2a7b9f3
Revises: bb9ad4eac78d
Create Date: 2026-11-11 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4e1d2a7b9f3"
down_revision: str | Sequence[str] | None = "bb9ad4eac78d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "task_instances", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("task_instances", sa.Column("completed_by_user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_task_instances_completed_by_user_id_users",
        "task_instances",
        "users",
        ["completed_by_user_id"],
        ["id"],
    )
    op.create_check_constraint(
        "ck_task_instances_completion",
        "task_instances",
        "(completed_at IS NULL) = (completed_by_user_id IS NULL)",
    )
    op.drop_constraint("uq_task_instances_task_id_due_on", "task_instances", type_="unique")
    # The dropped unique constraint was the only index starting with task_id.
    op.create_index(
        "ix_task_instances_task_id_completed_at", "task_instances", ["task_id", "completed_at"]
    )
    op.create_index(
        "uq_task_instances_open_task_id",
        "task_instances",
        ["task_id"],
        unique=True,
        postgresql_where=sa.text("completed_at IS NULL"),
    )


def downgrade() -> None:
    op.execute("DELETE FROM task_instances WHERE completed_at IS NOT NULL")
    op.drop_index("uq_task_instances_open_task_id", table_name="task_instances")
    op.drop_index("ix_task_instances_task_id_completed_at", table_name="task_instances")
    op.create_unique_constraint(
        "uq_task_instances_task_id_due_on", "task_instances", ["task_id", "due_on"]
    )
    op.drop_constraint("ck_task_instances_completion", "task_instances", type_="check")
    op.drop_constraint(
        "fk_task_instances_completed_by_user_id_users", "task_instances", type_="foreignkey"
    )
    op.drop_column("task_instances", "completed_by_user_id")
    op.drop_column("task_instances", "completed_at")
