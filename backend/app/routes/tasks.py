"""The TaskType catalog, Task Setup and a Home's Tasks (Story 2.1, FR-4, FR-8, AD-2, AD-6).

GET /task-types is user-scoped (signed in): the recommendations Task Setup shows. The two
Home-scoped routes go through require_role like every route with {home_id}: setting up Tasks
takes a Household Member or the Landlord (tasks.SETUP_ROLES), reading them any Member. The
route only translates; every rule lives in domain/tasks.
"""

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.clock import utc_now
from app.domain import task_types, tasks
from app.domain.task_types import Classification, Frequency
from app.permissions.current_user import CurrentUser
from app.routes.deps import AnyMember, ErrorOut, SessionDep, TaskSetter

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


class TaskOut(BaseModel):
    id: uuid.UUID
    task_type: str
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


class TasksOut(BaseModel):
    # Must first, then by due date, name and id.
    tasks: list[TaskOut]


def tasks_out(rows: list[tasks.TaskWithDue]) -> TasksOut:
    today = utc_now().date()
    return TasksOut(
        tasks=[
            TaskOut(
                id=row.task.id,
                task_type=row.task.task_type,
                name=row.task.name,
                classification=row.task.classification,
                frequency_days=row.task.frequency_days,
                due_on=row.due_on,
                due_status=tasks.due_status(row.due_on, today),
                days_until_due=(row.due_on - today).days,
            )
            for row in rows
        ]
    )


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
    return tasks_out(created)


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
    return tasks_out(tasks.tasks_of(session, member.home_id))
