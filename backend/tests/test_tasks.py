"""Story 2.1 (FR-4, FR-8, AD-2, AD-6): domain/tasks, one test per backend row of the matrix."""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.clock import utc_now
from app.domain import homes, tasks
from app.domain.task_types import TASK_TYPES
from app.models.membership import Membership
from app.models.task import Task, TaskInstance
from tests.helpers import count, new_user

TODAY = date(2026, 11, 9)


def all_choices() -> list[tasks.TaskChoice]:
    return [tasks.TaskChoice(t.key, t.classification, t.frequency_days) for t in TASK_TYPES]


def membership_of(session: Session, home_id: uuid.UUID, user_id: uuid.UUID) -> Membership:
    return session.exec(
        select(Membership).where(Membership.home_id == home_id, Membership.user_id == user_id)
    ).one()


def household(session: Session) -> Membership:
    user = new_user(session, "Mari")
    home = homes.create_home(session, user, name="Kollektivet", type="household").home
    return membership_of(session, home.id, user.id)


def landlord_and_tenant(session: Session) -> tuple[Membership, Membership]:
    kari = new_user(session, "Kari")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    anders = new_user(session, "Anders")
    homes.add_member(session, home, anders)
    return membership_of(session, home.id, kari.id), membership_of(session, home.id, anders.id)


def written(session: Session) -> tuple[int, int]:
    return count(session, Task), count(session, TaskInstance)


def test_accept_as_is_creates_every_entry_with_one_instance(session: Session) -> None:
    member = household(session)

    listed = tasks.set_up_tasks(session, member, all_choices(), today=TODAY)

    assert written(session) == (8, 8)
    by_key = {row.task.task_type: row for row in listed}
    for entry in TASK_TYPES:
        row = by_key[entry.key]
        assert row.task.name == entry.name
        assert (row.task.classification, row.task.frequency_days) == (
            entry.classification,
            entry.frequency_days,
        )
        assert row.due_on == TODAY + timedelta(days=entry.frequency_days)
        assert row.task.home_id == member.home_id


def test_today_defaults_to_the_utc_date(session: Session) -> None:
    [row] = tasks.set_up_tasks(session, household(session), [tasks.TaskChoice("gulv", "should", 7)])
    assert row.due_on == utc_now().date() + timedelta(days=7)


def test_adjusted_values_are_stored(session: Session) -> None:
    member = household(session)
    choices = [
        tasks.TaskChoice("stekeovn", "must", 60) if c.task_type == "stekeovn" else c
        for c in all_choices()
    ]

    tasks.set_up_tasks(session, member, choices, today=TODAY)

    stekeovn = session.exec(select(Task).where(Task.task_type == "stekeovn")).one()
    assert (stekeovn.classification, stekeovn.frequency_days) == ("must", 60)


def test_unticked_tasks_are_not_created(session: Session) -> None:
    member = household(session)
    choices = [c for c in all_choices() if c.task_type not in {"stekeovn", "dusjfuger"}]

    listed = tasks.set_up_tasks(session, member, choices, today=TODAY)

    assert len(listed) == 6 and written(session) == (6, 6)
    assert {r.task.task_type for r in listed}.isdisjoint({"stekeovn", "dusjfuger"})


@pytest.mark.parametrize(
    ("choices", "message"),
    [
        ([], tasks.NO_TASKS_CHOSEN),
        ([tasks.TaskChoice("finnes-ikke", "must", 7)], "Ukjent oppgave: «finnes-ikke»."),
        (
            [tasks.TaskChoice("gulv", "must", 7), tasks.TaskChoice("gulv", "should", 14)],
            "Oppgaven «gulv» er valgt mer enn én gang.",
        ),
        ([tasks.TaskChoice("gulv", "should", 10)], tasks.BAD_FREQUENCY),
        ([tasks.TaskChoice("gulv", "maybe", 7)], tasks.BAD_CLASSIFICATION),
    ],
    ids=["empty", "unknown", "duplicate", "frequency-10", "maybe"],
)
def test_bad_choices_create_nothing(
    session: Session, choices: list[tasks.TaskChoice], message: str
) -> None:
    member = household(session)
    with pytest.raises(tasks.InvalidTaskChoices) as caught:
        tasks.set_up_tasks(session, member, choices, today=TODAY)
    assert caught.value.message == message
    assert written(session) == (0, 0)


def test_a_valid_row_after_a_bad_one_is_not_written_either(session: Session) -> None:
    member = household(session)
    with pytest.raises(tasks.InvalidTaskChoices):
        tasks.set_up_tasks(
            session,
            member,
            [tasks.TaskChoice("gulv", "should", 14), tasks.TaskChoice("x", "must", 7)],
            today=TODAY,
        )
    assert written(session) == (0, 0)


def test_second_setup_creates_nothing(session: Session) -> None:
    member = household(session)
    tasks.set_up_tasks(session, member, all_choices()[:2], today=TODAY)

    with pytest.raises(tasks.TasksAlreadySetUp):
        tasks.set_up_tasks(session, member, all_choices()[2:], today=TODAY)

    assert written(session) == (2, 2)


def test_overlapping_race_is_already_set_up_not_an_integrity_error(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two setups that both passed the empty check: the unique (home_id, task_type) stops one.

    On Postgres the Home row lock serialises them, so the second sees Tasks; SQLite has no lock,
    so the check is faked here. A disjoint race is not caught on SQLite (accepted risk).
    """
    member = household(session)
    tasks.set_up_tasks(session, member, [tasks.TaskChoice("gulv", "should", 14)], today=TODAY)
    monkeypatch.setattr(tasks, "has_tasks", lambda *_: False)

    with pytest.raises(tasks.TasksAlreadySetUp):
        tasks.set_up_tasks(session, member, all_choices(), today=TODAY)

    assert written(session) == (1, 1)


def test_landlord_home_without_tenants_can_be_set_up(session: Session) -> None:
    kari = new_user(session, "Kari")
    home = homes.create_home(session, kari, name="Storgata 1", type="landlord").home

    listed = tasks.set_up_tasks(session, membership_of(session, home.id, kari.id), all_choices())

    assert len(listed) == 8


def test_a_tenant_may_not_set_up(session: Session) -> None:
    _, tenant = landlord_and_tenant(session)
    assert not tasks.can_set_up_tasks(tenant.role)
    with pytest.raises(ValueError, match="may not set up"):
        tasks.set_up_tasks(session, tenant, all_choices())
    assert written(session) == (0, 0)


@pytest.mark.parametrize(
    ("role", "allowed"), [("household_member", True), ("landlord", True), ("tenant", False)]
)
def test_who_may_set_up(role: str, allowed: bool) -> None:
    assert tasks.can_set_up_tasks(role) is allowed


def test_tasks_are_listed_must_first_then_by_due_date_then_name(session: Session) -> None:
    member = household(session)
    tasks.set_up_tasks(
        session,
        member,
        [
            tasks.TaskChoice("gulv", "should", 7),
            tasks.TaskChoice("stekeovn", "should", 7),
            tasks.TaskChoice("vask-badet", "must", 365),
            tasks.TaskChoice("rens-sluket", "must", 30),
            tasks.TaskChoice("dusjfuger", "should", 14),
        ],
        today=TODAY,
    )

    assert [r.task.name for r in tasks.tasks_of(session, member.home_id)] == [
        "Rens sluket",
        "Vask badet grundig",
        "Støvsug og vask gulvene",
        "Vask stekeovnen",
        "Vask fugene i dusjen",
    ]


def test_next_due_is_the_earliest_instance(session: Session) -> None:
    member = household(session)
    [row] = tasks.set_up_tasks(
        session, member, [tasks.TaskChoice("gulv", "should", 14)], today=TODAY
    )
    session.add(TaskInstance(task_id=row.task.id, due_on=TODAY + timedelta(days=28)))
    session.commit()

    [listed] = tasks.tasks_of(session, member.home_id)
    assert listed.due_on == TODAY + timedelta(days=14)


def test_tasks_of_another_home_are_not_listed(session: Session) -> None:
    mine = household(session)
    other = household(session)
    tasks.set_up_tasks(session, other, all_choices(), today=TODAY)

    assert tasks.tasks_of(session, mine.home_id) == []
    assert not tasks.has_tasks(session, mine.home_id)
    assert tasks.has_tasks(session, other.home_id)
    assert tasks.home_ids_with_tasks(session, [mine.home_id, other.home_id]) == {other.home_id}
    assert tasks.home_ids_with_tasks(session, []) == set()


@pytest.mark.parametrize(
    ("classification", "frequency_days", "constraint"),
    [("maybe", 7, "ck_tasks_classification"), ("must", 0, "ck_tasks_frequency_days")],
)
def test_check_constraints(
    session: Session, classification: str, frequency_days: int, constraint: str
) -> None:
    member = household(session)
    session.add(
        Task(
            home_id=member.home_id,
            task_type="gulv",
            name="x",
            classification=classification,
            frequency_days=frequency_days,
        )
    )
    with pytest.raises(IntegrityError, match=constraint):
        session.commit()


def test_one_instance_per_task_and_date(session: Session) -> None:
    member = household(session)
    [row] = tasks.set_up_tasks(
        session, member, [tasks.TaskChoice("gulv", "should", 7)], today=TODAY
    )
    session.add(TaskInstance(task_id=row.task.id, due_on=row.due_on))
    with pytest.raises(IntegrityError):
        session.commit()


def test_setup_leaves_fr3_unchanged(session: Session) -> None:
    landlord, _ = landlord_and_tenant(session)
    tasks.set_up_tasks(session, landlord, all_choices(), today=TODAY)
    tasks.set_up_tasks(session, household(session), all_choices(), today=TODAY)
    assert homes.fr3_violations(session) == []
