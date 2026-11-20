"""The onboarding guide for a Landlord Home's Tenants (Story 5.3, FR-16, AD-4).

The guide is two parts. The introduction is written once by the AI service when the Home's Tasks
are set up and stored (store_guide). The Home's name and its current active Must tasks are read
from the database every time the guide is shown (guide_for), so the guide is always right about
this Home and a Task changed later never makes it stale. Who may read and who may dismiss is
stated once here; routes and the frontend read it, never the Roles.
"""

import uuid
from typing import NamedTuple

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.clock import utc_now
from app.domain import tasks
from app.models.home import Home
from app.models.membership import Membership
from app.models.onboarding_guide import OnboardingGuide

# The Tenant reads and dismisses; the Landlord reads, to know what the Tenants are told.
VIEWER_ROLES: frozenset[str] = frozenset({"tenant", "landlord"})

# What a Home gets when the AI could not write one, and what a Home set up before Story 5.3 shows.
FALLBACK_INTRO = (
    "Velkommen! I Husly ser du hjemmets oppgaver samlet på ett sted. Oppgaver merket Må er de "
    "viktigste, og Bør er det som er fint å få gjort. Kryss av en oppgave når du har gjort den, så "
    "ser alle i hjemmet at den er tatt. Du får påminnelser om oppgaver som snart forfaller, og du "
    "kan spørre KI hvis du lurer på hvordan noe gjøres."
)


class GuideNotAvailable(Exception):
    """The Home has no Tasks yet, so there is nothing to show."""


class MustTask(NamedTuple):
    name: str
    # The catalog key, or None for a custom Task.
    task_type: str | None
    frequency_days: int


class GuideView(NamedTuple):
    home_name: str
    intro: str
    source: str
    must_tasks: list[MustTask]
    dismissed: bool


def can_view_guide(role: str) -> bool:
    return role in VIEWER_ROLES


def can_dismiss_guide(role: str) -> bool:
    return role == "tenant"


def must_tasks(session: Session, home_id: uuid.UUID) -> list[MustTask]:
    """The Home's active Must tasks in the server's order (due date, then name)."""
    return [
        MustTask(row.task.name, row.task.task_type, row.task.frequency_days)
        for row in tasks.tasks_of(session, home_id)
        if row.task.classification == "must"
    ]


def store_guide(session: Session, home_id: uuid.UUID, intro: str, source: str) -> None:
    """Stores the introduction if the Home has none. An existing one wins: written once."""
    if session.get(OnboardingGuide, home_id) is not None:
        return
    session.add(OnboardingGuide(home_id=home_id, intro=intro, source=source))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()


def guide_for(session: Session, membership: Membership) -> GuideView:
    """The guide as this Member sees it. Raises GuideNotAvailable before Tasks are set up."""
    if not tasks.has_tasks(session, membership.home_id):
        raise GuideNotAvailable
    home = session.get(Home, membership.home_id)
    assert home is not None
    stored = session.get(OnboardingGuide, membership.home_id)
    # No row (a Home set up before Story 5.3): the fixed text, nothing stored, no AI call.
    intro, source = (stored.intro, stored.source) if stored else (FALLBACK_INTRO, "fallback")
    return GuideView(
        home.name,
        intro,
        source,
        must_tasks(session, membership.home_id),
        membership.onboarding_dismissed_at is not None,
    )


def dismiss(session: Session, membership: Membership) -> None:
    """Hides the card for this Tenant. Idempotent: the first dismissal keeps its time."""
    if not can_dismiss_guide(membership.role):
        raise ValueError(f"role {membership.role!r} may not dismiss the guide")
    if membership.onboarding_dismissed_at is None:
        membership.onboarding_dismissed_at = utc_now()
        session.add(membership)
        session.commit()
