"""One claimed due notification: this Member, this task instance, this day (Story 3.2, AD-8).

The due-check inserts the row before it sends. The unique key makes a second or concurrent run
find the pair taken, so nobody gets two notifications for the same instance and day (SM-9b).
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    UniqueConstraint,
)
from sqlmodel import Field, SQLModel

from app.clock import utc_now


class DueNotification(SQLModel, table=True):
    __tablename__ = "due_notifications"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_due_notifications"),
        ForeignKeyConstraint(
            ["task_instance_id"],
            ["task_instances.id"],
            name="fk_due_notifications_task_instance_id_task_instances",
        ),
        ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_due_notifications_user_id_users"),
        UniqueConstraint(
            "task_instance_id", "user_id", "day", name="uq_due_notifications_instance_user_day"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    task_instance_id: uuid.UUID
    user_id: uuid.UUID
    # The UTC date of the run (clock.utc_today).
    day: date
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
