"""Story 1.2 (FR-1, AD-7): every row of the I/O & edge-case matrix in the spec."""

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event
from sqlmodel import Session, select

from app.domain import tokens
from app.models.user import User
from tests.conftest import TEST_SECRET, make_client

EMAIL = "ola@example.com"
PASSWORD = "hemmelig1"
REGISTER = {"email": EMAIL, "name": "Ola", "password": PASSWORD}


def register(client: TestClient, **overrides: str):
    return client.post("/api/auth/register", json={**REGISTER, **overrides})


def set_cookie_header(response) -> str:
    headers = response.headers.get_list("set-cookie")
    assert len(headers) == 1, headers
    return headers[0]


def refresh_cookie_value(response) -> str:
    return set_cookie_header(response).split(";")[0].split("=", 1)[1]


def assert_refresh_cookie_set(header: str, *, secure: bool) -> None:
    assert header.startswith("husly_refresh=")
    assert "HttpOnly" in header
    assert "SameSite=lax" in header
    assert "Path=/api/auth/refresh" in header
    assert "Max-Age=2592000" in header
    assert ("Secure" in header) is secure


def assert_refresh_cookie_cleared(header: str, *, secure: bool = False) -> None:
    assert header.startswith('husly_refresh=""') or header.startswith("husly_refresh=;")
    assert "Max-Age=0" in header
    assert "Path=/api/auth/refresh" in header
    assert "HttpOnly" in header
    assert "SameSite=lax" in header
    assert ("Secure" in header) is secure


# Register OK
def test_register_returns_201_token_user_and_refresh_cookie(client: TestClient) -> None:
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    # Story 1.4: joined_home_id only on /register, null without an invite link.
    assert set(body) == {"access_token", "token_type", "user", "joined_home_id"}
    assert body["joined_home_id"] is None
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == EMAIL
    assert body["user"]["name"] == "Ola"
    uuid.UUID(body["user"]["id"])
    assert tokens.decode(body["access_token"], "access", TEST_SECRET) == uuid.UUID(
        body["user"]["id"]
    )
    assert_refresh_cookie_set(set_cookie_header(response), secure=False)


@pytest.mark.parametrize("secure", [True, False])
def test_secure_flag_follows_settings(engine: Engine, secure: bool) -> None:
    response = register(make_client(engine, cookie_secure=secure))

    assert_refresh_cookie_set(set_cookie_header(response), secure=secure)


# Register duplicate
def test_register_duplicate_in_other_casing_is_409_and_creates_nothing(
    client: TestClient, session: Session
) -> None:
    register(client)

    response = register(client, email="Ola@Example.com ", name="Ola 2")

    assert response.status_code == 409
    assert response.json() == {"detail": "Det finnes allerede en konto med denne e-posten."}
    assert "set-cookie" not in response.headers
    assert len(session.exec(select(User)).all()) == 1


def test_register_has_no_pre_check_so_a_race_hits_the_constraint(
    client: TestClient, engine: Engine
) -> None:
    """Two concurrent requests both pass any "does it exist?" check; only the unique
    constraint catches the second. register() relies on it alone, so this path is the race path.
    """
    register(client)
    statements: list[str] = []
    listener = lambda *args: statements.append(args[2])  # noqa: E731  (conn, cursor, statement)
    event.listen(engine, "before_cursor_execute", listener)
    try:
        response = register(client)
    finally:
        event.remove(engine, "before_cursor_execute", listener)

    assert response.status_code == 409
    assert statements and statements[0].lstrip().upper().startswith("INSERT INTO USERS")


# Register invalid
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("email", "ikke-en-epost"),
        ("email", ""),
        ("password", "a" * 7),
        ("password", "a" * 129),
        ("name", ""),
        ("name", "   "),
        ("name", "a" * 51),
    ],
)
def test_register_invalid_field_is_422_with_its_loc(
    client: TestClient, field: str, value: str
) -> None:
    response = register(client, **{field: value})

    assert response.status_code == 422
    assert ["body", field] in [error["loc"] for error in response.json()["detail"]]


@pytest.mark.parametrize(
    ("field", "value"), [("password", "a" * 8), ("password", "a" * 128), ("name", "a" * 50)]
)
def test_register_accepts_boundary_values(client: TestClient, field: str, value: str) -> None:
    assert register(client, **{field: value}).status_code == 201


def test_register_trims_name(client: TestClient) -> None:
    assert register(client, name="  Mari  ").json()["user"]["name"] == "Mari"


# Login OK
def test_login_with_any_casing_returns_token_and_new_cookie(client: TestClient) -> None:
    first = refresh_cookie_value(register(client))

    response = client.post(
        "/api/auth/login", json={"email": " OLA@example.com", "password": PASSWORD}
    )

    assert response.status_code == 200
    assert response.json()["user"]["email"] == EMAIL
    # Story 1.4: login keeps the plain AuthResponse.
    assert "joined_home_id" not in response.json()
    header = set_cookie_header(response)
    assert_refresh_cookie_set(header, secure=False)
    assert refresh_cookie_value(response) != first


# Login wrong
@pytest.mark.parametrize(
    "credentials",
    [
        {"email": EMAIL, "password": "feilfeil1"},
        {"email": "ingen@example.com", "password": PASSWORD},
    ],
)
def test_login_wrong_password_and_unknown_email_give_same_401(
    client: TestClient, credentials: dict[str, str]
) -> None:
    register(client)
    client.cookies.clear()

    response = client.post("/api/auth/login", json=credentials)

    assert response.status_code == 401
    assert response.json() == {"detail": "Feil e-post eller passord."}
    assert "set-cookie" not in response.headers


# Refresh OK
def test_refresh_returns_new_access_token_and_rotated_cookie(client: TestClient) -> None:
    registered = register(client)
    old_cookie = refresh_cookie_value(registered)

    response = client.post("/api/auth/refresh")

    assert response.status_code == 200
    assert response.json()["user"]["email"] == EMAIL
    assert response.json()["access_token"] != registered.json()["access_token"]
    assert_refresh_cookie_set(set_cookie_header(response), secure=False)
    assert refresh_cookie_value(response) != old_cookie


def test_secure_cookie_is_sent_back_on_https(engine: Engine) -> None:
    client = make_client(engine, cookie_secure=True)
    register(client)

    assert client.post("/api/auth/refresh").status_code == 200


# Refresh bad
def _bad_refresh_cookies(client: TestClient) -> dict[str, str | None]:
    body = register(client).json()
    user_id = uuid.UUID(body["user"]["id"])
    valid = tokens.issue(user_id, "refresh", TEST_SECRET).token
    return {
        "missing": None,
        # A middle signature character: the last one partly holds base64 padding bits.
        "tampered": valid[:-10] + ("A" if valid[-10] != "A" else "B") + valid[-9:],
        "other secret": tokens.issue(user_id, "refresh", "x" * 40).token,
        "access token": body["access_token"],
        "garbage": "ikke-en-jwt",
    }


@pytest.mark.parametrize("case", ["missing", "tampered", "other secret", "access token", "garbage"])
def test_refresh_with_bad_cookie_is_401_and_clears_cookie(client: TestClient, case: str) -> None:
    cookie = _bad_refresh_cookies(client)[case]
    client.cookies.clear()
    if cookie is not None:
        client.cookies.set("husly_refresh", cookie, domain="testserver", path="/api/auth/refresh")

    response = client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert "detail" in response.json()
    assert_refresh_cookie_cleared(set_cookie_header(response))


def test_refresh_with_expired_cookie_is_401(client: TestClient) -> None:
    user_id = uuid.UUID(register(client).json()["user"]["id"])
    with patch.dict(tokens._TTL, {"refresh": -tokens.REFRESH_TTL}):
        expired = tokens.issue(user_id, "refresh", TEST_SECRET).token
    client.cookies.clear()
    client.cookies.set("husly_refresh", expired, domain="testserver", path="/api/auth/refresh")

    response = client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert_refresh_cookie_cleared(set_cookie_header(response))


def test_cleared_cookie_keeps_secure_when_settings_say_so(engine: Engine) -> None:
    response = make_client(engine, cookie_secure=True).post("/api/auth/refresh")

    assert_refresh_cookie_cleared(set_cookie_header(response), secure=True)


# Logout
def test_logout_with_cookie_is_204_and_clears_it(client: TestClient) -> None:
    register(client)

    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert_refresh_cookie_cleared(set_cookie_header(response))
    assert client.post("/api/auth/refresh").status_code == 401


def test_logout_without_cookie_is_still_204(client: TestClient) -> None:
    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert_refresh_cookie_cleared(set_cookie_header(response))


# Me
def test_me_with_access_token(client: TestClient) -> None:
    body = register(client).json()

    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )

    assert response.status_code == 200
    assert response.json() == body["user"]


def test_me_without_token_is_401(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_expired_access_token_is_401(client: TestClient) -> None:
    user_id = uuid.UUID(register(client).json()["user"]["id"])
    with patch.dict(tokens._TTL, {"access": -tokens.ACCESS_TTL}):
        expired = tokens.issue(user_id, "access", TEST_SECRET).token

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})

    assert response.status_code == 401


# Access as refresh (and the reverse)
def test_refresh_token_as_bearer_is_401(client: TestClient) -> None:
    refresh = refresh_cookie_value(register(client))

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {refresh}"})

    assert response.status_code == 401


# User deleted
def test_valid_tokens_for_a_deleted_user_are_401(client: TestClient, session: Session) -> None:
    access = register(client).json()["access_token"]
    session.delete(session.exec(select(User)).one())
    session.commit()

    assert (
        client.get("/api/auth/me", headers={"Authorization": f"Bearer {access}"}).status_code == 401
    )
    response = client.post("/api/auth/refresh")
    assert response.status_code == 401
    assert_refresh_cookie_cleared(set_cookie_header(response))


# Wrong method
@pytest.mark.parametrize("path", ["/api/auth/refresh", "/api/auth/logout"])
def test_get_on_refresh_and_logout_is_405(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 405


def test_refresh_cookie_is_not_sent_to_other_api_paths(client: TestClient) -> None:
    """Path=/api/auth/refresh: the browser (and TestClient) keep it off every other route."""
    register(client)

    request = client.build_request("GET", "https://testserver/api/auth/me")

    assert "husly_refresh" not in request.headers.get("cookie", "")
