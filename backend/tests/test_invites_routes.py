"""Story 1.4 (FR-2, UJ-1, UJ-2): the invite routes, one test per row of the spec's matrix."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, func, select

from app.clock import utc_now
from app.models.invite_link import InviteLink
from app.models.membership import Membership
from app.models.user import User
from app.permissions.require_role import FORBIDDEN
from app.routes.invites import invalid_message
from app.routes.messages import already_member_message, in_other_home_message
from tests.helpers import register_via_api, sign_up

INVALID_LANDLORD = "Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra utleieren."
INVALID_HOUSEHOLD = (
    "Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra et husstandsmedlem."
)
INVALID_UNKNOWN = (
    "Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra den som inviterte deg."
)


def create_home(client: TestClient, auth: dict[str, str], type: str, name: str = "Hjem") -> str:
    response = client.post("/api/homes", json={"name": name, "type": type}, headers=auth)
    assert response.status_code == 201
    return response.json()["id"]


def make_link(client: TestClient, auth: dict[str, str], home_id: str):
    return client.post(f"/api/homes/{home_id}/invites", headers=auth)


def token_for(client: TestClient, auth: dict[str, str], home_id: str) -> str:
    response = make_link(client, auth, home_id)
    assert response.status_code == 201
    return response.json()["token"]


def accept(client: TestClient, auth: dict[str, str], token: str):
    return client.post(f"/api/invites/{token}/accept", headers=auth)


def link_count(engine: Engine) -> int:
    with Session(engine) as session:
        return session.exec(select(func.count()).select_from(InviteLink)).one()


def membership_count(engine: Engine) -> int:
    with Session(engine) as session:
        return session.exec(select(func.count()).select_from(Membership)).one()


def expire_links(engine: Engine) -> None:
    with Session(engine) as session:
        for link in session.exec(select(InviteLink)).all():
            link.expires_at = utc_now() - timedelta(seconds=1)
            session.add(link)
        session.commit()


@pytest.fixture
def household(client: TestClient) -> tuple[dict[str, str], str]:
    auth = sign_up(client, "Mari")
    return auth, create_home(client, auth, "household", "Kollektivet")


@pytest.fixture
def rental(client: TestClient) -> tuple[dict[str, str], str]:
    auth = sign_up(client, "Kari")
    return auth, create_home(client, auth, "landlord", "Storgata 12")


# Generate
def test_household_member_creates_a_household_member_link(
    client: TestClient, household: tuple[dict[str, str], str]
) -> None:
    auth, home_id = household
    response = make_link(client, auth, home_id)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"token", "role", "expires_at"}
    assert body["role"] == "household_member"
    expires = datetime.fromisoformat(body["expires_at"])
    assert timedelta(days=6, hours=23) < expires - datetime.now(UTC) <= timedelta(days=7)


def test_landlord_creates_a_tenant_link(
    client: TestClient, rental: tuple[dict[str, str], str]
) -> None:
    auth, home_id = rental
    response = make_link(client, auth, home_id)
    assert response.status_code == 201
    assert response.json()["role"] == "tenant"


def test_tenant_calling_the_api_directly_is_403_and_nothing_is_written(
    client: TestClient, engine: Engine, rental: tuple[dict[str, str], str]
) -> None:
    landlord_auth, home_id = rental
    tenant_auth = sign_up(client, "Anders")
    assert accept(client, tenant_auth, token_for(client, landlord_auth, home_id)).status_code == 200

    response = make_link(client, tenant_auth, home_id)

    assert response.status_code == 403
    assert response.json() == {"detail": FORBIDDEN}
    assert link_count(engine) == 1


def test_outsider_and_unknown_home_get_the_same_403(
    client: TestClient, engine: Engine, household: tuple[dict[str, str], str]
) -> None:
    _, home_id = household
    outsider = sign_up(client, "Per")
    create_home(client, outsider, "household", "Pers")

    other_home = make_link(client, outsider, home_id)
    missing_home = make_link(client, outsider, str(uuid.uuid4()))

    assert other_home.status_code == missing_home.status_code == 403
    assert other_home.json() == missing_home.json() == {"detail": FORBIDDEN}
    assert link_count(engine) == 0


def test_malformed_home_id_is_422(client: TestClient) -> None:
    assert make_link(client, sign_up(client), "ikke-en-uuid").status_code == 422


def test_generate_signed_out_is_401(
    client: TestClient, household: tuple[dict[str, str], str]
) -> None:
    assert client.post(f"/api/homes/{household[1]}/invites").status_code == 401


def test_role_in_the_query_or_body_is_ignored(
    client: TestClient, household: tuple[dict[str, str], str]
) -> None:
    auth, home_id = household
    response = client.post(
        f"/api/homes/{home_id}/invites?role=landlord", json={"role": "landlord"}, headers=auth
    )
    assert response.json()["role"] == "household_member"


# Preview
def test_preview_signed_out_shows_home_and_role(
    client: TestClient, household: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *household)

    response = client.get(f"/api/invites/{token}")

    assert response.status_code == 200
    assert response.json() == {
        "status": "valid",
        "home_type": "household",
        "home_name": "Kollektivet",
        "role": "household_member",
        "viewer": None,
        "other_home_name": None,
    }


def test_preview_signed_in_says_can_join(
    client: TestClient, household: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *household)
    body = client.get(f"/api/invites/{token}", headers=sign_up(client, "Jonas")).json()
    assert body["viewer"] == "can_join"


def test_preview_for_a_member_elsewhere_names_that_home(
    client: TestClient, household: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *household)
    jonas = sign_up(client, "Jonas")
    create_home(client, jonas, "household", "Jonas sitt")

    body = client.get(f"/api/invites/{token}", headers=jonas).json()
    assert (body["viewer"], body["other_home_name"]) == ("in_other_home", "Jonas sitt")


def test_preview_with_an_invalid_bearer_is_401_not_signed_out(
    client: TestClient, household: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *household)
    response = client.get(f"/api/invites/{token}", headers={"Authorization": "Bearer utlopt"})
    assert response.status_code == 401


def test_preview_of_an_unknown_token_is_200_invalid(client: TestClient) -> None:
    response = client.get("/api/invites/finnes-ikke")
    assert response.status_code == 200
    assert response.json()["status"] == "invalid"
    assert response.json()["home_type"] is None


def test_preview_of_an_expired_link_is_invalid_with_home_type(
    client: TestClient, engine: Engine, rental: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *rental)
    expire_links(engine)

    body = client.get(f"/api/invites/{token}").json()
    assert (body["status"], body["home_type"], body["home_name"]) == ("invalid", "landlord", None)


def test_overlong_token_is_422(client: TestClient) -> None:
    assert client.get(f"/api/invites/{'x' * 65}").status_code == 422


# Accept
def test_join_gives_the_link_role_and_marks_the_link_used(
    client: TestClient, engine: Engine, rental: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *rental)
    anders = sign_up(client, "Anders")

    response = accept(client, anders, token)

    assert response.status_code == 200
    body = response.json()
    assert (body["name"], body["role"], body["can_invite"]) == ("Storgata 12", "tenant", False)
    homes_body = client.get("/api/homes", headers=anders).json()
    assert [(h["name"], h["role"]) for h in homes_body["homes"]] == [("Storgata 12", "tenant")]
    with Session(engine) as session:
        assert session.exec(select(InviteLink)).one().used_at is not None


def test_already_in_the_home_is_409_and_the_link_stays_unused(
    client: TestClient, engine: Engine, rental: tuple[dict[str, str], str]
) -> None:
    auth, _ = rental
    token = token_for(client, *rental)

    preview = client.get(f"/api/invites/{token}", headers=auth).json()
    response = accept(client, auth, token)

    assert preview["viewer"] == "already_member"
    assert response.status_code == 409
    assert response.json() == {"detail": already_member_message("Storgata 12")}
    assert client.get(f"/api/invites/{token}").json()["status"] == "valid"


def test_in_another_home_is_409_with_decision_3_message_and_writes_nothing(
    client: TestClient, engine: Engine, household: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *household)
    jonas = sign_up(client, "Jonas")
    create_home(client, jonas, "household", "Jonas sitt")

    response = accept(client, jonas, token)

    assert response.status_code == 409
    assert response.json() == {"detail": in_other_home_message("Jonas sitt")}
    assert response.json()["detail"] == (
        "Du er allerede med i «Jonas sitt». Du kan bare være med i ett hjem om gangen."
    )
    assert membership_count(engine) == 2
    assert client.get(f"/api/invites/{token}").json()["status"] == "valid"


def test_landlord_joins_a_household_home_and_may_still_create_landlord_homes(
    client: TestClient, household: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *household)
    kari = sign_up(client, "Kari")
    create_home(client, kari, "landlord", "Storgata 1")

    assert accept(client, kari, token).json()["role"] == "household_member"
    assert client.get("/api/homes", headers=kari).json()["allowed_types"] == ["landlord"]


def test_landlord_joins_another_landlords_home_as_tenant(
    client: TestClient, rental: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *rental)
    other = sign_up(client, "Ola")
    create_home(client, other, "landlord", "Storgata 1")

    assert accept(client, other, token).json()["role"] == "tenant"


def test_landlord_second_join_is_409(
    client: TestClient,
    household: tuple[dict[str, str], str],
    rental: tuple[dict[str, str], str],
) -> None:
    first, second = token_for(client, *household), token_for(client, *rental)
    ola = sign_up(client, "Ola")
    create_home(client, ola, "landlord", "Olas utleie")
    assert accept(client, ola, first).status_code == 200

    assert client.get(f"/api/invites/{second}", headers=ola).json()["viewer"] == "in_other_home"
    assert accept(client, ola, second).status_code == 409


def test_used_by_this_viewer_is_already_member(
    client: TestClient, household: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *household)
    jonas = sign_up(client, "Jonas")
    accept(client, jonas, token)

    body = client.get(f"/api/invites/{token}", headers=jonas).json()
    assert (body["status"], body["viewer"], body["home_name"]) == (
        "valid",
        "already_member",
        "Kollektivet",
    )


def test_leaver_reopening_their_own_used_link_gets_invalid_and_410(
    client: TestClient, engine: Engine, household: tuple[dict[str, str], str]
) -> None:
    # Story 1.8: once Jonas has left, the link he joined with is used like any other.
    token = token_for(client, *household)
    jonas = sign_up(client, "Jonas")
    accept(client, jonas, token)
    assert client.delete(f"/api/homes/{household[1]}/members/me", headers=jonas).status_code == 204

    body = client.get(f"/api/invites/{token}", headers=jonas).json()
    assert (body["status"], body["viewer"]) == ("invalid", None)
    response = accept(client, jonas, token)
    assert response.status_code == 410
    assert response.json() == {"detail": INVALID_HOUSEHOLD}
    assert membership_count(engine) == 1


@pytest.mark.parametrize("fixture", ["household", "rental"])
def test_link_used_by_someone_else_is_410_even_for_a_member_elsewhere(
    client: TestClient, request: pytest.FixtureRequest, fixture: str
) -> None:
    home = request.getfixturevalue(fixture)
    token = token_for(client, *home)
    accept(client, sign_up(client, "Jonas"), token)
    # 410 wins over 409: Per is in another Home, but the link is what failed.
    per = sign_up(client, "Per")
    create_home(client, per, "household", "Pers")

    response = accept(client, per, token)

    assert response.status_code == 410
    expected = INVALID_HOUSEHOLD if fixture == "household" else INVALID_LANDLORD
    assert response.json() == {"detail": expected}
    assert client.get(f"/api/invites/{token}", headers=per).json()["status"] == "invalid"


def test_expired_link_is_410(
    client: TestClient, engine: Engine, rental: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *rental)
    expire_links(engine)

    response = accept(client, sign_up(client, "Anders"), token)
    assert response.status_code == 410
    assert response.json() == {"detail": INVALID_LANDLORD}


def test_unknown_link_is_410_with_the_generic_message(client: TestClient) -> None:
    response = accept(client, sign_up(client), "finnes-ikke")
    assert response.status_code == 410
    assert response.json() == {"detail": INVALID_UNKNOWN}
    assert invalid_message(None) == INVALID_UNKNOWN


def test_accept_signed_out_is_401(
    client: TestClient, household: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *household)
    assert client.post(f"/api/invites/{token}/accept").status_code == 401


# Register through a link
def test_register_with_a_valid_link_joins_in_the_same_request(
    client: TestClient, engine: Engine, household: tuple[dict[str, str], str]
) -> None:
    _, home_id = household
    token = token_for(client, *household)

    response = register_via_api(client, "Jonas", invite_token=token)

    assert response.status_code == 201
    assert response.json()["joined_home_id"] == home_id
    auth = {"Authorization": f"Bearer {response.json()['access_token']}"}
    homes_body = client.get("/api/homes", headers=auth).json()
    assert [(h["name"], h["role"]) for h in homes_body["homes"]] == [
        ("Kollektivet", "household_member")
    ]
    # The invite page then sees the link as used by this viewer.
    assert client.get(f"/api/invites/{token}", headers=auth).json()["viewer"] == "already_member"


def test_register_with_a_dead_link_still_creates_the_account(
    client: TestClient, engine: Engine, rental: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *rental)
    expire_links(engine)

    response = register_via_api(client, "Anders", invite_token=token)

    assert response.status_code == 201
    assert response.json()["joined_home_id"] is None
    with Session(engine) as session:
        assert session.exec(select(User).where(User.name == "Anders")).one()
    assert membership_count(engine) == 1


def test_register_with_a_taken_email_is_409_and_leaves_the_link_unused(
    client: TestClient, engine: Engine, household: tuple[dict[str, str], str]
) -> None:
    token = token_for(client, *household)
    body = {"email": "jonas@example.com", "name": "Jonas", "password": "hemmelig1"}
    assert client.post("/api/auth/register", json=body).status_code == 201

    response = client.post("/api/auth/register", json={**body, "invite_token": token})

    assert response.status_code == 409
    assert client.get(f"/api/invites/{token}").json()["status"] == "valid"


def test_register_with_an_overlong_token_is_422(client: TestClient) -> None:
    response = register_via_api(client, invite_token="x" * 65)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "invite_token"]


# can_invite on GET /api/homes
def test_can_invite_is_true_for_members_and_landlords_and_false_for_tenants(
    client: TestClient,
    household: tuple[dict[str, str], str],
    rental: tuple[dict[str, str], str],
) -> None:
    anders = sign_up(client, "Anders")
    accept(client, anders, token_for(client, *rental))

    for auth, expected in ((household[0], True), (rental[0], True), (anders, False)):
        [home] = client.get("/api/homes", headers=auth).json()["homes"]
        assert home["can_invite"] is expected
