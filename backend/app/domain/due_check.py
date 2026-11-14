"""The daily due-check (Story 3.2, FR-10, SM-9b, AD-8, AD-16, FR-22).

run_due_check finds every open instance of an active Task that is due today or overdue, for every
*current* Member of its Home (a user who left has no Membership, so gets nothing, AD-16). It
claims each (instance, Member, day) in `due_notifications` BEFORE sending, so a second or
concurrent run finds the pairs taken and sends nothing. The price is deliberate (AD-8): a send
that fails is not retried that day. Each Member gets one push covering all their tasks, across
Homes, to each of their devices. Claims from earlier days are deleted at the start of a run.
"""

import logging
import uuid
from datetime import date
from typing import NamedTuple

from sqlalchemy import case, delete
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.domain import tasks
from app.models.due_notification import DueNotification
from app.models.membership import Membership
from app.models.push_subscription import PushSubscription
from app.models.task import Task, TaskInstance
from app.push import PushMessage, PushTarget, Sender, is_allowed_endpoint

logger = logging.getLogger(__name__)

# A notification names at most this many tasks; the rest is counted.
NAMES_SHOWN = 3
TAG = "husly-forfall"


class DueTask(NamedTuple):
    instance_id: uuid.UUID
    task_id: uuid.UUID
    home_id: uuid.UUID
    name: str
    due_on: date


class DueCheckResult(NamedTuple):
    members: int
    tasks: int
    pushes: int


def _due_text(due_on: date, today: date) -> str:
    days = (today - due_on).days
    if days <= 0:
        return "Skal gjøres i dag."
    if days == 1:
        return "Forfalt i går."
    return f"Forfalt for {days} dager siden."


def build_message(due: list[DueTask], today: date) -> PushMessage:
    """The text a Member gets. One task opens its detail page, several open the overview."""
    if len(due) == 1:
        only = due[0]
        return PushMessage(
            title=only.name,
            body=_due_text(only.due_on, today),
            url=f"/hjem/{only.home_id}/oppgaver/{only.task_id}",
            tag=TAG,
        )
    shown = [t.name for t in due[:NAMES_SHOWN]]
    rest = len(due) - len(shown)
    names = ", ".join(shown) + (f" og {rest} til" if rest else "")
    return PushMessage(title=f"{len(due)} oppgaver venter", body=names + ".", url="/", tag=TAG)


def _due_by_member(session: Session, today: date) -> dict[uuid.UUID, list[DueTask]]:
    """Due and overdue tasks per current Member, Må first, then oldest due date, name, id."""
    rows = session.exec(
        select(
            Membership.user_id,
            TaskInstance.id,
            Task.id,
            Task.home_id,
            Task.name,
            TaskInstance.due_on,
        )
        .join(Task, col(Task.home_id) == col(Membership.home_id))
        .join(TaskInstance, col(TaskInstance.task_id) == col(Task.id))
        .where(tasks.is_active(), tasks.is_open(), col(TaskInstance.due_on) <= today)
        .order_by(
            case((col(Task.classification) == "must", 0), else_=1),
            col(TaskInstance.due_on),
            col(Task.name),
            col(Task.id),
        )
    ).all()
    by_member: dict[uuid.UUID, list[DueTask]] = {}
    for user_id, instance_id, task_id, home_id, name, due_on in rows:
        by_member.setdefault(user_id, []).append(
            DueTask(instance_id, task_id, home_id, name, due_on)
        )
    return by_member


def _claim(session: Session, user_id: uuid.UUID, due: list[DueTask], today: date) -> list[DueTask]:
    """The tasks this Member has not been told about today, each now claimed for this run."""
    taken = set(
        session.exec(
            select(DueNotification.task_instance_id).where(
                DueNotification.user_id == user_id, DueNotification.day == today
            )
        ).all()
    )
    claimed = []
    for item in due:
        if item.instance_id in taken:
            continue
        session.add(DueNotification(task_instance_id=item.instance_id, user_id=user_id, day=today))
        try:
            session.commit()
        except IntegrityError:
            # A parallel run claimed the pair between our read and our insert.
            session.rollback()
            continue
        claimed.append(item)
    return claimed


def _forget_old_claims(session: Session, today: date) -> None:
    """A claim only matters on its own day, so earlier days go (the table stays one day long)."""
    session.execute(delete(DueNotification).where(col(DueNotification.day) < today))
    session.commit()


def run_due_check(session: Session, sender: Sender, today: date) -> DueCheckResult:
    _forget_old_claims(session, today)
    members = 0
    task_count = 0
    pushes = 0
    for user_id, due in _due_by_member(session, today).items():
        claimed = _claim(session, user_id, due, today)
        if not claimed:
            continue
        members += 1
        task_count += len(claimed)
        message = build_message(claimed, today)
        subscriptions = session.exec(
            select(
                PushSubscription.id,
                PushSubscription.endpoint,
                PushSubscription.p256dh,
                PushSubscription.auth,
            )
            .where(PushSubscription.user_id == user_id)
            .order_by(col(PushSubscription.created_at), col(PushSubscription.id))
        ).all()
        gone: list[uuid.UUID] = []
        for sub_id, endpoint, p256dh, auth in subscriptions:
            if not is_allowed_endpoint(endpoint):
                logger.warning("Hoppet over push-adresse utenfor tillatelseslisten.")
                continue
            result = sender.send(PushTarget(endpoint, p256dh, auth), message)
            if result == "sent":
                pushes += 1
            elif result == "gone":
                gone.append(sub_id)
        if gone:
            session.execute(delete(PushSubscription).where(col(PushSubscription.id).in_(gone)))
            session.commit()
    logger.info("Due-check: %d medlemmer, %d oppgaver, %d push.", members, task_count, pushes)
    return DueCheckResult(members, task_count, pushes)
