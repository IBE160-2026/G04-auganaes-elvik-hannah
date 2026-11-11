"""Task Setup and a Home's Tasks (Story 2.1, FR-4, FR-8, AD-2, AD-6).

set_up_tasks is the only place Tasks are created. It runs once per Home: the user reviews the
catalog's recommendations, adjusts Must/Should and Frequency, unticks what does not fit, and
every chosen Task is created with its first TaskInstance in one transaction. can_set_up_tasks
is the one statement of who may do it; routes and the frontend read it, never the Roles.

Story 2.3 (FR-5, FR-8, issue #40): adjust_task changes one Task's Må/Bør and/or Frequency after
setup. can_adjust_tasks is the one rule for who may; a new Frequency moves the open instance's
date from the same start point (team decision 1, 2026-11-11).
"""

import uuid
from collections.abc import Iterable, Sequence
from datetime import date, timedelta
from typing import Literal, NamedTuple

from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.clock import utc_now
from app.domain import task_types
from app.models.home import Home
from app.models.membership import Membership, Role
from app.models.task import Task, TaskInstance

# Decision (FR-8): Household Members and the Landlord; a Tenant inherits the Landlord's setup.
# household_member exists only in Household Homes and landlord only in Landlord Homes.
SETUP_ROLES: frozenset[Role] = frozenset({"household_member", "landlord"})

# Story 2.3: the same Roles as setup; a Tenant inherits the Landlord's setting.
ADJUST_ROLES: frozenset[Role] = SETUP_ROLES

NO_TASKS_CHOSEN = "Velg minst én oppgave."
UNKNOWN_TASK_TYPE = "Ukjent oppgave: «{key}»."
DUPLICATE_TASK_TYPE = "Oppgaven «{key}» er valgt mer enn én gang."
BAD_CLASSIFICATION = "En oppgave må være «Må» eller «Bør»."
BAD_FREQUENCY = "Velg et av intervallene i lista."
NO_CHANGE = "Ingen endring."

# Decision (Story 2.2, 1): a Task is due soon from today up to and including today + 3 days.
# With 7, a weekly Task would always be due soon.
DUE_SOON_DAYS = 3

DueStatus = Literal["overdue", "due_soon", "later"]


def due_status(due_on: date, today: date) -> DueStatus:
    """The one rule for a Task's due state (FR-6, UX-DR20); `today` is the UTC date."""
    if due_on < today:
        return "overdue"
    if due_on <= today + timedelta(days=DUE_SOON_DAYS):
        return "due_soon"
    return "later"


def can_set_up_tasks(role: str) -> bool:
    return role in SETUP_ROLES


def can_adjust_tasks(role: str) -> bool:
    return role in ADJUST_ROLES


class TaskChoice(NamedTuple):
    """One ticked row of Task Setup."""

    task_type: str
    classification: str
    frequency_days: int


class InvalidTaskChoices(ValueError):
    """The choices break a rule; `message` is the Norwegian reason for the user."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TasksAlreadySetUp(Exception):
    """The Home already has Tasks; setup runs once per Home."""


class TaskNotFound(Exception):
    """No Task with this id in the Membership's Home."""


class NothingToChange(ValueError):
    """Neither classification nor Frequency was given; the message is NO_CHANGE."""

    def __init__(self) -> None:
        super().__init__(NO_CHANGE)
        self.message = NO_CHANGE


class TaskWithDue(NamedTuple):
    task: Task
    # The earliest TaskInstance's date.
    due_on: date


def _validate(choices: Sequence[TaskChoice]) -> None:
    if not choices:
        raise InvalidTaskChoices(NO_TASKS_CHOSEN)
    seen: set[str] = set()
    for choice in choices:
        if task_types.task_type(choice.task_type) is None:
            raise InvalidTaskChoices(UNKNOWN_TASK_TYPE.format(key=choice.task_type))
        if choice.task_type in seen:
            raise InvalidTaskChoices(DUPLICATE_TASK_TYPE.format(key=choice.task_type))
        seen.add(choice.task_type)
        if choice.classification not in task_types.CLASSIFICATIONS:
            raise InvalidTaskChoices(BAD_CLASSIFICATION)
        if choice.frequency_days not in task_types.FREQUENCY_DAYS:
            raise InvalidTaskChoices(BAD_FREQUENCY)


def has_tasks(session: Session, home_id: uuid.UUID) -> bool:
    return session.exec(select(Task.id).where(Task.home_id == home_id)).first() is not None


def home_ids_with_tasks(session: Session, home_ids: Iterable[uuid.UUID]) -> set[uuid.UUID]:
    """Which of these Homes have at least one Task, in one query."""
    ids = list(home_ids)
    if not ids:
        return set()
    rows = session.exec(select(Task.home_id).where(col(Task.home_id).in_(ids)).distinct())
    return set(rows.all())


def set_up_tasks(
    session: Session,
    membership: Membership,
    choices: Sequence[TaskChoice],
    today: date | None = None,
) -> list[TaskWithDue]:
    """Create the chosen Tasks, each with its first TaskInstance due `today` + Frequency.

    `membership` is what require_role returned. `today` defaults to the UTC date; the seed passes
    an earlier date so some instances are due soon or overdue. Raises InvalidTaskChoices before
    touching the database, and TasksAlreadySetUp when the Home has Tasks (nothing is written).
    """
    if not can_set_up_tasks(membership.role):
        raise ValueError(f"role {membership.role!r} may not set up tasks")
    _validate(choices)
    today = today or utc_now().date()
    home_id = membership.home_id
    # Locks the Home row until commit, so two parallel setups (two tabs, a double click) cannot
    # both see an empty Home. Postgres only; SQLite ignores FOR UPDATE. The unique
    # (home_id, task_type) is the backstop below.
    session.exec(select(Home).where(Home.id == home_id).with_for_update()).one()
    if has_tasks(session, home_id):
        session.rollback()
        raise TasksAlreadySetUp
    try:
        created = []
        for choice in choices:
            entry = task_types.task_type(choice.task_type)
            assert entry is not None  # checked by _validate
            task = Task(
                home_id=home_id,
                task_type=entry.key,
                name=entry.name,
                classification=choice.classification,
                frequency_days=choice.frequency_days,
            )
            session.add(task)
            created.append(task)
        # The models have no relationship(), so the Tasks are flushed before their instances.
        session.flush()
        for task in created:
            due_on = today + timedelta(days=task.frequency_days)
            session.add(TaskInstance(task_id=task.id, due_on=due_on))
        session.commit()
    except IntegrityError:
        session.rollback()
        raise TasksAlreadySetUp from None
    return tasks_of(session, home_id)


def tasks_of(session: Session, home_id: uuid.UUID) -> list[TaskWithDue]:
    """The Home's Tasks with their next due date: Must first, then by due date, name and id."""
    due_on = func.min(TaskInstance.due_on)
    rows = session.exec(
        select(Task, due_on)
        .join(TaskInstance, col(TaskInstance.task_id) == col(Task.id))
        .where(Task.home_id == home_id)
        .group_by(col(Task.id))
        .order_by(
            case((col(Task.classification) == "must", 0), else_=1),
            due_on,
            col(Task.name),
            col(Task.id),
        )
    ).all()
    return [TaskWithDue(task, due) for task, due in rows]


def _open_instance(session: Session, task_id: uuid.UUID) -> TaskInstance:
    """The instance a Frequency change moves: the Task's earliest one.

    Story 2.4 must make this the earliest *open* instance, together with tasks_of
    (deferred-work.md).
    """
    return session.exec(
        select(TaskInstance)
        .where(TaskInstance.task_id == task_id)
        .order_by(col(TaskInstance.due_on))
        .limit(1)
    ).one()


def adjust_task(
    session: Session,
    membership: Membership,
    task_id: uuid.UUID,
    classification: task_types.Classification | None = None,
    frequency_days: task_types.Frequency | None = None,
) -> TaskWithDue:
    """Change a Task's Må/Bør and/or Frequency (Story 2.3, FR-5, FR-8).

    `membership` is what require_role returned; None means "leave as is". A new Frequency moves
    the open instance to `due_on - old + new` (same start point, new interval), so it may become
    overdue at once; a classification-only change leaves the date alone. Values equal to the
    stored ones write nothing. Raises NothingToChange when both are None, TaskNotFound when the
    Task is not in the Membership's Home, and InvalidTaskChoices for a value outside the catalog
    rules (the route's types already stop those).
    """
    if not can_adjust_tasks(membership.role):
        raise ValueError(f"role {membership.role!r} may not adjust tasks")
    if classification is None and frequency_days is None:
        raise NothingToChange
    if classification is not None and classification not in task_types.CLASSIFICATIONS:
        raise InvalidTaskChoices(BAD_CLASSIFICATION)
    if frequency_days is not None and frequency_days not in task_types.FREQUENCY_DAYS:
        raise InvalidTaskChoices(BAD_FREQUENCY)
    # Locks the Task row until commit, so two parallel saves cannot mix one's Frequency with the
    # other's date shift. Postgres only; SQLite ignores FOR UPDATE (accepted risk).
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.home_id == membership.home_id).with_for_update()
    ).first()
    if task is None:
        session.rollback()
        raise TaskNotFound
    instance = _open_instance(session, task.id)
    changed = False
    if frequency_days is not None and frequency_days != task.frequency_days:
        instance.due_on += timedelta(days=frequency_days - task.frequency_days)
        task.frequency_days = frequency_days
        session.add(instance)
        changed = True
    if classification is not None and classification != task.classification:
        task.classification = classification
        changed = True
    if changed:
        session.add(task)
        session.commit()
    else:
        # Nothing written; ends the transaction and releases the lock.
        session.rollback()
    session.refresh(task)
    return TaskWithDue(task, _next_due(session, task.id))


def _next_due(session: Session, task_id: uuid.UUID) -> date:
    """The Task's next due date as tasks_of reads it."""
    return session.exec(
        select(func.min(TaskInstance.due_on)).where(TaskInstance.task_id == task_id)
    ).one()
