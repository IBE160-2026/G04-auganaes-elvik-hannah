"""The fairness nudge: the first reminder goes to whoever has not done the task (Story 3.3).

FR-11, AD-9, AD-16. When a shared recurring Task's last three completions show that some Members
did none while another current Member did at least one, the first reminder for the open instance
goes only to those Members, and the others skip it that day. Once per instance: after that day
the regular daily reminders (FR-10) resume for everyone. The Landlord does not do the Tasks, so
only Household Members and Tenants count (decision 2); a Member who left counts for nothing.

`WINDOW` is the one place the number 3 lives. `apply_nudges` is called by the due-check between
selecting what is due and claiming it; the rule itself is the pure `nudge_targets`.
"""

import uuid
from collections.abc import Collection, Sequence
from datetime import date, datetime
from typing import Protocol

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.clock import to_utc
from app.models.fairness_nudge import FairnessNudge
from app.models.membership import Membership
from app.models.push_subscription import PushSubscription
from app.models.task import TaskInstance

WINDOW = 3
# The Roles that do a Home's tasks; the Landlord does not (decision 2).
DOERS = ("household_member", "tenant")


class _Due(Protocol):
    @property
    def instance_id(self) -> uuid.UUID: ...
    @property
    def task_id(self) -> uuid.UUID: ...
    @property
    def home_id(self) -> uuid.UUID: ...


def nudge_targets(
    counted: Collection[uuid.UUID], completers: Sequence[uuid.UUID | None]
) -> set[uuid.UUID]:
    """Who the reminder targets, or nobody when the rule does not hold (AD-9).

    `counted` are the Home's current Household Members and Tenants; `completers` the user of
    each of the Task's most recent completed instances (at most `WINDOW`).
    """
    counted = set(counted)
    # With fewer than two counted Members nobody is left to target once someone did the work.
    if len(completers) < WINDOW:
        return set()
    did_some = counted.intersection(c for c in completers if c is not None)
    if not did_some:
        return set()
    return counted - did_some


def _counted_members(session: Session, home_id: uuid.UUID, since: datetime) -> set[uuid.UUID]:
    """Current Household Members and Tenants who were already Members when the window began, so
    a new Member is never singled out for completions they could not have done."""
    return {
        user_id
        for user_id, joined in session.exec(
            select(Membership.user_id, Membership.created_at).where(
                Membership.home_id == home_id, col(Membership.role).in_(DOERS)
            )
        ).all()
        if to_utc(joined) <= to_utc(since)
    }


def _last_completions(
    session: Session, task_id: uuid.UUID
) -> list[tuple[uuid.UUID | None, datetime]]:
    """The user and time of the Task's last `WINDOW` completed instances, newest first."""
    return [
        (user_id, completed_at)
        for user_id, completed_at in session.exec(
            select(TaskInstance.completed_by_user_id, TaskInstance.completed_at)
            .where(TaskInstance.task_id == task_id, col(TaskInstance.completed_at).is_not(None))
            .order_by(
                col(TaskInstance.completed_at).desc(),
                col(TaskInstance.due_on).desc(),
                col(TaskInstance.id),
            )
            .limit(WINDOW)
        ).all()
        if completed_at is not None
    ]


def _claim(session: Session, instance_id: uuid.UUID, today: date) -> None:
    """Records today's nudge for the instance; a parallel run that got there first is fine."""
    session.add(FairnessNudge(task_instance_id=instance_id, day=today))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()


def _with_devices(session: Session, user_ids: set[uuid.UUID]) -> set[uuid.UUID]:
    """The users among `user_ids` who have at least one push device."""
    if not user_ids:
        return set()
    return set(
        session.exec(
            select(PushSubscription.user_id)
            .where(col(PushSubscription.user_id).in_(user_ids))
            .distinct()
        ).all()
    )


def apply_nudges[D: _Due](
    session: Session, by_member: dict[uuid.UUID, list[D]], today: date
) -> dict[uuid.UUID, list[D]]:
    """`by_member` with each nudged instance dropped for the counted Members who are not targets.

    An instance whose nudge was sent on an earlier day is left alone (regular reminders). One
    whose nudge was sent today stays targeted, so a second run the same day does not remind the
    Members who did the work. A new nudge is recorded before anything is sent. Only Members who
    would be reminded on this run and have a device can be targets (FR-13's cadence already
    filtered the others), so a nudge is never spent on nobody. The Landlord and a Member who
    joined after the window did not do the work either and keep the regular reminder.
    """
    reminded: dict[uuid.UUID, set[uuid.UUID]] = {}
    instances: dict[uuid.UUID, D] = {}
    for user_id, items in by_member.items():
        for item in items:
            instances.setdefault(item.instance_id, item)
            reminded.setdefault(item.instance_id, set()).add(user_id)
    if not instances:
        return by_member
    sent = {
        n.task_instance_id: n.day
        for n in session.exec(
            select(FairnessNudge).where(col(FairnessNudge.task_instance_id).in_(list(instances)))
        ).all()
    }
    counted_by_instance: dict[uuid.UUID, set[uuid.UUID]] = {}
    targets_by_instance: dict[uuid.UUID, set[uuid.UUID]] = {}
    for instance_id, item in instances.items():
        if instance_id in sent and sent[instance_id] != today:
            continue
        completions = _last_completions(session, item.task_id)
        if len(completions) < WINDOW:
            continue
        counted = _counted_members(session, item.home_id, completions[-1][1])
        targets = nudge_targets(counted, [user_id for user_id, _ in completions])
        targets &= _with_devices(session, targets & reminded[instance_id])
        if not targets:
            continue
        if instance_id not in sent:
            _claim(session, instance_id, today)
        counted_by_instance[instance_id] = counted
        targets_by_instance[instance_id] = targets
    if not targets_by_instance:
        return by_member
    result: dict[uuid.UUID, list[D]] = {}
    for user_id, items in by_member.items():
        kept = [
            i
            for i in items
            if i.instance_id not in targets_by_instance
            or user_id in targets_by_instance[i.instance_id]
            or user_id not in counted_by_instance[i.instance_id]
        ]
        if kept:
            result[user_id] = kept
    return result
