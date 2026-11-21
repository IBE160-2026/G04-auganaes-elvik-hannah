"""Story 6.1 (FR-20, FR-24, AD-3): the Landlord Portfolio and who has one."""

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session

from app.domain import homes, portfolio
from app.models.task import Task, TaskInstance
from app.models.user import User
from tests.helpers import auth_for, new_user

TODAY = date(2026, 11, 21)


def landlord_with_homes(session: Session, *names: str) -> tuple[User, list[uuid.UUID]]:
    landlord = new_user(session, "Kari")
    ids = [homes.create_home(session, landlord, name=n, type="landlord").home.id for n in names]
    return landlord, ids


def add_task(
    session: Session,
    home_id: uuid.UUID,
    name: str,
    due_on: date,
    classification: str = "must",
    archived: bool = False,
) -> Task:
    task = Task(home_id=home_id, name=name, classification=classification, frequency_days=7)
    if archived:
        task.archived_at = TODAY
    session.add(task)
    session.flush()
    session.add(TaskInstance(task_id=task.id, due_on=due_on))
    session.commit()
    return task


def row_of(rows: list[portfolio.PortfolioHome], home_id: uuid.UUID) -> portfolio.PortfolioHome:
    return next(r for r in rows if r.home.id == home_id)


def test_overdue_must_means_behind_with_the_task_listed(session: Session) -> None:
    landlord, (a, _b) = landlord_with_homes(session, "A", "B")
    add_task(session, a, "Støvsuge", TODAY - timedelta(days=3))
    add_task(session, a, "Vaske bad", TODAY - timedelta(days=9))

    row = row_of(portfolio.portfolio_of(session, landlord, TODAY), a)

    assert row.status == "behind"
    assert [(t.name, t.days_overdue) for t in row.overdue] == [("Vaske bad", 9), ("Støvsuge", 3)]


def test_overdue_should_does_not_make_a_home_behind(session: Session) -> None:
    landlord, (a, _b) = landlord_with_homes(session, "A", "B")
    add_task(session, a, "Vaske vinduer", TODAY - timedelta(days=5), classification="should")

    assert row_of(portfolio.portfolio_of(session, landlord, TODAY), a).status == "on_track"


def test_due_today_is_not_overdue_and_counts_as_due_soon(session: Session) -> None:
    landlord, (a, _b) = landlord_with_homes(session, "A", "B")
    add_task(session, a, "Støvsuge", TODAY)
    add_task(session, a, "Vaske bad", TODAY + timedelta(days=3))
    add_task(session, a, "Mopp", TODAY + timedelta(days=4))

    row = row_of(portfolio.portfolio_of(session, landlord, TODAY), a)

    assert (row.status, row.due_soon_count) == ("on_track", 2)


def test_a_home_without_tasks_is_not_set_up_never_on_track(session: Session) -> None:
    landlord, (a, _b) = landlord_with_homes(session, "A", "B")

    assert row_of(portfolio.portfolio_of(session, landlord, TODAY), a).status == "not_set_up"


def test_an_archived_task_never_counts(session: Session) -> None:
    landlord, (a, _b) = landlord_with_homes(session, "A", "B")
    add_task(session, a, "Støvsuge", TODAY - timedelta(days=3), archived=True)

    row = row_of(portfolio.portfolio_of(session, landlord, TODAY), a)

    # Task Setup has run (has_tasks), and the archived Task is not read for behaviour (FR-24).
    assert (row.status, row.overdue) == ("on_track", [])


def test_rows_are_behind_first_then_by_name(session: Session) -> None:
    landlord, (a, b, c) = landlord_with_homes(session, "Bakgata", "Aveny", "Cecilies gate")
    add_task(session, a, "x", TODAY)
    add_task(session, b, "x", TODAY)
    add_task(session, c, "x", TODAY - timedelta(days=1))

    rows = portfolio.portfolio_of(session, landlord, TODAY)

    assert [r.home.name for r in rows] == ["Cecilies gate", "Aveny", "Bakgata"]


def test_only_the_callers_landlord_homes_are_listed(session: Session) -> None:
    landlord, (a, b) = landlord_with_homes(session, "A", "B")
    _other, (c, _d) = landlord_with_homes(session, "C", "D")
    add_task(session, c, "x", TODAY - timedelta(days=1))
    household = homes.create_home(session, landlord, name="Husstand", type="household").home
    add_task(session, household.id, "x", TODAY - timedelta(days=1))

    rows = portfolio.portfolio_of(session, landlord, TODAY)

    assert {r.home.id for r in rows} == {a, b}


@pytest.mark.parametrize("count", [0, 1])
def test_fewer_than_two_landlord_homes_has_no_portfolio(session: Session, count: int) -> None:
    landlord = new_user(session, "Kari")
    for i in range(count):
        homes.create_home(session, landlord, name=f"H{i}", type="landlord")

    assert not portfolio.has_portfolio(homes.homes_for(session, landlord))
    with pytest.raises(portfolio.NotInPortfolio):
        portfolio.portfolio_of(session, landlord, TODAY)


def test_a_tenant_and_a_household_member_have_no_portfolio(session: Session) -> None:
    landlord, (a, b) = landlord_with_homes(session, "A", "B")
    tenant = new_user(session, "Anders")
    for home_id in (a, b):
        home = next(h.home for h in homes.homes_for(session, landlord) if h.home.id == home_id)
        if home_id == a:
            homes.add_member(session, home, tenant)

    assert not portfolio.has_portfolio(homes.homes_for(session, tenant))


def queries_for(session: Session, engine: Engine, home_count: int) -> int:
    landlord, ids = landlord_with_homes(session, *(f"H{i}" for i in range(home_count)))
    for home_id in ids:
        add_task(session, home_id, "x", TODAY - timedelta(days=1))
    session.refresh(landlord)
    seen: list[str] = []

    def count(_c: object, _cur: object, statement: str, *_a: object) -> None:
        seen.append(statement)

    event.listen(engine, "before_cursor_execute", count)
    try:
        portfolio.portfolio_of(session, landlord, TODAY)
    finally:
        event.remove(engine, "before_cursor_execute", count)
    return len(seen)


def test_the_number_of_queries_does_not_grow_with_the_homes(
    session: Session, engine: Engine
) -> None:
    # Guards portfolio_of's «two queries for the whole list, never one per Home».
    assert queries_for(session, engine, 6) == queries_for(session, engine, 2)


def test_route_answers_the_portfolio_and_homes_say_has_portfolio(
    client: TestClient, session: Session
) -> None:
    landlord, (a, _b) = landlord_with_homes(session, "A", "B")
    headers = auth_for(client, landlord.email)

    portfolio_body = client.get("/api/portfolio", headers=headers)
    homes_body = client.get("/api/homes", headers=headers)

    assert portfolio_body.status_code == 200
    assert {h["status"] for h in portfolio_body.json()["homes"]} == {"not_set_up"}
    assert homes_body.json()["has_portfolio"] is True
    assert str(a) in {h["home_id"] for h in portfolio_body.json()["homes"]}


@pytest.mark.parametrize("kind", ["one_home", "tenant"])
def test_route_is_403_without_a_portfolio(client: TestClient, session: Session, kind: str) -> None:
    landlord, (a, _b) = landlord_with_homes(session, "A", "B")
    if kind == "one_home":
        user = new_user(session, "Ola")
        homes.create_home(session, user, name="Alene", type="landlord")
    else:
        user = new_user(session, "Anders")
        home = next(h.home for h in homes.homes_for(session, landlord) if h.home.id == a)
        homes.add_member(session, home, user)

    response = client.get("/api/portfolio", headers=auth_for(client, user.email))

    assert response.status_code == 403
    homes_body = client.get("/api/homes", headers=auth_for(client, user.email))
    assert homes_body.json()["has_portfolio"] is False


def test_route_needs_a_session(client: TestClient) -> None:
    assert client.get("/api/portfolio").status_code == 401
