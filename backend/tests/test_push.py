"""Story 3.1 (FR-10, AD-12): one PushSubscription per User and device, and the push config."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, select

from app.config import DEV_VAPID_PUBLIC_KEY
from app.domain import push
from app.models.push_subscription import PushSubscription
from tests.helpers import new_user, sign_up

URL = "/api/push/subscriptions"
REMOVE_URL = URL + "/remove"


def body(
    endpoint: str = "https://fcm.googleapis.com/fcm/send/a", p256dh: str = "k1", auth: str = "a1"
) -> dict:
    return {"endpoint": endpoint, "p256dh": p256dh, "auth": auth}


def rows(session: Session) -> list[PushSubscription]:
    session.expire_all()
    return list(session.exec(select(PushSubscription)).all())


def test_first_device_is_stored_for_the_user(client: TestClient, session: Session) -> None:
    mari = sign_up(client, "Mari")
    assert client.put(URL, json=body(), headers=mari).status_code == 204
    [row] = rows(session)
    assert (row.endpoint, row.p256dh, row.auth) == (
        "https://fcm.googleapis.com/fcm/send/a",
        "k1",
        "a1",
    )


def test_a_second_device_adds_a_row_and_leaves_the_first(
    client: TestClient, session: Session
) -> None:
    mari = sign_up(client, "Mari")
    client.put(URL, json=body("https://fcm.googleapis.com/fcm/send/a"), headers=mari)
    client.put(URL, json=body("https://fcm.googleapis.com/fcm/send/b", "k2", "a2"), headers=mari)
    by_endpoint = {r.endpoint: r for r in rows(session)}
    assert set(by_endpoint) == {
        "https://fcm.googleapis.com/fcm/send/a",
        "https://fcm.googleapis.com/fcm/send/b",
    }
    assert by_endpoint["https://fcm.googleapis.com/fcm/send/a"].p256dh == "k1"
    assert len({r.user_id for r in by_endpoint.values()}) == 1


def test_the_same_endpoint_again_updates_the_row_instead_of_adding_one(
    client: TestClient, session: Session
) -> None:
    mari = sign_up(client, "Mari")
    client.put(URL, json=body(), headers=mari)
    assert client.put(URL, json=body(p256dh="k9", auth="a9"), headers=mari).status_code == 204
    [row] = rows(session)
    assert (row.p256dh, row.auth) == ("k9", "a9")


def test_an_endpoint_registered_by_another_user_moves_to_the_caller(
    client: TestClient, session: Session
) -> None:
    mari = sign_up(client, "Mari")
    jonas = sign_up(client, "Jonas")
    client.put(URL, json=body(), headers=mari)
    client.put(URL, json=body(), headers=jonas)
    [row] = rows(session)
    me = client.get("/api/auth/me", headers=jonas).json()
    assert str(row.user_id) == me["id"]


def test_the_eleventh_device_removes_the_oldest(client: TestClient, session: Session) -> None:
    mari = sign_up(client, "Mari")
    assert push.MAX_SUBSCRIPTIONS_PER_USER == 10
    for n in range(11):
        client.put(URL, json=body(f"https://fcm.googleapis.com/fcm/send/{n}"), headers=mari)
    endpoints = {r.endpoint for r in rows(session)}
    assert len(endpoints) == 10
    assert "https://fcm.googleapis.com/fcm/send/0" not in endpoints
    assert "https://fcm.googleapis.com/fcm/send/10" in endpoints


def test_sign_out_removes_only_the_callers_own_row(client: TestClient, session: Session) -> None:
    mari = sign_up(client, "Mari")
    jonas = sign_up(client, "Jonas")
    client.put(URL, json=body("https://fcm.googleapis.com/fcm/send/mari"), headers=mari)
    client.put(URL, json=body("https://fcm.googleapis.com/fcm/send/jonas"), headers=jonas)
    # Jonas cannot delete Mari's device, and deleting a row that is not there is fine.
    assert (
        client.post(
            REMOVE_URL, json={"endpoint": "https://fcm.googleapis.com/fcm/send/mari"}, headers=jonas
        ).status_code
        == 204
    )
    assert {r.endpoint for r in rows(session)} == {
        "https://fcm.googleapis.com/fcm/send/mari",
        "https://fcm.googleapis.com/fcm/send/jonas",
    }
    assert (
        client.post(
            REMOVE_URL, json={"endpoint": "https://fcm.googleapis.com/fcm/send/mari"}, headers=mari
        ).status_code
        == 204
    )
    assert {r.endpoint for r in rows(session)} == {"https://fcm.googleapis.com/fcm/send/jonas"}


def test_push_routes_need_a_signed_in_user(client: TestClient) -> None:
    assert client.put(URL, json=body()).status_code == 401
    assert client.post(REMOVE_URL, json={"endpoint": "https://x"}).status_code == 401
    assert client.get("/api/push/config").status_code == 401


def test_a_bad_body_is_422(client: TestClient) -> None:
    mari = sign_up(client, "Mari")
    assert (
        client.put(URL, json={"endpoint": "", "p256dh": "k", "auth": "a"}, headers=mari).status_code
        == 422
    )
    assert client.put(URL, json={"endpoint": "https://x"}, headers=mari).status_code == 422


def test_config_hands_out_the_dev_key_and_says_mock_without_vapid_keys(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    mari = sign_up(client, "Mari")
    assert client.get("/api/push/config", headers=mari).json() == {
        "public_key": DEV_VAPID_PUBLIC_KEY,
        "mock": True,
    }


def test_config_hands_out_the_real_key_only_when_both_keys_are_set(
    client: TestClient, monkeypatch
) -> None:
    mari = sign_up(client, "Mari")
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "ekte-nokkel")
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    assert client.get("/api/push/config", headers=mari).json()["mock"] is True
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "privat")
    assert client.get("/api/push/config", headers=mari).json() == {
        "public_key": "ekte-nokkel",
        "mock": False,
    }


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://push.example/a",
        "ftp://push.example/a",
        "https://fcm.googleapis.com/fcm/send/ø",
        "push",
    ],
)
def test_only_an_ascii_https_endpoint_is_accepted(client: TestClient, endpoint: str) -> None:
    mari = sign_up(client, "Mari")
    assert client.put(URL, json=body(endpoint), headers=mari).status_code == 422


def test_a_parallel_registration_of_the_same_endpoint_updates_the_row_that_won(
    engine: Engine, session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    jonas = new_user(session, "Jonas")
    mari = new_user(session, "Mari")
    endpoint = "https://fcm.googleapis.com/fcm/send/a"
    push.register_subscription(session, jonas.id, endpoint, "old", "old")

    # Mari's request looked the endpoint up before Jonas's insert was visible: the first lookup
    # misses, her insert hits the unique key, and the retry must update the row instead.
    with Session(engine) as racing:
        real_exec = racing.exec
        misses = [True]

        class Miss:
            def first(self) -> None:
                return None

        def exec_(*args: object, **kwargs: object) -> object:
            if misses:
                misses.pop()
                return Miss()
            return real_exec(*args, **kwargs)

        monkeypatch.setattr(racing, "exec", exec_)
        push.register_subscription(racing, mari.id, endpoint, "new", "new")

    session.expire_all()
    [row] = session.exec(select(PushSubscription)).all()
    assert (row.user_id, row.p256dh, row.auth) == (mari.id, "new", "new")


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://169.254.169.254/latest/meta-data",
        "https://localhost/push",
        "https://fcm.googleapis.com.evil.example/x",
        "https://fcm.googleapis.com@evil.example/x",
        "https://evilnotify.windows.com/x",
        "https://fcm.googleapis.com:8443/x",
        "http://fcm.googleapis.com/x",
    ],
)
def test_an_endpoint_outside_the_push_services_is_422(
    client: TestClient, session: Session, endpoint: str
) -> None:
    mari = sign_up(client, "Mari")
    assert client.put(URL, json=body(endpoint), headers=mari).status_code == 422
    assert rows(session) == []


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://updates.push.services.mozilla.com/wpush/v2/abc",
        "https://web.push.apple.com/abc",
        "https://eu.push.apple.com/abc",
        "https://db5p.notify.windows.com/?token=abc",
    ],
)
def test_the_known_push_services_are_accepted(
    client: TestClient, session: Session, endpoint: str
) -> None:
    mari = sign_up(client, "Mari")
    assert client.put(URL, json=body(endpoint), headers=mari).status_code == 204


def test_removing_an_endpoint_needs_no_known_host(client: TestClient) -> None:
    mari = sign_up(client, "Mari")
    assert (
        client.post(
            REMOVE_URL, json={"endpoint": "https://gammel.example/x"}, headers=mari
        ).status_code
        == 204
    )


def test_delete_with_a_body_is_gone(client: TestClient) -> None:
    mari = sign_up(client, "Mari")
    assert (
        client.request("DELETE", URL, json={"endpoint": "https://x"}, headers=mari).status_code
        == 405
    )
