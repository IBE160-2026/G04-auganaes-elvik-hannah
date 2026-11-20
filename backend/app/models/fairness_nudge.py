"""The day a task instance's fairness nudge was sent (Story 3.3, FR-11, AD-9).

One row per task instance, so at most one nudge exists per instance. The due-check inserts it
before it sends (like `due_notifications`), so a parallel run cannot send a second one. `day` is
the UTC date of that run: later runs the same day keep the nudge in force (the Members who did
the work are still skipped), later days remind everyone again.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Column, DateTime, ForeignKeyConstraint, PrimaryKeyConstraint
from sqlmodel import Field, SQLModel

from app.clock import utc_now


class FairnessNudge(SQLModel, table=True):
    __tablename__ = "fairness_nudges"
    __table_args__ = (
        PrimaryKeyConstraint("task_instance_id", name="pk_fairness_nudges"),
        ForeignKeyConstraint(
            ["task_instance_id"],
            ["task_instances.id"],
            name="fk_fairness_nudges_task_instance_id_task_instances",
        ),
    )

    task_instance_id: uuid.UUID
    day: date
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
