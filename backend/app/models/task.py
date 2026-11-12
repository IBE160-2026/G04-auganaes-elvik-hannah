"""A Home's Tasks and their dated occurrences (Story 2.1, FR-4, FR-8, AD-1, AD-6).

A Task copies its name from the catalog entry it was made from (task_type is the catalog key),
so a later custom task needs only a nullable task_type, and a new catalog version never rewrites
existing Tasks. A TaskInstance is one dated occurrence.

Story 2.4 (FR-7, FR-9, AD-3): a TaskInstance is open until completed; completed_at and
completed_by_user_id are set together by domain/tasks.complete_task_instance, which also adds the
next open instance. A Task has at most one open instance (uq_task_instances_open_task_id), and
«next due» is that instance's date. Attribution references the User, not the Membership, so a
completion outlives its completer's Membership (AD-16). Two instances of a Task may share a date
(a completed one and the next open one when completed on setup day).
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    UniqueConstraint,
    text,
)
from sqlmodel import Field, SQLModel

from app.clock import utc_now
from app.domain.task_types import TASK_NAME_MAX_LENGTH, TASK_TYPE_KEY_MAX_LENGTH


class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_tasks"),
        ForeignKeyConstraint(["home_id"], ["homes.id"], name="fk_tasks_home_id_homes"),
        # One Task per catalog entry and Home; its index also serves lookups by home_id.
        UniqueConstraint("home_id", "task_type", name="uq_tasks_home_id_task_type"),
        # Alembic check ignores CHECK constraints; tests/test_tasks.py and CI cover these.
        CheckConstraint("classification IN ('must', 'should')", name="ck_tasks_classification"),
        CheckConstraint("frequency_days > 0", name="ck_tasks_frequency_days"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    home_id: uuid.UUID
    task_type: str = Field(max_length=TASK_TYPE_KEY_MAX_LENGTH)
    name: str = Field(max_length=TASK_NAME_MAX_LENGTH)
    classification: str = Field(max_length=10)
    frequency_days: int
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class TaskInstance(SQLModel, table=True):
    __tablename__ = "task_instances"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_task_instances"),
        ForeignKeyConstraint(["task_id"], ["tasks.id"], name="fk_task_instances_task_id_tasks"),
        ForeignKeyConstraint(
            ["completed_by_user_id"],
            ["users.id"],
            name="fk_task_instances_completed_by_user_id_users",
        ),
        # Alembic check ignores CHECK constraints and index WHERE clauses; tests/test_tasks.py and
        # the CI probes cover these two.
        CheckConstraint(
            "(completed_at IS NULL) = (completed_by_user_id IS NULL)",
            name="ck_task_instances_completion",
        ),
        # Lookups by task_id, and a Task's latest completion (domain/tasks._rows).
        Index("ix_task_instances_task_id_completed_at", "task_id", "completed_at"),
        # At most one open instance per Task.
        Index(
            "uq_task_instances_open_task_id",
            "task_id",
            unique=True,
            postgresql_where=text("completed_at IS NULL"),
            sqlite_where=text("completed_at IS NULL"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    task_id: uuid.UUID
    # A calendar date (UTC), not a moment: sent as YYYY-MM-DD.
    due_on: date
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    # When the server received the completion (UTC); null while the instance is open.
    completed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    completed_by_user_id: uuid.UUID | None = None
