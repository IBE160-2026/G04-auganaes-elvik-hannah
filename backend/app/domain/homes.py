"""Creating Homes and adding Members (Story 1.3, FR-1, FR-3, AD-1, AD-2; Story 1.4, FR-2).

The creation rule and the Role a Member gets live only here. A caller never picks a Role:
the creator of a Household Home and anyone who joins it is a Household Member; the creator of a
Landlord Home is its Landlord and anyone who joins it is a Tenant. So a Home never mixes
Household Members with a Landlord or Tenants, and a Landlord Home has exactly one Landlord.

Story 1.4 (team decision 3, 2026-11-07): a user is Household Member or Tenant in at most one
Home. Landlord Memberships do not count, so a Landlord may also join one such Home.

Story 1.5 (FR-3, team decision 2, 2026-11-08): members_of lists a Home's Members. The
"never mixed" rule stays here (_CREATOR_ROLE, _JOINER_ROLE); create_home and add_member are the
only places a Membership is made, and a test guards against a new Membership constructor
elsewhere in app code. fr3_violations is the one check of that rule, run by the tests
over every write path and by CI on the seeded database.
"""

import uuid
from datetime import datetime
from typing import NamedTuple

from sqlalchemy import case, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.models.home import HOME_NAME_MAX_LENGTH, HOME_TYPES, Home, HomeType
from app.models.membership import Membership, Role
from app.models.user import User

_CREATOR_ROLE: dict[HomeType, Role] = {"household": "household_member", "landlord": "landlord"}
_JOINER_ROLE: dict[HomeType, Role] = {"household": "household_member", "landlord": "tenant"}

# Story 1.4: who may invite. household_member exists only in Household Homes and landlord only
# in Landlord Homes, so this one set means "any Household Member, or the Landlord" without
# looking at the Home type. Used by the route check (require_role) and by can_invite.
INVITER_ROLES: frozenset[Role] = frozenset({"household_member", "landlord"})


def can_invite(role: str) -> bool:
    return role in INVITER_ROLES


def joiner_role(home: Home) -> Role:
    """The Role anyone who joins this Home gets (an invite link carries it)."""
    return _JOINER_ROLE[home.type]


class HomeCreationNotAllowed(Exception):
    """The user may not create a Home of this type. `allowed` is what they may create."""

    def __init__(self, allowed: list[HomeType]) -> None:
        super().__init__(f"allowed types: {allowed}")
        self.allowed = allowed


class AlreadyMember(Exception):
    """The user already has a Membership in this Home."""

    def __init__(self, home: Home) -> None:
        super().__init__(f"already a member of {home.id}")
        self.home = home


class InOtherHome(Exception):
    """The user is Household Member or Tenant in another Home, `home` (decision 3)."""

    def __init__(self, home: Home) -> None:
        super().__init__(f"already in another home: {home.id}")
        self.home = home


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


def join_blocker(session: Session, home: Home, user: User) -> AlreadyMember | InOtherHome | None:
    """Why the user may not join this Home, or None. The one place the joining rule lives.

    The invite preview shows it before the tap; add_member enforces it.
    """
    rows = session.exec(
        select(Membership.home_id, Membership.role).where(Membership.user_id == user.id)
    ).all()
    if any(home_id == home.id for home_id, _ in rows):
        return AlreadyMember(home)
    other = next((home_id for home_id, role in rows if role != "landlord"), None)
    if other is not None:
        return InOtherHome(session.exec(select(Home).where(Home.id == other)).one())
    return None


def add_member(session: Session, home: Home, user: User) -> Membership:
    """Add a user to a Home as a joiner and commit. Raises AlreadyMember or InOtherHome.

    Commits whatever the caller has pending in the same transaction (invites.accept marks the
    link used first). A refused join rolls back first, so nothing of it is written.
    """
    # Locks the user's row until commit, so two parallel joins cannot both pass the rule below
    # (same as create_home). Postgres only; SQLite ignores FOR UPDATE.
    session.exec(select(User).where(User.id == user.id).with_for_update()).one()
    blocker = join_blocker(session, home, user)
    if blocker is not None:
        session.rollback()
        raise blocker
    membership = Membership(user_id=user.id, home_id=home.id, role=joiner_role(home))
    session.add(membership)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise AlreadyMember(home) from None
    session.refresh(membership)
    return membership


def homes_for(session: Session, user: User) -> list[MemberHome]:
    """The user's Homes, the one they most recently created or joined first, with their Role."""
    rows = session.exec(
        select(Home, Membership.role)
        .join(Membership, col(Membership.home_id) == col(Home.id))
        .where(Membership.user_id == user.id)
        # Story 1.4: by the Membership, so a user who joins an older Home sees it on "/".
        # id breaks ties: on Windows the clock ticks ~15.6 ms, so two creates can share a time.
        .order_by(col(Membership.created_at).desc(), col(Home.id).desc())
    ).all()
    return [MemberHome(home, role) for home, role in rows]


class HomeMember(NamedTuple):
    user_id: uuid.UUID
    name: str
    role: Role
    joined_at: datetime


def members_of(session: Session, home_id: uuid.UUID) -> list[HomeMember]:
    """Every Member of the Home with their Role: the Landlord first, then in the order they joined.

    The id breaks ties: on Windows the clock ticks ~15.6 ms, so two joins can share a time.
    """
    rows = session.exec(
        select(User.id, User.name, Membership.role, Membership.created_at)
        .join(Membership, col(Membership.user_id) == col(User.id))
        .where(Membership.home_id == home_id)
        .order_by(
            case((col(Membership.role) == "landlord", 0), else_=1),
            col(Membership.created_at),
            col(Membership.id),
        )
    ).all()
    return [HomeMember(user_id, name, role, joined_at) for user_id, name, role, joined_at in rows]


# FR-3: a Household Home has only Household Members; a Landlord Home has exactly one Landlord and
# otherwise only Tenants. Plain SQL, so CI can run it on the seeded Postgres database as well.
_FR3_VIOLATIONS = text(
    """
    SELECT h.id FROM homes h LEFT JOIN memberships m ON m.home_id = h.id
    GROUP BY h.id, h.type
    HAVING (h.type = 'household'
            AND SUM(CASE WHEN m.role <> 'household_member' THEN 1 ELSE 0 END) > 0)
        OR (h.type = 'landlord'
            AND (SUM(CASE WHEN m.role = 'landlord' THEN 1 ELSE 0 END) <> 1
                 OR SUM(CASE WHEN m.role NOT IN ('landlord', 'tenant') THEN 1 ELSE 0 END) > 0))
        OR h.type NOT IN ('household', 'landlord')
    """
)


def fr3_violations(session: Session) -> list[uuid.UUID]:
    """Ids of Homes that break FR-3 (empty when the rule holds). Used by the tests and CI."""
    # SQLite gives the id back as hex text, Postgres as a UUID.
    return [uuid.UUID(str(home_id)) for home_id in session.execute(_FR3_VIOLATIONS).scalars()]
