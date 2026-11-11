"""Story 2.1 (FR-4, FR-8, AD-2, AD-6) and Story 2.3 (FR-5, FR-8): domain/tasks, one test per
backend row of the matrices.
"""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

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


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (-30, "overdue"),
        (-1, "overdue"),
        (0, "due_soon"),
        (1, "due_soon"),
        (tasks.DUE_SOON_DAYS, "due_soon"),
        (tasks.DUE_SOON_DAYS + 1, "later"),
        (365, "later"),
    ],
)
def test_due_status_boundaries(offset: int, expected: str) -> None:
    assert tasks.due_status(TODAY + timedelta(days=offset), TODAY) == expected


def test_due_soon_is_three_days_by_team_decision() -> None:
    # Story 2.2, decision 1: with 7, a weekly Task would always be due soon.
    assert tasks.DUE_SOON_DAYS == 3


def test_a_must_due_much_later_is_listed_above_an_overdue_should(session: Session) -> None:
    member = household(session)
    # Set up 8 days ago: the Should (7 days) is a day overdue, the Must (30 days) due in 22.
    tasks.set_up_tasks(
        session,
        member,
        [tasks.TaskChoice("gulv", "should", 7), tasks.TaskChoice("rens-sluket", "must", 30)],
        today=TODAY - timedelta(days=8),
    )

    listed = tasks.tasks_of(session, member.home_id)
    assert [(r.task.classification, tasks.due_status(r.due_on, TODAY)) for r in listed] == [
        ("must", "later"),
        ("should", "overdue"),
    ]


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


# Story 2.3 (FR-5, FR-8, issue #40): adjust_task.


def one_task(
    session: Session, member: Membership, frequency: int = 30, today: date = TODAY
) -> Task:
    [row] = tasks.set_up_tasks(
        session, member, [tasks.TaskChoice("rens-sluket", "must", frequency)], today=today
    )
    return row.task


def due_dates(session: Session, task_id: uuid.UUID) -> list[date]:
    return list(
        session.exec(
            select(TaskInstance.due_on)
            .where(TaskInstance.task_id == task_id)
            .order_by(col(TaskInstance.due_on))
        ).all()
    )


def test_classification_only_leaves_the_date_alone(session: Session) -> None:
    member = household(session)
    task = one_task(session, member)

    row = tasks.adjust_task(session, member, task.id, classification="should")

    assert row.task.classification == "should"
    assert row.task.frequency_days == 30
    assert row.due_on == TODAY + timedelta(days=30)
    assert due_dates(session, task.id) == [TODAY + timedelta(days=30)]


def test_a_longer_frequency_moves_the_open_date_later(session: Session) -> None:
    landlord, _ = landlord_and_tenant(session)
    # Kari set it up on 2026-11-01 with 30 days: open due 2026-12-01.
    task = one_task(session, landlord, 30, today=date(2026, 11, 1))

    row = tasks.adjust_task(session, landlord, task.id, frequency_days=60)

    assert row.task.frequency_days == 60
    assert row.due_on == date(2026, 12, 31)
    assert due_dates(session, task.id) == [date(2026, 12, 31)]


def test_a_shorter_frequency_past_today_makes_it_overdue(session: Session) -> None:
    member = household(session)
    today = utc_now().date()
    task = one_task(session, member, 365, today=today - timedelta(days=65))

    row = tasks.adjust_task(session, member, task.id, frequency_days=7)

    assert row.due_on == today - timedelta(days=58)
    assert tasks.due_status(row.due_on, today) == "overdue"


def test_both_fields_at_once(session: Session) -> None:
    member = household(session)
    task = one_task(session, member, 30)

    row = tasks.adjust_task(session, member, task.id, classification="should", frequency_days=14)

    assert (row.task.classification, row.task.frequency_days) == ("should", 14)
    assert row.due_on == TODAY + timedelta(days=14)


def test_equal_values_write_nothing(session: Session) -> None:
    member = household(session)
    task = one_task(session, member, 30)
    created = (task.classification, task.frequency_days, due_dates(session, task.id))

    for _ in range(2):
        row = tasks.adjust_task(session, member, task.id, classification="must", frequency_days=30)
        assert (row.task.classification, row.task.frequency_days) == ("must", 30)
        assert row.due_on == TODAY + timedelta(days=30)

    stored = session.exec(select(Task).where(Task.id == task.id)).one()
    assert (stored.classification, stored.frequency_days, due_dates(session, task.id)) == created


def test_resending_a_new_frequency_does_not_move_the_date_twice(session: Session) -> None:
    member = household(session)
    task = one_task(session, member, 30)

    tasks.adjust_task(session, member, task.id, frequency_days=60)
    row = tasks.adjust_task(session, member, task.id, frequency_days=60)

    assert row.due_on == TODAY + timedelta(days=60)


def test_only_the_earliest_instance_moves(session: Session) -> None:
    member = household(session)
    task = one_task(session, member, 30)
    later = TODAY + timedelta(days=200)
    session.add(TaskInstance(task_id=task.id, due_on=later))
    session.commit()

    row = tasks.adjust_task(session, member, task.id, frequency_days=7)

    assert row.due_on == TODAY + timedelta(days=7)
    assert due_dates(session, task.id) == [TODAY + timedelta(days=7), later]


def test_other_tasks_and_homes_are_untouched(session: Session) -> None:
    member = household(session)
    listed = tasks.set_up_tasks(session, member, all_choices(), today=TODAY)
    other = household(session)
    other_listed = tasks.set_up_tasks(session, other, all_choices(), today=TODAY)
    target = next(r.task for r in listed if r.task.task_type == "rens-sluket")
    before = {
        (r.task.id, r.task.classification, r.task.frequency_days, r.due_on)
        for r in listed + other_listed
        if r.task.id != target.id
    }

    tasks.adjust_task(session, member, target.id, classification="should", frequency_days=7)

    after = {
        (r.task.id, r.task.classification, r.task.frequency_days, r.due_on)
        for r in tasks.tasks_of(session, member.home_id) + tasks.tasks_of(session, other.home_id)
        if r.task.id != target.id
    }
    assert after == before


def test_a_classification_change_moves_the_task_between_tiers(session: Session) -> None:
    member = household(session)
    tasks.set_up_tasks(
        session,
        member,
        [tasks.TaskChoice("gulv", "should", 7), tasks.TaskChoice("rens-sluket", "must", 30)],
        today=TODAY,
    )
    sluket = session.exec(select(Task).where(Task.task_type == "rens-sluket")).one()

    tasks.adjust_task(session, member, sluket.id, classification="should")

    assert [r.task.task_type for r in tasks.tasks_of(session, member.home_id)] == [
        "gulv",
        "rens-sluket",
    ]


def test_another_homes_task_or_an_unknown_id_is_not_found(session: Session) -> None:
    member = household(session)
    other = household(session)
    foreign = one_task(session, other)

    for task_id in (foreign.id, uuid.uuid4()):
        with pytest.raises(tasks.TaskNotFound):
            tasks.adjust_task(session, member, task_id, classification="should")
    assert session.exec(select(Task).where(Task.id == foreign.id)).one().classification == "must"


def test_nothing_given_is_no_change(session: Session) -> None:
    member = household(session)
    task = one_task(session, member)
    with pytest.raises(tasks.NothingToChange) as exc:
        tasks.adjust_task(session, member, task.id)
    assert exc.value.message == tasks.NO_CHANGE == "Ingen endring."


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"classification": "maybe"}, tasks.BAD_CLASSIFICATION),
        ({"frequency_days": 10}, tasks.BAD_FREQUENCY),
    ],
)
def test_values_outside_the_catalog_rules_are_refused(
    session: Session, fields: dict, message: str
) -> None:
    member = household(session)
    task = one_task(session, member)
    with pytest.raises(tasks.InvalidTaskChoices, match=message):
        tasks.adjust_task(session, member, task.id, **fields)


def test_a_tenant_may_not_adjust(session: Session) -> None:
    landlord, tenant = landlord_and_tenant(session)
    task = one_task(session, landlord)
    with pytest.raises(ValueError, match="may not adjust"):
        tasks.adjust_task(session, tenant, task.id, classification="should")
    assert session.exec(select(Task).where(Task.id == task.id)).one().classification == "must"


@pytest.mark.parametrize(
    ("role", "allowed"),
    [("household_member", True), ("landlord", True), ("tenant", False)],
)
def test_who_may_adjust(role: str, allowed: bool) -> None:
    assert tasks.can_adjust_tasks(role) is allowed
    assert tasks.ADJUST_ROLES == tasks.SETUP_ROLES
