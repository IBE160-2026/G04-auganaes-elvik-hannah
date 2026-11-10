"""Story 1.3 (FR-1, FR-3, AD-1, AD-2): the Home creation rule and the Role a Member gets.

Story 1.9 (issue #30): one rule for creating and joining (lived_in_home), the matrix in
spec-1-9-one-rule-for-creating-homes.md.

Story 1.5: the members list (members_of) and the FR-3 "never mixed" check (fr3_violations).

Story 1.8 (FR-23, AD-16): leave, remove_tenant and the rules can_leave / can_remove.
"""

import inspect as inspect_module
import re
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.domain import homes
from app.models.home import Home
from app.models.membership import Membership
from app.models.user import User
from tests.helpers import count, new_user

T0 = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)


def set_joined_at(session: Session, user: User, home: Home, when: datetime) -> None:
    """Pins the Membership's created_at (homes_for orders by it, Story 1.4), so ordering tests
    never depend on the clock's resolution."""
    membership = session.exec(
        select(Membership).where(Membership.user_id == user.id, Membership.home_id == home.id)
    ).one()
    membership.created_at = when
    session.add(membership)
    session.commit()


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
    assert homes.allowed_types(session, user) == ["landlord"]
    assert homes.lived_in_home(session, user) == created.home


def test_create_landlord_makes_creator_the_only_landlord_with_zero_tenants(
    session: Session,
) -> None:
    user = new_user(session)
    created = homes.create_home(session, user, name="Storgata 1", type="landlord")

    assert created.role == "landlord"
    roles = session.exec(select(Membership.role).where(Membership.home_id == created.home.id))
    assert roles.all() == ["landlord"]
    assert homes.allowed_types(session, user) == ["household", "landlord"]
    assert homes.lived_in_home(session, user) is None


def test_landlord_may_create_another_landlord_home(session: Session) -> None:
    user = new_user(session)
    first = homes.create_home(session, user, name="Storgata 1", type="landlord")
    second = homes.create_home(session, user, name="Storgata 2", type="landlord")
    set_joined_at(session, user, first.home, T0)
    set_joined_at(session, user, second.home, T0 + timedelta(seconds=1))

    assert second.role == "landlord"
    assert [h.home.name for h in homes.homes_for(session, user)] == ["Storgata 2", "Storgata 1"]


def test_landlord_may_create_her_own_household_home(session: Session) -> None:
    kari = new_user(session, "Kari")
    homes.create_home(session, kari, name="Storgata 12", type="landlord")

    created = homes.create_home(session, kari, name="Karis", type="household")

    assert created.role == "household_member"
    assert homes.lived_in_home(session, kari) == created.home
    assert homes.allowed_types(session, kari) == ["landlord"]
    assert homes.fr3_violations(session) == []


def test_landlord_with_her_own_household_may_not_create_another(session: Session) -> None:
    kari = new_user(session, "Kari")
    homes.create_home(session, kari, name="Storgata 12", type="landlord")
    own = homes.create_home(session, kari, name="Karis", type="household").home

    with pytest.raises(homes.HomeCreationNotAllowed) as exc:
        homes.create_home(session, kari, name="Hytta", type="household")
    assert exc.value.home.id == own.id
    assert count(session, Home) == 2 and count(session, Membership) == 2
    assert homes.fr3_violations(session) == []


def test_landlord_who_is_a_tenant_elsewhere_may_create_only_landlord_homes(
    session: Session,
) -> None:
    kari, other = new_user(session, "Kari"), new_user(session, "Annen")
    homes.create_home(session, kari, name="Storgata 12", type="landlord")
    hybel = homes.create_home(session, other, name="Hybel", type="landlord").home
    homes.add_member(session, hybel, kari)

    assert homes.allowed_types(session, kari) == ["landlord"]
    assert homes.lived_in_home(session, kari) == hybel
    with pytest.raises(homes.HomeCreationNotAllowed) as exc:
        homes.create_home(session, kari, name="Eget", type="household")
    assert exc.value.home.id == hybel.id
    homes.create_home(session, kari, name="Storgata 14", type="landlord")
    assert homes.fr3_violations(session) == []


def test_household_member_may_create_a_landlord_home_and_keeps_her_membership(
    session: Session,
) -> None:
    jonas = new_user(session, "Jonas")
    own = homes.create_home(session, jonas, name="Mari og Jonas sitt hjem", type="household")

    created = homes.create_home(session, jonas, name="Jonas sin utleie", type="landlord")

    assert created.role == "landlord"
    roles = {h.home.id: h.role for h in homes.homes_for(session, jonas)}
    assert roles == {own.home.id: "household_member", created.home.id: "landlord"}
    assert homes.lived_in_home(session, jonas) == own.home
    assert homes.fr3_violations(session) == []


def test_household_member_may_not_create_a_household_home(session: Session) -> None:
    user = new_user(session)
    own = homes.create_home(session, user, name="Kollektivet", type="household").home

    with pytest.raises(homes.HomeCreationNotAllowed) as exc:
        homes.create_home(session, user, name="Nytt", type="household")
    assert exc.value.home.id == own.id
    assert count(session, Home) == 1
    assert homes.fr3_violations(session) == []


def test_tenant_may_create_a_landlord_home_but_not_a_household_home(session: Session) -> None:
    landlord, tenant = new_user(session, "Utleier"), new_user(session, "Leietaker")
    home = homes.create_home(session, landlord, name="Storgata 12", type="landlord").home
    homes.add_member(session, home, tenant)

    assert homes.allowed_types(session, tenant) == ["landlord"]
    with pytest.raises(homes.HomeCreationNotAllowed) as exc:
        homes.create_home(session, tenant, name="Eget", type="household")
    assert exc.value.home.id == home.id
    assert count(session, Home) == 1

    created = homes.create_home(session, tenant, name="Eget bygg", type="landlord")
    assert created.role == "landlord"
    assert homes.lived_in_home(session, tenant) == home
    assert homes.fr3_violations(session) == []


def test_refused_create_rolls_back_pending_changes(session: Session) -> None:
    user = new_user(session)
    home = homes.create_home(session, user, name="Kollektivet", type="household").home
    home.name = "Endret uten commit"
    session.add(home)

    with pytest.raises(homes.HomeCreationNotAllowed):
        homes.create_home(session, user, name="Nytt", type="household")
    session.expire_all()
    assert session.get(Home, home.id).name == "Kollektivet"  # type: ignore[union-attr]


def test_invite_to_own_home_is_already_member_not_in_other_home(session: Session) -> None:
    mari = new_user(session, "Mari")
    home = homes.create_home(session, mari, name="Kollektivet", type="household").home

    assert isinstance(homes.join_blocker(session, home, mari), homes.AlreadyMember)


def test_landlord_with_her_own_household_may_not_join_another(session: Session) -> None:
    kari, mari = new_user(session, "Kari"), new_user(session, "Mari")
    homes.create_home(session, kari, name="Storgata 12", type="landlord")
    own = homes.create_home(session, kari, name="Karis", type="household").home
    other = homes.create_home(session, mari, name="Kollektivet", type="household").home

    blocker = homes.join_blocker(session, other, kari)
    assert isinstance(blocker, homes.InOtherHome) and blocker.home.id == own.id


def _function_source(name: str) -> str:
    return inspect_module.getsource(getattr(homes, name))


def test_one_home_limit_is_stated_only_in_lived_in_home() -> None:
    # Story 1.9 (issue #34): a second Household Home later must be a one-place change.
    for name in ("allowed_types", "join_blocker"):
        assert "lived_in_home(" in _function_source(name), name
    landlord_filter = re.compile(r"""!==?\s*["']landlord["']""")
    repo = Path(homes.__file__).resolve().parents[3]
    sources = [*(repo / "backend" / "app").rglob("*.py")]
    sources += [p for p in (repo / "frontend" / "src").rglob("*.ts*") if p.is_file()]
    found = {
        p.relative_to(repo).as_posix(): len(landlord_filter.findall(p.read_text("utf-8")))
        for p in sources
        if landlord_filter.search(p.read_text("utf-8"))
    }
    assert found == {"backend/app/domain/homes.py": 1}
    assert landlord_filter.search(_function_source("lived_in_home"))


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
    set_joined_at(session, ola, a, T0)
    set_joined_at(session, ola, b, T0 + timedelta(seconds=1))

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
        set_joined_at(session, user, home, T0)

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


# Story 1.4: who may invite, and the one-Home rule for joining (decision 3).
@pytest.mark.parametrize(
    ("role", "allowed"), [("household_member", True), ("landlord", True), ("tenant", False)]
)
def test_can_invite_follows_inviter_roles(role: str, allowed: bool) -> None:
    assert homes.can_invite(role) is allowed
    assert (role in homes.INVITER_ROLES) is allowed


@pytest.mark.parametrize("other_type", ["household", "landlord"])
def test_household_member_cannot_join_a_second_home(session: Session, other_type: str) -> None:
    mari, kari = new_user(session, "Mari"), new_user(session, "Kari")
    own = homes.create_home(session, mari, name="Kollektivet", type="household").home
    other = homes.create_home(session, kari, name="Annet", type=other_type).home  # type: ignore[arg-type]

    with pytest.raises(homes.InOtherHome) as exc:
        homes.add_member(session, other, mari)
    assert exc.value.home.id == own.id
    assert count(session, Membership) == 2


def test_tenant_cannot_join_a_second_home(session: Session) -> None:
    landlord, tenant = new_user(session, "Utleier"), new_user(session, "Leietaker")
    first = homes.create_home(session, landlord, name="Storgata 1", type="landlord").home
    second = homes.create_home(session, landlord, name="Storgata 2", type="landlord").home
    homes.add_member(session, first, tenant)

    with pytest.raises(homes.InOtherHome):
        homes.add_member(session, second, tenant)
    assert {h.home.id for h in homes.homes_for(session, tenant)} == {first.id}


def test_refused_add_member_rolls_back_pending_changes(session: Session) -> None:
    mari, jonas = new_user(session, "Mari"), new_user(session, "Jonas")
    home = homes.create_home(session, mari, name="Kollektivet", type="household").home
    home.name = "Endret uten commit"
    session.add(home)

    with pytest.raises(homes.AlreadyMember):
        homes.add_member(session, home, mari)
    session.expire_all()
    assert session.get(Home, home.id).name == "Kollektivet"  # type: ignore[union-attr]
    assert homes.join_blocker(session, home, jonas) is None


# Story 1.5: the members list and the FR-3 "never mixed" invariant.
def test_members_of_lists_household_members_in_join_order(session: Session) -> None:
    mari, jonas = new_user(session, "Mari"), new_user(session, "Jonas")
    home = homes.create_home(session, mari, name="Kollektivet", type="household").home
    homes.add_member(session, home, jonas)
    set_joined_at(session, mari, home, T0)
    set_joined_at(session, jonas, home, T0 + timedelta(seconds=1))

    members = homes.members_of(session, home.id)

    assert [(m.user_id, m.name, m.role) for m in members] == [
        (mari.id, "Mari", "household_member"),
        (jonas.id, "Jonas", "household_member"),
    ]


def test_members_of_orders_by_join_time_not_by_who_created(session: Session) -> None:
    mari, jonas = new_user(session, "Mari"), new_user(session, "Jonas")
    home = homes.create_home(session, mari, name="Kollektivet", type="household").home
    homes.add_member(session, home, jonas)
    set_joined_at(session, mari, home, T0 + timedelta(seconds=1))
    set_joined_at(session, jonas, home, T0)

    assert [m.name for m in homes.members_of(session, home.id)] == ["Jonas", "Mari"]


def test_members_of_puts_the_landlord_first_even_if_a_tenant_joined_earlier(
    session: Session,
) -> None:
    kari, anders, ola = new_user(session, "Kari"), new_user(session, "Anders"), new_user(session)
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    homes.add_member(session, home, anders)
    homes.add_member(session, home, ola)
    set_joined_at(session, anders, home, T0)
    set_joined_at(session, ola, home, T0 + timedelta(seconds=1))
    set_joined_at(session, kari, home, T0 + timedelta(seconds=2))

    assert [(m.name, m.role) for m in homes.members_of(session, home.id)] == [
        ("Kari", "landlord"),
        ("Anders", "tenant"),
        ("Ola", "tenant"),
    ]


def test_members_of_breaks_a_join_time_tie_by_membership_id(session: Session) -> None:
    users = [new_user(session, n) for n in ("A", "B", "C")]
    home = homes.create_home(session, users[0], name="Kollektivet", type="household").home
    for user in users[1:]:
        homes.add_member(session, home, user)
    for user in users:
        set_joined_at(session, user, home, T0)
    by_membership = {
        m.user_id: m.id
        for m in session.exec(select(Membership).where(Membership.home_id == home.id)).all()
    }

    first = [m.user_id for m in homes.members_of(session, home.id)]
    assert first == sorted(by_membership, key=by_membership.__getitem__)


def test_members_of_shows_only_that_homes_members_and_a_landlords_role_per_home(
    session: Session,
) -> None:
    kari, anders, mari = new_user(session, "Kari"), new_user(session, "Anders"), new_user(session)
    rental = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    homes.add_member(session, rental, anders)
    kollektiv = homes.create_home(session, mari, name="Kollektivet", type="household").home
    homes.add_member(session, kollektiv, kari)

    assert {(m.name, m.role) for m in homes.members_of(session, rental.id)} == {
        ("Kari", "landlord"),
        ("Anders", "tenant"),
    }
    assert {(m.name, m.role) for m in homes.members_of(session, kollektiv.id)} == {
        ("Ola", "household_member"),
        ("Kari", "household_member"),
    }
    assert homes.fr3_violations(session) == []


def test_members_of_an_unknown_home_is_empty(session: Session) -> None:
    assert homes.members_of(session, uuid.uuid4()) == []


@pytest.mark.parametrize("type", ["household", "landlord"])
def test_fr3_holds_after_create_home_and_add_member(session: Session, type: str) -> None:
    creator, joiner, other = new_user(session, "A"), new_user(session, "B"), new_user(session)
    home = homes.create_home(session, creator, name="Hjem", type=type).home  # type: ignore[arg-type]
    assert homes.fr3_violations(session) == []

    homes.add_member(session, home, joiner)
    homes.add_member(session, home, other)
    assert homes.fr3_violations(session) == []


def test_fr3_holds_when_a_landlord_joins_another_landlord_home(session: Session) -> None:
    kari, per = new_user(session, "Kari"), new_user(session, "Per")
    homes.create_home(session, per, name="Pers bygg", type="landlord")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home

    homes.add_member(session, home, per)

    assert homes.fr3_violations(session) == []


def _insert_membership(session: Session, home: Home, role: str) -> None:
    # Bypasses the domain on purpose, to prove the check is not vacuous.
    session.execute(
        text(
            "INSERT INTO memberships (id, user_id, home_id, role, created_at) "
            "VALUES (:id, :u, :h, :r, :t)"
        ),
        {
            "id": uuid.uuid4().hex,
            "u": new_user(session, "Inntrenger").id.hex,
            "h": home.id.hex,
            "r": role,
            "t": "2026-11-08 12:00:00",
        },
    )
    session.commit()


@pytest.mark.parametrize(
    ("type", "role"),
    [
        ("household", "tenant"),
        ("household", "landlord"),
        ("landlord", "household_member"),
        ("landlord", "landlord"),
    ],
)
def test_fr3_check_finds_a_mixed_home(session: Session, type: str, role: str) -> None:
    home = homes.create_home(session, new_user(session), name="Hjem", type=type).home  # type: ignore[arg-type]
    _insert_membership(session, home, role)

    assert homes.fr3_violations(session) == [home.id]


def test_fr3_check_finds_a_landlord_home_without_a_landlord(session: Session) -> None:
    home = Home(name="Uten utleier", type="landlord")
    session.add(home)
    session.commit()
    _insert_membership(session, home, "tenant")

    assert homes.fr3_violations(session) == [home.id]


def test_only_create_home_and_add_member_construct_a_membership() -> None:
    # Every other write path (register with invite_token, invites.accept, the seed) goes through
    # add_member. Guards against a new Membership(...) constructor outside create_home/add_member;
    # it does not see model_validate, insert(Membership) or raw SQL.
    constructor = re.compile(r"(?<!class )\bMembership\(")
    app_dir = Path(homes.__file__).resolve().parents[1]
    found = {
        path.relative_to(app_dir).as_posix(): len(constructor.findall(path.read_text("utf-8")))
        for path in app_dir.rglob("*.py")
        if constructor.search(path.read_text("utf-8"))
    }
    assert found == {"domain/homes.py": 2}
    source = Path(homes.__file__).read_text("utf-8")
    for function in ("def create_home(", "def add_member("):
        start = source.index(function)
        end = source.find("\ndef ", start + 1)
        assert constructor.search(source[start:end]), function


# Story 1.8 (FR-23, AD-16): leaving and removing delete the Membership row only.
def membership_of(session: Session, user: User, home: Home) -> Membership:
    return session.exec(
        select(Membership).where(Membership.user_id == user.id, Membership.home_id == home.id)
    ).one()


@pytest.mark.parametrize(
    ("role", "allowed"), [("household_member", True), ("tenant", True), ("landlord", False)]
)
def test_can_leave_follows_leaver_roles(role: str, allowed: bool) -> None:
    assert homes.can_leave(role) is allowed


@pytest.mark.parametrize(
    ("caller", "target", "allowed"),
    [
        ("landlord", "tenant", True),
        ("landlord", "landlord", False),
        ("household_member", "household_member", False),
        ("tenant", "tenant", False),
        ("tenant", "landlord", False),
    ],
)
def test_can_remove_only_a_landlord_on_a_tenant(caller: str, target: str, allowed: bool) -> None:
    assert homes.can_remove(caller, target) is allowed


def test_household_member_leaves_and_the_others_stay(session: Session) -> None:
    mari, jonas = new_user(session, "Mari"), new_user(session, "Jonas")
    home = homes.create_home(session, mari, name="Kollektivet", type="household").home
    homes.add_member(session, home, jonas)

    homes.leave(session, membership_of(session, jonas, home))

    assert [m.name for m in homes.members_of(session, home.id)] == ["Mari"]
    assert homes.homes_for(session, jonas) == []
    assert homes.allowed_types(session, jonas) == ["household", "landlord"]
    assert homes.fr3_violations(session) == []


def test_last_household_member_leaves_and_the_home_stays(session: Session) -> None:
    ola = new_user(session, "Ola")
    home = homes.create_home(session, ola, name="Hybel", type="household").home

    homes.leave(session, membership_of(session, ola, home))

    assert session.get(Home, home.id) is not None
    assert count(session, Membership) == 0
    assert count(session, User) == 1
    assert homes.fr3_violations(session) == []


def test_tenant_leaves_and_the_landlord_stays(session: Session) -> None:
    kari, anders = new_user(session, "Kari"), new_user(session, "Anders")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    homes.add_member(session, home, anders)

    homes.leave(session, membership_of(session, anders, home))

    assert [(m.name, m.role) for m in homes.members_of(session, home.id)] == [("Kari", "landlord")]
    assert homes.fr3_violations(session) == []


def test_a_landlord_may_not_leave_her_own_home(session: Session) -> None:
    kari = new_user(session, "Kari")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home

    with pytest.raises(ValueError):
        homes.leave(session, membership_of(session, kari, home))
    assert count(session, Membership) == 1


def test_leaving_twice_deletes_nothing_else_and_raises_nothing(session: Session) -> None:
    mari, jonas = new_user(session, "Mari"), new_user(session, "Jonas")
    home = homes.create_home(session, mari, name="Kollektivet", type="household").home
    homes.add_member(session, home, jonas)
    membership = membership_of(session, jonas, home)

    homes.leave(session, membership)
    homes.leave(session, membership)

    assert [m.name for m in homes.members_of(session, home.id)] == ["Mari"]


def test_leaving_while_being_removed_raises_nothing(session: Session) -> None:
    kari, anders = new_user(session, "Kari"), new_user(session, "Anders")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    homes.add_member(session, home, anders)
    anders_membership = membership_of(session, anders, home)

    homes.remove_tenant(session, membership_of(session, kari, home), anders.id)
    homes.leave(session, anders_membership)

    assert [m.name for m in homes.members_of(session, home.id)] == ["Kari"]


def test_landlord_removes_a_tenant(session: Session) -> None:
    kari, anders, ola = new_user(session, "Kari"), new_user(session, "Anders"), new_user(session)
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    homes.add_member(session, home, anders)
    homes.add_member(session, home, ola)

    homes.remove_tenant(session, membership_of(session, kari, home), anders.id)

    assert [m.name for m in homes.members_of(session, home.id)] == ["Kari", "Ola"]
    assert homes.homes_for(session, anders) == []
    assert homes.fr3_violations(session) == []


def test_remove_refuses_the_landlord_herself_an_outsider_and_a_tenant_elsewhere(
    session: Session,
) -> None:
    kari, anders = new_user(session, "Kari"), new_user(session, "Anders")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    other = homes.create_home(session, kari, name="Storgata 14", type="landlord").home
    homes.add_member(session, other, anders)
    outsider = new_user(session, "Per")
    landlord = membership_of(session, kari, home)

    for target in (kari.id, outsider.id, anders.id, uuid.uuid4()):
        with pytest.raises(homes.NotATenant):
            homes.remove_tenant(session, landlord, target)
    assert count(session, Membership) == 3


def test_a_household_member_may_not_remove_another(session: Session) -> None:
    mari, jonas = new_user(session, "Mari"), new_user(session, "Jonas")
    home = homes.create_home(session, mari, name="Kollektivet", type="household").home
    homes.add_member(session, home, jonas)

    with pytest.raises(homes.NotATenant):
        homes.remove_tenant(session, membership_of(session, mari, home), jonas.id)
    assert count(session, Membership) == 2


def test_removing_a_tenant_who_already_left_raises_not_a_tenant(session: Session) -> None:
    kari, anders = new_user(session, "Kari"), new_user(session, "Anders")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    homes.add_member(session, home, anders)
    homes.leave(session, membership_of(session, anders, home))

    with pytest.raises(homes.NotATenant):
        homes.remove_tenant(session, membership_of(session, kari, home), anders.id)
    assert count(session, Membership) == 1


def test_after_leaving_a_user_may_create_a_home_or_rejoin(session: Session) -> None:
    mari, jonas = new_user(session, "Mari"), new_user(session, "Jonas")
    home = homes.create_home(session, mari, name="Kollektivet", type="household").home
    homes.add_member(session, home, jonas)
    homes.leave(session, membership_of(session, jonas, home))

    assert homes.join_blocker(session, home, jonas) is None
    own = homes.create_home(session, jonas, name="Jonas sin hybel", type="household")
    assert own.role == "household_member"
    assert homes.fr3_violations(session) == []


def test_is_member_reads_only_current_memberships(session: Session) -> None:
    mari, jonas = new_user(session, "Mari"), new_user(session, "Jonas")
    home = homes.create_home(session, mari, name="Kollektivet", type="household").home
    homes.add_member(session, home, jonas)
    assert homes.is_member(session, home.id, jonas.id)

    homes.leave(session, membership_of(session, jonas, home))
    assert not homes.is_member(session, home.id, jonas.id)
    assert homes.is_member(session, home.id, mari.id)


def test_remove_raises_not_a_tenant_when_the_tenant_left_in_between(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    kari, anders = new_user(session, "Kari"), new_user(session, "Anders")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    homes.add_member(session, home, anders)
    landlord = membership_of(session, kari, home)
    real_can_remove = homes.can_remove

    def anders_leaves_first(caller_role: str, target_role: str) -> bool:
        # Runs between the role SELECT and the DELETE: Anders leaves in the meantime.
        homes.leave(session, membership_of(session, anders, home))
        return real_can_remove(caller_role, target_role)

    monkeypatch.setattr(homes, "can_remove", anders_leaves_first)
    with pytest.raises(homes.NotATenant):
        homes.remove_tenant(session, landlord, anders.id)
    assert [m.name for m in homes.members_of(session, home.id)] == ["Kari"]


def test_only_leave_and_remove_tenant_delete_a_membership() -> None:
    # Story 1.8 (AD-16): Membership rows are deleted only in domain/homes, by these two functions.
    # Like the constructor guard above, it does not see session.delete(obj) or raw SQL.
    statement = re.compile(r"\bdelete\(Membership\b")
    app_dir = Path(homes.__file__).resolve().parents[1]
    found = {
        path.relative_to(app_dir).as_posix(): len(statement.findall(path.read_text("utf-8")))
        for path in app_dir.rglob("*.py")
        if statement.search(path.read_text("utf-8"))
    }
    assert found == {"domain/homes.py": 2}
    source = Path(homes.__file__).read_text("utf-8")
    for function in ("def leave(", "def remove_tenant("):
        start = source.index(function)
        end = source.find("\ndef ", start + 1)
        assert statement.search(source[start:end]), function
