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


def body(endpoint: str = "https://push.example/a", p256dh: str = "k1", auth: str = "a1") -> dict:
    return {"endpoint": endpoint, "p256dh": p256dh, "auth": auth}


def rows(session: Session) -> list[PushSubscription]:
    session.expire_all()
    return list(session.exec(select(PushSubscription)).all())


def test_first_device_is_stored_for_the_user(client: TestClient, session: Session) -> None:
    mari = sign_up(client, "Mari")
    assert client.put(URL, json=body(), headers=mari).status_code == 204
    [row] = rows(session)
    assert (row.endpoint, row.p256dh, row.auth) == ("https://push.example/a", "k1", "a1")


def test_a_second_device_adds_a_row_and_leaves_the_first(
    client: TestClient, session: Session
) -> None:
    mari = sign_up(client, "Mari")
    client.put(URL, json=body("https://push.example/a"), headers=mari)
    client.put(URL, json=body("https://push.example/b", "k2", "a2"), headers=mari)
    by_endpoint = {r.endpoint: r for r in rows(session)}
    assert set(by_endpoint) == {"https://push.example/a", "https://push.example/b"}
    assert by_endpoint["https://push.example/a"].p256dh == "k1"
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
        client.put(URL, json=body(f"https://push.example/{n}"), headers=mari)
    endpoints = {r.endpoint for r in rows(session)}
    assert len(endpoints) == 10
    assert "https://push.example/0" not in endpoints
    assert "https://push.example/10" in endpoints


def test_sign_out_removes_only_the_callers_own_row(client: TestClient, session: Session) -> None:
    mari = sign_up(client, "Mari")
    jonas = sign_up(client, "Jonas")
    client.put(URL, json=body("https://push.example/mari"), headers=mari)
    client.put(URL, json=body("https://push.example/jonas"), headers=jonas)
    # Jonas cannot delete Mari's device, and deleting a row that is not there is fine.
    assert (
        client.request(
            "DELETE", URL, json={"endpoint": "https://push.example/mari"}, headers=jonas
        ).status_code
        == 204
    )
    assert {r.endpoint for r in rows(session)} == {
        "https://push.example/mari",
        "https://push.example/jonas",
    }
    assert (
        client.request(
            "DELETE", URL, json={"endpoint": "https://push.example/mari"}, headers=mari
        ).status_code
        == 204
    )
    assert {r.endpoint for r in rows(session)} == {"https://push.example/jonas"}


def test_push_routes_need_a_signed_in_user(client: TestClient) -> None:
    assert client.put(URL, json=body()).status_code == 401
    assert client.request("DELETE", URL, json={"endpoint": "x"}).status_code == 401
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
    "endpoint", ["http://push.example/a", "ftp://push.example/a", "https://push.example/ø", "push"]
)
def test_only_an_ascii_https_endpoint_is_accepted(client: TestClient, endpoint: str) -> None:
    mari = sign_up(client, "Mari")
    assert client.put(URL, json=body(endpoint), headers=mari).status_code == 422


def test_a_parallel_registration_of_the_same_endpoint_updates_the_row_that_won(
    engine: Engine, session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    jonas = new_user(session, "Jonas")
    mari = new_user(session, "Mari")
    endpoint = "https://push.example/a"
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
