"""Story 3.4 (FR-12, AD-14, AD-16, FR-22): the Landlord's broadcast to a Home's Tenants.

Each test that guards a rule names the line it guards (review convention, Epic 2 retro P1).
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.domain import broadcast, homes
from app.models.home import Home
from app.models.membership import Membership
from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.push import MOCK_SENDER, MockSender, PushMessage, PushTarget, SendResult
from app.routes.broadcast import NO_TENANTS
from tests.helpers import auth_for, count, new_user

FCM = "https://fcm.googleapis.com/fcm/send/"


@pytest.fixture(autouse=True)
def clean_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    MOCK_SENDER.sent.clear()
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)


def landlord_home(session: Session) -> tuple[uuid.UUID, User]:
    kari = new_user(session, "Kari")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    return home.id, kari


def add_tenant(session: Session, home_id: uuid.UUID, name: str, *devices: str) -> User:
    user = new_user(session, name)
    home = session.get(Home, home_id)
    assert home is not None
    homes.add_member(session, home, user)
    for endpoint in devices:
        session.add(
            PushSubscription(user_id=user.id, endpoint=FCM + endpoint, p256dh="k", auth="a")
        )
    session.commit()
    return user


def post(client: TestClient, session: Session, user: User, home_id: uuid.UUID, message: str):
    headers = auth_for(client, user.email)
    return client.post(
        f"/api/homes/{home_id}/broadcast", json={"message": message}, headers=headers
    )


def endpoints_sent() -> list[str]:
    return sorted(target.endpoint.removeprefix(FCM) for target, _ in MOCK_SENDER.sent)


class RecordingSender:
    def __init__(self, answers: dict[str, SendResult]) -> None:
        self.answers = answers

    def send(self, target: PushTarget, message: PushMessage) -> SendResult:
        return self.answers.get(target.endpoint.removeprefix(FCM), "sent")


def test_the_push_goes_to_every_device_of_a_tenant_and_counts_tenants_not_devices(
    client: TestClient, session: Session
) -> None:
    home_id, kari = landlord_home(session)
    add_tenant(session, home_id, "Anders", "anders-mobil", "anders-pc")
    add_tenant(session, home_id, "Mari")

    response = post(client, session, kari, home_id, "  Rørlegger kommer i morgen.  ")

    assert response.status_code == 200
    # Guards `sum(1 for ... if deliver(...) > 0)`: two devices of one Tenant are one recipient.
    assert response.json() == {"recipients": 1, "without_push": 1, "demo": True}
    assert endpoints_sent() == ["anders-mobil", "anders-pc"]
    message = MOCK_SENDER.sent[0][1]
    assert message.title == "Melding fra utleier"
    assert message.body == "Rørlegger kommer i morgen."
    assert message.url == f"/hjem/{home_id}"


def test_only_current_tenants_are_addressed_not_the_landlord_or_household_members(
    client: TestClient, session: Session
) -> None:
    home_id, kari = landlord_home(session)
    add_tenant(session, home_id, "Anders", "anders")
    session.add(PushSubscription(user_id=kari.id, endpoint=FCM + "kari", p256dh="k", auth="a"))
    session.commit()

    post(client, session, kari, home_id, "Hei")

    # Guards `Membership.role == "tenant"` in send_broadcast.
    assert endpoints_sent() == ["anders"]


def test_a_tenant_who_left_gets_nothing_and_is_not_counted(
    client: TestClient, session: Session
) -> None:
    home_id, kari = landlord_home(session)
    anders = add_tenant(session, home_id, "Anders", "anders")
    add_tenant(session, home_id, "Mari", "mari")
    leaver = session.exec(select(Membership).where(Membership.user_id == anders.id)).one()
    session.delete(leaver)
    session.commit()

    response = post(client, session, kari, home_id, "Hei")

    # Guards the Membership lookup (AD-16): the device row stays, the Membership is gone.
    assert response.json() == {"recipients": 1, "without_push": 0, "demo": True}
    assert endpoints_sent() == ["mari"]


def test_a_tenant_in_another_home_gets_nothing(client: TestClient, session: Session) -> None:
    home_id, kari = landlord_home(session)
    other = new_user(session, "Berit")
    other_home = homes.create_home(session, other, name="Torget 1", type="landlord").home
    add_tenant(session, other_home.id, "Olav", "olav")
    add_tenant(session, home_id, "Anders", "anders")

    post(client, session, kari, home_id, "Hei")

    # Guards `Membership.home_id == home_id`.
    assert endpoints_sent() == ["anders"]


def test_a_home_without_tenants_answers_409_and_sends_nothing(
    client: TestClient, session: Session
) -> None:
    home_id, kari = landlord_home(session)

    response = post(client, session, kari, home_id, "Hei")

    # Guards `if not tenant_ids: raise NoTenants` and its mapping to 409.
    assert response.status_code == 409
    assert response.json() == {"detail": NO_TENANTS}
    assert endpoints_sent() == []


def test_a_tenant_may_not_send(client: TestClient, session: Session) -> None:
    home_id, _kari = landlord_home(session)
    tenant = add_tenant(session, home_id, "Anders", "anders")

    response = post(client, session, tenant, home_id, "Hei")

    # Guards the Landlord alias (require_role("landlord")) on the route.
    assert response.status_code == 403
    assert endpoints_sent() == []


def test_a_household_member_may_not_send(client: TestClient, session: Session) -> None:
    hanne = new_user(session, "Hanne")
    household = homes.create_home(session, hanne, name="Kollektivet", type="household").home
    per = new_user(session, "Per")
    homes.add_member(session, household, per)
    session.add(PushSubscription(user_id=per.id, endpoint=FCM + "per", p256dh="k", auth="a"))
    session.commit()

    response = post(client, session, hanne, household.id, "Hei")

    # Guards the Landlord alias: a Household Member of the Home has a Membership, but no right.
    assert response.status_code == 403
    assert endpoints_sent() == []


def test_a_stranger_gets_the_same_403(client: TestClient, session: Session) -> None:
    home_id, _kari = landlord_home(session)
    tenant = add_tenant(session, home_id, "Anders", "anders")
    stranger = new_user(session, "Fremmed")

    response = post(client, session, stranger, home_id, "Hei")
    tenant_response = post(client, session, tenant, home_id, "Hei")

    # Guards require_role's single answer: no Membership gives the same 403 as the wrong Role.
    assert response.status_code == 403
    assert response.json() == tenant_response.json()
    assert endpoints_sent() == []


@pytest.mark.parametrize("text", ["", "   ", "x" * 301])
def test_empty_or_too_long_text_is_422_and_sends_nothing(
    client: TestClient, session: Session, text: str
) -> None:
    home_id, kari = landlord_home(session)
    add_tenant(session, home_id, "Anders", "anders")

    response = post(client, session, kari, home_id, text)

    # Guards MessageText (strip, min 1, max MESSAGE_MAX_LENGTH).
    assert response.status_code == 422
    assert endpoints_sent() == []


def test_exactly_300_characters_is_accepted(client: TestClient, session: Session) -> None:
    home_id, kari = landlord_home(session)
    add_tenant(session, home_id, "Anders", "anders")

    response = post(client, session, kari, home_id, "x" * broadcast.MESSAGE_MAX_LENGTH)

    assert response.status_code == 200


def test_two_sends_do_not_share_a_tag_so_the_second_does_not_replace_the_first(
    session: Session,
) -> None:
    home_id, _kari = landlord_home(session)
    add_tenant(session, home_id, "Anders", "anders")
    sender = MockSender()

    broadcast.send_broadcast(session, sender, home_id, "En")
    broadcast.send_broadcast(session, sender, home_id, "To")

    # Guards the uuid in the tag.
    tags = [message.tag for _, message in sender.sent]
    assert len(set(tags)) == 2


def test_a_gone_device_is_deleted_and_the_tenant_is_not_reached(session: Session) -> None:
    home_id, _kari = landlord_home(session)
    add_tenant(session, home_id, "Anders", "weg")
    add_tenant(session, home_id, "Mari", "mari-ok", "mari-weg")

    result = broadcast.send_broadcast(
        session, RecordingSender({"weg": "gone", "mari-weg": "gone"}), home_id, "Hei"
    )

    # Guards the 404/410 clean-up in push.deliver: only the working device is left.
    assert result == broadcast.BroadcastResult(recipients=1, without_push=1)
    left = {row.endpoint.removeprefix(FCM) for row in session.exec(select(PushSubscription)).all()}
    assert left == {"mari-ok"}


def test_a_failed_send_counts_as_not_reached_and_keeps_the_device(session: Session) -> None:
    home_id, _kari = landlord_home(session)
    add_tenant(session, home_id, "Anders", "anders")

    result = broadcast.send_broadcast(
        session, RecordingSender({"anders": "failed"}), home_id, "Hei"
    )

    assert result == broadcast.BroadcastResult(recipients=0, without_push=1)
    assert count(session, PushSubscription) == 1


def test_home_out_says_only_the_landlord_can_broadcast(
    client: TestClient, session: Session
) -> None:
    home_id, kari = landlord_home(session)
    anders = add_tenant(session, home_id, "Anders")

    def flag(user: User) -> bool:
        headers = auth_for(client, user.email)
        homes_list = client.get("/api/homes", headers=headers).json()["homes"]
        return homes_list[0]["can_broadcast"]

    # Guards `can_broadcast(role) == "landlord"`.
    assert flag(kari) is True
    assert flag(anders) is False


def test_the_confirmation_says_demo_only_for_the_mock_sender(
    client: TestClient, session: Session
) -> None:
    # Guards `isinstance(sender, MockSender)` in the route: «Sendt til N» must not read as delivered
    # when no real push was made (no VAPID keys), and must not say demo when one was.
    from app.push import get_sender

    home_id, kari = landlord_home(session)
    add_tenant(session, home_id, "Anders", "anders-mobil")

    mock = post(client, session, kari, home_id, "Hei")
    client.app.dependency_overrides[get_sender] = lambda: RecordingSender({})  # type: ignore[attr-defined]
    try:
        real = post(client, session, kari, home_id, "Hei igjen")
    finally:
        client.app.dependency_overrides.pop(get_sender, None)  # type: ignore[attr-defined]

    assert (mock.json()["demo"], real.json()["demo"]) == (True, False)
