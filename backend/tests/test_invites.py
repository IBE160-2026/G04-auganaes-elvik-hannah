"""Story 1.4 (FR-2, AD-1, AD-2): invite links in the domain, with a fixed clock.

The invite-row lock (with_for_update in invites.accept) only works on Postgres; SQLite ignores
FOR UPDATE, so a parallel double accept is reasoned in the spec, and only the sequential case
is tested here.
"""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from app.domain import homes, invites
from app.domain.accounts import register
from app.models.home import Home
from app.models.invite_link import InviteLink
from app.models.membership import Membership
from app.models.user import User

T0 = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)


def new_user(session: Session, name: str = "Ola") -> User:
    return register(
        session,
        email=f"{name.lower()}-{uuid.uuid4().hex[:6]}@example.com",
        name=name,
        password="hemmelig1",
    )


def membership(session: Session, user: User, home: Home) -> Membership:
    return session.exec(
        select(Membership).where(Membership.user_id == user.id, Membership.home_id == home.id)
    ).one()


def home_with_creator(session: Session, type: str, name: str = "Hjem") -> tuple[Home, User]:
    creator = new_user(session, "Skaper")
    home = homes.create_home(session, creator, name=name, type=type).home  # type: ignore[arg-type]
    return home, creator


def link_for(session: Session, home: Home, creator: User, now: datetime = T0) -> str:
    return invites.create_invite(session, membership(session, creator, home), now=now).token


def count(session: Session, model: type) -> int:
    return session.exec(select(func.count()).select_from(model)).one()


# Create
@pytest.mark.parametrize(
    ("type", "role"), [("household", "household_member"), ("landlord", "tenant")]
)
def test_link_role_comes_from_the_home_type(session: Session, type: str, role: str) -> None:
    home, creator = home_with_creator(session, type)

    created = invites.create_invite(session, membership(session, creator, home), now=T0)

    assert created.link.role == role
    assert created.link.home_id == home.id
    assert created.link.created_by_user_id == creator.id
    assert invites.preview(session, created.token, None, now=T0).role == role


def test_link_expires_after_seven_days(session: Session) -> None:
    home, creator = home_with_creator(session, "household")
    link = invites.create_invite(session, membership(session, creator, home), now=T0).link

    assert invites.INVITE_TTL == timedelta(days=7)
    session.refresh(link)
    assert invites.as_utc(link.expires_at) == T0 + timedelta(days=7)


def test_only_the_hash_of_the_token_is_stored(session: Session) -> None:
    home, creator = home_with_creator(session, "household")
    token = link_for(session, home, creator)

    link = session.exec(select(InviteLink)).one()
    assert link.token_hash == hashlib.sha256(token.encode()).hexdigest()
    stored = session.execute(text("SELECT * FROM invite_links")).one()
    assert all(token not in str(value) for value in stored)


def test_a_new_link_leaves_the_earlier_one_valid(session: Session) -> None:
    home, creator = home_with_creator(session, "household")
    first = link_for(session, home, creator)
    second = link_for(session, home, creator)

    assert first != second
    for token in (first, second):
        assert invites.preview(session, token, None, now=T0).status == "valid"


def test_a_tenant_may_not_create_a_link(session: Session) -> None:
    home, _ = home_with_creator(session, "landlord")
    tenant = new_user(session, "Leietaker")
    homes.add_member(session, home, tenant)

    with pytest.raises(invites.InviteNotAllowed):
        invites.create_invite(session, membership(session, tenant, home), now=T0)
    assert count(session, InviteLink) == 0


def test_check_constraint_rejects_a_landlord_link(session: Session) -> None:
    home, creator = home_with_creator(session, "landlord")
    with pytest.raises(IntegrityError, match="ck_invite_links_role"):
        session.execute(
            text(
                "INSERT INTO invite_links (id, home_id, role, token_hash, created_by_user_id, "
                "created_at, expires_at) VALUES (:id, :h, 'landlord', 'x', :u, :t, :t)"
            ),
            {"id": uuid.uuid4().hex, "h": home.id.hex, "u": creator.id.hex, "t": "2026-11-07"},
        )


# Preview
def test_preview_signed_out_shows_home_and_role_without_viewer(session: Session) -> None:
    home, creator = home_with_creator(session, "household", "Kollektivet")
    result = invites.preview(session, link_for(session, home, creator), None, now=T0)

    assert (result.status, result.home_type, result.role, result.viewer) == (
        "valid",
        "household",
        "household_member",
        None,
    )
    assert result.home is not None and result.home.name == "Kollektivet"


def test_preview_for_a_user_without_homes_is_can_join(session: Session) -> None:
    home, creator = home_with_creator(session, "household")
    token = link_for(session, home, creator)

    assert invites.preview(session, token, new_user(session), now=T0).viewer == "can_join"


def test_preview_for_the_creator_is_already_member(session: Session) -> None:
    home, creator = home_with_creator(session, "landlord")
    token = link_for(session, home, creator)

    assert invites.preview(session, token, creator, now=T0).viewer == "already_member"


def test_preview_for_a_member_elsewhere_is_in_other_home_with_its_name(session: Session) -> None:
    home, creator = home_with_creator(session, "household")
    jonas = new_user(session, "Jonas")
    homes.create_home(session, jonas, name="Jonas sitt", type="household")

    result = invites.preview(session, link_for(session, home, creator), jonas, now=T0)

    assert result.viewer == "in_other_home"
    assert result.other_home is not None and result.other_home.name == "Jonas sitt"


@pytest.mark.parametrize(
    ("moment", "status"),
    [
        (T0 + timedelta(days=7) - timedelta(seconds=1), "valid"),
        (T0 + timedelta(days=7), "invalid"),
    ],
)
def test_preview_expiry_boundary(session: Session, moment: datetime, status: str) -> None:
    home, creator = home_with_creator(session, "landlord")
    token = link_for(session, home, creator)
    session.expire_all()  # read expires_at back from SQLite (naive) like a new request would

    result = invites.preview(session, token, None, now=moment)
    assert result.status == status
    assert result.home_type == "landlord"


def test_preview_of_an_unknown_token_is_invalid_without_home_type(session: Session) -> None:
    result = invites.preview(session, "finnes-ikke", None, now=T0)
    assert (result.status, result.home_type, result.home) == ("invalid", None, None)


def test_preview_of_an_overlong_token_is_invalid(session: Session) -> None:
    assert invites.preview(session, "x" * 65, None, now=T0).status == "invalid"


def test_preview_of_a_link_used_by_someone_else_is_invalid(session: Session) -> None:
    home, creator = home_with_creator(session, "household")
    token = link_for(session, home, creator)
    invites.accept(session, token, new_user(session, "Jonas"), now=T0)

    result = invites.preview(session, token, new_user(session, "Per"), now=T0)
    assert (result.status, result.home_type) == ("invalid", "household")


def test_preview_of_a_link_used_by_the_viewer_is_already_member(session: Session) -> None:
    home, creator = home_with_creator(session, "household")
    token = link_for(session, home, creator)
    jonas = new_user(session, "Jonas")
    invites.accept(session, token, jonas, now=T0)

    # Even after it has expired: they used it, so they are told they are in.
    result = invites.preview(session, token, jonas, now=T0 + timedelta(days=30))
    assert (result.status, result.viewer) == ("valid", "already_member")


# Accept
def test_accept_adds_the_member_with_the_link_role_and_marks_the_link_used(
    session: Session,
) -> None:
    home, creator = home_with_creator(session, "landlord")
    token = link_for(session, home, creator)
    tenant = new_user(session, "Leietaker")

    joined = invites.accept(session, token, tenant, now=T0 + timedelta(hours=1))

    assert (joined.home.id, joined.role) == (home.id, "tenant")
    link = session.exec(select(InviteLink)).one()
    assert link.used_by_user_id == tenant.id
    assert invites.as_utc(link.used_at) == T0 + timedelta(hours=1)  # type: ignore[arg-type]
    assert membership(session, tenant, home).role == "tenant"


def test_sequential_second_accept_fails(session: Session) -> None:
    home, creator = home_with_creator(session, "household")
    token = link_for(session, home, creator)
    invites.accept(session, token, new_user(session, "Jonas"), now=T0)

    with pytest.raises(invites.InviteInvalid) as exc:
        invites.accept(session, token, new_user(session, "Per"), now=T0)
    assert exc.value.home_type == "household"
    assert count(session, Membership) == 2


def test_accept_by_the_same_user_again_is_already_member(session: Session) -> None:
    home, creator = home_with_creator(session, "household")
    token = link_for(session, home, creator)
    jonas = new_user(session, "Jonas")
    invites.accept(session, token, jonas, now=T0)

    with pytest.raises(homes.AlreadyMember):
        invites.accept(session, token, jonas, now=T0)


def test_accept_after_expiry_is_invalid_and_writes_nothing(session: Session) -> None:
    home, creator = home_with_creator(session, "landlord")
    token = link_for(session, home, creator)

    with pytest.raises(invites.InviteInvalid) as exc:
        invites.accept(session, token, new_user(session), now=T0 + timedelta(days=8))
    assert exc.value.home_type == "landlord"
    assert count(session, Membership) == 1
    assert session.exec(select(InviteLink)).one().used_at is None


def test_accept_unknown_token_is_invalid_without_home_type(session: Session) -> None:
    with pytest.raises(invites.InviteInvalid) as exc:
        invites.accept(session, "finnes-ikke", new_user(session), now=T0)
    assert exc.value.home_type is None


def test_accept_own_link_is_already_member_and_leaves_the_link_unused(session: Session) -> None:
    home, creator = home_with_creator(session, "landlord")
    token = link_for(session, home, creator)

    with pytest.raises(homes.AlreadyMember):
        invites.accept(session, token, creator, now=T0)
    session.expire_all()
    link = session.exec(select(InviteLink)).one()
    assert (link.used_at, link.used_by_user_id) == (None, None)
    assert invites.preview(session, token, None, now=T0).status == "valid"


def test_refused_join_from_another_home_leaves_the_link_unused(session: Session) -> None:
    home, creator = home_with_creator(session, "household")
    token = link_for(session, home, creator)
    jonas = new_user(session, "Jonas")
    homes.create_home(session, jonas, name="Jonas sitt", type="household")

    with pytest.raises(homes.InOtherHome) as exc:
        invites.accept(session, token, jonas, now=T0)
    assert exc.value.home.name == "Jonas sitt"
    session.expire_all()
    assert session.exec(select(InviteLink)).one().used_at is None
    assert count(session, Membership) == 2


def test_landlord_only_joins_a_household_home_as_household_member(session: Session) -> None:
    home, creator = home_with_creator(session, "household")
    landlord = new_user(session, "Utleier")
    homes.create_home(session, landlord, name="Storgata 1", type="landlord")

    joined = invites.accept(session, link_for(session, home, creator), landlord, now=T0)

    assert joined.role == "household_member"
    # Still a Landlord, so still allowed to create Landlord Homes.
    assert homes.allowed_types(session, landlord) == ["landlord"]


def test_landlord_only_joins_another_landlords_home_as_tenant(session: Session) -> None:
    home, creator = home_with_creator(session, "landlord")
    landlord = new_user(session, "Utleier")
    homes.create_home(session, landlord, name="Storgata 1", type="landlord")

    assert invites.accept(session, link_for(session, home, creator), landlord, now=T0).role == (
        "tenant"
    )


def test_landlord_already_in_a_non_landlord_home_cannot_join_a_second(session: Session) -> None:
    first, first_creator = home_with_creator(session, "household", "Kollektivet")
    second, second_creator = home_with_creator(session, "landlord", "Storgata 2")
    landlord = new_user(session, "Utleier")
    homes.create_home(session, landlord, name="Storgata 1", type="landlord")
    invites.accept(session, link_for(session, first, first_creator), landlord, now=T0)
    token = link_for(session, second, second_creator)

    assert invites.preview(session, token, landlord, now=T0).viewer == "in_other_home"
    with pytest.raises(homes.InOtherHome) as exc:
        invites.accept(session, token, landlord, now=T0)
    assert exc.value.home.name == "Kollektivet"


def test_homes_for_shows_the_joined_home_first(session: Session) -> None:
    """A Landlord who joins an older Household Home sees it on "/" (ordered by Membership)."""
    home, creator = home_with_creator(session, "household", "Kollektivet")
    landlord = new_user(session, "Utleier")
    own = homes.create_home(session, landlord, name="Storgata 1", type="landlord").home
    own_membership = membership(session, landlord, own)
    own_membership.created_at = T0
    session.add(own_membership)
    session.commit()

    invites.accept(session, link_for(session, home, creator), landlord, now=T0)
    joined = membership(session, landlord, home)
    joined.created_at = T0 + timedelta(seconds=1)
    session.add(joined)
    session.commit()

    assert [h.home.name for h in homes.homes_for(session, landlord)] == [
        "Kollektivet",
        "Storgata 1",
    ]
