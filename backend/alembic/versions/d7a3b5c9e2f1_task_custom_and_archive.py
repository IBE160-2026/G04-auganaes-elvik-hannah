"""custom and archived tasks (Story 2.6, FR-24, AD-6, AD-16)

Written by hand like the earlier revisions. A Task gains archived_at, and task_type becomes
nullable (a custom Task has no catalog key). The unique constraint (home_id, task_type) is
replaced by partial unique indexes on active Tasks: one per catalog type and one per lower-case
name in a Home, so either can be added again after archiving. The constraint's index served
lookups by home_id, so a plain index on home_id replaces that.

The downgrade deletes custom and archived Tasks with their instances, since the old unique
constraint cannot hold once an archived Task and its re-added twin exist, and task_type cannot be
NOT NULL with custom Tasks. It is for throwaway databases only, never the local husly or Neon.

Revision ID: d7a3b5c9e2f1
Revises: c4e1d2a7b9f3
Create Date: 2026-11-12 19:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d7a3b5c9e2f1"
down_revision: str | Sequence[str] | None = "c4e1d2a7b9f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("tasks", "task_type", existing_type=sa.String(length=50), nullable=True)
    op.drop_constraint("uq_tasks_home_id_task_type", "tasks", type_="unique")
    op.create_index("ix_tasks_home_id", "tasks", ["home_id"])
    op.create_index(
        "uq_tasks_active_home_id_task_type",
        "tasks",
        ["home_id", "task_type"],
        unique=True,
        postgresql_where=sa.text("archived_at IS NULL"),
    )
    op.create_index(
        "uq_tasks_active_home_id_lower_name",
        "tasks",
        ["home_id", sa.text("lower(name)")],
        unique=True,
        postgresql_where=sa.text("archived_at IS NULL"),
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM task_instances WHERE task_id IN "
        "(SELECT id FROM tasks WHERE task_type IS NULL OR archived_at IS NOT NULL)"
    )
    op.execute("DELETE FROM tasks WHERE task_type IS NULL OR archived_at IS NOT NULL")
    op.drop_index("uq_tasks_active_home_id_lower_name", table_name="tasks")
    op.drop_index("uq_tasks_active_home_id_task_type", table_name="tasks")
    op.drop_index("ix_tasks_home_id", table_name="tasks")
    op.create_unique_constraint("uq_tasks_home_id_task_type", "tasks", ["home_id", "task_type"])
    op.alter_column("tasks", "task_type", existing_type=sa.String(length=50), nullable=False)
    op.drop_column("tasks", "archived_at")
