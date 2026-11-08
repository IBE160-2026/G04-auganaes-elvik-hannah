"""Story 1.3 (FR-1, FR-3): GET and POST /api/homes, one test per row of the spec's matrix.

Story 1.5 (FR-3, SM-6, AD-2): GET /api/homes/{home_id}/members, and the FR-3 check after the
route-level write paths.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, col, func, select

from app.domain import homes
from app.models.home import Home
from app.models.membership import Membership
from app.models.user import User
from app.permissions.require_role import FORBIDDEN
from app.routes.homes import ALREADY_IN_HOME, LANDLORD_ONLY


def sign_up(client: TestClient, name: str = "Ola") -> dict[str, str]:
    """Registers a new user and returns the Authorization header for them."""
    email = f"{name.lower()}-{uuid.uuid4().hex[:6]}@example.com"
    response = client.post(
        "/api/auth/register", json={"email": email, "name": name, "password": "hemmelig1"}
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create(client: TestClient, auth: dict[str, str], name: str, type: str):
    return client.post("/api/homes", json={"name": name, "type": type}, headers=auth)


def counts(engine: Engine) -> tuple[int, int]:
    with Session(engine) as session:
        return (
            session.exec(select(func.count()).select_from(Home)).one(),
            session.exec(select(func.count()).select_from(Membership)).one(),
        )


@pytest.mark.parametrize(
    ("type", "role"), [("household", "household_member"), ("landlord", "landlord")]
)
def test_create_without_memberships_is_201_with_derived_role(
    client: TestClient, engine: Engine, type: str, role: str
) -> None:
    auth = sign_up(client)
    response = create(client, auth, "  Kollektivet  ", type)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Kollektivet"
    assert (body["type"], body["role"]) == (type, role)
    uuid.UUID(body["id"])
    assert counts(engine) == (1, 1)


def test_role_in_the_body_is_ignored(client: TestClient, engine: Engine) -> None:
    auth = sign_up(client)
    response = client.post(
        "/api/homes",
        json={"name": "Hjem", "type": "household", "role": "landlord"},
        headers=auth,
    )
    assert response.status_code == 201
    assert response.json()["role"] == "household_member"


def test_landlord_creates_another_landlord_home(client: TestClient, engine: Engine) -> None:
    auth = sign_up(client)
    first = create(client, auth, "Storgata 1", "landlord")
    second = create(client, auth, "Storgata 2", "landlord")
    assert (first.status_code, second.status_code) == (201, 201)
    # Distinct times, so the order never depends on the clock's resolution (Windows: ~15.6 ms).
    t0 = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
    with Session(engine) as session:
        for response, when in ((first, t0), (second, t0 + timedelta(seconds=1))):
            # homes_for orders by the Membership (Story 1.4).
            membership = session.exec(
                select(Membership).where(Membership.home_id == uuid.UUID(response.json()["id"]))
            ).one()
            membership.created_at = when
            session.add(membership)
        session.commit()

    body = client.get("/api/homes", headers=auth).json()
    assert [h["name"] for h in body["homes"]] == ["Storgata 2", "Storgata 1"]
    assert body["allowed_types"] == ["landlord"]


def test_landlord_creating_household_is_409_and_writes_nothing(
    client: TestClient, engine: Engine
) -> None:
    auth = sign_up(client)
    create(client, auth, "Storgata 1", "landlord")

    response = create(client, auth, "Kollektivet", "household")
    assert response.status_code == 409
    assert response.json() == {"detail": LANDLORD_ONLY}
    assert counts(engine) == (1, 1)


@pytest.mark.parametrize("type", ["household", "landlord"])
def test_member_creating_again_is_409_and_writes_nothing(
    client: TestClient, engine: Engine, type: str
) -> None:
    auth = sign_up(client)
    create(client, auth, "Kollektivet", "household")

    response = create(client, auth, "Nytt", type)
    assert response.status_code == 409
    assert response.json() == {"detail": ALREADY_IN_HOME}
    assert counts(engine) == (1, 1)


def test_tenant_creating_is_409(client: TestClient, engine: Engine) -> None:
    landlord_auth = sign_up(client, "Utleier")
    home_id = create(client, landlord_auth, "Storgata 1", "landlord").json()["id"]
    tenant_auth = sign_up(client, "Leietaker")
    with Session(engine) as session:
        home = session.get(Home, uuid.UUID(home_id))
        tenant = session.exec(select(User).where(User.name == "Leietaker")).one()
        homes.add_member(session, home, tenant)

    body = client.get("/api/homes", headers=tenant_auth).json()
    assert [(h["name"], h["role"]) for h in body["homes"]] == [("Storgata 1", "tenant")]
    assert body["allowed_types"] == []
    response = create(client, tenant_auth, "Eget", "landlord")
    assert response.status_code == 409
    assert response.json() == {"detail": ALREADY_IN_HOME}


@pytest.mark.parametrize("name", ["", "   ", "x" * 61])
def test_invalid_name_is_422_on_the_name_field(
    client: TestClient, engine: Engine, name: str
) -> None:
    response = create(client, sign_up(client), name, "household")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "name"]
    assert counts(engine) == (0, 0)


def test_name_of_60_characters_is_accepted(client: TestClient) -> None:
    assert create(client, sign_up(client), "x" * 60, "household").status_code == 201


def test_unknown_type_is_422(client: TestClient, engine: Engine) -> None:
    response = create(client, sign_up(client), "Hjem", "other")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "type"]
    assert counts(engine) == (0, 0)


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_signed_out_is_401(client: TestClient, engine: Engine, method: str) -> None:
    response = client.request(method, "/api/homes", json={"name": "Hjem", "type": "household"})
    assert response.status_code == 401
    assert counts(engine) == (0, 0)


def test_list_without_homes_is_empty_with_both_types(client: TestClient) -> None:
    body = client.get("/api/homes", headers=sign_up(client)).json()
    assert body == {"homes": [], "allowed_types": ["household", "landlord"]}


def test_list_shows_only_the_callers_homes_with_their_role(client: TestClient) -> None:
    ola, kari = sign_up(client, "Ola"), sign_up(client, "Kari")
    created = create(client, ola, "Olas hjem", "household").json()
    create(client, kari, "Karis utleie", "landlord")

    body = client.get("/api/homes", headers=ola).json()
    assert body["homes"] == [created]
    assert body["allowed_types"] == []


# Story 1.5: GET /api/homes/{home_id}/members, one test per row of the spec's matrix.
def members(client: TestClient, auth: dict[str, str] | None, home_id: str):
    return client.get(f"/api/homes/{home_id}/members", headers=auth or {})


def invite_link(client: TestClient, auth: dict[str, str], home_id: str) -> str:
    response = client.post(f"/api/homes/{home_id}/invites", headers=auth)
    assert response.status_code == 201
    return response.json()["token"]


def join(client: TestClient, inviter: dict[str, str], home_id: str, joiner: dict[str, str]):
    token = invite_link(client, inviter, home_id)
    response = client.post(f"/api/invites/{token}/accept", headers=joiner)
    assert response.status_code == 200


def pin_joined_at(engine: Engine, home_id: str, names: list[str]) -> None:
    """Pins created_at in this order, so ordering never depends on the clock's resolution."""
    t0 = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
    with Session(engine) as session:
        for i, name in enumerate(names):
            membership = session.exec(
                select(Membership)
                .join(User, col(User.id) == col(Membership.user_id))
                .where(Membership.home_id == uuid.UUID(home_id), User.name == name)
            ).one()
            membership.created_at = t0 + timedelta(seconds=i)
            session.add(membership)
        session.commit()


def rows(response) -> list[tuple[str, str, bool]]:
    assert response.status_code == 200
    return [(m["name"], m["role"], m["is_you"]) for m in response.json()["members"]]


def fr3_violations(engine: Engine) -> list[uuid.UUID]:
    with Session(engine) as session:
        return homes.fr3_violations(session)


@pytest.fixture
def household(client: TestClient, engine: Engine) -> tuple[dict[str, str], dict[str, str], str]:
    mari, jonas = sign_up(client, "Mari"), sign_up(client, "Jonas")
    home_id = create(client, mari, "Kollektivet", "household").json()["id"]
    join(client, mari, home_id, jonas)
    pin_joined_at(engine, home_id, ["Mari", "Jonas"])
    return mari, jonas, home_id


@pytest.fixture
def rental(client: TestClient, engine: Engine) -> tuple[dict[str, str], dict[str, str], str]:
    kari, anders = sign_up(client, "Kari"), sign_up(client, "Anders")
    home_id = create(client, kari, "Storgata 12", "landlord").json()["id"]
    join(client, kari, home_id, anders)
    # Anders first in time: the Landlord still comes first.
    pin_joined_at(engine, home_id, ["Anders", "Kari"])
    return kari, anders, home_id


def test_household_member_sees_every_member_in_join_order(client: TestClient, household) -> None:
    mari, _, home_id = household
    response = members(client, mari, home_id)

    assert rows(response) == [
        ("Mari", "household_member", True),
        ("Jonas", "household_member", False),
    ]
    # Decision 1: no email leaves the server.
    assert all(set(m) == {"user_id", "name", "role", "is_you"} for m in response.json()["members"])


def test_landlord_sees_herself_first_then_the_tenant(client: TestClient, rental) -> None:
    kari, _, home_id = rental
    assert rows(members(client, kari, home_id)) == [
        ("Kari", "landlord", True),
        ("Anders", "tenant", False),
    ]


def test_tenant_sees_the_same_list(client: TestClient, rental) -> None:
    _, anders, home_id = rental
    assert rows(members(client, anders, home_id)) == [
        ("Kari", "landlord", False),
        ("Anders", "tenant", True),
    ]


def test_member_of_another_home_gets_the_same_403_as_for_an_unknown_home(
    client: TestClient, household, rental
) -> None:
    mari, _, _ = household
    _, _, rental_id = rental

    other_home = members(client, mari, rental_id)
    missing_home = members(client, mari, str(uuid.uuid4()))

    assert other_home.status_code == missing_home.status_code == 403
    assert other_home.json() == missing_home.json() == {"detail": FORBIDDEN}


def test_role_in_the_query_is_ignored(client: TestClient, household, rental) -> None:
    mari, _, _ = household
    _, _, rental_id = rental
    response = client.get(
        f"/api/homes/{rental_id}/members",
        params={"role": "landlord", "home_id": household[2]},
        headers=mari,
    )
    assert response.status_code == 403


def test_members_with_a_malformed_home_id_is_422(client: TestClient) -> None:
    response = members(client, sign_up(client), "not-a-uuid")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "home_id"]


def test_members_signed_out_is_401(client: TestClient, household) -> None:
    assert members(client, None, household[2]).status_code == 401


def test_landlord_who_is_also_a_household_member_has_her_role_per_home(
    client: TestClient, engine: Engine, household, rental
) -> None:
    mari, _, kollektiv_id = household
    kari, _, rental_id = rental
    join(client, mari, kollektiv_id, kari)

    assert ("Kari", "landlord", True) in rows(members(client, kari, rental_id))
    assert ("Kari", "household_member", True) in rows(members(client, kari, kollektiv_id))
    assert fr3_violations(engine) == []


def test_single_member_sees_only_themself(client: TestClient) -> None:
    auth = sign_up(client, "Ola")
    home_id = create(client, auth, "Hjem", "household").json()["id"]
    assert rows(members(client, auth, home_id)) == [("Ola", "household_member", True)]


def test_two_members_with_the_same_name_are_told_apart_by_is_you(
    client: TestClient, engine: Engine
) -> None:
    first, second = sign_up(client, "Ola"), sign_up(client, "Ola")
    home_id = create(client, first, "Hjem", "household").json()["id"]
    join(client, first, home_id, second)

    body = members(client, second, home_id).json()["members"]
    assert [m["name"] for m in body] == ["Ola", "Ola"]
    assert sorted(m["is_you"] for m in body) == [False, True]
    assert len({m["user_id"] for m in body}) == 2


# FR-3 (decision 2): the "never mixed" check after every write path that makes a Membership.
def test_fr3_holds_after_register_with_an_invite_token(
    client: TestClient, engine: Engine, rental
) -> None:
    kari, _, home_id = rental
    token = invite_link(client, kari, home_id)
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"ny-{uuid.uuid4().hex[:6]}@example.com",
            "name": "Ny",
            "password": "hemmelig1",
            "invite_token": token,
        },
    )
    assert response.json()["joined_home_id"] == home_id
    assert fr3_violations(engine) == []


def test_fr3_holds_when_a_landlord_accepts_into_another_landlord_home(
    client: TestClient, engine: Engine, rental
) -> None:
    kari, _, home_id = rental
    per = sign_up(client, "Per")
    create(client, per, "Pers bygg", "landlord")
    join(client, kari, home_id, per)

    roles = [r for _, r, _ in rows(members(client, kari, home_id))]
    assert roles == ["landlord", "tenant", "tenant"]
    assert fr3_violations(engine) == []
