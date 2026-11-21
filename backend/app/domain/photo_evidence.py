"""The Landlord's Photo Evidence requirement on a Task (Story 4.1, FR-18, AD-6).

A Landlord can require Photo Evidence on one Task at a time. Turning it on is allowed only for a
Must Task of a catalog type flagged `photo_evidence_eligible`; a custom Task never is (AD-6).
Eligibility is read from the catalog by key, never from the request. Turning it off is always
allowed. Changing a Task to Bør clears the requirement (domain/tasks.adjust_task).

Story 4.2 (FR-19, AD-5, AD-3): `complete_with_photo` is how a Tenant completes such a Task. The
photo is stored under the one server-computed key of the Task (overwritten, so no history), the
Task's single `photo_evidence` row is updated, and the instance is completed by
`tasks.complete_task_instance`, the same function as the checkbox.

Story 4.3 (FR-19, NFR5, NFR6): `current_evidence` and `read_photo` are the Landlord's view of that
photo. The routes run `require_role("landlord")` first; the key comes from the Task id only.
"""

import logging
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

logger = logging.getLogger(__name__)

NOT_ELIGIBLE = "Denne oppgavetypen kan ikke kreve bildebevis."
NOT_MUST = "Bare Må-oppgaver kan kreve bildebevis."
NOT_REQUIRED = "Denne oppgaven krever ikke bilde."
FORMER_MEMBER = "Tidligere medlem"
NO_EVIDENCE = "Det finnes ikke noe bildebevis ennå."
PHOTO_GONE = "Bildet finnes ikke lenger."
READ_FAILED = "Vi fikk ikke hentet bildet. Prøv igjen."
NOT_JPEG = "Bildet må være en JPEG-fil. Ta et nytt bilde eller velg en annen fil."
TOO_LARGE = "Bildet er for stort. Velg et mindre bilde."
STORE_FAILED = "Vi fikk ikke lagret bildet. Prøv igjen."

# Vercel's request body limit is 4.5 MB; the photo is the whole body, so this keeps clear of it.
MAX_PHOTO_BYTES = 3_500_000
JPEG_SIGNATURE = b"\xff\xd8\xff"
# A complete JPEG ends with this marker (padding zeros allowed). The browser re-encodes every photo
# before it is sent (PhotoUpload), so a cut-off or glued-on file is not one of ours.
JPEG_END = b"\xff\xd9"
_MONTHS = ("jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des")


class CannotRequire(Exception):
    """The Task may not require Photo Evidence; `message` says why, in Norwegian."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def can_require_photo_evidence(role: Role) -> bool:
    return role == "landlord"


def can_view_photo_evidence(role: Role) -> bool:
    """Only the Home's Landlord (NFR5, NFR6). Its own rule, so widening who may set the
    requirement can never widen who sees the photo."""
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
    if not data.startswith(JPEG_SIGNATURE) or not data.rstrip(b"\x00").endswith(JPEG_END):
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
        
    ).first()
    if instance is None:
        session.rollback()
        raise tasks.TaskNotFound
    stored: tuple[str, bytes | None] | None = None
    if instance.completed_at is None:
        try:
            check_photo(data)
        except InvalidPhoto:
            session.rollback()
            raise
        user = session.get(User, membership.user_id)
        assert user is not None
        key = evidence_key(task.id)
        evidence = session.get(PhotoEvidence, task.id)
        try:
            # The previous photo is read only when there is one, so a first upload costs no read.
            previous = store.read(key) if evidence is not None else None
            store.put(key, data)
        except StorageError:
            session.rollback()
            raise
        stored = (key, previous)
    try:
        if stored is not None:
            description = describe(user.name, now.date())[:DESCRIPTION_MAX_LENGTH]
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
        result = tasks.complete_task_instance(
            session, membership, task.id, instance_id, now=now, photo_attached=True
        )
    except Exception:
        # The photo was stored before the completion could commit. Put back what was there (or
        # nothing), unless the database shows the new evidence committed after all (the connection
        # may have dropped after the commit): then the new photo is the right one.
        if stored is not None and _evidence_committed(session, task.id, instance_id, now) is False:
            _restore(store, *stored)
        raise
    # complete_task_instance can swallow a lost race (rolls back and returns normally): the photo
    # is then not the Task's evidence, so it goes the same way.
    if stored is not None and _evidence_committed(session, task.id, instance_id, now) is False:
        _restore(store, *stored)
    return result


def _evidence_committed(
    session: Session, task_id: uuid.UUID, instance_id: uuid.UUID, now: datetime
) -> bool | None:
    """Whether the Task's evidence row is the one this upload wrote. None when it cannot be read."""
    try:
        session.rollback()  # Nothing of this upload is pending any more, committed or not.
        row = session.exec(
            select(PhotoEvidence)
            .where(PhotoEvidence.task_id == task_id)
            .execution_options(populate_existing=True)
        ).first()
    except Exception:  # noqa: BLE001
        logger.warning(
            "Fikk ikke lest bildebeviset for %s etter opplasting", task_id, exc_info=True
        )
        return None
    return (
        row is not None and row.task_instance_id == instance_id and to_utc(row.uploaded_at) == now
    )


def _restore(store: PhotoStore, key: str, previous: bytes | None) -> None:
    """Best effort: a failure is only logged, the completion's own error is what the caller sees."""
    try:
        if previous is None:
            store.delete(key)
        else:
            store.put(key, previous)
    except Exception:  # noqa: BLE001
        logger.warning(
            "Fikk ikke satt tilbake bildet %s etter en mislykket fullføring", key, exc_info=True
        )


class NoEvidence(Exception):
    """No Photo Evidence is stored for the Task, or the stored object is gone."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def current_evidence(
    session: Session, membership: Membership, task_id: uuid.UUID
) -> PhotoEvidence | None:
    """The Task's one evidence row, or None when no photo was uploaded yet (Landlord's view).

    Raises tasks.TaskNotFound for a Task outside the Home or archived, so «no photo» is never
    confused with «no such Task».
    """
    if not can_view_photo_evidence(membership.role):
        raise ValueError(f"role {membership.role!r} may not view Photo Evidence")
    task = tasks.active_task(session, membership.home_id, task_id)
    return session.get(PhotoEvidence, task.id)


def read_photo(
    session: Session, store: PhotoStore, membership: Membership, task_id: uuid.UUID
) -> bytes:
    """The Task's current photo. Raises TaskNotFound, NoEvidence (no row, or object missing) and
    StorageError. Only the key computed from the Task id is read (AD-5)."""
    evidence = current_evidence(session, membership, task_id)
    if evidence is None:
        raise NoEvidence(NO_EVIDENCE)
    data = store.read(evidence_key(evidence.task_id))
    if data is None:
        raise NoEvidence(PHOTO_GONE)
    return data


def shown_description(session: Session, membership: Membership, evidence: PhotoEvidence) -> str:
    """The description the Landlord sees. The saved text holds the uploader's name at upload time;
    once that user is no longer a Member of the Home it reads «Tidligere medlem» instead (AD-16)."""
    still_member = session.exec(
        select(Membership).where(
            Membership.home_id == membership.home_id,
            Membership.user_id == evidence.uploaded_by_user_id,
        )
    ).first()
    if still_member is not None:
        return evidence.description
    return describe(FORMER_MEMBER, to_utc(evidence.uploaded_at).date())[:DESCRIPTION_MAX_LENGTH]
