"""Story 4.2 (FR-18, FR-19, AD-3, AD-5, FR-22): a Tenant completes a task with a photo.

Each test that guards a rule names the line it guards (review convention, Epic 2 retro P1).
"""

import uuid
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.domain import homes, photo_evidence, tasks
from app.models.membership import Membership
from app.models.photo_evidence import PhotoEvidence
from app.models.task import Task, TaskInstance
from app.models.user import User
from tests.helpers import auth_for, new_user

JPEG = b"\xff\xd8\xff\xe0" + b"jpegdata" * 50 + b"\xff\xd9"


def landlord_home(session: Session) -> tuple[uuid.UUID, User, User]:
    kari = new_user(session, "Kari")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    martin = new_user(session, "Martin")
    homes.add_member(session, home, martin)
    return home.id, kari, martin


def add_task(
    session: Session,
    home_id: uuid.UUID,
    required: bool = True,
    name: str = "Rens sluket",
    task_type: str | None = "rens-sluket",
) -> tuple[Task, uuid.UUID]:
    task = Task(
        home_id=home_id,
        name=name,
        task_type=task_type,
        classification="must",
        frequency_days=30,
        requires_photo_evidence=required,
    )
    session.add(task)
    session.flush()
    instance = TaskInstance(task_id=task.id, due_on=date(2026, 11, 20))
    session.add(instance)
    session.commit()
    return task, instance.id


def upload(client: TestClient, user: User, home_id: uuid.UUID, task: Task, instance_id, body=JPEG):
    return client.post(
        f"/api/homes/{home_id}/tasks/{task.id}/instances/{instance_id}/photo-evidence",
        content=body,
        headers={**auth_for(client, user.email), "Content-Type": "image/jpeg"},
    )


def tick(client: TestClient, user: User, home_id: uuid.UUID, task: Task, instance_id):
    return client.post(
        f"/api/homes/{home_id}/tasks/{task.id}/instances/{instance_id}/completion",
        headers=auth_for(client, user.email),
    )


def stored_file(folder: Path, task: Task) -> bytes | None:
    path = folder / photo_evidence.evidence_key(task.id)
    return path.read_bytes() if path.is_file() else None


def test_a_tenant_uploads_and_the_task_is_completed_with_the_photo_stored_once(
    client: TestClient, session: Session, local_photo_store: Path
) -> None:
    home_id, _kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)

    response = upload(client, martin, home_id, task, instance_id)

    assert response.status_code == 200
    body = response.json()
    assert body["completion"]["by"] == "you"
    assert body["instance_id"] != str(instance_id)
    # Guards the photo going under the one server-computed key.
    assert stored_file(local_photo_store, task) == JPEG
    rows = session.exec(select(PhotoEvidence)).all()
    assert len(rows) == 1
    assert (rows[0].task_id, rows[0].task_instance_id) == (task.id, instance_id)
    assert rows[0].uploaded_by_user_id == martin.id
    assert rows[0].description.startswith("Bildebevis lastet opp av Martin, ")


def test_a_tenant_ticking_without_a_photo_is_refused_and_nothing_is_completed(
    client: TestClient, session: Session
) -> None:
    home_id, _kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)

    response = tick(client, martin, home_id, task, instance_id)

    # Guards `task.requires_photo_evidence and membership.role == "tenant" and not photo_attached`.
    assert response.status_code == 409
    assert response.json() == {"detail": tasks.PHOTO_REQUIRED}
    session.expire_all()
    instance = session.get(TaskInstance, instance_id)
    assert instance is not None and instance.completed_at is None


def test_the_landlord_and_a_task_without_a_requirement_complete_as_before(
    client: TestClient, session: Session
) -> None:
    home_id, kari, martin = landlord_home(session)
    required, required_instance = add_task(session, home_id)
    plain = Task(
        home_id=home_id, name="Vask gulv", task_type=None, classification="should", frequency_days=7
    )
    session.add(plain)
    session.flush()
    plain_instance = TaskInstance(task_id=plain.id, due_on=date(2026, 11, 20))
    session.add(plain_instance)
    session.commit()

    # Guards `membership.role == "tenant"`: the requirement is for Tenants (FR-18).
    assert tick(client, kari, home_id, required, required_instance).status_code == 200
    assert tick(client, martin, home_id, plain, plain_instance.id).status_code == 200


def test_a_household_member_and_the_landlord_may_not_use_the_upload_route(
    client: TestClient, session: Session
) -> None:
    home_id, kari, _martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)

    response = upload(client, kari, home_id, task, instance_id)

    # Guards the Tenant alias on the route.
    assert response.status_code == 403
    assert session.exec(select(PhotoEvidence)).all() == []


def test_an_upload_for_a_task_that_needs_no_photo_is_409_and_stores_nothing(
    client: TestClient, session: Session, local_photo_store: Path
) -> None:
    home_id, _kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id, required=False)

    response = upload(client, martin, home_id, task, instance_id)

    # Guards `if not task.requires_photo_evidence: raise PhotoNotRequired`.
    assert response.status_code == 409
    assert response.json() == {"detail": photo_evidence.NOT_REQUIRED}
    assert stored_file(local_photo_store, task) is None


# Short ids on purpose: a bytes value in a parameter id would put the whole body in the test name.
@pytest.mark.parametrize(
    ("body", "status_code", "message"),
    [
        pytest.param(b"\x89PNG\r\n\x1a\n" + b"x" * 100, 415, photo_evidence.NOT_JPEG, id="png"),
        pytest.param(b"", 415, photo_evidence.NOT_JPEG, id="empty"),
        pytest.param(b"just text", 415, photo_evidence.NOT_JPEG, id="text"),
        pytest.param(
            JPEG + b"x" * photo_evidence.MAX_PHOTO_BYTES, 413, photo_evidence.TOO_LARGE, id="large"
        ),
    ],
)
def test_a_bad_photo_is_refused_before_anything_is_stored_or_completed(
    client: TestClient,
    session: Session,
    local_photo_store: Path,
    body: bytes,
    status_code: int,
    message: str,
) -> None:
    home_id, _kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)

    response = upload(client, martin, home_id, task, instance_id, body)

    # Guards check_photo (signature) and the route's size limit running before store and completion.
    assert response.status_code == status_code
    assert response.json() == {"detail": message}
    assert stored_file(local_photo_store, task) is None
    session.expire_all()
    instance = session.get(TaskInstance, instance_id)
    assert instance is not None and instance.completed_at is None


def test_exactly_the_size_limit_is_accepted(client: TestClient, session: Session) -> None:
    home_id, _kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)
    body = JPEG[:-2] + b"x" * (photo_evidence.MAX_PHOTO_BYTES - len(JPEG)) + b"\xff\xd9"

    assert upload(client, martin, home_id, task, instance_id, body).status_code == 200


def test_a_second_completion_overwrites_the_photo_and_keeps_one_row(
    client: TestClient, session: Session, local_photo_store: Path
) -> None:
    home_id, _kari, martin = landlord_home(session)
    task, first_instance = add_task(session, home_id)
    first = upload(client, martin, home_id, task, first_instance)
    second_instance = first.json()["instance_id"]
    newer = JPEG[:-2] + b"newer" + b"\xff\xd9"

    second = upload(client, martin, home_id, task, second_instance, newer)

    # Guards AD-5: the same key and the same single row, now pointing at the second instance.
    assert second.status_code == 200
    assert stored_file(local_photo_store, task) == newer
    rows = session.exec(select(PhotoEvidence)).all()
    assert len(rows) == 1
    assert str(rows[0].task_instance_id) == second_instance
    files = [p for p in (local_photo_store / "tasks").rglob("*") if p.is_file()]
    assert len(files) == 1


def test_an_instance_completed_by_someone_else_stores_nothing_and_keeps_the_first_completer(
    client: TestClient, session: Session, local_photo_store: Path
) -> None:
    home_id, kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)
    landlord = session.exec(select(Membership).where(Membership.user_id == kari.id)).one()
    tasks.complete_task_instance(session, landlord, task.id, instance_id)

    response = upload(client, martin, home_id, task, instance_id)

    # Guards `if instance.completed_at is None:` in complete_with_photo: no store, no row.
    assert response.status_code == 200
    assert stored_file(local_photo_store, task) is None
    assert session.exec(select(PhotoEvidence)).all() == []
    session.expire_all()
    done = session.get(TaskInstance, instance_id)
    assert done is not None and done.completed_by_user_id == kari.id


def test_a_task_in_another_home_or_an_instance_of_another_task_is_404(
    client: TestClient, session: Session
) -> None:
    home_id, _kari, martin = landlord_home(session)
    task, _instance_id = add_task(session, home_id)
    _other_task, other_instance = add_task(
        session, home_id, name="Rens filteret i kjøkkenviften", task_type="kjokkenviftefilter"
    )
    other_home_owner = new_user(session, "Berit")
    other_home = homes.create_home(session, other_home_owner, name="Torget 1", type="landlord").home
    foreign, foreign_instance = add_task(session, other_home.id)

    # Guards the Home scoping and the instance-belongs-to-task check.
    assert upload(client, martin, home_id, foreign, foreign_instance).status_code == 404
    assert upload(client, martin, home_id, task, other_instance).status_code == 404


def test_the_upload_completes_through_the_same_function_as_the_checkbox(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    home_id, _kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)
    calls: list[bool] = []
    original = tasks.complete_task_instance

    def spy(*args, **kwargs):
        calls.append(kwargs.get("photo_attached", False))
        return original(*args, **kwargs)

    monkeypatch.setattr(tasks, "complete_task_instance", spy)

    upload(client, martin, home_id, task, instance_id)

    # Guards AD-3: one completion path, with the photo flag only from the upload.
    assert calls == [True]


def test_only_the_landlord_view_routes_serve_a_photo(client: TestClient) -> None:
    from tests.test_permissions import api_routes, has_require_role

    # The same walk as test_permissions: `app.routes` alone does not list included routers, so the
    # Story 4.2 version of this guard saw no routes at all and passed for nothing.
    served = {
        c.path: has_require_role(c)
        for c in api_routes(client.app)  # type: ignore[arg-type]
        if "GET" in (c.original_route.methods or ())  # type: ignore[union-attr]
        and ("evidence" in c.path or "photo" in c.path or "image" in c.path)
    }

    # Story 4.3: exactly the two Landlord routes (see test_photo_view.py); a new GET that could
    # serve the stored file must be added here on purpose.
    assert served == {
        "/api/homes/{home_id}/tasks/{task_id}/photo-evidence": True,
        "/api/homes/{home_id}/tasks/{task_id}/photo-evidence/image": True,
    }


def test_check_photo_refuses_a_too_large_or_non_jpeg_body_by_itself() -> None:
    with pytest.raises(photo_evidence.InvalidPhoto) as large:
        photo_evidence.check_photo(JPEG + b"x" * photo_evidence.MAX_PHOTO_BYTES)
    with pytest.raises(photo_evidence.InvalidPhoto) as plain:
        photo_evidence.check_photo(b"GIF89a")

    # Guards `len(data) > MAX_PHOTO_BYTES` and the signature check, without the route in front.
    assert (large.value.too_large, plain.value.too_large) == (True, False)
    photo_evidence.check_photo(JPEG)


def test_a_chunked_body_without_content_length_is_stopped_at_the_limit(
    client: TestClient, session: Session, local_photo_store: Path
) -> None:
    home_id, _kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)

    def chunks():
        for _ in range(8):
            yield JPEG + b"x" * 500_000

    response = client.post(
        f"/api/homes/{home_id}/tasks/{task.id}/instances/{instance_id}/photo-evidence",
        content=chunks(),
        headers={**auth_for(client, martin.email), "Content-Type": "image/jpeg"},
    )

    # Guards the running count in read_photo_body: no Content-Length to trust.
    assert response.status_code == 413
    assert stored_file(local_photo_store, task) is None


def test_a_missing_task_is_404_whatever_the_body_is(client: TestClient, session: Session) -> None:
    home_id, _kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)
    gone = Task(
        home_id=home_id, name="Fjernet", task_type=None, classification="must", frequency_days=7
    )
    gone.id = uuid.uuid4()

    # Guards the order: the Task is looked up before the photo is checked (matrix: 404, not 415).
    assert upload(client, martin, home_id, gone, instance_id, b"not a jpeg").status_code == 404
    assert upload(client, martin, home_id, task, instance_id, b"not a jpeg").status_code == 415


def test_an_archived_task_is_404(client: TestClient, session: Session) -> None:
    home_id, _kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)
    task.archived_at = tasks.utc_now()
    session.add(task)
    session.commit()

    assert upload(client, martin, home_id, task, instance_id).status_code == 404


def test_a_store_that_fails_answers_503_and_completes_nothing(
    client: TestClient, session: Session
) -> None:
    from app.storage import StorageError, get_photo_store

    class FailingStore:
        def put(self, key: str, data: bytes) -> None:
            raise StorageError("disk")

        def read(self, key: str) -> bytes | None:
            return None

    home_id, _kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)
    client.app.dependency_overrides[get_photo_store] = FailingStore  # type: ignore[attr-defined]
    try:
        response = upload(client, martin, home_id, task, instance_id)
    finally:
        client.app.dependency_overrides.pop(get_photo_store, None)  # type: ignore[attr-defined]

    # Guards `except StorageError` in the route and the rollback: no row, no completion.
    assert response.status_code == 503
    assert response.json() == {"detail": photo_evidence.STORE_FAILED}
    assert session.exec(select(PhotoEvidence)).all() == []
    session.expire_all()
    instance = session.get(TaskInstance, instance_id)
    assert instance is not None and instance.completed_at is None


def test_a_long_display_name_does_not_overflow_the_description(session: Session) -> None:
    text = photo_evidence.describe("A" * 500, date(2026, 9, 29))

    assert (
        len(text[: photo_evidence.DESCRIPTION_MAX_LENGTH]) == photo_evidence.DESCRIPTION_MAX_LENGTH
    )


def test_the_description_is_written_by_the_server_with_a_norwegian_short_month() -> None:
    assert photo_evidence.describe("Martin", date(2026, 9, 29)) == (
        "Bildebevis lastet opp av Martin, 29. sep"
    )
    assert (
        photo_evidence.describe("Mari", date(2026, 5, 1)) == "Bildebevis lastet opp av Mari, 1. mai"
    )


def test_check_photo_refuses_a_cut_off_jpeg_and_accepts_padding() -> None:
    # Guards the end-marker check in check_photo: a file that starts like a JPEG but is cut off.
    with pytest.raises(photo_evidence.InvalidPhoto) as cut:
        photo_evidence.check_photo(JPEG[:-2] + b"abc")
    with pytest.raises(photo_evidence.InvalidPhoto) as glued:
        photo_evidence.check_photo(JPEG + b"trailing")

    assert (cut.value.too_large, glued.value.too_large) == (False, False)
    photo_evidence.check_photo(JPEG + b"\x00\x00")


@pytest.mark.parametrize("had_photo", [True, False])
def test_a_failed_completion_puts_the_old_photo_back(
    client: TestClient,
    session: Session,
    local_photo_store: Path,
    monkeypatch: pytest.MonkeyPatch,
    had_photo: bool,
) -> None:
    # Guards `_restore` in complete_with_photo: the photo is stored before the completion commits,
    # so a failing completion must not leave the new photo under the Task's key.
    from app.storage import LocalPhotoStore

    home_id, _kari, martin = landlord_home(session)
    task, instance_id = add_task(session, home_id)
    store = LocalPhotoStore(local_photo_store)
    key = photo_evidence.evidence_key(task.id)
    if had_photo:
        store.put(key, b"old")
    membership = session.exec(
        select(Membership).where(Membership.user_id == martin.id, Membership.home_id == home_id)
    ).one()

    def boom(*_a: object, **_k: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(tasks, "complete_task_instance", boom)

    with pytest.raises(RuntimeError):
        photo_evidence.complete_with_photo(session, store, membership, task.id, instance_id, JPEG)

    assert store.read(key) == (b"old" if had_photo else None)
