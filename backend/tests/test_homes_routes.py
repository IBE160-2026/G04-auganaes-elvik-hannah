"""Story 1.3 (FR-1, FR-3): GET and POST /api/homes, one test per row of the spec's matrix."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, func, select

from app.domain import homes
from app.models.home import Home
from app.models.membership import Membership
from app.models.user import User
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
