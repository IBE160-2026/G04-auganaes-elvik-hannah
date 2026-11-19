"""create photo_evidence (Story 4.2, FR-19, AD-5)

Written by hand after the model: one row per Task (the primary key is the task id), the instance
that produced the photo, the uploader, the time and the server-written description. No history
column and no per-instance key: a new upload updates the one row. No ondelete: Tasks and users are
only archived, never deleted.

Revision ID: e8a2c4d6f1b3
Revises: d6f1b3a9c2e8
Create Date: 2026-11-20 00:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e8a2c4d6f1b3"
down_revision: str | Sequence[str] | None = "d6f1b3a9c2e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "photo_evidence",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("task_instance_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], name="fk_photo_evidence_task_id_tasks"),
        sa.ForeignKeyConstraint(
            ["task_instance_id"],
            ["task_instances.id"],
            name="fk_photo_evidence_task_instance_id_task_instances",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_user_id"],
            ["users.id"],
            name="fk_photo_evidence_uploaded_by_user_id_users",
        ),
        sa.PrimaryKeyConstraint("task_id", name="pk_photo_evidence"),
    )


def downgrade() -> None:
    op.drop_table("photo_evidence")
