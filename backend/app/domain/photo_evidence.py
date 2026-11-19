"""The Landlord's Photo Evidence requirement on a Task (Story 4.1, FR-18, AD-6).

A Landlord can require Photo Evidence on one Task at a time. Turning it on is allowed only for a
Must Task of a catalog type flagged `photo_evidence_eligible`; a custom Task never is (AD-6).
Eligibility is read from the catalog by key, never from the request. Turning it off is always
allowed. Changing a Task to Bør clears the requirement (domain/tasks.adjust_task).

Story 4.2 (FR-19, AD-5, AD-3): `complete_with_photo` is how a Tenant completes such a Task. The
photo is stored under the one server-computed key of the Task (overwritten, so no history), the
Task's single `photo_evidence` row is updated, and the instance is completed by
`tasks.complete_task_instance`, the same function as the checkbox. Nothing here returns a photo
(Story 4.3).
"""

import uuid
from datetime import date, datetime

from sqlmodel import Session, select

from app.clock import to_utc, utc_now
from app.domain import tasks
from app.models.membership import Membership, Role
from app.models.photo_evidence import DESCRIPTION_MAX_LENGTH, PhotoEvidence
from app.models.task import Task, TaskInstance
from app.models.user import User
from app.storage import PhotoStore, StorageError

NOT_ELIGIBLE = "Denne oppgavetypen kan ikke kreve bildebevis."
NOT_MUST = "Bare Må-oppgaver kan kreve bildebevis."
NOT_REQUIRED = "Denne oppgaven krever ikke bilde."
NOT_JPEG = "Bildet må være en JPEG-fil. Ta et nytt bilde eller velg en annen fil."
TOO_LARGE = "Bildet er for stort. Velg et mindre bilde."
STORE_FAILED = "Vi fikk ikke lagret bildet. Prøv igjen."

# Vercel's request body limit is 4.5 MB; the photo is the whole body, so this keeps clear of it.
MAX_PHOTO_BYTES = 3_500_000
JPEG_SIGNATURE = b"\xff\xd8\xff"
_MONTHS = ("jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des")


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


class InvalidPhoto(Exception):
    """The upload is not an acceptable photo; `message` says why, `too_large` picks the status."""

    def __init__(self, message: str, *, too_large: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.too_large = too_large


class PhotoNotRequired(Exception):
    """The Task does not require Photo Evidence, so an upload has no purpose."""

    message = NOT_REQUIRED


def evidence_key(task_id: uuid.UUID) -> str:
    """The one place a Task's photo lives (AD-5): computed here, never from the request."""
    return f"tasks/{task_id}/evidence.jpg"


def describe(name: str, uploaded_on: date) -> str:
    """The accessible description saved with the photo «Bildebevis … Martin, 29. sep»."""
    return f"Bildebevis lastet opp av {name}, {uploaded_on.day}. {_MONTHS[uploaded_on.month - 1]}"


def check_photo(data: bytes) -> None:
    """Raises InvalidPhoto unless `data` is a JPEG within the size limit."""
    if len(data) > MAX_PHOTO_BYTES:
        raise InvalidPhoto(TOO_LARGE, too_large=True)
    if not data.startswith(JPEG_SIGNATURE):
        raise InvalidPhoto(NOT_JPEG)


def complete_with_photo(
    session: Session,
    store: PhotoStore,
    membership: Membership,
    task_id: uuid.UUID,
    instance_id: uuid.UUID,
    data: bytes,
    now: datetime | None = None,
) -> tasks.TaskWithDue:
    """A Tenant completes the open instance of a Task that requires a photo, with the photo.

    Checks the photo, stores it, updates the Task's one row and completes through
    `tasks.complete_task_instance` (AD-3). An instance that is already completed (another Member,
    a retry) stores nothing and changes nothing: the first completer and the photo they sent stand.
    The Task, then the requirement, then the instance are checked before the photo, so a missing
    Task is a 404 whatever the body is. Raises tasks.TaskNotFound (Task not in this Home, archived,
    or the instance is not the Task's), PhotoNotRequired, InvalidPhoto and StorageError.
    """
    if membership.role != "tenant":
        raise ValueError(f"role {membership.role!r} does not upload Photo Evidence")
    now = to_utc(now) if now is not None else utc_now()
    # Locks the Task and the instance first (the order complete_task_instance uses), so two
    # parallel uploads for one instance serialize: the second finds it completed and stores
    # nothing. Postgres only; SQLite ignores FOR UPDATE.
    task = session.exec(
        select(Task)
        .where(Task.id == task_id, Task.home_id == membership.home_id, tasks.is_active())
        .with_for_update()
    ).first()
    if task is None:
        session.rollback()
        raise tasks.TaskNotFound
    if not task.requires_photo_evidence:
        session.rollback()
        raise PhotoNotRequired
    instance = session.exec(
        select(TaskInstance)
        .where(TaskInstance.id == instance_id, TaskInstance.task_id == task.id)
        .with_for_update()
    ).first()
    if instance is None:
        session.rollback()
        raise tasks.TaskNotFound
    if instance.completed_at is None:
        try:
            check_photo(data)
        except InvalidPhoto:
            session.rollback()
            raise
        user = session.get(User, membership.user_id)
        assert user is not None
        try:
            store.put(evidence_key(task.id), data)
        except StorageError:
            session.rollback()
            raise
        description = describe(user.name, now.date())[:DESCRIPTION_MAX_LENGTH]
        evidence = session.get(PhotoEvidence, task.id)
        if evidence is None:
            evidence = PhotoEvidence(
                task_id=task.id,
                task_instance_id=instance.id,
                uploaded_by_user_id=user.id,
                uploaded_at=now,
                description=description,
            )
        else:
            evidence.task_instance_id = instance.id
            evidence.uploaded_by_user_id = user.id
            evidence.uploaded_at = now
            evidence.description = description
        # Pending until complete_task_instance commits it with the completion.
        session.add(evidence)
    return tasks.complete_task_instance(
        session, membership, task.id, instance_id, now=now, photo_attached=True
    )
