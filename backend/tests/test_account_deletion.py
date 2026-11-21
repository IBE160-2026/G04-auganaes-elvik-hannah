"""Story 1.10 (FR-25, FR-23, AD-16, AD-17): deleting an account.

Each test names the line it guards in `domain/account_deletion.py` (spec Implementation Notes).
"""

import uuid
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, col, select

from app.domain import account_deletion, accounts, homes, invites, photo_evidence
from app.models.ai_usage import AiUsage
from app.models.due_notification import DueNotification
from app.models.home import Home
from app.models.invite_link import InviteLink
from app.models.membership import Membership
from app.models.photo_evidence import PhotoEvidence
from app.models.push_subscription import PushSubscription
from app.models.task import Task, TaskInstance
from app.models.user import User
from app.storage import LocalPhotoStore, StorageError, get_photo_store
from tests.helpers import PASSWORD, auth_for, new_user

TODAY = date(2026, 11, 21)
LOADED = datetime(2026, 11, 20, 10, 0, tzinfo=UTC)


def add_task(session: Session, home_id: uuid.UUID, name: str = "Støvsuge") -> TaskInstance:
    task = Task(home_id=home_id, name=name, classification="must", frequency_days=7)
    session.add(task)
    session.flush()
    instance = TaskInstance(task_id=task.id, due_on=TODAY)
    session.add(instance)
    session.commit()
    return instance


def add_photo(
    session: Session, instance: TaskInstance, uploader: User, store: LocalPhotoStore
) -> str:
    key = photo_evidence.evidence_key(instance.task_id)
    store.put(key, b"jpeg")
    session.add(
        PhotoEvidence(
            task_id=instance.task_id,
            task_instance_id=instance.id,
            uploaded_by_user_id=uploader.id,
            uploaded_at=LOADED,
            description=photo_evidence.describe(uploader.name, LOADED.date()),
        )
    )
    session.commit()
    return key


def landlord_home(session: Session, name: str = "Storgata 12") -> tuple[User, Home]:
    landlord = new_user(session, "Kari")
    return landlord, homes.create_home(session, landlord, name=name, type="landlord").home


def with_tenant(session: Session, home: Home, name: str = "Anders") -> User:
    tenant = new_user(session, name)
    homes.add_member(session, home, tenant)
    return tenant


def household(session: Session) -> tuple[User, User, Home]:
    mari = new_user(session, "Mari")
    home = homes.create_home(session, mari, name="Kollektivet", type="household").home
    jonas = new_user(session, "Jonas")
    homes.add_member(session, home, jonas)
    return mari, jonas, home


def delete(session: Session, user: User) -> None:
    account_deletion.delete_account(session, user, PASSWORD, get_photo_store())


def exists(session: Session, model: type, **where: object) -> bool:
    query = select(model)
    for column, value in where.items():
        query = query.where(getattr(model, column) == value)
    return session.exec(query).first() is not None


@pytest.fixture
def store(local_photo_store: Path) -> LocalPhotoStore:
    return LocalPhotoStore(local_photo_store)


def test_the_user_is_anonymised_not_deleted(session: Session) -> None:
    # Guards the anonymising lines at the end of delete_account.
    mari, _jonas, _home = household(session)
    email = mari.email

    delete(session, mari)

    kept = session.get(User, mari.id)
    assert kept is not None
    assert kept.name == photo_evidence.FORMER_MEMBER
    assert kept.email == f"deleted-{mari.id}@deleted.invalid"
    assert kept.deleted_at is not None
    assert accounts.authenticate(session, email=email, password=PASSWORD) is None
    assert accounts.authenticate(session, email=kept.email, password=PASSWORD) is None


def test_a_wrong_password_changes_nothing(session: Session) -> None:
    # Guards the verify() check at the top of delete_account.
    mari, _jonas, home = household(session)

    with pytest.raises(account_deletion.WrongPassword):
        account_deletion.delete_account(session, mari, "feil passord 1", get_photo_store())

    assert session.get(User, mari.id).deleted_at is None  # type: ignore[union-attr]
    assert exists(session, Membership, user_id=mari.id, home_id=home.id)


def test_a_deleted_user_cannot_delete_again(session: Session) -> None:
    # Guards `is_deleted(user)` in delete_account.
    mari, _jonas, _home = household(session)
    delete(session, mari)

    with pytest.raises(account_deletion.WrongPassword):
        delete(session, mari)


def test_a_landlord_with_a_tenant_is_refused_and_nothing_changes(session: Session) -> None:
    # Guards `_tenant_homes` and the refusal before any delete (FR-23).
    landlord, home = landlord_home(session)
    with_tenant(session, home)
    add_task(session, home.id)

    with pytest.raises(account_deletion.LandlordHasTenants) as caught:
        delete(session, landlord)

    assert caught.value.home_names == ["Storgata 12"]
    assert "Storgata 12" in str(caught.value)
    assert session.get(User, landlord.id).deleted_at is None  # type: ignore[union-attr]
    assert exists(session, Home, id=home.id)
    assert exists(session, Membership, user_id=landlord.id, home_id=home.id)
    assert exists(session, Task, home_id=home.id)


def test_a_landlord_home_without_tenants_is_deleted_with_everything_in_it(
    session: Session, store: LocalPhotoStore
) -> None:
    # Guards `_delete_home`: every table under a Home, and its stored photo.
    landlord, home = landlord_home(session)
    instance = add_task(session, home.id)
    key = add_photo(session, instance, landlord, store)
    task_id, home_id = instance.task_id, home.id
    session.add(DueNotification(task_instance_id=instance.id, user_id=landlord.id, day=TODAY))
    session.commit()
    link = invites.create_invite(
        session, session.exec(select(Membership).where(Membership.home_id == home.id)).one()
    )

    delete(session, landlord)

    assert not exists(session, Home, id=home_id)
    assert not exists(session, Task, home_id=home_id)
    assert not exists(session, TaskInstance, task_id=task_id)
    assert not exists(session, PhotoEvidence, task_id=task_id)
    assert not exists(session, DueNotification, user_id=landlord.id)
    assert not exists(session, InviteLink, home_id=home_id)
    assert link.token
    assert store.read(key) is None


def test_the_last_household_member_deletes_the_home(session: Session) -> None:
    # Guards the «still_has_member is None» branch.
    mari, jonas, home = household(session)
    add_task(session, home.id)

    delete(session, mari)
    assert exists(session, Home, id=home.id)
    delete(session, jonas)

    assert not exists(session, Home, id=home.id)
    assert not exists(session, Task, home_id=home.id)


def test_a_home_with_other_members_stays_and_keeps_the_history(
    session: Session, store: LocalPhotoStore
) -> None:
    # Guards that only a Home left without Members is deleted, and that history stays (AD-16).
    landlord, home = landlord_home(session)
    tenant = with_tenant(session, home)
    instance = add_task(session, home.id)
    # Both set in one flush: the CHECK wants them together, and reading tenant.id can autoflush.
    tenant_id = tenant.id
    instance.completed_by_user_id = tenant_id
    instance.completed_at = LOADED
    session.add(instance)
    key = add_photo(session, instance, tenant, store)

    delete(session, tenant)

    assert exists(session, Home, id=home.id)
    assert not exists(session, Membership, user_id=tenant.id)
    kept = session.exec(select(TaskInstance).where(TaskInstance.id == instance.id)).one()
    assert kept.completed_by_user_id == tenant.id
    assert store.read(key) == b"jpeg"
    evidence = session.exec(
        select(PhotoEvidence).where(PhotoEvidence.task_id == kept.task_id)
    ).one()
    assert "Anders" not in evidence.description
    assert photo_evidence.FORMER_MEMBER in evidence.description


def test_what_only_exists_for_the_user_is_deleted(session: Session) -> None:
    # Guards the four deletes after the Homes: devices, notifications, AI counts, unused links.
    mari, jonas, home = household(session)
    instance = add_task(session, home.id)
    session.add(
        PushSubscription(
            user_id=mari.id, endpoint="https://fcm.googleapis.com/x", p256dh="k", auth="a"
        )
    )
    session.add(DueNotification(task_instance_id=instance.id, user_id=mari.id, day=TODAY))
    session.add(AiUsage(user_id=mari.id, day=TODAY, count=3))
    mari_member = session.exec(
        select(Membership).where(Membership.user_id == mari.id, Membership.home_id == home.id)
    ).one()
    unused = invites.create_invite(session, mari_member)
    used = invites.create_invite(session, mari_member)
    newcomer = new_user(session, "Ola")
    session.commit()
    invites.accept(session, used.token, newcomer)

    delete(session, mari)

    assert not exists(session, PushSubscription, user_id=mari.id)
    assert not exists(session, DueNotification, user_id=mari.id)
    assert not exists(session, AiUsage, user_id=mari.id)
    remaining = session.exec(
        select(InviteLink).where(col(InviteLink.created_by_user_id) == mari.id)
    ).all()
    assert [link.used_by_user_id for link in remaining] == [newcomer.id]
    assert unused.token
    assert exists(session, Membership, user_id=jonas.id, home_id=home.id)


def test_another_users_data_is_untouched(session: Session) -> None:
    # Guards that every delete is scoped to the user or the emptied Homes.
    mari, _jonas, _home = household(session)
    other_landlord, other_home = landlord_home(session, "Bakgata 3")
    add_task(session, other_home.id)
    session.add(AiUsage(user_id=other_landlord.id, day=TODAY, count=2))
    session.commit()

    delete(session, mari)

    assert exists(session, Home, id=other_home.id)
    assert exists(session, Task, home_id=other_home.id)
    assert exists(session, AiUsage, user_id=other_landlord.id)
    assert session.get(User, other_landlord.id).deleted_at is None  # type: ignore[union-attr]


def test_a_failure_in_the_middle_rolls_everything_back(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Guards the try/except around the deletes: one transaction, all or nothing.
    landlord, home = landlord_home(session)
    instance = add_task(session, home.id)
    # A photo by the Tenant in a Home that stays reaches `describe`, which is made to fail.
    tenant = with_tenant(session, home)
    session.add(
        PhotoEvidence(
            task_id=instance.task_id,
            task_instance_id=instance.id,
            uploaded_by_user_id=tenant.id,
            uploaded_at=LOADED,
            description="x",
        )
    )
    session.commit()

    def boom(*_a: object) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr(photo_evidence, "describe", boom)

    with pytest.raises(RuntimeError):
        delete(session, tenant)

    session.expire_all()
    assert session.get(User, tenant.id).deleted_at is None  # type: ignore[union-attr]
    assert exists(session, Membership, user_id=tenant.id, home_id=home.id)
    assert landlord.id


def test_a_failing_photo_store_does_not_undo_the_deletion(
    session: Session, store: LocalPhotoStore
) -> None:
    # Guards the best-effort delete after the commit: an orphan photo is unreachable.
    landlord, home = landlord_home(session)
    add_photo(session, add_task(session, home.id), landlord, store)

    class Broken:
        def delete(self, key: str) -> None:
            raise StorageError("nede")

    account_deletion.delete_account(session, landlord, PASSWORD, Broken())  # type: ignore[arg-type]

    assert session.get(User, landlord.id).deleted_at is not None  # type: ignore[union-attr]
    assert not exists(session, Home, id=home.id)


def test_every_table_that_points_at_users_or_homes_is_handled() -> None:
    # Guards the metadata listing: a new table must be added to delete_account and here.
    handled_for_users = {
        "memberships",
        "invite_links",
        "push_subscriptions",
        "due_notifications",
        "ai_usage",
        "photo_evidence",
        "task_instances",
    }
    handled_for_homes = {"memberships", "tasks", "invite_links", "onboarding_guides"}

    assert handled_for_users  # the listing found something (it saw no tables once, Epic 4 A2)
    assert account_deletion.tables_pointing_at("users") == handled_for_users
    assert account_deletion.tables_pointing_at("homes") == handled_for_homes


def test_a_deleted_email_can_be_registered_again(client: TestClient) -> None:
    # Guards the tombstone e-mail: the address is free once the account is gone.
    response = client.post(
        "/api/auth/register", json={"email": "ola@example.com", "name": "Ola", "password": PASSWORD}
    )
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    gone = client.post("/api/auth/delete-account", json={"password": PASSWORD}, headers=headers)
    again = client.post(
        "/api/auth/register", json={"email": "ola@example.com", "name": "Ola", "password": PASSWORD}
    )

    assert gone.status_code == 204
    assert again.status_code == 201


def test_tokens_of_a_deleted_account_are_refused(client: TestClient) -> None:
    # Guards `deleted_at` in current_user and in the refresh route.
    registered = client.post(
        "/api/auth/register", json={"email": "ola@example.com", "name": "Ola", "password": PASSWORD}
    )
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    assert client.get("/api/auth/me", headers=headers).status_code == 200

    gone = client.post("/api/auth/delete-account", json={"password": PASSWORD}, headers=headers)

    assert gone.status_code == 204
    assert "husly_refresh" in gone.headers["set-cookie"]
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert client.post("/api/auth/refresh").status_code == 401
    login = client.post("/api/auth/login", json={"email": "ola@example.com", "password": PASSWORD})
    assert login.status_code == 401


def test_the_route_answers_400_for_a_wrong_password_and_409_for_a_landlord(
    client: TestClient, session: Session
) -> None:
    # Guards the two error mappings in the route (400, not 401/403, which the client reacts to).
    landlord, home = landlord_home(session)
    with_tenant(session, home)
    headers = auth_for(client, landlord.email)

    wrong = client.post(
        "/api/auth/delete-account", json={"password": "feil passord 1"}, headers=headers
    )
    blocked = client.post("/api/auth/delete-account", json={"password": PASSWORD}, headers=headers)

    assert wrong.status_code == 400
    assert wrong.json()["detail"] == account_deletion.WRONG_PASSWORD
    assert blocked.status_code == 409
    assert "Storgata 12" in blocked.json()["detail"]


def test_the_route_needs_a_session(client: TestClient) -> None:
    assert client.post("/api/auth/delete-account", json={"password": PASSWORD}).status_code == 401
