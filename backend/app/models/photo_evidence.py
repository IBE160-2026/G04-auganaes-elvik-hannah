"""The current Photo Evidence of a Task (Story 4.2, FR-19, AD-5).

One row per Task, not per TaskInstance: it is "the current evidence for this Task", with the
instance that produced it, who uploaded it and when. A new upload overwrites the stored photo and
updates this row; no code path adds a second row or a second key per completion (no history).
The photo itself is in the photo store under `tasks/{task_id}/evidence.jpg`.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKeyConstraint, PrimaryKeyConstraint
from sqlmodel import Field, SQLModel

DESCRIPTION_MAX_LENGTH = 200


class PhotoEvidence(SQLModel, table=True):
    __tablename__ = "photo_evidence"
    __table_args__ = (
        PrimaryKeyConstraint("task_id", name="pk_photo_evidence"),
        ForeignKeyConstraint(["task_id"], ["tasks.id"], name="fk_photo_evidence_task_id_tasks"),
        ForeignKeyConstraint(
            ["task_instance_id"],
            ["task_instances.id"],
            name="fk_photo_evidence_task_instance_id_task_instances",
        ),
        ForeignKeyConstraint(
            ["uploaded_by_user_id"],
            ["users.id"],
            name="fk_photo_evidence_uploaded_by_user_id_users",
        ),
    )

    task_id: uuid.UUID
    # The instance whose completion this photo proved.
    task_instance_id: uuid.UUID
    uploaded_by_user_id: uuid.UUID
    uploaded_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    # The accessible description, written by the server: «Bildebevis lastet opp av Martin, 29. sep».
    description: str = Field(max_length=DESCRIPTION_MAX_LENGTH)
