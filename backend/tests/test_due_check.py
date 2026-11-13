"""Story 3.2 (FR-10, SM-9b, AD-8, AD-16, FR-22): the due-check job, its senders and its route."""

import uuid
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pywebpush import WebPushException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.domain import due_check, homes, tasks
from app.models.due_notification import DueNotification
from app.models.membership import Membership
from app.models.push_subscription import PushSubscription
from app.models.task import Task, TaskInstance
from app.models.user import User
from app.push import MOCK_SENDER, MockSender, PushMessage, PushTarget, Sender, SendResult
from app.push import senders as senders_module
from tests.helpers import new_user, sign_up

TODAY = date(2026, 11, 13)
FCM = "https://fcm.googleapis.com/fcm/send/"


def landlord_home(session: Session) -> tuple[uuid.UUID, User, User]:
    """A Landlord Home with Kari (landlord) and Anders (tenant)."""
    kari = new_user(session, "Kari")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    anders = new_user(session, "Anders")
    homes.add_member(session, home, anders)
    return home.id, kari, anders


def membership_of(session: Session, home_id: uuid.UUID, user: User) -> Membership:
    return session.exec(
        select(Membership).where(Membership.home_id == home_id, Membership.user_id == user.id)
    ).one()


def add_task(
    session: Session,
    home_id: uuid.UUID,
    kari: User,
    name: str,
    due_on: date,
    classification: str = "should",
) -> Task:
    """A custom Task whose one open instance is due on `due_on` (built directly: no setup rule)."""
    task = Task(home_id=home_id, name=name, classification=classification, frequency_days=7)
    session.add(task)
    session.flush()
    session.add(TaskInstance(task_id=task.id, due_on=due_on))
    session.commit()
    return task


def device(session: Session, user: User, endpoint: str) -> None:
    session.add(PushSubscription(user_id=user.id, endpoint=FCM + endpoint, p256dh="k", auth="a"))
    session.commit()


def run(session: Session, sender: Sender, today: date = TODAY) -> due_check.DueCheckResult:
    return due_check.run_due_check(session, sender, today)


def sent_to(sender: MockSender) -> dict[str, PushMessage]:
    return {target.endpoint.removeprefix(FCM): message for target, message in sender.sent}


class RecordingSender:
    """Answers per endpoint, like a push service would."""

    def __init__(self, answers: dict[str, SendResult]) -> None:
        self.answers = answers
        self.calls: list[str] = []

    def send(self, target: PushTarget, message: PushMessage) -> SendResult:
        self.calls.append(target.endpoint.removeprefix(FCM))
        return self.answers.get(target.endpoint.removeprefix(FCM), "sent")


def test_each_member_gets_one_push_per_device_naming_all_their_tasks(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", TODAY)
    add_task(session, home_id, kari, "Vaske bad", TODAY - timedelta(days=2))
    device(session, anders, "anders-mobil")
    device(session, anders, "anders-pc")
    device(session, kari, "kari-mobil")
    sender = MockSender()

    result = run(session, sender)

    assert result == due_check.DueCheckResult(members=2, tasks=4, pushes=3)
    messages = sent_to(sender)
    assert set(messages) == {"anders-mobil", "anders-pc", "kari-mobil"}
    assert messages["anders-mobil"] == messages["anders-pc"]
    assert messages["anders-mobil"].title == "2 oppgaver venter"
    assert messages["anders-mobil"].body == "Vaske bad, Støvsuge."
    assert messages["anders-mobil"].url == "/"


def test_one_task_opens_its_detail_page_and_says_when_it_was_due(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    task = add_task(session, home_id, kari, "Støvsuge", TODAY - timedelta(days=3))
    device(session, anders, "a")
    sender = MockSender()

    run(session, sender)

    message = sent_to(sender)["a"]
    assert message.title == "Støvsuge"
    assert message.body == "Forfalt for 3 dager siden."
    assert message.url == f"/hjem/{home_id}/oppgaver/{task.id}"


@pytest.mark.parametrize(
    ("days_overdue", "text"),
    [(0, "Skal gjøres i dag."), (1, "Forfalt i går."), (5, "Forfalt for 5 dager siden.")],
)
def test_the_text_follows_how_late_the_task_is(
    session: Session, days_overdue: int, text: str
) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", TODAY - timedelta(days=days_overdue))
    device(session, anders, "a")
    sender = MockSender()

    run(session, sender)

    assert sent_to(sender)["a"].body == text


def test_more_than_three_tasks_are_counted_and_must_comes_first(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "A bør", TODAY - timedelta(days=9))
    add_task(session, home_id, kari, "B bør", TODAY - timedelta(days=8))
    add_task(session, home_id, kari, "C bør", TODAY - timedelta(days=7))
    add_task(session, home_id, kari, "D må", TODAY, classification="must")
    device(session, anders, "a")
    sender = MockSender()

    run(session, sender)

    assert sent_to(sender)["a"].body == "D må, A bør, B bør og 1 til."


def test_a_task_due_tomorrow_or_later_sends_nothing_and_claims_nothing(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "I morgen", TODAY + timedelta(days=1))
    add_task(session, home_id, kari, "Om en uke", TODAY + timedelta(days=7))
    device(session, anders, "a")
    sender = MockSender()

    assert run(session, sender) == due_check.DueCheckResult(0, 0, 0)

    assert len(sender.sent) == 0
    assert session.exec(select(DueNotification)).all() == []


def test_a_second_run_the_same_day_sends_nothing(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", TODAY)
    device(session, anders, "a")
    sender = MockSender()

    run(session, sender)
    second = run(session, sender)

    assert second == due_check.DueCheckResult(0, 0, 0)
    assert len(sender.sent) == 1


def test_an_overdue_task_is_notified_again_the_next_day(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", TODAY - timedelta(days=1))
    device(session, anders, "a")
    sender = MockSender()

    run(session, sender, TODAY)
    run(session, sender, TODAY + timedelta(days=1))

    assert len(sender.sent) == 2


def test_a_claim_taken_in_parallel_is_skipped_without_an_error(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    home_id, kari, anders = landlord_home(session)
    task = add_task(session, home_id, kari, "Støvsuge", TODAY)
    instance = session.exec(select(TaskInstance).where(TaskInstance.task_id == task.id)).one()
    due = [due_check.DueTask(instance.id, task.id, home_id, task.name, TODAY)]
    # The other run inserts its claim after this run has read the already-claimed set.
    session.add(DueNotification(task_instance_id=instance.id, user_id=anders.id, day=TODAY))
    session.commit()
    real_exec = session.exec
    first = []

    def stale_first_read(statement, *args, **kwargs):  # type: ignore[no-untyped-def]
        if not first:
            first.append(True)
            return SimpleNamespace(all=lambda: [])
        return real_exec(statement, *args, **kwargs)

    monkeypatch.setattr(session, "exec", stale_first_read)

    assert due_check._claim(session, anders.id, due, TODAY) == []
    assert len(real_exec(select(DueNotification)).all()) == 1


def test_a_user_who_left_the_home_gets_nothing_from_it(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", TODAY)
    device(session, anders, "anders")
    device(session, kari, "kari")
    homes.leave(session, membership_of(session, home_id, anders))
    sender = MockSender()

    run(session, sender)

    assert set(sent_to(sender)) == {"kari"}


def test_an_archived_task_and_a_completed_instance_are_not_due(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    archived = add_task(session, home_id, kari, "Arkivert", TODAY)
    done = add_task(session, home_id, kari, "Ferdig", TODAY)
    kari_membership = membership_of(session, home_id, kari)
    tasks.archive_task(session, kari_membership, archived.id)
    instance = session.exec(select(TaskInstance).where(TaskInstance.task_id == done.id)).one()
    tasks.complete_task_instance(session, kari_membership, done.id, instance.id)
    device(session, anders, "a")
    sender = MockSender()

    assert run(session, sender) == due_check.DueCheckResult(0, 0, 0)


def test_a_member_without_devices_is_claimed_and_still_not_notified_by_a_later_run(
    session: Session,
) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", TODAY)
    sender = MockSender()

    first = run(session, sender)
    device(session, anders, "late")
    second = run(session, sender)

    assert first == due_check.DueCheckResult(members=2, tasks=2, pushes=0)
    assert second.pushes == 0
    assert len(sender.sent) == 0


def test_a_gone_device_is_deleted_and_the_others_are_still_sent(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", TODAY)
    device(session, anders, "dead")
    device(session, anders, "alive")
    sender = RecordingSender({"dead": "gone"})

    result = run(session, sender)

    assert result.pushes == 1
    assert sorted(sender.calls) == ["alive", "dead"]
    remaining = session.exec(select(PushSubscription.endpoint)).all()
    assert remaining == [FCM + "alive"]


def test_a_failed_device_is_kept_and_not_retried_that_day(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", TODAY)
    device(session, anders, "flaky")
    sender = RecordingSender({"flaky": "failed"})

    run(session, sender)
    run(session, sender)

    assert sender.calls == ["flaky"]
    assert session.exec(select(PushSubscription)).all() != []


def test_an_endpoint_outside_the_allowlist_is_never_called(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", TODAY)
    session.add(
        PushSubscription(
            user_id=anders.id, endpoint="https://169.254.169.254/x", p256dh="k", auth="a"
        )
    )
    session.commit()
    sender = MockSender()

    run(session, sender)

    assert len(sender.sent) == 0


def test_a_run_claims_one_row_per_member_and_instance_on_its_day(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", TODAY)
    run(session, MockSender())
    rows = session.exec(select(DueNotification).order_by(col(DueNotification.user_id))).all()
    assert len(rows) == 2
    assert {r.user_id for r in rows} == {kari.id, anders.id}
    assert {r.day for r in rows} == {TODAY}


def test_the_database_refuses_a_second_claim_for_the_same_instance_member_and_day(
    session: Session,
) -> None:
    home_id, kari, anders = landlord_home(session)
    task = add_task(session, home_id, kari, "Støvsuge", TODAY)
    instance = session.exec(select(TaskInstance).where(TaskInstance.task_id == task.id)).one()
    session.add(DueNotification(task_instance_id=instance.id, user_id=anders.id, day=TODAY))
    session.commit()
    session.add(DueNotification(task_instance_id=instance.id, user_id=anders.id, day=TODAY))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    # The same pair on another day is a different claim.
    session.add(
        DueNotification(task_instance_id=instance.id, user_id=anders.id, day=TODAY + timedelta(1))
    )
    session.commit()


def test_claims_from_earlier_days_are_deleted_by_the_next_run(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", TODAY - timedelta(days=1))
    run(session, MockSender(), TODAY)
    run(session, MockSender(), TODAY + timedelta(days=1))
    assert {r.day for r in session.exec(select(DueNotification)).all()} == {TODAY + timedelta(1)}


def test_a_member_of_two_homes_gets_one_push_covering_both_and_the_overview_link(
    session: Session,
) -> None:
    first, kari, _anders = landlord_home(session)
    second = homes.create_home(session, kari, name="Bakgata 3", type="landlord").home.id
    add_task(session, first, kari, "Støvsuge", TODAY)
    add_task(session, second, kari, "Vaske bad", TODAY)
    # A Landlord may own several Homes (Anders, a Tenant, may not): Kari is in both.
    device(session, kari, "a")
    sender = MockSender()

    run(session, sender)

    message = sent_to(sender)["a"]
    assert (message.title, message.url) == ("2 oppgaver venter", "/")


def test_the_cron_in_vercel_json_calls_a_route_that_exists_on_the_schedule_in_the_story(
    client: TestClient,
) -> None:
    import json
    from pathlib import Path

    config = json.loads((Path(__file__).parents[2] / "vercel.json").read_text(encoding="utf-8"))
    [cron] = config["crons"]
    assert cron["schedule"] == "0 6 * * *"
    assert client.get(cron["path"]).status_code == 200


# --- the senders ---------------------------------------------------------------------------------


def target() -> PushTarget:
    return PushTarget(FCM + "x", "k", "a")


def message() -> PushMessage:
    return PushMessage("Støvsuge", "Skal gjøres i dag.", "/hjem/1/oppgaver/2", "husly-forfall")


def test_the_mock_sender_records_and_says_sent() -> None:
    mock = MockSender()
    assert mock.send(target(), message()) == "sent"
    assert list(mock.sent) == [(target(), message())]


def test_the_mock_keeps_only_the_latest_pushes() -> None:
    mock = MockSender()
    for _ in range(senders_module.MOCK_KEEP + 5):
        mock.send(target(), message())
    assert len(mock.sent) == senders_module.MOCK_KEEP


def test_the_payload_is_json_with_title_body_url_and_tag() -> None:
    import json

    assert json.loads(message().payload()) == {
        "title": "Støvsuge",
        "body": "Skal gjøres i dag.",
        "url": "/hjem/1/oppgaver/2",
        "tag": "husly-forfall",
    }


def test_get_sender_is_the_mock_unless_both_vapid_keys_are_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    assert senders_module.get_sender() is MOCK_SENDER
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "privat")
    assert senders_module.get_sender() is MOCK_SENDER
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "offentlig")
    assert isinstance(senders_module.get_sender(), senders_module.WebPushSender)


def test_the_web_push_sender_sends_the_payload_with_a_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict = {}
    monkeypatch.setattr(senders_module, "webpush", lambda **kwargs: seen.update(kwargs))
    sender = senders_module.WebPushSender("privat", "mailto:a@b.example")

    assert sender.send(target(), message()) == "sent"

    assert seen["subscription_info"] == {
        "endpoint": FCM + "x",
        "keys": {"p256dh": "k", "auth": "a"},
    }
    assert seen["data"] == message().payload()
    assert seen["vapid_private_key"] == "privat"
    assert seen["vapid_claims"] == {"sub": "mailto:a@b.example"}
    assert seen["timeout"] == senders_module.PUSH_TIMEOUT_SECONDS
    assert seen["ttl"] == 24 * 3600


@pytest.mark.parametrize(("status", "expected"), [(404, "gone"), (410, "gone"), (500, "failed")])
def test_the_web_push_sender_reads_the_push_services_answer(
    monkeypatch: pytest.MonkeyPatch, status: int, expected: str
) -> None:
    def fail(**kwargs: object) -> None:
        raise WebPushException("nei", response=SimpleNamespace(status_code=status, text=""))

    monkeypatch.setattr(senders_module, "webpush", fail)
    assert senders_module.WebPushSender("p", "mailto:a@b.example").send(target(), message()) == (
        expected
    )


def test_a_network_error_is_failed_not_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(**kwargs: object) -> None:
        raise ConnectionError("ingen forbindelse")

    monkeypatch.setattr(senders_module, "webpush", fail)
    assert senders_module.WebPushSender("p", "mailto:a@b.example").send(target(), message()) == (
        "failed"
    )


# --- the route -----------------------------------------------------------------------------------

ROUTE = "/api/internal/run-due-check"


@pytest.fixture(autouse=True)
def clean_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    MOCK_SENDER.sent.clear()
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("CRON_SECRET", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)


def seed_due(session: Session) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", date(2000, 1, 1))
    device(session, anders, "a")


def test_the_route_runs_with_the_right_secret_and_the_mock_records(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CRON_SECRET", "hemmelig")
    seed_due(session)

    response = client.get(ROUTE, headers={"Authorization": "Bearer hemmelig"})

    assert response.status_code == 200
    assert response.json() == {"members": 2, "tasks": 2, "pushes": 1}
    assert [m.title for _, m in MOCK_SENDER.sent] == ["Støvsuge"]
    assert client.get(ROUTE, headers={"Authorization": "Bearer hemmelig"}).json()["pushes"] == 0


@pytest.mark.parametrize(
    "header", [None, "Bearer feil", "hemmelig", "Bearer hemmelig ", "bearer hemmelig"]
)
def test_the_route_rejects_a_missing_or_wrong_secret_and_scans_nothing(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch, header: str | None
) -> None:
    monkeypatch.setenv("CRON_SECRET", "hemmelig")
    seed_due(session)

    response = client.get(ROUTE, headers={"Authorization": header} if header else {})

    assert response.status_code == 401
    assert session.exec(select(DueNotification)).all() == []


def test_a_user_token_is_not_a_cron_secret(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CRON_SECRET", "hemmelig")
    assert client.get(ROUTE, headers=sign_up(client, "Mari")).status_code == 401


def test_without_a_secret_the_job_runs_by_hand_only_in_local_mock_mode(
    client: TestClient, session: Session
) -> None:
    seed_due(session)
    assert client.get(ROUTE).status_code == 200


def test_without_a_secret_every_call_is_rejected_on_vercel(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VERCEL", "1")
    assert client.get(ROUTE).status_code == 401


def test_without_a_secret_every_call_is_rejected_when_real_vapid_keys_are_set(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "offentlig")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "privat")
    assert client.get(ROUTE).status_code == 401


def test_the_route_uses_the_utc_today_of_the_clock(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, kari, "Støvsuge", date(2026, 6, 1))
    monkeypatch.setattr("app.routes.internal.utc_today", lambda: date(2026, 5, 31))
    assert client.get(ROUTE).json()["tasks"] == 0
    monkeypatch.setattr("app.routes.internal.utc_today", lambda: date(2026, 6, 1))
    assert client.get(ROUTE).json()["tasks"] == 2


def test_the_internal_route_is_not_in_the_api_document(client: TestClient) -> None:
    assert "/api/internal/run-due-check" not in client.get("/openapi.json").json()["paths"]
