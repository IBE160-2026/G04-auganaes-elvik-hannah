"""Creating Homes and adding Members (Story 1.3, FR-1, FR-3, AD-1, AD-2).

The creation rule and the Role a Member gets live only here. A caller never picks a Role:
the creator of a Household Home and anyone who joins it is a Household Member; the creator of a
Landlord Home is its Landlord and anyone who joins it is a Tenant. So a Home never mixes
Household Members with a Landlord or Tenants, and a Landlord Home has exactly one Landlord.
"""

from typing import NamedTuple

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.models.home import HOME_NAME_MAX_LENGTH, HOME_TYPES, Home, HomeType
from app.models.membership import Membership, Role
from app.models.user import User

_CREATOR_ROLE: dict[HomeType, Role] = {"household": "household_member", "landlord": "landlord"}
_JOINER_ROLE: dict[HomeType, Role] = {"household": "household_member", "landlord": "tenant"}


class HomeCreationNotAllowed(Exception):
    """The user may not create a Home of this type. `allowed` is what they may create."""

    def __init__(self, allowed: list[HomeType]) -> None:
        super().__init__(f"allowed types: {allowed}")
        self.allowed = allowed


class AlreadyMember(Exception):
    """The user already has a Membership in this Home."""


class MemberHome(NamedTuple):
    home: Home
    role: Role


def _roles(session: Session, user: User) -> set[str]:
    return set(session.exec(select(Membership.role).where(Membership.user_id == user.id)).all())


def allowed_types(session: Session, user: User) -> list[HomeType]:
    """The Home types this user may create through the self-service flow.

    No Membership: either type. Landlord in at least one Home: more Landlord Homes (Epic 6
    portfolio). Only Household Member or Tenant Memberships: none, they join by invite.
    """
    roles = _roles(session, user)
    if not roles:
        return list(HOME_TYPES)
    if "landlord" in roles:
        return ["landlord"]
    return []


def create_home(session: Session, user: User, *, name: str, type: HomeType) -> MemberHome:
    """Create a Home with the user as its first Member. Raises HomeCreationNotAllowed."""
    name = name.strip()
    if not 1 <= len(name) <= HOME_NAME_MAX_LENGTH:
        raise ValueError("name must be 1-60 characters after stripping")
    if type not in HOME_TYPES:
        raise ValueError(f"unknown Home type: {type!r}")
    # Locks the user's row until commit, so two parallel requests cannot both pass the rule
    # below (a double click would otherwise give a Household Member two Homes). Postgres only;
    # SQLite ignores FOR UPDATE.
    session.exec(select(User).where(User.id == user.id).with_for_update()).one()
    allowed = allowed_types(session, user)
    if type not in allowed:
        session.rollback()
        raise HomeCreationNotAllowed(allowed)
    home = Home(name=name, type=type)
    role = _CREATOR_ROLE[type]
    session.add(home)
    session.flush()
    session.add(Membership(user_id=user.id, home_id=home.id, role=role))
    session.commit()
    session.refresh(home)
    return MemberHome(home, role)


def add_member(session: Session, home: Home, user: User) -> Membership:
    """Add a user to a Home as a joiner (Story 1.4 reuses this). Raises AlreadyMember."""
    role = _JOINER_ROLE[home.type]
    membership = Membership(user_id=user.id, home_id=home.id, role=role)
    session.add(membership)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise AlreadyMember from None
    session.refresh(membership)
    return membership


def homes_for(session: Session, user: User) -> list[MemberHome]:
    """The user's Homes, newest first, each with the user's Role in it."""
    rows = session.exec(
        select(Home, Membership.role)
        .join(Membership, col(Membership.home_id) == col(Home.id))
        .where(Membership.user_id == user.id)
        # id breaks ties: on Windows the clock ticks ~15.6 ms, so two creates can share a time.
        .order_by(col(Home.created_at).desc(), col(Home.id).desc())
    ).all()
    return [MemberHome(home, role) for home, role in rows]
