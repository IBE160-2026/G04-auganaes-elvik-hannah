"""Story 4.1 (FR-18, AD-6): the Landlord's Photo Evidence requirement on a Task.

Each test that guards a rule names the line it guards (review convention, Epic 2 retro P1).
"""

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, select

from app.domain import homes, photo_evidence, tasks
from app.models.membership import Membership
from app.models.task import Task, TaskInstance
from app.models.user import User
from tests.helpers import auth_for, new_user

TODAY = date(2026, 11, 19)


def landlord_home(session: Session) -> tuple[uuid.UUID, User, User]:
    """A Landlord Home with Kari (landlord) and Anders (tenant)."""
    kari = new_user(session, "Kari")
    home = homes.create_home(session, kari, name="Storgata 12", type="landlord").home
    anders = new_user(session, "Anders")
    homes.add_member(session, home, anders)
    return home.id, kari, anders


def add_task(
    session: Session,
    home_id: uuid.UUID,
    name: str,
    task_type: str | None = "rens-sluket",
    classification: str = "must",
) -> Task:
    task = Task(
        home_id=home_id,
        name=name,
        task_type=task_type,
        classification=classification,
        frequency_days=30,
    )
    session.add(task)
    session.flush()
    session.add(TaskInstance(task_id=task.id, due_on=TODAY))
    session.commit()
    return task


def put(client: TestClient, user: User, home_id: uuid.UUID, task: Task, required: bool):
    return client.put(
        f"/api/homes/{home_id}/tasks/{task.id}/photo-evidence-requirement",
        json={"required": required},
        headers=auth_for(client, user.email),
    )


def stored(session: Session, task: Task) -> bool:
    session.expire_all()
    row = session.get(Task, task.id)
    assert row is not None
    return row.requires_photo_evidence


def test_the_landlord_requires_a_photo_on_an_eligible_must_task_and_no_other(
    client: TestClient, session: Session
) -> None:
    home_id, kari, _anders = landlord_home(session)
    sink = add_task(session, home_id, "Rens sluket")
    filter_ = add_task(session, home_id, "Rens filteret i kjøkkenviften", "kjokkenviftefilter")

    response = put(client, kari, home_id, sink, True)

    # Guards `task.requires_photo_evidence = required`, and that one call changes one Task.
    assert response.status_code == 200
    assert response.json() == {"requires_photo_evidence": True}
    assert stored(session, sink) is True
    assert stored(session, filter_) is False


def test_a_new_task_does_not_require_a_photo(session: Session) -> None:
    home_id, _kari, _anders = landlord_home(session)

    # Guards the column default: a requirement is an explicit Landlord setting, never a default.
    assert stored(session, add_task(session, home_id, "Rens sluket")) is False


@pytest.mark.parametrize(
    ("task_type", "name"),
    [("vask-badet", "Vask badet grundig"), (None, "Vask vinduer")],
)
def test_a_task_that_is_not_eligible_is_refused_with_409(
    client: TestClient, session: Session, task_type: str | None, name: str
) -> None:
    home_id, kari, _anders = landlord_home(session)
    task = add_task(session, home_id, name, task_type)

    response = put(client, kari, home_id, task, True)

    # Guards `photo_evidence_eligible(task)` in set_requirement: a catalog type without the flag
    # and a custom Task (no key) are both refused, and nothing is saved (AD-6).
    assert response.status_code == 409
    assert response.json() == {"detail": photo_evidence.NOT_ELIGIBLE}
    assert stored(session, task) is False


def test_a_should_task_of_an_eligible_type_is_refused_with_409(
    client: TestClient, session: Session
) -> None:
    home_id, kari, _anders = landlord_home(session)
    task = add_task(session, home_id, "Rens sluket", classification="should")

    response = put(client, kari, home_id, task, True)

    # Guards `task.classification != "must"` in set_requirement.
    assert response.status_code == 409
    assert response.json() == {"detail": photo_evidence.NOT_MUST}
    assert stored(session, task) is False


def test_turning_it_off_is_allowed_even_when_the_task_may_no_longer_require_it(
    client: TestClient, session: Session
) -> None:
    home_id, kari, _anders = landlord_home(session)
    task = add_task(session, home_id, "Rens sluket", classification="should")
    task.requires_photo_evidence = True
    session.add(task)
    session.commit()

    response = put(client, kari, home_id, task, False)

    # Guards the `if required:` branch: only turning it ON is checked.
    assert response.status_code == 200
    assert stored(session, task) is False


def test_changing_a_task_to_bor_clears_the_requirement_and_back_does_not_restore_it(
    session: Session,
) -> None:
    home_id, kari, _anders = landlord_home(session)
    task = add_task(session, home_id, "Rens sluket")
    task.requires_photo_evidence = True
    session.add(task)
    session.commit()
    landlord = session.exec(select(Membership).where(Membership.user_id == kari.id)).one()

    tasks.adjust_task(session, landlord, task.id, classification="should")
    assert stored(session, task) is False

    tasks.adjust_task(session, landlord, task.id, classification="must")
    # Guards `if classification != "must": task.requires_photo_evidence = False`.
    assert stored(session, task) is False


def test_a_frequency_change_keeps_the_requirement(session: Session) -> None:
    home_id, kari, _anders = landlord_home(session)
    task = add_task(session, home_id, "Rens sluket")
    task.requires_photo_evidence = True
    session.add(task)
    session.commit()
    landlord = session.exec(select(Membership).where(Membership.user_id == kari.id)).one()

    tasks.adjust_task(session, landlord, task.id, frequency_days=60)

    # The clearing is only for a change to Bør, not for any adjustment.
    assert stored(session, task) is True


def test_a_tenant_may_not_set_it(client: TestClient, session: Session) -> None:
    home_id, _kari, anders = landlord_home(session)
    task = add_task(session, home_id, "Rens sluket")

    response = put(client, anders, home_id, task, True)

    # Guards the Landlord alias on the route.
    assert response.status_code == 403
    assert stored(session, task) is False


def test_a_household_member_and_a_stranger_get_the_same_403(
    client: TestClient, session: Session
) -> None:
    hanne = new_user(session, "Hanne")
    household = homes.create_home(session, hanne, name="Kollektivet", type="household").home
    task = add_task(session, household.id, "Rens sluket")
    stranger = new_user(session, "Fremmed")

    member = put(client, hanne, household.id, task, True)
    outsider = put(client, stranger, household.id, task, True)

    # Guards require_role: a Household Home has no Landlord, so nobody there may require a photo.
    assert member.status_code == 403
    assert member.json() == outsider.json()
    assert stored(session, task) is False


def test_a_task_in_another_home_or_an_archived_task_is_404(
    client: TestClient, session: Session
) -> None:
    home_id, kari, _anders = landlord_home(session)
    other = new_user(session, "Berit")
    other_home = homes.create_home(session, other, name="Torget 1", type="landlord").home
    foreign = add_task(session, other_home.id, "Rens sluket")
    archived = add_task(session, home_id, "Rens sluket")
    archived.archived_at = tasks.utc_now()
    session.add(archived)
    session.commit()

    # Guards the Home scoping in active_task: Kari's Home cannot reach another Home's Task.
    assert put(client, kari, home_id, foreign, True).status_code == 404
    assert put(client, kari, home_id, archived, True).status_code == 404
    assert stored(session, foreign) is False


def test_tasks_and_home_say_what_the_frontend_may_show(
    client: TestClient, session: Session
) -> None:
    home_id, kari, anders = landlord_home(session)
    add_task(session, home_id, "Rens sluket")
    add_task(session, home_id, "Vask badet grundig", "vask-badet")
    add_task(session, home_id, "Vask vinduer", None)
    add_task(session, home_id, "Rens filteret i kjøkkenviften", "kjokkenviftefilter", "should")
    headers = auth_for(client, kari.email)

    listed = client.get(f"/api/homes/{home_id}/tasks", headers=headers).json()["tasks"]
    may = {t["name"]: t["may_require_photo_evidence"] for t in listed}

    # Guards `may_require`: Must and an eligible catalog type, nothing else.
    assert may == {
        "Rens sluket": True,
        "Vask badet grundig": False,
        "Vask vinduer": False,
        "Rens filteret i kjøkkenviften": False,
    }
    assert client.get("/api/homes", headers=headers).json()["homes"][0][
        "can_require_photo_evidence"
    ]
    tenant = client.get("/api/homes", headers=auth_for(client, anders.email)).json()["homes"][0]
    assert tenant["can_require_photo_evidence"] is False


def test_the_database_has_the_column_with_a_false_default(session: Session) -> None:
    home_id, _kari, _anders = landlord_home(session)
    task_id = uuid.uuid4()

    session.execute(
        text(
            "INSERT INTO tasks (id, home_id, task_type, name, classification, frequency_days,"
            " created_at) VALUES (:id, :h, NULL, 'x', 'must', 7, :t)"
        ),
        {"id": task_id.hex, "h": home_id.hex, "t": "2026-11-19 12:00:00"},
    )
    session.commit()

    row = session.get(Task, task_id)
    assert row is not None
    # Guards the server default: existing rows and raw inserts start without a requirement.
    assert row.requires_photo_evidence is False
