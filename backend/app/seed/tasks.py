"""The example Homes' Tasks (Story 2.1, FR-4, FR-8, FR-22; decisions 4 and 7, 2026-11-09).

Both example Homes get every catalog entry with its recommended values, set up through the
domain as of an earlier date, so the lists show tasks due soon and overdue right after seeding.
Each Home is found by its creator's Membership and its name (as seed/homes.py does), so a Home
the homes step skipped is never confused with another Home of the same user. Never deletes or
overwrites: a Home that already has Tasks is left as it is.

Story 2.4 (FR-7, FR-17): in the run that sets up the Household Home, Jonas completes «Avkalk
vannkokeren» (60 days) two days before seeding, if he is a Member, so Mari sees «Fullført
… av Jonas» on her list right after seeding. Through complete_task_instance, like the checkbox.
"""

from datetime import timedelta

from sqlmodel import Session, select

from app.clock import utc_now
from app.domain import task_types, tasks
from app.models.home import Home
from app.models.membership import Membership
from app.seed.homes import (
    CREATOR_EMAIL,
    EXAMPLE_HOME_NAME,
    JOINER_EMAIL,
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


# Story 2.4: (who, in which Home, the Task with this Må/Bør and Frequency, how many days ago).
# The one 60-day Bør in the catalog is «Avkalk vannkokeren»; it is picked by its values, since no
# seed module names a catalog key (AD-6, tests/test_task_types.py). 60 days from two days ago is
# «later», so the completion shows; the 30-day Task stays due soon (tests/test_seed.py).
EXAMPLE_COMPLETION = (JOINER_EMAIL, EXAMPLE_HOME_NAME, ("should", 60), 2)


def _membership(session: Session, email: str, home: Home) -> Membership | None:
    user = _user(session, email)
    return session.exec(
        select(Membership).where(Membership.user_id == user.id, Membership.home_id == home.id)
    ).first()


def _complete_example(session: Session, home: Home) -> None:
    email, home_name, values, days_ago = EXAMPLE_COMPLETION
    if home.name != home_name:
        return
    member = _membership(session, email, home)
    if member is None:
        print(f"Hoppet over avkrysningen i «{home_name}»: {email} er ikke medlem")
        return
    row = next(
        r
        for r in tasks.tasks_of(session, home.id)
        if (r.task.classification, r.task.frequency_days) == values
    )
    now = utc_now() - timedelta(days=days_ago)
    tasks.complete_task_instance(session, member, row.task.id, row.instance_id, now=now)
    print(f"{email} krysset av «{row.task.name}» i «{home_name}»")


def _set_up(session: Session, email: str, home_name: str, days_ago: int) -> None:
    creator = _user(session, email)
    home = _own_home(session, creator, home_name)
    if home is None:
        print(f"Hoppet over oppgavene i «{home_name}»: hjemmet finnes ikke for {email}")
        return
    if tasks.has_tasks(session, home.id):
        print(f"Oppgavene i «{home_name}» er allerede satt opp")
        return
    membership = _membership(session, email, home)
    assert membership is not None  # _own_home found the Home through it
    choices = [
        tasks.TaskChoice(t.key, t.classification, t.frequency_days) for t in task_types.TASK_TYPES
    ]
    today = utc_now().date() - timedelta(days=days_ago)
    created = tasks.set_up_tasks(session, membership, choices, today=today)
    print(f"Satte opp {len(created)} oppgaver i «{home_name}»")
    _complete_example(session, home)


def seed_tasks(session: Session) -> None:
    for email, home_name, days_ago in EXAMPLE_SETUPS:
        _set_up(session, email, home_name, days_ago)
