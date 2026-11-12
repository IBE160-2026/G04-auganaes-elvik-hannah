"""The TaskType catalog, Task Setup and a Home's Tasks (Story 2.1, FR-4, FR-8, AD-2, AD-6).

GET /task-types is user-scoped (signed in): the recommendations Task Setup shows. The two
Home-scoped routes go through require_role like every route with {home_id}: setting up Tasks
takes a Household Member or the Landlord (tasks.SETUP_ROLES), reading them any Member. The
route only translates; every rule lives in domain/tasks.

Story 2.3 (FR-5, FR-8): PATCH /homes/{home_id}/tasks/{task_id} changes one Task's Må/Bør and/or
Frequency, for a Household Member or the Landlord (tasks.ADJUST_ROLES). require_role runs first,
so a Tenant gets 403 whatever the body or task_id; a Task outside the Home is 404.

Story 2.6 (FR-24): POST /homes/{home_id}/tasks adds one catalog or custom Task and DELETE
/homes/{home_id}/tasks/{task_id} archives one (idempotent, 204), both for tasks.ADJUST_ROLES.

Story 2.4 (FR-7, FR-9, AD-3): POST /homes/{home_id}/tasks/{task_id}/instances/{instance_id}/
completion completes the open instance, for any Member. Every TaskOut carries the open
instance's id and, while that instance is due «later» (decision 1), the latest completion: who
did it is said from the viewer's side (you / member + name / former_member), so the frontend
never compares ids or reads the clock.
"""

import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.clock import utc_now
from app.domain import task_types, tasks
from app.domain.task_types import Classification, Frequency
from app.permissions.current_user import CurrentUser
from app.routes.deps import (
    TASK_NOT_FOUND,
    AnyMember,
    ErrorOut,
    SessionDep,
    TaskAdjuster,
    TaskSetter,
)

router = APIRouter(tags=["tasks"])

ALREADY_SET_UP = "Oppgavene i dette hjemmet er allerede satt opp."


class TaskTypeOut(BaseModel):
    key: str
    name: str
    classification: Classification
    frequency_days: Frequency
    photo_evidence_eligible: bool


class TaskTypesOut(BaseModel):
    catalog_version: int
    # In catalog order.
    task_types: list[TaskTypeOut]
    # The intervals a Frequency is picked from, shortest first.
    frequencies: list[Frequency]


class TaskChoiceIn(BaseModel):
    task_type: str = Field(max_length=task_types.TASK_TYPE_KEY_MAX_LENGTH)
    classification: Classification
    frequency_days: Frequency


class SetUpTasksRequest(BaseModel):
    # Only the ticked rows. An empty list is the domain's 422 («Velg minst én oppgave.»); more
    # rows than the catalog has entries is a shape error, so a huge body is never validated.
    tasks: list[TaskChoiceIn] = Field(max_length=len(task_types.TASK_TYPES))


class AdjustTaskRequest(BaseModel):
    # Omitted or null = leave as is. Values outside the literals are a shape 422; both absent is
    # the domain's 422 («Ingen endring.»).
    classification: Classification | None = None
    frequency_days: Frequency | None = None


class AddTaskRequest(BaseModel):
    # Exactly one of task_type and name; the domain's 422 says so in Norwegian. The name's length
    # is the domain's rule too (1–100 after trimming), so this bound only stops a huge body.
    task_type: str | None = Field(default=None, max_length=task_types.TASK_TYPE_KEY_MAX_LENGTH)
    name: str | None = Field(default=None, max_length=1000)
    classification: Classification
    frequency_days: Frequency


class CompletionOut(BaseModel):
    # The completion's UTC calendar date, YYYY-MM-DD.
    completed_on: date
    # The server's UTC today minus completed_on: 0 «i dag», 1 «i går».
    days_since: int
    # Whether completed_on is in the server's UTC year; the date gets its year otherwise.
    completed_this_year: bool
    # From the viewer's side: their own completion, a current Member of this Home, or someone
    # without a Membership in this Home now (AD-16, «tidligere medlem»).
    by: Literal["you", "member", "former_member"]
    # The completer's name, only when by is "member".
    name: str | None


class TaskOut(BaseModel):
    id: uuid.UUID
    # The open instance; the checkbox completes this one.
    instance_id: uuid.UUID
    # The catalog key; null for a custom Task.
    task_type: str | None
    name: str
    classification: Classification
    frequency_days: Frequency
    # The next instance's date (UTC calendar date), YYYY-MM-DD.
    due_on: date
    # From due_on and the server's UTC today (domain/tasks.due_status); the frontend renders it.
    due_status: tasks.DueStatus
    # due_on minus the same UTC today; negative when overdue. The due text reads this, never the
    # browser's clock, so the words and due_status always agree.
    days_until_due: int
    # The latest completion while the open instance is due «later», else null (decision 1).
    completion: CompletionOut | None


class TasksOut(BaseModel):
    # Must first, then by due date, name and id.
    tasks: list[TaskOut]


def completion_out(
    completion: tasks.Completion, today: date, viewer_id: uuid.UUID
) -> CompletionOut:
    completed_on = completion.completed_at.date()
    by: Literal["you", "member", "former_member"]
    if completion.user_id == viewer_id:
        by = "you"
    elif completion.is_member:
        by = "member"
    else:
        by = "former_member"
    return CompletionOut(
        completed_on=completed_on,
        days_since=(today - completed_on).days,
        completed_this_year=completed_on.year == today.year,
        by=by,
        name=completion.name if by == "member" else None,
    )


def task_out(row: tasks.TaskWithDue, today: date, viewer_id: uuid.UUID) -> TaskOut:
    status_ = tasks.due_status(row.due_on, today)
    completion = None
    if row.last_completion is not None and status_ == "later":
        completion = completion_out(row.last_completion, today, viewer_id)
    return TaskOut(
        id=row.task.id,
        instance_id=row.instance_id,
        task_type=row.task.task_type,
        name=row.task.name,
        classification=row.task.classification,
        frequency_days=row.task.frequency_days,
        due_on=row.due_on,
        due_status=status_,
        days_until_due=(row.due_on - today).days,
        completion=completion,
    )


def tasks_out(rows: list[tasks.TaskWithDue], viewer_id: uuid.UUID) -> TasksOut:
    today = utc_now().date()
    return TasksOut(tasks=[task_out(row, today, viewer_id) for row in rows])


@router.get("/task-types")
def list_task_types(_user: CurrentUser) -> TaskTypesOut:
    return TaskTypesOut(
        catalog_version=task_types.CATALOG_VERSION,
        task_types=[TaskTypeOut(**entry._asdict()) for entry in task_types.TASK_TYPES],
        frequencies=list(task_types.FREQUENCY_DAYS),
    )


@router.post(
    "/homes/{home_id}/tasks/setup",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not a Household Member or the Landlord of this Home, or no such Home",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorOut,
            "description": "The Home's Tasks are already set up",
        },
    },
)
def set_up_tasks(body: SetUpTasksRequest, setter: TaskSetter, session: SessionDep) -> TasksOut:
    # home_id is read by require_role, which also puts it in the OpenAPI path.
    choices = [
        tasks.TaskChoice(c.task_type, c.classification, c.frequency_days) for c in body.tasks
    ]
    try:
        created = tasks.set_up_tasks(session, setter, choices)
    except tasks.InvalidTaskChoices as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.message) from None
    except tasks.TasksAlreadySetUp:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=ALREADY_SET_UP) from None
    return tasks_out(created, setter.user_id)


@router.get(
    "/homes/{home_id}/tasks",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not a Member of this Home, or no such Home",
        }
    },
)
def list_tasks(member: AnyMember, session: SessionDep) -> TasksOut:
    return tasks_out(tasks.tasks_of(session, member.home_id), member.user_id)


@router.post(
    "/homes/{home_id}/tasks",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not a Household Member or the Landlord of this Home, or no such Home",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorOut,
            "description": "The Home's Tasks are not set up yet",
        },
    },
)
def add_task(body: AddTaskRequest, adjuster: TaskAdjuster, session: SessionDep) -> TaskOut:
    try:
        row = tasks.add_task(
            session,
            adjuster,
            body.classification,
            body.frequency_days,
            task_type=body.task_type,
            name=body.name,
        )
    except tasks.TasksNotSetUp:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=tasks.SET_UP_FIRST) from None
    except tasks.InvalidTaskChoices as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.message) from None
    return task_out(row, utc_now().date(), adjuster.user_id)


@router.delete(
    "/homes/{home_id}/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not a Household Member or the Landlord of this Home, or no such Home",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorOut,
            "description": "No such Task in this Home",
        },
    },
)
def archive_task(task_id: uuid.UUID, adjuster: TaskAdjuster, session: SessionDep) -> None:
    """Archives the Task (idempotent: an already archived one changes nothing), 204."""
    try:
        tasks.archive_task(session, adjuster, task_id)
    except tasks.TaskNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND) from None


@router.patch(
    "/homes/{home_id}/tasks/{task_id}",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not a Household Member or the Landlord of this Home, or no such Home",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorOut,
            "description": "No such Task in this Home",
        },
    },
)
def adjust_task(
    task_id: uuid.UUID, body: AdjustTaskRequest, adjuster: TaskAdjuster, session: SessionDep
) -> TaskOut:
    try:
        row = tasks.adjust_task(
            session,
            adjuster,
            task_id,
            classification=body.classification,
            frequency_days=body.frequency_days,
        )
    except tasks.TaskNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND) from None
    except (tasks.NothingToChange, tasks.InvalidTaskChoices) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.message) from None
    return task_out(row, utc_now().date(), adjuster.user_id)


@router.post(
    "/homes/{home_id}/tasks/{task_id}/instances/{instance_id}/completion",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not a Member of this Home, or no such Home",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorOut,
            "description": "No such Task in this Home, or no such instance of the Task",
        },
    },
)
def complete_task(
    task_id: uuid.UUID, instance_id: uuid.UUID, member: AnyMember, session: SessionDep
) -> TaskOut:
    """Completes the instance (idempotent: an already completed one changes nothing), 200."""
    try:
        row = tasks.complete_task_instance(session, member, task_id, instance_id)
    except tasks.TaskNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND) from None
    return task_out(row, utc_now().date(), member.user_id)
