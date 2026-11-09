"""create tasks and task_instances (Story 2.1, FR-4, FR-8, AD-1, AD-6)

Written by hand in the style of the earlier revisions: plain sa.String, every constraint named.
No task_types table: the catalog is the code module app/domain/task_types.py (decision 2), and a
Task stores its key. The unique (home_id, task_type) makes setup run once per Home and also
serves lookups by home_id, so there is no separate index. No ondelete: Homes cannot be deleted.

Revision ID: bb9ad4eac78d
Revises: fa600902c94e
Create Date: 2026-11-09 20:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "bb9ad4eac78d"
down_revision: str | Sequence[str] | None = "fa600902c94e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("home_id", sa.Uuid(), nullable=False),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("classification", sa.String(length=10), nullable=False),
        sa.Column("frequency_days", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "classification IN ('must', 'should')", name="ck_tasks_classification"
        ),
        sa.CheckConstraint("frequency_days > 0", name="ck_tasks_frequency_days"),
        sa.ForeignKeyConstraint(["home_id"], ["homes.id"], name="fk_tasks_home_id_homes"),
        sa.PrimaryKeyConstraint("id", name="pk_tasks"),
        sa.UniqueConstraint("home_id", "task_type", name="uq_tasks_home_id_task_type"),
    )
    op.create_table(
        "task_instances",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], name="fk_task_instances_task_id_tasks"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_task_instances"),
        sa.UniqueConstraint("task_id", "due_on", name="uq_task_instances_task_id_due_on"),
    )


def downgrade() -> None:
    op.drop_table("task_instances")
    op.drop_table("tasks")
