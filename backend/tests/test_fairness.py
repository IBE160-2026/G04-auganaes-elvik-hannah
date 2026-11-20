"""Story 3.3 (FR-11, AD-9, AD-16, FR-13): the first reminder goes to whoever has not done the task.

Each test that guards a rule names the line it guards (review convention, Epic 2 retro P1).
"""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import update
from sqlmodel import Session, col, select

from app.domain import due_check, fairness, homes
from app.models.fairness_nudge import FairnessNudge
from app.models.membership import Membership
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
    return home.id, users


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

    # Guards `sent[instance_id] != today`: a nudge sent today stays in force today, so Mari is
    # not reminded by a repeated run, and nobody gets a second push.
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

    # Guards `len(counted) < 2`.
    assert reached(sender) == {"mari"}


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

    # Guards `if not did_some` (AD-16): nobody current did any of the last 3, so everyone is
    # reminded and nobody is singled out.
    assert reached(sender) == {"mari", "jonas"}


def test_the_landlord_is_neither_counted_nor_targeted(session: Session) -> None:
    kari = new_user(session, "Kari")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    anders = new_user(session, "Anders")
    homes.add_member(session, home, anders)
    device(session, kari, "kari")
    device(session, anders, "anders")
    task_with_history(session, home.id, [anders, anders, anders])
    sender = MockSender()

    run(session, sender)

    # Guards `Membership.role.in_(DOERS)` (decision 2): one Tenant is one counted Member.
    assert reached(sender) == {"kari", "anders"}


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

    assert len(sender.sent) == 0
    assert session.exec(select(FairnessNudge)).all() == []


def test_a_cadence_skipping_the_target_today_sends_no_nudge_and_claims_nothing(
    session: Session,
) -> None:
    kari = new_user(session, "Kari")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    anders = new_user(session, "Anders")
    homes.add_member(session, home, anders)
    siv = new_user(session, "Siv")
    homes.add_member(session, home, siv)
    for user in (kari, anders, siv):
        device(session, user, user.name.lower())
    home.notification_cadence_days = 7
    session.add(home)
    session.commit()
    # Overdue by 3 days and a weekly cadence: the Tenants' Must reminder is skipped today.
    task_with_history(
        session,
        home.id,
        [anders, anders, anders],
        due_on=TODAY - timedelta(days=3),
        classification="must",
    )
    sender = MockSender()

    run(session, sender)

    # Guards `targets &= {…notified…}` (decision 4): a target the cadence skips is not nudged, and
    # the instance is not claimed, so the nudge can still fire on a day the cadence allows. Only
    # the Landlord, whom the cadence does not hold back, is reminded.
    assert reached(sender) == {"kari"}
    assert session.exec(select(FairnessNudge)).all() == []


def test_the_rule_in_one_place_has_the_window_in_one_constant() -> None:
    mari, jonas = uuid.uuid4(), uuid.uuid4()

    # Guards WINDOW as the only number: changing it changes the rule without touching the text.
    assert fairness.WINDOW == 3
    assert fairness.nudge_targets({mari, jonas}, [mari] * fairness.WINDOW) == {jonas}
    assert fairness.nudge_targets({mari, jonas}, [mari] * (fairness.WINDOW - 1)) == set()


def test_the_database_allows_one_nudge_per_instance(session: Session) -> None:
    import pytest
    from sqlalchemy.exc import IntegrityError

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


def test_the_due_check_module_runs_the_nudges(session: Session) -> None:
    assert due_check.fairness is fairness
