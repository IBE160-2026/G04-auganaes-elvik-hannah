"""The Landlord's Portfolio: status per Landlord Home (Story 6.1, FR-20, FR-24, AD-3).

A Home is behind when it has at least one overdue Må task (an open instance of an active Task
past its date, by `tasks.due_status` and the UTC day). A unit is its own Home, so there is one
row per Home (decision 1, 2026-11-21). A Home that has never had Tasks is «not_set_up», never
on track. The Portfolio exists for a Landlord with MIN_HOMES or more Landlord Homes: that rule
lives here and reaches the frontend as HomesOut.has_portfolio.
"""

import uuid
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Literal, NamedTuple

from sqlmodel import Session, col, select

from app.domain import tasks
from app.domain.homes import MemberHome, homes_for
from app.models.home import Home
from app.models.task import Task, TaskInstance
from app.models.user import User

MIN_HOMES = 2

PortfolioStatus = Literal["behind", "on_track", "not_set_up"]

NOT_IN_PORTFOLIO = "Du har ikke en portefølje."


class NotInPortfolio(Exception):
    """The caller is Landlord in fewer than MIN_HOMES Homes."""


class OverdueTask(NamedTuple):
    task_id: uuid.UUID
    name: str
    due_on: date
    days_overdue: int


class PortfolioHome(NamedTuple):
    home: Home
    status: PortfolioStatus
    # Overdue Må tasks, the oldest first.
    overdue: list[OverdueTask]
    # Må tasks due within DUE_SOON_DAYS, not yet overdue.
    due_soon_count: int


def landlord_homes(member_homes: Sequence[MemberHome]) -> list[Home]:
    return [m.home for m in member_homes if m.role == "landlord"]


def has_portfolio(member_homes: Sequence[MemberHome]) -> bool:
    """The one statement of who has a Portfolio."""
    return len(landlord_homes(member_homes)) >= MIN_HOMES


def portfolio_of(session: Session, user: User, today: date) -> list[PortfolioHome]:
    """One row per Landlord Home: behind first, then by name and id. Raises NotInPortfolio.

    Three queries for the whole list, never one per Home: the caller's Homes, which of them have
    Tasks (archived ones count: Task Setup has run), and the open Må instances due by today + 3.
    """
    member_homes = homes_for(session, user)
    if not has_portfolio(member_homes):
        raise NotInPortfolio
    homes = landlord_homes(member_homes)
    home_ids = [h.id for h in homes]
    set_up = tasks.home_ids_with_tasks(session, home_ids)

    rows = session.exec(
        select(Task.home_id, Task.id, Task.name, TaskInstance.due_on)
        .join(TaskInstance, col(TaskInstance.task_id) == col(Task.id))
        .where(
            col(Task.home_id).in_(home_ids),
            Task.classification == "must",
            tasks.is_active(),
            tasks.is_open(),
            # Only overdue and due-soon Må tasks are read, never the whole list.
            col(TaskInstance.due_on) <= today + timedelta(days=tasks.DUE_SOON_DAYS),
        )
        .order_by(col(TaskInstance.due_on), col(Task.name), col(Task.id))
    ).all()
    overdue: dict[uuid.UUID, list[OverdueTask]] = {}
    soon: dict[uuid.UUID, int] = {}
    for home_id, task_id, name, due_on in rows:
        state = tasks.due_status(due_on, today)
        if state == "overdue":
            overdue.setdefault(home_id, []).append(
                OverdueTask(task_id, name, due_on, (today - due_on).days)
            )
        elif state == "due_soon":
            soon[home_id] = soon.get(home_id, 0) + 1

    result = []
    for home in homes:
        late = overdue.get(home.id, [])
        if late:
            state: PortfolioStatus = "behind"
        elif home.id in set_up:
            state = "on_track"
        else:
            state = "not_set_up"
        result.append(PortfolioHome(home, state, late, soon.get(home.id, 0)))
    result.sort(key=lambda p: (p.status != "behind", p.home.name.casefold(), str(p.home.id)))
    return result
