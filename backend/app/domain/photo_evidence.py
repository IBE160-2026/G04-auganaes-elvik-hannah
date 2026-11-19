"""The Landlord's Photo Evidence requirement on a Task (Story 4.1, FR-18, AD-6).

A Landlord can require Photo Evidence on one Task at a time. Turning it on is allowed only for a
Must Task of a catalog type flagged `photo_evidence_eligible`; a custom Task never is (AD-6).
Eligibility is read from the catalog by key, never from the request. Turning it off is always
allowed. Changing a Task to Bør clears the requirement (domain/tasks.adjust_task). This module only
stores the requirement; stopping a Tenant from completing without a photo is Story 4.2 (FR-19).
"""

import uuid

from sqlmodel import Session, select

from app.domain import tasks
from app.models.membership import Membership, Role
from app.models.task import Task

NOT_ELIGIBLE = "Denne oppgavetypen kan ikke kreve bildebevis."
NOT_MUST = "Bare Må-oppgaver kan kreve bildebevis."


class CannotRequire(Exception):
    """The Task may not require Photo Evidence; `message` says why, in Norwegian."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def can_require_photo_evidence(role: Role) -> bool:
    return role == "landlord"


def refusal(task: Task) -> str | None:
    """Why this Task may not require Photo Evidence, or None when it may (AD-6).

    The one statement of the rule: a Must Task of a catalog type flagged eligible. A custom Task
    has no catalog key, so it is never eligible.
    """
    if not tasks.photo_evidence_eligible(task):
        return NOT_ELIGIBLE
    if task.classification != "must":
        return NOT_MUST
    return None


def may_require(task: Task) -> bool:
    return refusal(task) is None


def set_requirement(
    session: Session, membership: Membership, task_id: uuid.UUID, required: bool
) -> bool:
    """Saves the requirement on the Membership's Home's Task and returns the stored value.

    Raises TaskNotFound (not in this Home, or archived) and CannotRequire (turning it on for a
    Task that may not). The Task row is locked until commit, so a parallel change to Bør cannot
    leave a Bør Task with a requirement (Postgres only; SQLite ignores FOR UPDATE, and the CHECK
    ck_tasks_photo_evidence_must still refuses the combination).
    """
    if not can_require_photo_evidence(membership.role):
        raise ValueError(f"role {membership.role!r} may not require Photo Evidence")
    task = session.exec(
        select(Task)
        .where(Task.id == task_id, Task.home_id == membership.home_id, tasks.is_active())
        .with_for_update()
    ).first()
    if task is None:
        session.rollback()
        raise tasks.TaskNotFound
    if required and (reason := refusal(task)) is not None:
        session.rollback()
        raise CannotRequire(reason)
    if task.requires_photo_evidence != required:
        task.requires_photo_evidence = required
        session.add(task)
        session.commit()
        session.refresh(task)
    else:
        session.rollback()
    return task.requires_photo_evidence
