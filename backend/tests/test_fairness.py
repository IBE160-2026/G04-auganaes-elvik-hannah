"""Story 3.3 (FR-11, AD-9, AD-16, FR-13): the first reminder goes to whoever has not done the task.

Each test that guards a rule names the line it guards (review convention, Epic 2 retro P1).
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.domain import fairness, homes
from app.models.fairness_nudge import FairnessNudge
from app.models.home import Home
from app.models.membership import Membership
from app.models.push_subscription import PushSubscription
from app.models.task import Task, TaskInstance
from app.models.user import User
from app.push import MockSender
from tests.helpers import new_user
from tests.test_due_check import TODAY, device, run, sent_to


def household(session: Session, *names: str) -> tuple[uuid.UUID, list[User]]:
    owner = new_user(session, names[0])
    home = homes.create_home(session, owner, name="Kollektivet", type="household").home
    users = [owner]
    for name in names[1:]:
        user = new_user(session, name)
        homes.add_member(session, home, user)
        users.append(user)
    for user in users:
        device(session, user, user.name.lower())
    long_ago(session, home.id)
    return home.id, users


def long_ago(session: Session, home_id: uuid.UUID) -> None:
    """All Memberships of the Home date from before the task history, as for a settled Home."""
    session.execute(
        update(Membership)
        .where(col(Membership.home_id) == home_id)
        .values(created_at=datetime(2026, 9, 1, tzinfo=UTC))
    )
    session.commit()


def tenancy(session: Session, *tenants: str) -> tuple[uuid.UUID, User, list[User]]:
    """A Landlord Home with Kari and the named Tenants, all with a device."""
    kari = new_user(session, "Kari")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    users = []
    for name in tenants:
        user = new_user(session, name)
        homes.add_member(session, home, user)
        users.append(user)
    for user in (kari, *users):
        device(session, user, user.name.lower())
    long_ago(session, home.id)
    return home.id, kari, users


def task_with_history(
    session: Session,
    home_id: uuid.UUID,
    completers: list[User | None],
    due_on: date = TODAY,
    classification: str = "should",
) -> Task:
    """A Task with one completed instance per entry (oldest first) and an open one due `due_on`."""
    task = Task(home_id=home_id, name="Støvsuge", classification=classification, frequency_days=7)
    session.add(task)
    session.flush()
    for i, user in enumerate(completers):
        session.add(
            TaskInstance(
                task_id=task.id,
                due_on=date(2026, 10, 1) + timedelta(days=7 * i),
                completed_at=datetime(2026, 10, 1 + 7 * i, 12, tzinfo=UTC),
                completed_by_user_id=user.id if user else None,
            )
        )
    session.add(TaskInstance(task_id=task.id, due_on=due_on))
    session.commit()
    return task


def open_instance(session: Session, task: Task) -> TaskInstance:
    return session.exec(
        select(TaskInstance).where(
            TaskInstance.task_id == task.id, col(TaskInstance.completed_at).is_(None)
        )
    ).one()


def reached(sender: MockSender) -> set[str]:
    return set(sent_to(sender))


def test_the_member_who_did_none_of_the_last_three_is_reminded_and_the_one_who_did_is_not(
    session: Session,
) -> None:
    home_id, (mari, jonas) = household(session, "Mari", "Jonas")
    task_with_history(session, home_id, [mari, mari, mari])
    sender = MockSender()

    run(session, sender)

    # Guards `counted - did_some` and the removal of the non-targets in `apply_nudges`.
    assert reached(sender) == {"jonas"}
    assert len(session.exec(select(FairnessNudge)).all()) == 1


def test_the_nudge_text_is_the_normal_due_text(session: Session) -> None:
    home_id, (mari, jonas) = household(session, "Mari", "Jonas")
    task_with_history(session, home_id, [mari, mari, mari])
    sender = MockSender()

    run(session, sender)

    # Guards FR-11's tone rule: the same builder, so no «you're the only one» framing.
    message = sent_to(sender)["jonas"]
    assert message.title == "Støvsuge"
    assert message.body == "Skal gjøres i dag."


def test_a_second_run_the_same_day_still_skips_the_one_who_did_the_work(
    session: Session,
) -> None:
    home_id, (mari, jonas) = household(session, "Mari", "Jonas")
    task_with_history(session, home_id, [mari, mari, mari])
    run(session, MockSender())
    again = MockSender()

    run(session, again)

    # Guards the same-day branch (`sent[instance_id] != today` is false): the nudge stays in force
    # today, so Mari is not reminded by a repeated run, and nobody gets a second push.
    assert len(again.sent) == 0


def test_the_next_day_everyone_is_reminded_as_before_and_no_second_nudge_exists(
    session: Session,
) -> None:
    home_id, (mari, jonas) = household(session, "Mari", "Jonas")
    task_with_history(session, home_id, [mari, mari, mari])
    run(session, MockSender())
    sender = MockSender()

    run(session, sender, TODAY + timedelta(days=1))

    # Guards `sent[instance_id] != today -> continue`: at most one nudge per instance (SM-15).
    assert reached(sender) == {"mari", "jonas"}
    assert len(session.exec(select(FairnessNudge)).all()) == 1


def test_fewer_than_three_completed_instances_reminds_everyone(session: Session) -> None:
    home_id, (mari, jonas) = household(session, "Mari", "Jonas")
    task_with_history(session, home_id, [mari, mari])
    sender = MockSender()

    run(session, sender)

    # Guards `len(completers) < WINDOW`.
    assert reached(sender) == {"mari", "jonas"}
    assert session.exec(select(FairnessNudge)).all() == []


def test_evenly_shared_work_reminds_everyone(session: Session) -> None:
    home_id, (mari, jonas) = household(session, "Mari", "Jonas")
    task_with_history(session, home_id, [mari, jonas, mari])
    sender = MockSender()

    run(session, sender)

    # Guards `counted - did_some`: nobody is left without a completion, so no target.
    assert reached(sender) == {"mari", "jonas"}


def test_a_home_with_one_counted_member_never_nudges(session: Session) -> None:
    home_id, (mari,) = household(session, "Mari")
    task_with_history(session, home_id, [mari, mari, mari])
    sender = MockSender()

    run(session, sender)

    # Guards `counted - did_some` leaving nobody: with one counted Member there is no target and no
    # nudge is spent.
    assert reached(sender) == {"mari"}
    assert session.exec(select(FairnessNudge)).all() == []


def test_completions_by_someone_who_left_start_no_nudge(session: Session) -> None:
    home_id, (mari, jonas, otto) = household(session, "Mari", "Jonas", "Otto")
    task_with_history(session, home_id, [otto, otto, otto])
    membership = session.exec(
        select(Membership).where(Membership.home_id == home_id, Membership.user_id == otto.id)
    ).one()
    session.delete(membership)
    session.commit()
    sender = MockSender()

    run(session, sender)

    # Guards `if not did_some` (AD-16): nobody current did any of the last 3, so no nudge is spent
    # (without the guard both would be targets and a row would exist).
    assert reached(sender) == {"mari", "jonas"}
    assert session.exec(select(FairnessNudge)).all() == []


def test_the_landlord_is_neither_counted_nor_targeted(session: Session) -> None:
    home_id, _kari, (anders,) = tenancy(session, "Anders")
    task_with_history(session, home_id, [anders, anders, anders])
    sender = MockSender()

    run(session, sender)

    # Guards `Membership.role.in_(DOERS)` (decision 2): one Tenant is one counted Member.
    assert reached(sender) == {"kari", "anders"}
    assert session.exec(select(FairnessNudge)).all() == []


def test_the_landlord_keeps_the_regular_reminder_on_a_nudge_day(session: Session) -> None:
    home_id, _kari, (anders, siv) = tenancy(session, "Anders", "Siv")
    task_with_history(session, home_id, [anders, anders, anders])
    sender = MockSender()

    run(session, sender)

    # Guards `user_id not in counted_by_instance[...]` in `apply_nudges`: Siv is nudged, Anders
    # (did the work) is skipped, and the Landlord, who did not do the work either, still gets the
    # regular reminder.
    assert reached(sender) == {"siv", "kari"}


def test_a_member_who_joined_after_the_window_is_not_singled_out(session: Session) -> None:
    home_id, (mari, jonas) = household(session, "Mari", "Jonas")
    task_with_history(session, home_id, [mari, mari, mari])
    # Jonas joined after the last of the three completions.
    session.execute(
        update(Membership)
        .where(col(Membership.user_id) == jonas.id)
        .values(created_at=datetime(2026, 11, 1, tzinfo=UTC))
    )
    session.commit()
    sender = MockSender()

    run(session, sender)

    # Guards `to_utc(joined) <= to_utc(since)` in `_counted_members`: Jonas could not have done
    # the earlier completions, so only one Member counts and nobody is nudged.
    assert reached(sender) == {"mari", "jonas"}
    assert session.exec(select(FairnessNudge)).all() == []


def test_a_target_without_a_device_spends_no_nudge_and_everyone_is_reminded(
    session: Session,
) -> None:
    home_id, (mari, jonas) = household(session, "Mari", "Jonas")
    task_with_history(session, home_id, [mari, mari, mari])
    session.execute(delete(PushSubscription).where(col(PushSubscription.user_id) == jonas.id))
    session.commit()
    sender = MockSender()

    run(session, sender)

    # Guards `_with_devices`: a target nobody can reach would leave the instance without any
    # reminder that day, so the rule does not fire.
    assert reached(sender) == {"mari"}
    assert session.exec(select(FairnessNudge)).all() == []


def test_the_nudge_is_recorded_before_the_push_is_sent(session: Session) -> None:
    home_id, (mari, jonas) = household(session, "Mari", "Jonas")
    task_with_history(session, home_id, [mari, mari, mari])
    seen: list[int] = []

    class CheckingSender(MockSender):
        def send(self, target, message):  # type: ignore[no-untyped-def]
            seen.append(len(session.exec(select(FairnessNudge)).all()))
            return super().send(target, message)

    run(session, CheckingSender())

    # Guards the order in `apply_nudges`: the claim is committed before any send (as AD-8).
    assert seen == [1]


def test_two_members_with_no_completions_are_both_targeted(session: Session) -> None:
    home_id, (mari, jonas, sara) = household(session, "Mari", "Jonas", "Sara")
    task_with_history(session, home_id, [mari, mari, mari])
    sender = MockSender()

    run(session, sender)

    # Guards the set difference: every Member with none of the three is a target.
    assert reached(sender) == {"jonas", "sara"}


def test_the_window_is_the_last_three_completions_not_all_of_them(session: Session) -> None:
    home_id, (mari, jonas) = household(session, "Mari", "Jonas")
    task_with_history(session, home_id, [jonas, jonas, mari, mari, mari])
    sender = MockSender()

    run(session, sender)

    # Guards `.limit(WINDOW)` with the newest first: Jonas did two older ones and still counts as
    # having done none of the last three.
    assert reached(sender) == {"jonas"}


def test_a_completed_instance_is_not_due_so_nothing_is_nudged(session: Session) -> None:
    home_id, (mari, jonas) = household(session, "Mari", "Jonas")
    task = task_with_history(session, home_id, [mari, mari, mari])
    session.execute(
        update(TaskInstance)
        .where(col(TaskInstance.id) == open_instance(session, task).id)
        .values(completed_at=datetime(2026, 11, 13, 8, tzinfo=UTC), completed_by_user_id=mari.id)
    )
    session.add(TaskInstance(task_id=task.id, due_on=TODAY + timedelta(days=7)))
    session.commit()
    sender = MockSender()

    run(session, sender)

    # Guards the selection that feeds `apply_nudges` (`is_open`): a completed instance never
    # reaches the rule, so it cannot be nudged.
    assert len(sender.sent) == 0
    assert session.exec(select(FairnessNudge)).all() == []


def test_a_cadence_skipping_the_target_today_sends_no_nudge_and_claims_nothing(
    session: Session,
) -> None:
    home_id, _kari, (anders, siv) = tenancy(session, "Anders", "Siv")
    home = session.get(Home, home_id)
    assert home is not None
    home.notification_cadence_days = 7
    session.add(home)
    session.commit()
    # Overdue by 3 days and a weekly cadence: the Tenants' Must reminder is skipped today.
    task_with_history(
        session,
        home_id,
        [anders, anders, anders],
        due_on=TODAY - timedelta(days=3),
        classification="must",
    )
    sender = MockSender()

    run(session, sender)

    # Guards `reminded[instance_id]` in `apply_nudges` (decision 4): a target the cadence skips is
    # not nudged and the instance is not claimed, so the nudge can still fire on a day the
    # cadence allows. Only the Landlord, whom the cadence does not hold back, is reminded.
    assert reached(sender) == {"kari"}
    assert session.exec(select(FairnessNudge)).all() == []
    nudging = MockSender()

    # Seven days overdue is a cadence day: now Siv is nudged and Anders is skipped.
    run(session, nudging, TODAY + timedelta(days=4))

    assert reached(nudging) == {"siv", "kari"}


def test_fewer_completions_than_the_window_give_no_target() -> None:
    mari, jonas = uuid.uuid4(), uuid.uuid4()

    # Guards `len(completers) < WINDOW` and that WINDOW is the only number the rule reads.
    assert fairness.nudge_targets({mari, jonas}, [mari] * fairness.WINDOW) == {jonas}
    assert fairness.nudge_targets({mari, jonas}, [mari] * (fairness.WINDOW - 1)) == set()


def test_the_database_allows_one_nudge_per_instance(session: Session) -> None:
    home_id, (mari, jonas) = household(session, "Mari", "Jonas")
    task = task_with_history(session, home_id, [mari, mari, mari])
    instance = open_instance(session, task)
    session.add(FairnessNudge(task_instance_id=instance.id, day=TODAY))
    session.commit()
    session.add(FairnessNudge(task_instance_id=instance.id, day=TODAY))

    # Guards `pk_fairness_nudges`: at most one nudge row per instance (FR-11).
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
