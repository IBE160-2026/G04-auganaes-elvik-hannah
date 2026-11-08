"""Invite links: create, preview and accept (Story 1.4, FR-2, AD-1, AD-2).

Link policy (team decision 1, 2026-11-07): single-use, valid for 7 days. Making a new link
leaves earlier unused ones valid; there is no revoking. The raw token is returned once, at
creation; only its SHA-256 hash is stored. The Role a link gives comes from the Home type
(homes.joiner_role), never from the person who made it, and joining goes through
homes.add_member, which holds the one-Home rule (decision 3).

Every function takes an optional `now`, so tests can fix the clock.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Literal, NamedTuple

from sqlmodel import Session, select

from app.clock import as_utc, utc_now
from app.domain import homes
from app.models.home import Home, HomeType
from app.models.invite_link import InviteLink
from app.models.membership import Membership, Role
from app.models.user import User

INVITE_TTL = timedelta(days=7)
# token_urlsafe(32) gives 43 characters; anything longer than this is never a real token.
TOKEN_MAX_LENGTH = 64

ViewerState = Literal["can_join", "already_member", "in_other_home"]


class InviteNotAllowed(Exception):
    """The inviter's Role may not invite (a Tenant). Routes reject this earlier with 403."""


class InviteInvalid(Exception):
    """Unknown, expired or used by someone else. `home_type` is None for an unknown token."""

    def __init__(self, home_type: HomeType | None) -> None:
        super().__init__(f"invalid invite (home type: {home_type})")
        self.home_type = home_type


class CreatedInvite(NamedTuple):
    # Raw token: shown once, never stored.
    token: str
    link: InviteLink


class Preview(NamedTuple):
    """What the invite page shows. `home` is set when valid, `home_type` always when known.

    "valid" also covers a link the viewer used themselves, so they are told they are already a
    Member rather than that the link is invalid.
    """

    status: Literal["valid", "invalid"]
    home_type: HomeType | None
    home: Home | None = None
    role: Role | None = None
    viewer: ViewerState | None = None
    other_home: Home | None = None


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _find(session: Session, token: str, *, lock: bool = False) -> InviteLink | None:
    if not 1 <= len(token) <= TOKEN_MAX_LENGTH:
        return None
    query = select(InviteLink).where(InviteLink.token_hash == hash_token(token))
    if lock:
        query = query.with_for_update()
    return session.exec(query).first()


def _usable(link: InviteLink, now: datetime) -> bool:
    return link.used_at is None and now < as_utc(link.expires_at)


def create_invite(
    session: Session, inviter: Membership, *, now: datetime | None = None
) -> CreatedInvite:
    """A new link to the inviter's Home. Raises InviteNotAllowed for a Role that may not invite."""
    if not homes.can_invite(inviter.role):
        raise InviteNotAllowed
    now = now or utc_now()
    home = session.exec(select(Home).where(Home.id == inviter.home_id)).one()
    token = secrets.token_urlsafe(32)
    link = InviteLink(
        home_id=home.id,
        role=homes.joiner_role(home),
        token_hash=hash_token(token),
        created_by_user_id=inviter.user_id,
        created_at=now,
        expires_at=now + INVITE_TTL,
    )
    session.add(link)
    session.commit()
    session.refresh(link)
    return CreatedInvite(token, link)


def preview(
    session: Session, token: str, viewer: User | None, *, now: datetime | None = None
) -> Preview:
    """The link's Home and Role, and, for a signed-in viewer, whether they can join."""
    now = now or utc_now()
    link = _find(session, token)
    if link is None:
        return Preview("invalid", None)
    home = session.exec(select(Home).where(Home.id == link.home_id)).one()
    home_type: HomeType = home.type
    used_by_viewer = viewer is not None and link.used_by_user_id == viewer.id
    if not used_by_viewer and not _usable(link, now):
        return Preview("invalid", home_type)
    result = Preview("valid", home_type, home, link.role)
    if viewer is None:
        return result
    if used_by_viewer:
        return result._replace(viewer="already_member")
    blocker = homes.join_blocker(session, home, viewer)
    if isinstance(blocker, homes.AlreadyMember):
        return result._replace(viewer="already_member")
    if isinstance(blocker, homes.InOtherHome):
        return result._replace(viewer="in_other_home", other_home=blocker.home)
    return result._replace(viewer="can_join")


def accept(
    session: Session, token: str, user: User, *, now: datetime | None = None
) -> homes.MemberHome:
    """Join the link's Home and mark the link used, in one commit.

    Raises InviteInvalid (unknown, expired, or used by someone else), or homes.AlreadyMember /
    homes.InOtherHome. A refused join leaves the link unused.
    """
    now = now or utc_now()
    # Locks the link until commit, so two parallel accepts cannot both use it. Postgres only.
    link = _find(session, token, lock=True)
    if link is None:
        session.rollback()
        raise InviteInvalid(None)
    home = session.exec(select(Home).where(Home.id == link.home_id)).one()
    if link.used_by_user_id == user.id:
        session.rollback()
        raise homes.AlreadyMember(home)
    if not _usable(link, now):
        session.rollback()
        raise InviteInvalid(home.type)
    link.used_at = now
    link.used_by_user_id = user.id
    session.add(link)
    # add_member commits the link and the Membership together, or rolls both back.
    membership = homes.add_member(session, home, user)
    return homes.MemberHome(home, membership.role)
