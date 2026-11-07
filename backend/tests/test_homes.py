"""Story 1.3 (FR-1, FR-3, AD-1, AD-2): the Home creation rule and the Role a Member gets."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from app.domain import homes
from app.domain.accounts import register
from app.models.home import Home
from app.models.membership import Membership
from app.models.user import User


def new_user(session: Session, name: str = "Ola") -> User:
    return register(
        session,
        email=f"{name.lower()}-{uuid.uuid4().hex[:6]}@example.com",
        name=name,
        password="hemmelig1",
    )


T0 = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)


def set_created_at(session: Session, home: Home, when: datetime) -> None:
    """Pins created_at, so ordering tests never depend on the clock's resolution."""
    home.created_at = when
    session.add(home)
    session.commit()


def count(session: Session, model: type) -> int:
    return session.exec(select(func.count()).select_from(model)).one()


def test_role_is_not_a_column_on_users(session: Session) -> None:
    columns = {c["name"] for c in inspect(session.get_bind()).get_columns("users")}
    assert "role" not in columns


def test_no_memberships_may_create_either_type(session: Session) -> None:
    assert homes.allowed_types(session, new_user(session)) == ["household", "landlord"]


def test_create_household_makes_creator_a_household_member(session: Session) -> None:
    user = new_user(session)
    created = homes.create_home(session, user, name="  Kollektivet  ", type="household")

    assert created.role == "household_member"
    assert created.home.name == "Kollektivet"
    assert created.home.type == "household"
    membership = session.exec(select(Membership)).one()
    assert (membership.user_id, membership.home_id) == (user.id, created.home.id)
    assert homes.allowed_types(session, user) == []


def test_create_landlord_makes_creator_the_only_landlord_with_zero_tenants(
    session: Session,
) -> None:
    user = new_user(session)
    created = homes.create_home(session, user, name="Storgata 1", type="landlord")

    assert created.role == "landlord"
    roles = session.exec(select(Membership.role).where(Membership.home_id == created.home.id))
    assert roles.all() == ["landlord"]
    assert homes.allowed_types(session, user) == ["landlord"]


def test_landlord_may_create_another_landlord_home(session: Session) -> None:
    user = new_user(session)
    first = homes.create_home(session, user, name="Storgata 1", type="landlord")
    second = homes.create_home(session, user, name="Storgata 2", type="landlord")
    set_created_at(session, first.home, T0)
    set_created_at(session, second.home, T0 + timedelta(seconds=1))

    assert second.role == "landlord"
    assert [h.home.name for h in homes.homes_for(session, user)] == ["Storgata 2", "Storgata 1"]


def test_landlord_may_not_create_a_household_home(session: Session) -> None:
    user = new_user(session)
    homes.create_home(session, user, name="Storgata 1", type="landlord")

    with pytest.raises(homes.HomeCreationNotAllowed) as exc:
        homes.create_home(session, user, name="Kollektivet", type="household")
    assert exc.value.allowed == ["landlord"]
    assert count(session, Home) == 1 and count(session, Membership) == 1


@pytest.mark.parametrize("type", ["household", "landlord"])
def test_household_member_may_not_create_again(session: Session, type: str) -> None:
    user = new_user(session)
    homes.create_home(session, user, name="Kollektivet", type="household")

    with pytest.raises(homes.HomeCreationNotAllowed) as exc:
        homes.create_home(session, user, name="Nytt", type=type)  # type: ignore[arg-type]
    assert exc.value.allowed == []
    assert count(session, Home) == 1


@pytest.mark.parametrize("type", ["household", "landlord"])
def test_tenant_may_not_create_a_home(session: Session, type: str) -> None:
    landlord, tenant = new_user(session, "Utleier"), new_user(session, "Leietaker")
    home = homes.create_home(session, landlord, name="Storgata 1", type="landlord").home
    homes.add_member(session, home, tenant)

    assert homes.allowed_types(session, tenant) == []
    with pytest.raises(homes.HomeCreationNotAllowed):
        homes.create_home(session, tenant, name="Eget", type=type)  # type: ignore[arg-type]
    assert count(session, Home) == 1


def test_add_member_to_household_home_gives_household_member(session: Session) -> None:
    mari, jonas = new_user(session, "Mari"), new_user(session, "Jonas")
    home = homes.create_home(session, mari, name="Kollektivet", type="household").home

    membership = homes.add_member(session, home, jonas)

    # No creator privilege: the joiner's row looks exactly like the creator's.
    assert membership.role == "household_member"
    assert {r.role for r in session.exec(select(Membership)).all()} == {"household_member"}


def test_add_member_to_landlord_home_gives_tenant_never_a_second_landlord(
    session: Session,
) -> None:
    landlord, other_landlord = new_user(session, "Utleier"), new_user(session, "Annen")
    homes.create_home(session, other_landlord, name="Annet bygg", type="landlord")
    home = homes.create_home(session, landlord, name="Storgata 1", type="landlord").home

    # Even someone who is a Landlord elsewhere joins as a Tenant.
    assert homes.add_member(session, home, other_landlord).role == "tenant"
    roles = session.exec(select(Membership.role).where(Membership.home_id == home.id)).all()
    assert sorted(roles) == ["landlord", "tenant"]


def test_landlord_who_joins_a_household_home_holds_two_roles(session: Session) -> None:
    landlord, mari = new_user(session, "Utleier"), new_user(session, "Mari")
    homes.create_home(session, landlord, name="Storgata 1", type="landlord")
    kollektiv = homes.create_home(session, mari, name="Kollektivet", type="household").home

    homes.add_member(session, kollektiv, landlord)

    assert {h.role for h in homes.homes_for(session, landlord)} == {"landlord", "household_member"}
    # Still a Landlord, so still allowed to create Landlord Homes.
    assert homes.allowed_types(session, landlord) == ["landlord"]


def test_add_member_twice_raises_already_member(session: Session) -> None:
    mari, jonas = new_user(session, "Mari"), new_user(session, "Jonas")
    home = homes.create_home(session, mari, name="Kollektivet", type="household").home
    homes.add_member(session, home, jonas)

    with pytest.raises(homes.AlreadyMember):
        homes.add_member(session, home, jonas)
    assert count(session, Membership) == 2


def test_homes_for_returns_only_the_callers_homes_newest_first(session: Session) -> None:
    ola, kari = new_user(session, "Ola"), new_user(session, "Kari")
    a = homes.create_home(session, ola, name="A", type="landlord").home
    homes.create_home(session, kari, name="Karis", type="household")
    b = homes.create_home(session, ola, name="B", type="landlord").home
    set_created_at(session, a, T0)
    set_created_at(session, b, T0 + timedelta(seconds=1))

    assert [(h.home.name, h.role) for h in homes.homes_for(session, ola)] == [
        ("B", "landlord"),
        ("A", "landlord"),
    ]


def test_homes_for_breaks_a_created_at_tie_by_id_stably(session: Session) -> None:
    user = new_user(session)
    created = [
        homes.create_home(session, user, name=n, type="landlord").home for n in ("A", "B", "C")
    ]
    for home in created:
        set_created_at(session, home, T0)

    first = [h.home.id for h in homes.homes_for(session, user)]
    assert first == sorted((h.id for h in created), reverse=True)
    assert all([h.home.id for h in homes.homes_for(session, user)] == first for _ in range(5))


@pytest.mark.parametrize("name", ["", "   ", "x" * 61])
def test_create_home_rejects_invalid_name(session: Session, name: str) -> None:
    with pytest.raises(ValueError):
        homes.create_home(session, new_user(session), name=name, type="household")
    assert count(session, Home) == 0


def test_unknown_type_is_rejected_by_the_domain(session: Session) -> None:
    with pytest.raises(ValueError):
        homes.create_home(session, new_user(session), name="Hjem", type="other")  # type: ignore[arg-type]
    assert count(session, Home) == 0


def test_check_constraint_rejects_unknown_home_type(session: Session) -> None:
    with pytest.raises(IntegrityError, match="ck_homes_type"):
        session.execute(
            text("INSERT INTO homes (id, name, type, created_at) VALUES (:id, 'x', 'other', :t)"),
            {"id": uuid.uuid4().hex, "t": "2026-11-07 12:00:00"},
        )


def test_check_constraint_rejects_unknown_role(session: Session) -> None:
    user = new_user(session)
    home = homes.create_home(session, user, name="Hjem", type="landlord").home
    other = new_user(session, "Kari")
    with pytest.raises(IntegrityError, match="ck_memberships_role"):
        session.execute(
            text(
                "INSERT INTO memberships (id, user_id, home_id, role, created_at) "
                "VALUES (:id, :u, :h, 'owner', :t)"
            ),
            {"id": uuid.uuid4().hex, "u": other.id.hex, "h": home.id.hex, "t": "2026-11-07"},
        )


def test_foreign_key_rejects_membership_to_missing_home(session: Session) -> None:
    user = new_user(session)
    session.add(Membership(user_id=user.id, home_id=uuid.uuid4(), role="household_member"))
    with pytest.raises(IntegrityError, match="FOREIGN KEY"):
        session.commit()
