"""Task Setup and a Home's Tasks (Story 2.1, FR-4, FR-8, AD-2, AD-6).

set_up_tasks is the only place Tasks are created. It runs once per Home: the user reviews the
catalog's recommendations, adjusts Must/Should and Frequency, unticks what does not fit, and
every chosen Task is created with its first TaskInstance in one transaction. can_set_up_tasks
is the one statement of who may do it; routes and the frontend read it, never the Roles.

Story 2.3 (FR-5, FR-8, issue #40): adjust_task changes one Task's Må/Bør and/or Frequency after
setup. can_adjust_tasks is the one rule for who may; a new Frequency moves the open instance's
date from the same start point (team decision 1, 2026-11-11).

Story 2.6 (FR-24, AD-6, AD-16, issue #31): add_task adds one catalog or custom Task after setup,
and archive_task removes one by setting archived_at (nothing is deleted). Every read that drives
behaviour goes through _rows, which sees active Tasks only; has_tasks keeps counting archived
ones, so archiving the last Task never reopens setup. The same Roles as adjusting may add and
archive (can_adjust_tasks).

Story 2.4 (FR-7, FR-9, AD-3, AD-16, issue #43): complete_task_instance is the one completion
path. It records who completed which instance and when, and adds the next open instance due on
the completion's UTC date + the Task's Frequency (Story 2.5 closed in the same change). Every
Task read (tasks_of, adjust_task, complete_task_instance) goes through _rows, which reads the
open instance and the latest completion with its completer's Membership in this Home.
"""

import uuid
from collections.abc import Iterable, Sequence
from datetime import date, datetime, timedelta
from typing import Literal, NamedTuple

from sqlalchemy import ColumnElement, case, func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.clock import as_utc, to_utc, utc_now
from app.domain import task_types
from app.models.home import Home
from app.models.membership import Membership, Role
from app.models.task import Task, TaskInstance
from app.models.user import User

# Decision (FR-8): Household Members and the Landlord; a Tenant inherits the Landlord's setup.
# household_member exists only in Household Homes and landlord only in Landlord Homes.
SETUP_ROLES: frozenset[Role] = frozenset({"household_member", "landlord"})

# Story 2.3: the same Roles as setup; a Tenant inherits the Landlord's setting. Story 2.6: the same
# Roles also add and archive Tasks (FR-24), so there is one flag, HomeOut.can_adjust_tasks.
ADJUST_ROLES: frozenset[Role] = SETUP_ROLES

NO_TASKS_CHOSEN = "Velg minst én oppgave."
UNKNOWN_TASK_TYPE = "Ukjent oppgave: «{key}»."
DUPLICATE_TASK_TYPE = "Oppgaven «{key}» er valgt mer enn én gang."
BAD_CLASSIFICATION = "En oppgave må være «Må» eller «Bør»."
BAD_FREQUENCY = "Velg et av intervallene i lista."
NO_CHANGE = "Ingen endring."
NO_CHOICE = "Velg en oppgave eller skriv et navn."
BAD_NAME = "Navnet må være mellom 1 og 100 tegn."
DUPLICATE_NAME = "Hjemmet har allerede en oppgave som heter «{name}»."
NOT_ADDED = "Vi fikk ikke lagt til oppgaven."
SET_UP_FIRST = "Sett opp oppgavene først."

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


class TasksNotSetUp(Exception):
    """The Home's Task Setup has not run; a Task cannot be added before it (Story 2.6)."""


class NothingToChange(ValueError):
    """Neither classification nor Frequency was given; the message is NO_CHANGE."""

    def __init__(self) -> None:
        super().__init__(NO_CHANGE)
        self.message = NO_CHANGE


class Completion(NamedTuple):
    """A Task's latest completed instance and who completed it."""

    # When the server received it, UTC.
    completed_at: datetime
    user_id: uuid.UUID
    name: str
    # Whether the completer has a Membership in the Task's Home now (AD-16).
    is_member: bool


class TaskWithDue(NamedTuple):
    task: Task
    # The open instance: the one a checkbox completes and a Frequency change moves.
    instance_id: uuid.UUID
    due_on: date
    # The latest completion, whatever the open instance's due state; None if never completed.
    last_completion: Completion | None


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
            session.add(_first_instance(task, today))
        session.commit()
    except IntegrityError:
        session.rollback()
        raise TasksAlreadySetUp from None
    return tasks_of(session, home_id)


def _first_instance(task: Task, today: date) -> TaskInstance:
    """A new Task's first open instance, due `today` + its Frequency."""
    return TaskInstance(task_id=task.id, due_on=today + timedelta(days=task.frequency_days))


def _is_open() -> ColumnElement[bool]:
    """The one statement of what an open instance is."""
    return col(TaskInstance.completed_at).is_(None)


def _is_active() -> ColumnElement[bool]:
    """The one statement of what an active (not archived) Task is."""
    return col(Task.archived_at).is_(None)


def photo_evidence_eligible(task: Task) -> bool:
    """Whether Photo Evidence may be required on this Task (AD-6, Story 4.1).

    Read from the catalog by key, never stored. A custom Task has no key, so it never is.
    """
    if task.task_type is None:
        return False
    entry = task_types.task_type(task.task_type)
    return entry is not None and entry.photo_evidence_eligible


def _open_instance(session: Session, task_id: uuid.UUID) -> TaskInstance:
    """The Task's one open instance (uq_task_instances_open_task_id)."""
    return session.exec(
        select(TaskInstance).where(TaskInstance.task_id == task_id, _is_open())
    ).one()


def _rows(
    session: Session, home_id: uuid.UUID, task_id: uuid.UUID | None = None
) -> list[TaskWithDue]:
    """The Home's Tasks (or one of them) with the open instance and the latest completion.

    Three queries for the whole list, never one per row: the Tasks with their open instance,
    the latest completed instance per Task with its completer, and which completers are Members
    of this Home now. Must first, then by due date, name and id.
    """
    query = (
        select(Task, TaskInstance)
        .join(TaskInstance, col(TaskInstance.task_id) == col(Task.id))
        .where(Task.home_id == home_id, _is_active(), _is_open())
        .order_by(
            case((col(Task.classification) == "must", 0), else_=1),
            col(TaskInstance.due_on),
            col(Task.name),
            col(Task.id),
        )
    )
    if task_id is not None:
        query = query.where(Task.id == task_id)
    found = session.exec(query).all()
    if not found:
        return []
    task_ids = [task.id for task, _ in found]

    latest = (
        select(
            col(TaskInstance.task_id).label("task_id"),
            func.max(TaskInstance.completed_at).label("completed_at"),
        )
        .where(col(TaskInstance.task_id).in_(task_ids), col(TaskInstance.completed_at).is_not(None))
        .group_by(col(TaskInstance.task_id))
        .subquery()
    )
    completed = session.exec(
        select(TaskInstance, User)
        .join(
            latest,
            (col(TaskInstance.task_id) == latest.c.task_id)
            & (col(TaskInstance.completed_at) == latest.c.completed_at),
        )
        .join(User, col(User.id) == col(TaskInstance.completed_by_user_id))
    ).all()
    by_task: dict[uuid.UUID, tuple[TaskInstance, User]] = {}
    for instance, user in completed:
        # Two completions of one Task in the same microsecond: keep one, deterministically.
        kept = by_task.get(instance.task_id)
        if kept is None or instance.id < kept[0].id:
            by_task[instance.task_id] = (instance, user)
    completer_ids = {user.id for _, user in by_task.values()}
    members: set[uuid.UUID] = set()
    if completer_ids:
        members = set(
            session.exec(
                select(Membership.user_id).where(
                    Membership.home_id == home_id, col(Membership.user_id).in_(completer_ids)
                )
            ).all()
        )

    rows = []
    for task, instance in found:
        last = by_task.get(task.id)
        completion = None
        if last is not None:
            done, user = last
            assert done.completed_at is not None
            at = as_utc(done.completed_at)
            completion = Completion(at, user.id, user.name, user.id in members)
        rows.append(TaskWithDue(task, instance.id, instance.due_on, completion))
    return rows


def _row(session: Session, task: Task) -> TaskWithDue:
    [row] = _rows(session, task.home_id, task.id)
    return row


def tasks_of(session: Session, home_id: uuid.UUID) -> list[TaskWithDue]:
    """The Home's Tasks with their open instance: Must first, then by due date, name and id."""
    return _rows(session, home_id)


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
        select(Task)
        .where(Task.id == task_id, Task.home_id == membership.home_id, _is_active())
        .with_for_update()
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
    return _row(session, task)


def _is_duplicate(session: Session, home_id: uuid.UUID, key: str | None, name: str) -> bool:
    """Whether an active Task of the Home has this catalog key or this name (case-insensitive)."""
    rows = session.exec(
        select(Task.task_type, Task.name).where(Task.home_id == home_id, _is_active())
    ).all()
    folded = name.casefold()
    return any((key is not None and k == key) or n.casefold() == folded for k, n in rows)


def add_task(
    session: Session,
    membership: Membership,
    classification: str,
    frequency_days: int,
    task_type: str | None = None,
    name: str | None = None,
    today: date | None = None,
) -> TaskWithDue:
    """Add one Task to a set-up Home: a catalog type or a custom Task (Story 2.6, FR-24).

    Exactly one of `task_type` and `name` is given. A custom name is trimmed and 1–100 characters;
    a catalog Task takes the catalog's name. An active Task of the Home may not share the catalog
    type or the name (case-insensitive), whichever path adds it. The first instance is due
    `today` + Frequency like in set_up_tasks. Raises InvalidTaskChoices (Norwegian reason) for a
    rule break and TasksNotSetUp when the Home has no Tasks yet (nothing is written).
    """
    if not can_adjust_tasks(membership.role):
        raise ValueError(f"role {membership.role!r} may not add tasks")
    if (task_type is None) == (name is None):
        raise InvalidTaskChoices(NO_CHOICE)
    if classification not in task_types.CLASSIFICATIONS:
        raise InvalidTaskChoices(BAD_CLASSIFICATION)
    if frequency_days not in task_types.FREQUENCY_DAYS:
        raise InvalidTaskChoices(BAD_FREQUENCY)
    if task_type is not None:
        entry = task_types.task_type(task_type)
        if entry is None:
            raise InvalidTaskChoices(UNKNOWN_TASK_TYPE.format(key=task_type))
        key: str | None = entry.key
        task_name = entry.name
    else:
        assert name is not None
        key = None
        task_name = name.strip()
        if not 1 <= len(task_name) <= task_types.TASK_NAME_MAX_LENGTH:
            raise InvalidTaskChoices(BAD_NAME)
    today = today or utc_now().date()
    home_id = membership.home_id
    # Same Home lock as set_up_tasks, so an add and a parallel add see each other's Task.
    # Postgres only; SQLite ignores FOR UPDATE. The unique indexes are the backstop below.
    session.exec(select(Home).where(Home.id == home_id).with_for_update()).one()
    if not has_tasks(session, home_id):
        session.rollback()
        raise TasksNotSetUp
    if _is_duplicate(session, home_id, key, task_name):
        session.rollback()
        raise InvalidTaskChoices(DUPLICATE_NAME.format(name=task_name))
    task = Task(
        home_id=home_id,
        task_type=key,
        name=task_name,
        classification=classification,
        frequency_days=frequency_days,
    )
    try:
        session.add(task)
        session.flush()
        session.add(_first_instance(task, today))
        session.commit()
    except IntegrityError:
        session.rollback()
        # A parallel add won: say which rule it broke, never "already set up".
        if _is_duplicate(session, home_id, key, task_name):
            raise InvalidTaskChoices(DUPLICATE_NAME.format(name=task_name)) from None
        raise InvalidTaskChoices(NOT_ADDED) from None
    return _row(session, task)


def archive_task(
    session: Session,
    membership: Membership,
    task_id: uuid.UUID,
    now: datetime | None = None,
) -> None:
    """Remove a Task by setting archived_at; instances and completions stay (Story 2.6, FR-24).

    Idempotent: an already archived Task changes nothing. Found by id and Home without the
    active filter, unlike adjust_task and complete_task_instance, which treat an archived Task
    as not found. Raises TaskNotFound when the Task is not in the Membership's Home.
    """
    if not can_adjust_tasks(membership.role):
        raise ValueError(f"role {membership.role!r} may not archive tasks")
    now = to_utc(now) if now is not None else utc_now()
    # Same lock as adjust_task and complete_task_instance. Postgres only.
    task = session.exec(
        select(Task).where(Task.id == task_id, Task.home_id == membership.home_id).with_for_update()
    ).first()
    if task is None:
        session.rollback()
        raise TaskNotFound
    if task.archived_at is not None:
        # Nothing written; ends the transaction and releases the lock.
        session.rollback()
        return
    task.archived_at = now
    session.add(task)
    session.commit()


def complete_task_instance(
    session: Session,
    membership: Membership,
    task_id: uuid.UUID,
    instance_id: uuid.UUID,
    now: datetime | None = None,
) -> TaskWithDue:
    """Mark one instance completed by the Membership's User and add the next one (FR-7, FR-9).

    The only completion path (AD-3); the checkbox and, in Epic 4, the photo upload call it.
    `membership` is what require_role returned: any Member may complete. `now` is when the server
    received the completion (defaults to now, UTC); the next open instance is due on its UTC date
    + the Task's Frequency, whatever the old due date was.

    Addressed by instance id, so it is idempotent: an instance already completed (a retry after a
    lost response, a double tap, another Member, a stale id) changes nothing and returns the
    current state, the first completer kept. Raises TaskNotFound when the Task is not in the
    Membership's Home or the instance is not the Task's (Task checked first).
    """
    now = to_utc(now) if now is not None else utc_now()
    # Same lock as adjust_task (Task row first, then the instance), so a completion and a
    # Frequency change serialize. Postgres only; SQLite ignores FOR UPDATE (accepted risk).
    task = session.exec(
        select(Task)
        .where(Task.id == task_id, Task.home_id == membership.home_id, _is_active())
        .with_for_update()
    ).first()
    if task is None:
        session.rollback()
        raise TaskNotFound
    instance = session.exec(
        select(TaskInstance)
        .where(TaskInstance.id == instance_id, TaskInstance.task_id == task.id)
        .with_for_update()
    ).first()
    if instance is None:
        session.rollback()
        raise TaskNotFound
    if instance.completed_at is not None:
        # Nothing written; ends the transaction and releases the locks.
        session.rollback()
        return _row(session, task)
    instance.completed_at = now
    instance.completed_by_user_id = membership.user_id
    session.add(instance)
    # Flushed first, so the partial unique index sees this instance as completed before the
    # next open one is inserted.
    session.flush()
    session.add(
        TaskInstance(task_id=task.id, due_on=now.date() + timedelta(days=task.frequency_days))
    )
    try:
        session.commit()
    except IntegrityError:
        # A parallel completion added the next open instance first: theirs stands.
        session.rollback()
    return _row(session, task)
