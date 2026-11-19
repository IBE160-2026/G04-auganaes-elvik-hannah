"""The Landlord's reminder cadence for a Home's Tenants (Story 3.5, FR-13, AD-8, AD-3).

A Home keeps `notification_cadence_days` (1, 2 or 7). The daily due-check reminds a Tenant about an
open Must task only when the days since its due date divide by the cadence, so the due day always
reminds and nothing is stored per reminder. Household Members, the Landlord and Bør tasks keep
FR-10's daily rule. Days are UTC days (AD-3). The cadence never touches a task's Frequency.
"""

import uuid
from datetime import date

from sqlmodel import Session

from app.models.home import CADENCE_OPTIONS, Home
from app.models.membership import Role


class InvalidCadence(ValueError):
    """The days are not one of CADENCE_OPTIONS."""


def can_set_cadence(role: Role) -> bool:
    return role == "landlord"


def reminder_day(due_on: date, today: date, cadence_days: int) -> bool:
    """True on a reminder day: the days since `due_on` divide by the cadence."""
    return (today - due_on).days % cadence_days == 0


def set_cadence(session: Session, home_id: uuid.UUID, days: int) -> Home:
    if days not in CADENCE_OPTIONS:
        raise InvalidCadence(days)
    home = session.get(Home, home_id)
    if home is None:
        raise LookupError(home_id)
    home.notification_cadence_days = days
    session.add(home)
    session.commit()
    session.refresh(home)
    return home
