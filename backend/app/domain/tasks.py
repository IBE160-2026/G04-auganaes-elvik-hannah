"""Task Setup and a Home's Tasks (Story 2.1, FR-4, FR-8, AD-2, AD-6).

set_up_tasks is the only place Tasks are created. It runs once per Home: the user reviews the
catalog's recommendations, adjusts Must/Should and Frequency, unticks what does not fit, and
every chosen Task is created with its first TaskInstance in one transaction. can_set_up_tasks
is the one statement of who may do it; routes and the frontend read it, never the Roles.
"""

import uuid
from collections.abc import Iterable, Sequence
from datetime import date, timedelta
from typing import NamedTuple

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

NO_TASKS_CHOSEN = "Velg minst én oppgave."
UNKNOWN_TASK_TYPE = "Ukjent oppgave: «{key}»."
DUPLICATE_TASK_TYPE = "Oppgaven «{key}» er valgt mer enn én gang."
BAD_CLASSIFICATION = "En oppgave må være «Må» eller «Bør»."
BAD_FREQUENCY = "Velg et av intervallene i lista."


def can_set_up_tasks(role: str) -> bool:
    return role in SETUP_ROLES


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
