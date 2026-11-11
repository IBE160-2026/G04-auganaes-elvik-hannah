"""The example Homes' Tasks (Story 2.1, FR-4, FR-8, FR-22; decisions 4 and 7, 2026-11-09).

Both example Homes get every catalog entry with its recommended values, set up through the
domain as of an earlier date, so the lists show tasks due soon and overdue right after seeding.
Each Home is found by its creator's Membership and its name (as seed/homes.py does), so a Home
the homes step skipped is never confused with another Home of the same user. Never deletes or
overwrites: a Home that already has Tasks is left as it is.
"""

from datetime import timedelta

from sqlmodel import Session, select

from app.clock import utc_now
from app.domain import task_types, tasks
from app.models.membership import Membership
from app.seed.homes import (
    CREATOR_EMAIL,
    EXAMPLE_HOME_NAME,
    LANDLORD_EMAIL,
    LANDLORD_HOME_NAME,
    _own_home,
    _user,
)

# (creator, Home name, set up this many days ago). 28 and 40 days give each Home overdue tasks and,
# on the seed day, one task due soon by the 3-day rule (domain/tasks.DUE_SOON_DAYS): the 30-day
# one in the Household Home and the 42-day one in the Landlord Home, both due in 2 days. See
# tests/test_seed.py.
EXAMPLE_SETUPS: tuple[tuple[str, str, int], ...] = (
    (CREATOR_EMAIL, EXAMPLE_HOME_NAME, 28),
    (LANDLORD_EMAIL, LANDLORD_HOME_NAME, 40),
)


def _set_up(session: Session, email: str, home_name: str, days_ago: int) -> None:
    creator = _user(session, email)
    home = _own_home(session, creator, home_name)
    if home is None:
        print(f"Hoppet over oppgavene i «{home_name}»: hjemmet finnes ikke for {email}")
        return
    if tasks.has_tasks(session, home.id):
        print(f"Oppgavene i «{home_name}» er allerede satt opp")
        return
    membership = session.exec(
        select(Membership).where(Membership.user_id == creator.id, Membership.home_id == home.id)
    ).one()
    choices = [
        tasks.TaskChoice(t.key, t.classification, t.frequency_days) for t in task_types.TASK_TYPES
    ]
    today = utc_now().date() - timedelta(days=days_ago)
    created = tasks.set_up_tasks(session, membership, choices, today=today)
    print(f"Satte opp {len(created)} oppgaver i «{home_name}»")


def seed_tasks(session: Session) -> None:
    for email, home_name, days_ago in EXAMPLE_SETUPS:
        _set_up(session, email, home_name, days_ago)
