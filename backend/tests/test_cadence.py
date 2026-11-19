"""Story 3.5 (FR-13, AD-8, AD-3): the Landlord's reminder cadence for a Home's Tenants.

Each test that guards a rule names the line it guards (review convention, Epic 2 retro P1).
"""

import uuid
from datetime import date, timedelta
from typing import get_args

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.domain import cadence, due_check, homes
from app.models.due_notification import DueNotification
from app.models.home import CADENCE_OPTIONS, Home
from app.models.push_subscription import PushSubscription
from app.models.task import Task, TaskInstance
from app.models.user import User
from app.push import MockSender
from app.routes.cadence import CadenceIn
from tests.helpers import auth_for, new_user

TODAY = date(2026, 11, 19)
FCM = "https://fcm.googleapis.com/fcm/send/"


def landlord_home(session: Session) -> tuple[uuid.UUID, User, User]:
    """A Landlord Home with Kari (landlord) and Anders (tenant), each with one device."""
    kari = new_user(session, "Kari")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    anders = new_user(session, "Anders")
    homes.add_member(session, home, anders)
    for user, name in ((kari, "kari"), (anders, "anders")):
        session.add(PushSubscription(user_id=user.id, endpoint=FCM + name, p256dh="k", auth="a"))
    session.commit()
    return home.id, kari, anders


def add_task(
    session: Session, home_id: uuid.UUID, name: str, days_ago: int, classification: str = "must"
) -> Task:
    task = Task(home_id=home_id, name=name, classification=classification, frequency_days=7)
    session.add(task)
    session.flush()
    session.add(TaskInstance(task_id=task.id, due_on=TODAY - timedelta(days=days_ago)))
    session.commit()
    return task


def set_days(session: Session, home_id: uuid.UUID, days: int) -> None:
    cadence.set_cadence(session, home_id, days)


def reminded(session: Session) -> dict[str, list[str]]:
    """Task names each device was told about in one run, by device name."""
    sender = MockSender()
    due_check.run_due_check(session, sender, TODAY)
    told: dict[str, list[str]] = {}
    for target, message in sender.sent:
        told.setdefault(target.endpoint.removeprefix(FCM), []).append(message.title)
    return told


@pytest.mark.parametrize(
    ("days", "days_ago", "tenant_told"),
    [
        (1, 0, True),
        (1, 3, True),
        (2, 0, True),
        (2, 4, True),
        (2, 3, False),
        (7, 0, True),
        (7, 7, True),
        (7, 6, False),
        (7, 8, False),
    ],
)
def test_a_tenant_is_reminded_about_a_must_task_only_on_cadence_days(
    session: Session, days: int, days_ago: int, tenant_told: bool
) -> None:
    home_id, _kari, _anders = landlord_home(session)
    add_task(session, home_id, "Rens sluket", days_ago)
    set_days(session, home_id, days)

    told = reminded(session)

    # Guards `not reminder_day(due_on, today, days)` in due_check._due_by_member.
    assert ("anders" in told) is tenant_told


def test_a_should_task_keeps_the_daily_rule_for_a_tenant(session: Session) -> None:
    home_id, _kari, _anders = landlord_home(session)
    add_task(session, home_id, "Avkalk vannkokeren", 3, classification="should")
    set_days(session, home_id, 7)

    # Guards `classification == "must"`: the cadence is for Må tasks only.
    assert reminded(session)["anders"] == ["Avkalk vannkokeren"]


def test_the_landlord_keeps_the_daily_rule_whatever_the_cadence(session: Session) -> None:
    home_id, _kari, _anders = landlord_home(session)
    add_task(session, home_id, "Rens sluket", 3)
    set_days(session, home_id, 7)

    told = reminded(session)

    # Guards `role == "tenant"`: only Tenants follow the cadence.
    assert told["kari"] == ["Rens sluket"]
    assert "anders" not in told


def test_a_tenant_gets_one_push_for_the_tasks_that_fall_on_the_day(session: Session) -> None:
    home_id, _kari, _anders = landlord_home(session)
    add_task(session, home_id, "Rens sluket", 4)
    add_task(session, home_id, "Tøm sluket", 3)
    set_days(session, home_id, 2)

    # Only the first task falls on a reminder day, so the push names it and nothing else.
    assert reminded(session)["anders"] == ["Rens sluket"]


def test_a_cadence_is_per_home(session: Session) -> None:
    home_id, _kari, _anders = landlord_home(session)
    other = new_user(session, "Berit")
    other_home = homes.create_home(session, other, name="Torget 1", type="landlord").home
    olav = new_user(session, "Olav")
    homes.add_member(session, other_home, olav)
    session.add(PushSubscription(user_id=olav.id, endpoint=FCM + "olav", p256dh="k", auth="a"))
    session.commit()
    add_task(session, home_id, "Rens sluket", 3)
    add_task(session, other_home.id, "Vask gulv", 3)
    set_days(session, home_id, 7)

    told = reminded(session)

    # Guards the join on `Home.id == Membership.home_id`: the other Home stays on daily.
    assert "anders" not in told
    assert told["olav"] == ["Vask gulv"]


def test_a_new_home_is_on_the_daily_cadence(session: Session) -> None:
    home_id, _kari, _anders = landlord_home(session)

    home = session.get(Home, home_id)
    assert home is not None
    # Guards DEFAULT_CADENCE_DAYS: a Home that never set one keeps FR-10's daily reminder.
    assert home.notification_cadence_days == 1


def test_a_cadence_change_leaves_the_task_frequency_and_due_dates_alone(session: Session) -> None:
    home_id, _kari, _anders = landlord_home(session)
    task = add_task(session, home_id, "Rens sluket", 4)

    set_days(session, home_id, 7)

    session.expire_all()
    stored = session.get(Task, task.id)
    instance = session.exec(select(TaskInstance).where(TaskInstance.task_id == task.id)).one()
    # Guards the independence of FR-13 from FR-8/FR-9.
    assert stored is not None
    assert (stored.frequency_days, instance.due_on) == (7, TODAY - timedelta(days=4))


@pytest.mark.parametrize("days", [0, 3, 14, -1])
def test_the_domain_refuses_days_outside_the_options(session: Session, days: int) -> None:
    home_id, _kari, _anders = landlord_home(session)

    # Guards `if days not in CADENCE_OPTIONS`.
    with pytest.raises(cadence.InvalidCadence):
        cadence.set_cadence(session, home_id, days)
    home = session.get(Home, home_id)
    assert home is not None
    assert home.notification_cadence_days == 1


def test_the_database_refuses_unknown_days(session: Session) -> None:
    with pytest.raises(IntegrityError, match="ck_homes_notification_cadence_days"):
        session.execute(
            text(
                "INSERT INTO homes (id, name, type, notification_cadence_days, created_at)"
                " VALUES (:id, 'x', 'landlord', 3, :t)"
            ),
            {"id": uuid.uuid4().hex, "t": "2026-11-19 12:00:00"},
        )


def test_the_landlord_saves_a_cadence_and_home_out_says_so(
    client: TestClient, session: Session
) -> None:
    home_id, kari, _anders = landlord_home(session)
    headers = auth_for(client, kari.email)

    response = client.put(
        f"/api/homes/{home_id}/notification-cadence", json={"days": 2}, headers=headers
    )

    assert response.status_code == 200
    assert response.json() == {"notification_cadence_days": 2}
    listed = client.get("/api/homes", headers=headers).json()["homes"][0]
    assert (listed["notification_cadence_days"], listed["can_set_cadence"]) == (2, True)


@pytest.mark.parametrize("days", [0, 3, "ofte", None])
def test_a_bad_value_is_422_and_nothing_is_saved(
    client: TestClient, session: Session, days: object
) -> None:
    home_id, kari, _anders = landlord_home(session)

    response = client.put(
        f"/api/homes/{home_id}/notification-cadence",
        json={"days": days},
        headers=auth_for(client, kari.email),
    )

    # Guards the Literal[1, 2, 7] on CadenceIn.
    assert response.status_code == 422
    session.expire_all()
    home = session.get(Home, home_id)
    assert home is not None
    assert home.notification_cadence_days == 1


def test_a_tenant_may_not_change_the_cadence(client: TestClient, session: Session) -> None:
    home_id, _kari, anders = landlord_home(session)
    headers = auth_for(client, anders.email)

    response = client.put(
        f"/api/homes/{home_id}/notification-cadence", json={"days": 7}, headers=headers
    )

    # Guards the Landlord alias on the route, and that the flag says no for a Tenant.
    assert response.status_code == 403
    session.expire_all()
    home = session.get(Home, home_id)
    assert home is not None
    assert home.notification_cadence_days == 1
    assert client.get("/api/homes", headers=headers).json()["homes"][0]["can_set_cadence"] is False


def test_a_household_member_and_a_stranger_get_the_same_403(
    client: TestClient, session: Session
) -> None:
    home_id, _kari, anders = landlord_home(session)
    tenant = client.put(
        f"/api/homes/{home_id}/notification-cadence",
        json={"days": 7},
        headers=auth_for(client, anders.email),
    )
    stranger = new_user(session, "Fremmed")

    response = client.put(
        f"/api/homes/{home_id}/notification-cadence",
        json={"days": 7},
        headers=auth_for(client, stranger.email),
    )

    # Guards require_role's single answer: no Membership gives the same 403 as the wrong Role,
    # and the Home is left alone.
    assert response.status_code == 403
    assert response.json() == tenant.json()
    session.expire_all()
    home = session.get(Home, home_id)
    assert home is not None
    assert home.notification_cadence_days == 1


def test_a_household_home_member_may_not_change_it(client: TestClient, session: Session) -> None:
    hanne = new_user(session, "Hanne")
    household = homes.create_home(session, hanne, name="Kollektivet", type="household").home

    response = client.put(
        f"/api/homes/{household.id}/notification-cadence",
        json={"days": 2},
        headers=auth_for(client, hanne.email),
    )

    # Guards the Landlord alias: a Household Member has a Membership but not the right.
    assert response.status_code == 403
    session.expire_all()
    stored = session.get(Home, household.id)
    assert stored is not None
    assert stored.notification_cadence_days == 1


def test_the_route_the_database_and_the_domain_offer_the_same_options() -> None:
    literal = get_args(CadenceIn.model_fields["days"].annotation)
    constraint = next(
        c
        for c in Home.__table__.constraints
        if c.name == "ck_homes_notification_cadence_days"  # type: ignore[attr-defined]
    )

    # Guards the options being written once: adding one to CADENCE_OPTIONS must reach the route.
    assert literal == CADENCE_OPTIONS
    assert all(str(days) in str(constraint.sqltext) for days in CADENCE_OPTIONS)


def test_a_skipped_day_writes_no_claim_and_the_next_cadence_day_sends(session: Session) -> None:
    home_id, _kari, _anders = landlord_home(session)
    add_task(session, home_id, "Rens sluket", 3)
    set_days(session, home_id, 2)

    off_day = MockSender()
    due_check.run_due_check(session, off_day, TODAY)
    off_claims = session.exec(select(DueNotification)).all()
    on_day = MockSender()
    due_check.run_due_check(session, on_day, TODAY + timedelta(days=1))

    # Guards the filter running before the claim: the off day claims nothing for the Tenant
    # (only the Landlord's daily claim exists), and the next day is not blocked by it.
    assert [t.endpoint.removeprefix(FCM) for t, _ in off_day.sent] == ["kari"]
    assert len(off_claims) == 1
    assert sorted(t.endpoint.removeprefix(FCM) for t, _ in on_day.sent) == ["anders", "kari"]


def test_a_task_due_in_the_future_is_not_reminded_whatever_the_cadence(session: Session) -> None:
    home_id, _kari, _anders = landlord_home(session)
    add_task(session, home_id, "Rens sluket", -7)
    set_days(session, home_id, 7)

    # Guards `due_on <= today`: 7 % 7 == 0 would otherwise let a task due next week through.
    assert reminded(session) == {}
