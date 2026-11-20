"""Story 4.3 (FR-19, AD-5, NFR5, NFR6): the Landlord views the current photo.

Each test that guards a rule names the line it guards (review convention, Epic 2 retro P1).
"""

import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.domain import homes, photo_evidence
from app.models.task import Task, TaskInstance
from app.models.user import User
from app.storage import StorageError, get_photo_store
from tests.helpers import auth_for, new_user
from tests.test_photo_upload import JPEG, add_task, landlord_home, upload

SECOND = b"\xff\xd8\xff\xe1" + b"second" * 40


def base(home_id: uuid.UUID, task: Task) -> str:
    return f"/api/homes/{home_id}/tasks/{task.id}/photo-evidence"


def get(client: TestClient, user: User, url: str):
    return client.get(url, headers=auth_for(client, user.email))


def uploaded(client: TestClient, session: Session):
    home_id, kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)
    assert upload(client, martin, home_id, task, instance_id).status_code == 200
    return home_id, kari, martin, task


def test_the_landlord_gets_the_photo_through_the_backend_and_it_is_never_cached(
    client: TestClient, session: Session
) -> None:
    home_id, kari, _martin, task = uploaded(client, session)

    info = get(client, kari, base(home_id, task))
    image = get(client, kari, base(home_id, task) + "/image")

    assert info.status_code == 200
    assert info.json()["evidence"]["description"].startswith("Bildebevis lastet opp av Martin, ")
    assert image.status_code == 200
    assert image.content == JPEG
    assert image.headers["content-type"] == "image/jpeg"
    # Guards the headers on the image response: a per-user photo never lives in a shared cache.
    assert image.headers["cache-control"] == "private, no-store"
    assert image.headers["x-content-type-options"] == "nosniff"
    # Guards AD-5/NFR5: the body is the JPEG itself, no Blob or other URL is in any answer.
    assert "http" not in info.text


def test_no_photo_yet_is_a_200_without_evidence_and_the_image_is_404(
    client: TestClient, session: Session
) -> None:
    home_id, kari, _martin = landlord_home(session)
    task, _instance = add_task(session, home_id)

    info = get(client, kari, base(home_id, task))
    image = get(client, kari, base(home_id, task) + "/image")

    # Guards `row is None` in the info route: «no photo» is not «no such Task».
    assert info.status_code == 200 and info.json() == {"evidence": None}
    assert image.status_code == 404
    assert image.json() == {"detail": photo_evidence.NO_EVIDENCE}


def test_only_the_landlord_of_the_home_may_view_the_photo(
    client: TestClient, session: Session
) -> None:
    home_id, _kari, martin, task = uploaded(client, session)
    member = new_user(session, "Mia")
    household = homes.create_home(session, member, name="Hybel", type="household").home
    other_landlord = new_user(session, "Olav")
    homes.create_home(session, other_landlord, name="Annen gate", type="landlord")
    url = base(home_id, task)

    for user in (martin, member, other_landlord):
        for suffix in ("", "/image"):
            # Guards the Landlord alias on both routes (NFR5, NFR6): not the uploader, not a
            # member of another Home, not another Landlord.
            assert get(client, user, url + suffix).status_code == 403
    # A Landlord asking for this Task under their own Home does not find it either.
    assert get(client, other_landlord, base(household.id, task)).status_code == 403


def test_a_task_of_another_home_or_an_archived_task_is_404(
    client: TestClient, session: Session
) -> None:
    home_id, kari, _martin, task = uploaded(client, session)
    other = homes.create_home(session, kari, name="Nr 2", type="landlord").home
    task_row = session.get(Task, task.id)
    assert task_row is not None

    # Guards `Task.home_id == membership.home_id` in `active_task`.
    assert get(client, kari, base(other.id, task)).status_code == 404
    from app.clock import utc_now

    task_row.archived_at = utc_now()
    session.add(task_row)
    session.commit()
    # Guards `is_active()`: an archived Task is gone for the view as everywhere else.
    assert get(client, kari, base(home_id, task)).status_code == 404
    assert get(client, kari, base(home_id, task) + "/image").status_code == 404


def test_a_replaced_photo_is_the_only_one_viewed_and_one_object_exists(
    client: TestClient, session: Session, local_photo_store: Path
) -> None:
    home_id, kari, martin, task = uploaded(client, session)
    first = get(client, kari, base(home_id, task)).json()["evidence"]
    next_instance = session.exec(
        TaskInstance.__table__.select().where(  # type: ignore[attr-defined]
            TaskInstance.task_id == task.id,
            TaskInstance.completed_at.is_(None),  # type: ignore[union-attr]
        )
    ).one()

    assert upload(client, martin, home_id, task, next_instance.id, SECOND).status_code == 200

    image = get(client, kari, base(home_id, task) + "/image")
    # Guards the overwrite under the fixed key (FR-19, AD-5): no history, only the newest bytes.
    assert image.content == SECOND
    files = [p for p in (local_photo_store / "tasks").rglob("*") if p.is_file()]
    assert [p.relative_to(local_photo_store).as_posix() for p in files] == [
        photo_evidence.evidence_key(task.id)
    ]
    # The time changes with the photo, so the browser's query key changes and never shows stale.
    assert (
        get(client, kari, base(home_id, task)).json()["evidence"]["uploaded_at"]
        >= first["uploaded_at"]
    )


def test_a_row_without_a_stored_object_is_404_and_a_store_failure_is_503(
    client: TestClient, session: Session, local_photo_store: Path
) -> None:
    home_id, kari, _martin, task = uploaded(client, session)
    (local_photo_store / photo_evidence.evidence_key(task.id)).unlink()
    url = base(home_id, task) + "/image"

    # Guards `data is None` in read_photo: a clear message, not a 500.
    gone = get(client, kari, url)
    assert gone.status_code == 404
    assert gone.json() == {"detail": photo_evidence.PHOTO_GONE}

    class FailingStore:
        def put(self, key: str, data: bytes) -> None:
            raise StorageError("disk")

        def read(self, key: str) -> bytes | None:
            raise StorageError("blob down")

    client.app.dependency_overrides[get_photo_store] = FailingStore  # type: ignore[attr-defined]
    try:
        failed = get(client, kari, url)
    finally:
        client.app.dependency_overrides.pop(get_photo_store, None)  # type: ignore[attr-defined]
    # Guards `except StorageError` in the image route.
    assert failed.status_code == 503
    assert failed.json() == {"detail": photo_evidence.READ_FAILED}
