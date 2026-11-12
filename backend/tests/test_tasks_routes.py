"""Story 2.1 (FR-4, FR-8, AD-2, AD-6): GET /api/task-types, POST /api/homes/{home_id}/tasks/setup,
GET /api/homes/{home_id}/tasks and HomeOut's can_set_up_tasks / has_tasks.

Story 2.3 (FR-5, FR-8): PATCH /api/homes/{home_id}/tasks/{task_id} and HomeOut.can_adjust_tasks.

Story 2.4 (FR-7, FR-9, AD-3, AD-16): POST .../tasks/{task_id}/instances/{instance_id}/completion
and TaskOut.instance_id / completion.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, col, select

from app.clock import utc_now
from app.domain import homes, tasks
from app.domain.task_types import CATALOG_VERSION, FREQUENCY_DAYS, TASK_TYPES
from app.models.task import Task, TaskInstance
from app.permissions.require_role import FORBIDDEN
from app.routes.tasks import ALREADY_SET_UP, TASK_NOT_FOUND
from tests.helpers import count, sign_up

ALL = [
    {"task_type": t.key, "classification": t.classification, "frequency_days": t.frequency_days}
    for t in TASK_TYPES
]


def create_home(client: TestClient, auth: dict[str, str], type: str = "household") -> str:
    response = client.post("/api/homes", json={"name": "Hjem", "type": type}, headers=auth)
    assert response.status_code == 201
    return response.json()["id"]


def set_up(client: TestClient, auth: dict[str, str] | None, home_id: str, chosen: list) -> object:
    return client.post(f"/api/homes/{home_id}/tasks/setup", json={"tasks": chosen}, headers=auth)


def list_tasks(client: TestClient, auth: dict[str, str], home_id: str):
    return client.get(f"/api/homes/{home_id}/tasks", headers=auth)


def written(engine: Engine) -> tuple[int, int]:
    with Session(engine) as session:
        return count(session, Task), count(session, TaskInstance)


def join(client: TestClient, inviter: dict[str, str], home_id: str, name: str) -> dict[str, str]:
    token = client.post(f"/api/homes/{home_id}/invites", headers=inviter).json()["token"]
    joiner = sign_up(client, name)
    assert client.post(f"/api/invites/{token}/accept", headers=joiner).status_code == 200
    return joiner


def test_task_types_lists_the_catalog_and_the_intervals(client: TestClient) -> None:
    response = client.get("/api/task-types", headers=sign_up(client))

    assert response.status_code == 200
    body = response.json()
    assert body["catalog_version"] == CATALOG_VERSION
    assert body["frequencies"] == list(FREQUENCY_DAYS)
    assert [t["key"] for t in body["task_types"]] == [t.key for t in TASK_TYPES]
    assert body["task_types"][1] == {
        "key": "rens-sluket",
        "name": "Rens sluket",
        "classification": "must",
        "frequency_days": 30,
        "photo_evidence_eligible": True,
    }


def test_task_types_needs_sign_in(client: TestClient) -> None:
    assert client.get("/api/task-types").status_code == 401


def test_accept_as_is_is_201_with_the_same_body_as_get(client: TestClient, engine: Engine) -> None:
    auth = sign_up(client)
    home_id = create_home(client, auth)

    response = set_up(client, auth, home_id, ALL)

    assert response.status_code == 201
    body = response.json()
    assert len(body["tasks"]) == 8 and written(engine) == (8, 8)
    assert body == list_tasks(client, auth, home_id).json()
    today = utc_now().date()
    for task in body["tasks"]:
        assert set(task) == {
            "id",
            "instance_id",
            "task_type",
            "name",
            "classification",
            "frequency_days",
            "due_on",
            "due_status",
            "days_until_due",
            "completion",
        }
        assert task["completion"] is None
        assert date.fromisoformat(task["due_on"]) == today + timedelta(days=task["frequency_days"])
        assert task["days_until_due"] == task["frequency_days"]
        due_soon = task["frequency_days"] <= tasks.DUE_SOON_DAYS
        assert task["due_status"] == ("due_soon" if due_soon else "later")
    classes = [t["classification"] for t in body["tasks"]]
    assert classes == sorted(classes)  # "must" < "should": Must first


def test_adjusted_and_unticked_rows(client: TestClient) -> None:
    auth = sign_up(client)
    home_id = create_home(client, auth)
    chosen = [
        {**row, "classification": "must", "frequency_days": 60}
        if row["task_type"] == "stekeovn"
        else row
        for row in ALL
        if row["task_type"] not in {"gulv", "dusjfuger"}
    ]

    response = set_up(client, auth, home_id, chosen)

    assert response.status_code == 201
    by_key = {t["task_type"]: t for t in response.json()["tasks"]}
    assert set(by_key) == {row["task_type"] for row in chosen}
    assert (by_key["stekeovn"]["classification"], by_key["stekeovn"]["frequency_days"]) == (
        "must",
        60,
    )
    assert by_key["stekeovn"]["name"] == "Vask stekeovnen"


@pytest.mark.parametrize(
    ("chosen", "detail"),
    [
        ([], tasks.NO_TASKS_CHOSEN),
        (
            [{"task_type": "finnes-ikke", "classification": "must", "frequency_days": 7}],
            "Ukjent oppgave: «finnes-ikke».",
        ),
        ([ALL[0], ALL[0]], f"Oppgaven «{ALL[0]['task_type']}» er valgt mer enn én gang."),
    ],
    ids=["empty", "unknown", "duplicate"],
)
def test_domain_errors_are_422_with_a_norwegian_detail(
    client: TestClient, engine: Engine, chosen: list, detail: str
) -> None:
    auth = sign_up(client)
    response = set_up(client, auth, create_home(client, auth), chosen)
    assert response.status_code == 422
    assert response.json() == {"detail": detail}
    assert written(engine) == (0, 0)


@pytest.mark.parametrize(
    "row",
    [
        {"task_type": "gulv", "classification": "should", "frequency_days": 10},
        {"task_type": "gulv", "classification": "maybe", "frequency_days": 14},
        {"task_type": "gulv", "classification": "should"},
    ],
    ids=["frequency-10", "maybe", "missing-frequency"],
)
def test_shape_errors_are_pydantic_422s(client: TestClient, engine: Engine, row: dict) -> None:
    auth = sign_up(client)
    response = set_up(client, auth, create_home(client, auth), [ALL[0], row])
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert written(engine) == (0, 0)


def test_more_rows_than_the_catalog_is_a_pydantic_422(client: TestClient, engine: Engine) -> None:
    auth = sign_up(client)
    response = set_up(client, auth, create_home(client, auth), [*ALL, ALL[0]])
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert written(engine) == (0, 0)


def test_second_setup_is_409_and_creates_nothing(client: TestClient, engine: Engine) -> None:
    auth = sign_up(client)
    home_id = create_home(client, auth)
    assert set_up(client, auth, home_id, ALL[:3]).status_code == 201

    response = set_up(client, auth, home_id, ALL[3:])

    assert response.status_code == 409
    assert response.json() == {"detail": ALREADY_SET_UP}
    assert written(engine) == (3, 3)


def test_overlapping_race_is_409_not_500(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    auth = sign_up(client)
    home_id = create_home(client, auth)
    assert set_up(client, auth, home_id, ALL[:1]).status_code == 201
    # Both requests passed the empty check (see test_tasks.py for why this is faked).
    monkeypatch.setattr(tasks, "has_tasks", lambda *_: False)

    response = set_up(client, auth, home_id, ALL)

    assert response.status_code == 409
    assert written(engine) == (1, 1)


def test_landlord_home_without_tenants_is_201(client: TestClient) -> None:
    auth = sign_up(client, "Kari")
    response = set_up(client, auth, create_home(client, auth, "landlord"), ALL)
    assert response.status_code == 201


def test_tenant_outsider_and_unknown_home_get_the_same_403(
    client: TestClient, engine: Engine
) -> None:
    kari = sign_up(client, "Kari")
    home_id = create_home(client, kari, "landlord")
    anders = join(client, kari, home_id, "Anders")
    outsider = sign_up(client, "Per")
    create_home(client, outsider)

    for auth, target in ((anders, home_id), (outsider, home_id), (outsider, str(uuid.uuid4()))):
        response = set_up(client, auth, target, ALL)
        assert response.status_code == 403
        assert response.json() == {"detail": FORBIDDEN}
    assert written(engine) == (0, 0)


def test_signed_out_is_401(client: TestClient) -> None:
    auth = sign_up(client)
    home_id = create_home(client, auth)
    assert set_up(client, None, home_id, ALL).status_code == 401
    assert client.get(f"/api/homes/{home_id}/tasks").status_code == 401


def test_any_member_reads_the_tasks_a_landlord_set_up(client: TestClient) -> None:
    kari = sign_up(client, "Kari")
    home_id = create_home(client, kari, "landlord")
    anders = join(client, kari, home_id, "Anders")
    set_up(client, kari, home_id, ALL)

    response = list_tasks(client, anders, home_id)

    assert response.status_code == 200
    assert response.json() == list_tasks(client, kari, home_id).json()
    assert len(response.json()["tasks"]) == 8


@pytest.mark.parametrize(
    ("offset", "status"),
    [
        (-1, "overdue"),
        (0, "due_soon"),
        (tasks.DUE_SOON_DAYS, "due_soon"),
        (tasks.DUE_SOON_DAYS + 1, "later"),
    ],
)
def test_get_says_each_tasks_due_status_and_day_count_from_the_utc_date(
    client: TestClient, engine: Engine, offset: int, status: str
) -> None:
    auth = sign_up(client)
    home_id = create_home(client, auth)
    set_up(client, auth, home_id, [ALL[0]])
    today = utc_now().date()
    with Session(engine) as session:
        instance = session.exec(select(TaskInstance)).one()
        instance.due_on = today + timedelta(days=offset)
        session.add(instance)
        session.commit()

    [task_out] = list_tasks(client, auth, home_id).json()["tasks"]

    assert (task_out["due_status"], task_out["days_until_due"]) == (status, offset)
    assert task_out["due_on"] == (today + timedelta(days=offset)).isoformat()


def test_a_home_without_tasks_lists_none(client: TestClient) -> None:
    auth = sign_up(client)
    response = list_tasks(client, auth, create_home(client, auth))
    assert response.status_code == 200
    assert response.json() == {"tasks": []}


def test_outsider_reading_tasks_is_403(client: TestClient) -> None:
    auth = sign_up(client)
    home_id = create_home(client, auth)
    response = list_tasks(client, sign_up(client, "Per"), home_id)
    assert response.status_code == 403
    assert response.json() == {"detail": FORBIDDEN}


def test_home_out_says_who_may_set_up_and_whether_tasks_exist(client: TestClient) -> None:
    kari = sign_up(client, "Kari")
    created = client.post("/api/homes", json={"name": "Storgata", "type": "landlord"}, headers=kari)
    assert (created.json()["can_set_up_tasks"], created.json()["has_tasks"]) == (True, False)
    home_id = created.json()["id"]
    token = client.post(f"/api/homes/{home_id}/invites", headers=kari).json()["token"]
    anders = sign_up(client, "Anders")

    # Accepting an invite returns HomeOut too.
    accepted = client.post(f"/api/invites/{token}/accept", headers=anders).json()
    assert (accepted["can_set_up_tasks"], accepted["has_tasks"]) == (False, False)

    set_up(client, kari, home_id, ALL)
    [kari_home] = client.get("/api/homes", headers=kari).json()["homes"]
    [anders_home] = client.get("/api/homes", headers=anders).json()["homes"]
    assert (kari_home["can_set_up_tasks"], kari_home["has_tasks"]) == (True, True)
    assert (anders_home["can_set_up_tasks"], anders_home["has_tasks"]) == (False, True)


def test_accepting_into_a_set_up_home_says_it_has_tasks(client: TestClient) -> None:
    mari = sign_up(client, "Mari")
    home_id = create_home(client, mari)
    set_up(client, mari, home_id, ALL)
    token = client.post(f"/api/homes/{home_id}/invites", headers=mari).json()["token"]

    accepted = client.post(f"/api/invites/{token}/accept", headers=sign_up(client, "Jonas"))

    assert (accepted.json()["can_set_up_tasks"], accepted.json()["has_tasks"]) == (True, True)


def test_a_landlords_homes_each_say_whether_they_have_tasks(client: TestClient) -> None:
    kari = sign_up(client, "Kari")
    older = create_home(client, kari, "landlord")
    newer = create_home(client, kari, "landlord")
    set_up(client, kari, newer, ALL)

    listed = {
        h["id"]: h["has_tasks"] for h in client.get("/api/homes", headers=kari).json()["homes"]
    }

    assert listed == {older: False, newer: True}


def test_setup_through_the_api_leaves_fr3_unchanged(client: TestClient, engine: Engine) -> None:
    kari = sign_up(client, "Kari")
    home_id = create_home(client, kari, "landlord")
    join(client, kari, home_id, "Anders")
    set_up(client, kari, home_id, ALL)
    with Session(engine) as session:
        assert homes.fr3_violations(session) == []


# Story 2.3 (FR-5, FR-8, issue #40): PATCH /api/homes/{home_id}/tasks/{task_id}.


def adjust(client: TestClient, auth: dict[str, str], home_id: str, task_id: str, body: object):
    return client.patch(f"/api/homes/{home_id}/tasks/{task_id}", json=body, headers=auth)


def sluket(client: TestClient, auth: dict[str, str], home_id: str) -> dict:
    return next(
        t
        for t in list_tasks(client, auth, home_id).json()["tasks"]
        if t["task_type"] == "rens-sluket"
    )


def stored(engine: Engine, task_id: str) -> tuple[str, int, list[date]]:
    with Session(engine) as session:
        task = session.exec(select(Task).where(Task.id == uuid.UUID(task_id))).one()
        dates = session.exec(
            select(TaskInstance.due_on).where(TaskInstance.task_id == task.id)
        ).all()
        return task.classification, task.frequency_days, sorted(dates)


def household_with_tasks(client: TestClient) -> tuple[dict[str, str], dict[str, str], str]:
    mari = sign_up(client, "Mari")
    home_id = create_home(client, mari)
    set_up(client, mari, home_id, ALL)
    jonas = join(client, mari, home_id, "Jonas")
    return mari, jonas, home_id


def landlord_with_tasks(client: TestClient) -> tuple[dict[str, str], dict[str, str], str]:
    kari = sign_up(client, "Kari")
    home_id = create_home(client, kari, "landlord")
    set_up(client, kari, home_id, ALL)
    anders = join(client, kari, home_id, "Anders")
    return kari, anders, home_id


def test_a_member_moves_a_task_to_bor_and_every_member_sees_it(
    client: TestClient, engine: Engine
) -> None:
    mari, jonas, home_id = household_with_tasks(client)
    task = sluket(client, mari, home_id)

    response = adjust(client, mari, home_id, task["id"], {"classification": "should"})

    assert response.status_code == 200
    body = response.json()
    assert body == {**task, "classification": "should"}
    listed = list_tasks(client, jonas, home_id).json()["tasks"]
    musts = [t["name"] for t in listed if t["classification"] == "must"]
    shoulds = [t["name"] for t in listed if t["classification"] == "should"]
    assert "Rens sluket" in shoulds and "Rens sluket" not in musts
    assert stored(engine, task["id"])[2] == [date.fromisoformat(task["due_on"])]


def test_a_landlord_lengthens_the_frequency_and_the_open_date_moves(
    client: TestClient, engine: Engine
) -> None:
    kari, anders, home_id = landlord_with_tasks(client)
    task = sluket(client, kari, home_id)
    old_due = date.fromisoformat(task["due_on"])

    response = adjust(client, kari, home_id, task["id"], {"frequency_days": 60})

    assert response.status_code == 200
    assert response.json()["frequency_days"] == 60
    assert response.json()["due_on"] == (old_due + timedelta(days=30)).isoformat()
    assert response.json()["days_until_due"] == task["days_until_due"] + 30
    # The Tenant reads the Landlord's change.
    assert sluket(client, anders, home_id)["frequency_days"] == 60
    assert stored(engine, task["id"]) == ("must", 60, [old_due + timedelta(days=30)])


def test_a_shorter_frequency_can_make_it_overdue_at_once(
    client: TestClient, engine: Engine
) -> None:
    mari, _, home_id = household_with_tasks(client)
    task = sluket(client, mari, home_id)
    today = utc_now().date()
    # As if set up 65 days ago with «Hvert år».
    with Session(engine) as session:
        row = session.exec(select(Task).where(Task.id == uuid.UUID(task["id"]))).one()
        row.frequency_days = 365
        instance = session.exec(select(TaskInstance).where(TaskInstance.task_id == row.id)).one()
        instance.due_on = today - timedelta(days=65) + timedelta(days=365)
        session.add(row)
        session.add(instance)
        session.commit()

    response = adjust(client, mari, home_id, task["id"], {"frequency_days": 7})

    assert response.json()["due_on"] == (today - timedelta(days=58)).isoformat()
    assert (response.json()["due_status"], response.json()["days_until_due"]) == ("overdue", -58)


def test_equal_values_or_a_resend_are_200_and_write_nothing(
    client: TestClient, engine: Engine
) -> None:
    mari, _, home_id = household_with_tasks(client)
    task = sluket(client, mari, home_id)
    before = stored(engine, task["id"])

    same = adjust(
        client, mari, home_id, task["id"], {"classification": "must", "frequency_days": 30}
    )
    assert same.status_code == 200
    assert same.json() == task
    assert stored(engine, task["id"]) == before

    first = adjust(client, mari, home_id, task["id"], {"frequency_days": 60})
    again = adjust(client, mari, home_id, task["id"], {"frequency_days": 60})
    assert again.status_code == 200
    assert again.json() == first.json()


def test_null_means_leave_as_is(client: TestClient, engine: Engine) -> None:
    mari, _, home_id = household_with_tasks(client)
    task = sluket(client, mari, home_id)

    response = adjust(
        client, mari, home_id, task["id"], {"classification": None, "frequency_days": 14}
    )

    assert (response.json()["classification"], response.json()["frequency_days"]) == ("must", 14)


@pytest.mark.parametrize(
    "body", [{"classification": "should"}, {"frequency_days": 60}, {}, {"frequency_days": 10}]
)
def test_a_tenant_gets_403_for_any_body_and_any_task(
    client: TestClient, engine: Engine, body: dict
) -> None:
    kari, anders, home_id = landlord_with_tasks(client)
    task = sluket(client, kari, home_id)
    before = stored(engine, task["id"])
    mari, _, other_home = household_with_tasks(client)
    foreign = sluket(client, mari, other_home)

    for task_id in (task["id"], foreign["id"], str(uuid.uuid4())):
        response = adjust(client, anders, home_id, task_id, body)
        assert response.status_code == 403
        assert response.json() == {"detail": FORBIDDEN}
    assert stored(engine, task["id"]) == before


def test_outsider_and_unknown_home_get_403(client: TestClient) -> None:
    mari, _, home_id = household_with_tasks(client)
    task = sluket(client, mari, home_id)
    outsider = sign_up(client, "Per")
    create_home(client, outsider)

    for target in (home_id, str(uuid.uuid4())):
        response = adjust(client, outsider, target, task["id"], {"classification": "should"})
        assert response.status_code == 403
        assert response.json() == {"detail": FORBIDDEN}


def test_another_homes_task_or_an_unknown_id_is_404(client: TestClient, engine: Engine) -> None:
    mari, _, home_id = household_with_tasks(client)
    kari, _, other_home = landlord_with_tasks(client)
    foreign = sluket(client, kari, other_home)
    before = stored(engine, foreign["id"])

    for task_id in (foreign["id"], str(uuid.uuid4())):
        response = adjust(client, mari, home_id, task_id, {"classification": "should"})
        assert response.status_code == 404
        assert response.json() == {"detail": TASK_NOT_FOUND}
    assert stored(engine, foreign["id"]) == before


@pytest.mark.parametrize("body", [{}, {"classification": None, "frequency_days": None}])
def test_nothing_to_change_is_422_ingen_endring(client: TestClient, body: dict) -> None:
    mari, _, home_id = household_with_tasks(client)
    task = sluket(client, mari, home_id)

    response = adjust(client, mari, home_id, task["id"], body)

    assert response.status_code == 422
    assert response.json() == {"detail": tasks.NO_CHANGE}


@pytest.mark.parametrize(
    "body",
    [
        {"frequency_days": 10},
        {"frequency_days": "x"},
        {"classification": "x"},
        {"classification": "Må"},
    ],
)
def test_adjust_shape_errors_are_pydantic_422s(
    client: TestClient, engine: Engine, body: dict
) -> None:
    mari, _, home_id = household_with_tasks(client)
    task = sluket(client, mari, home_id)
    before = stored(engine, task["id"])

    response = adjust(client, mari, home_id, task["id"], body)

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert stored(engine, task["id"]) == before


def test_a_bad_task_id_is_a_shape_422(client: TestClient) -> None:
    mari, _, home_id = household_with_tasks(client)
    response = adjust(client, mari, home_id, "ikke-en-uuid", {"classification": "should"})
    assert response.status_code == 422


def test_adjusting_signed_out_is_401(client: TestClient) -> None:
    mari, _, home_id = household_with_tasks(client)
    task = sluket(client, mari, home_id)
    response = client.patch(
        f"/api/homes/{home_id}/tasks/{task['id']}", json={"classification": "should"}
    )
    assert response.status_code == 401


def test_home_out_says_who_may_adjust_tasks(client: TestClient) -> None:
    kari, anders, home_id = landlord_with_tasks(client)
    mari, jonas, household_id = household_with_tasks(client)

    def flag(auth: dict[str, str], home: str) -> bool:
        listed = client.get("/api/homes", headers=auth).json()["homes"]
        return next(h for h in listed if h["id"] == home)["can_adjust_tasks"]

    assert flag(kari, home_id) is True
    assert flag(anders, home_id) is False
    assert flag(mari, household_id) is True
    assert flag(jonas, household_id) is True
    created = client.post("/api/homes", json={"name": "Ny", "type": "landlord"}, headers=kari)
    assert created.json()["can_adjust_tasks"] is True


# Story 2.4 (FR-7, FR-9, AD-3, AD-16, issue #43): completing a Task's open instance.


def complete(client: TestClient, auth: dict[str, str], home_id: str, task_id: str, instance: str):
    return client.post(
        f"/api/homes/{home_id}/tasks/{task_id}/instances/{instance}/completion", headers=auth
    )


def complete_sluket(client: TestClient, auth: dict[str, str], home_id: str) -> dict:
    task = sluket(client, auth, home_id)
    response = complete(client, auth, home_id, task["id"], task["instance_id"])
    assert response.status_code == 200
    return response.json()


def instance_count(engine: Engine, task_id: str) -> int:
    with Session(engine) as session:
        rows = session.exec(
            select(TaskInstance).where(TaskInstance.task_id == uuid.UUID(task_id))
        ).all()
        return len(rows)


def move_open_instance(engine: Engine, task_id: str, due_on: date) -> None:
    with Session(engine) as session:
        instance = session.exec(
            select(TaskInstance).where(
                TaskInstance.task_id == uuid.UUID(task_id),
                col(TaskInstance.completed_at).is_(None),
            )
        ).one()
        instance.due_on = due_on
        session.add(instance)
        session.commit()


def test_jonas_completes_and_mari_sees_it_done_by_jonas(client: TestClient, engine: Engine) -> None:
    """Matrix «Complete» and «Seen by another»; AC 1."""
    mari, jonas, home_id = household_with_tasks(client)
    before = sluket(client, jonas, home_id)
    today = utc_now().date()

    body = complete_sluket(client, jonas, home_id)

    assert body["id"] == before["id"] and body["instance_id"] != before["instance_id"]
    assert body["due_on"] == (today + timedelta(days=30)).isoformat()
    assert (body["due_status"], body["days_until_due"]) == ("later", 30)
    assert body["completion"] == {
        "completed_on": today.isoformat(),
        "days_since": 0,
        "completed_this_year": True,
        "by": "you",
        "name": None,
    }
    # The response is the Task as the list shows it.
    assert body == sluket(client, jonas, home_id)
    assert sluket(client, mari, home_id)["completion"] == {
        **body["completion"],
        "by": "member",
        "name": "Jonas",
    }
    assert instance_count(engine, body["id"]) == 2


def test_a_retry_or_a_second_member_on_the_same_instance_changes_nothing(
    client: TestClient, engine: Engine
) -> None:
    """Matrix «Retry / race / double tap» and «Stale old instance id»."""
    mari, jonas, home_id = household_with_tasks(client)
    first = sluket(client, jonas, home_id)
    done = complete(client, jonas, home_id, first["id"], first["instance_id"]).json()

    again = complete(client, jonas, home_id, first["id"], first["instance_id"])
    by_mari = complete(client, mari, home_id, first["id"], first["instance_id"])

    assert again.status_code == by_mari.status_code == 200
    assert again.json() == done
    assert by_mari.json()["completion"]["by"] == "member"
    assert by_mari.json()["completion"]["name"] == "Jonas"
    assert by_mari.json()["instance_id"] == done["instance_id"]
    assert instance_count(engine, first["id"]) == 2


def test_ones_own_completion_never_has_a_name_also_in_a_one_person_home(
    client: TestClient,
) -> None:
    """Matrix «Own / one-person»; AC 4: Sara alone."""
    sara = sign_up(client, "Sara")
    home_id = create_home(client, sara)
    set_up(client, sara, home_id, ALL)

    body = complete_sluket(client, sara, home_id)

    assert (body["completion"]["by"], body["completion"]["name"]) == ("you", None)
    assert all(
        t["completion"] is None or t["completion"]["name"] is None
        for t in list_tasks(client, sara, home_id).json()["tasks"]
    )


def test_a_departed_completer_shows_as_former_member(client: TestClient) -> None:
    """Matrix «Departed»: Jonas leaves; then he is only a Member (Landlord) elsewhere."""
    mari, jonas, home_id = household_with_tasks(client)
    complete_sluket(client, jonas, home_id)

    assert client.delete(f"/api/homes/{home_id}/members/me", headers=jonas).status_code == 204
    left = sluket(client, mari, home_id)["completion"]
    create_home(client, jonas, "landlord")
    elsewhere = sluket(client, mari, home_id)["completion"]

    for completion in (left, elsewhere):
        assert (completion["by"], completion["name"]) == ("former_member", None)


@pytest.mark.parametrize(
    ("days_until_due", "shown"),
    [(tasks.DUE_SOON_DAYS + 1, True), (tasks.DUE_SOON_DAYS, False), (-1, False)],
)
def test_the_completion_is_shown_only_while_the_next_date_is_later(
    client: TestClient, engine: Engine, days_until_due: int, shown: bool
) -> None:
    """Decision 1 (1b): once due soon or overdue, the card shows the due line again."""
    mari, _, home_id = household_with_tasks(client)
    body = complete_sluket(client, mari, home_id)
    move_open_instance(engine, body["id"], utc_now().date() + timedelta(days=days_until_due))

    task = sluket(client, mari, home_id)

    assert (task["completion"] is not None) is shown


def test_an_older_completion_says_how_long_ago_and_whether_this_year(
    client: TestClient, engine: Engine
) -> None:
    mari, _, home_id = household_with_tasks(client)
    body = complete_sluket(client, mari, home_id)
    today = utc_now().date()
    last_year = date(today.year - 1, 12, 31)
    with Session(engine) as session:
        done = session.exec(
            select(TaskInstance).where(
                TaskInstance.task_id == uuid.UUID(body["id"]),
                col(TaskInstance.completed_at).is_not(None),
            )
        ).one()
        done.completed_at = datetime(last_year.year, 12, 31, 23, 59, tzinfo=UTC)
        session.add(done)
        session.commit()
    move_open_instance(engine, body["id"], today + timedelta(days=30))

    completion = sluket(client, mari, home_id)["completion"]

    assert completion["completed_on"] == last_year.isoformat()
    assert completion["days_since"] == (today - last_year).days
    assert completion["completed_this_year"] is False


def test_a_frequency_change_after_completion_keeps_the_completion(client: TestClient) -> None:
    """Matrix «Adjust after completion»."""
    mari, jonas, home_id = household_with_tasks(client)
    body = complete_sluket(client, jonas, home_id)

    response = adjust(client, mari, home_id, body["id"], {"frequency_days": 60})

    assert response.json()["due_on"] == (utc_now().date() + timedelta(days=60)).isoformat()
    assert response.json()["completion"] == {**body["completion"], "by": "member", "name": "Jonas"}


def test_a_tenant_may_complete(client: TestClient) -> None:
    """Matrix «Tenant»: 200 (the photo rule is Epic 4); the Landlord sees «av Anders»."""
    kari, anders, home_id = landlord_with_tasks(client)

    body = complete_sluket(client, anders, home_id)

    assert body["completion"]["by"] == "you"
    assert sluket(client, kari, home_id)["completion"]["name"] == "Anders"


def test_another_homes_task_or_another_tasks_instance_is_404(
    client: TestClient, engine: Engine
) -> None:
    """Matrix «Foreign ids»."""
    mari, _, home_id = household_with_tasks(client)
    kari, _, other_home = landlord_with_tasks(client)
    foreign = sluket(client, kari, other_home)
    mine = list_tasks(client, mari, home_id).json()["tasks"]
    a, b = mine[0], mine[1]

    cases = [
        (foreign["id"], foreign["instance_id"]),
        (str(uuid.uuid4()), a["instance_id"]),
        (a["id"], b["instance_id"]),
        (a["id"], foreign["instance_id"]),
        (a["id"], str(uuid.uuid4())),
    ]
    for task_id, instance_id in cases:
        response = complete(client, mari, home_id, task_id, instance_id)
        assert response.status_code == 404
        assert response.json() == {"detail": TASK_NOT_FOUND}
    assert written(engine) == (16, 16)


def test_completing_as_outsider_or_in_an_unknown_home_is_403(
    client: TestClient, engine: Engine
) -> None:
    """Matrix «Not a Member»."""
    mari, _, home_id = household_with_tasks(client)
    task = sluket(client, mari, home_id)
    outsider = sign_up(client, "Per")
    create_home(client, outsider)

    for target in (home_id, str(uuid.uuid4())):
        response = complete(client, outsider, target, task["id"], task["instance_id"])
        assert response.status_code == 403
        assert response.json() == {"detail": FORBIDDEN}
    assert instance_count(engine, task["id"]) == 1


def test_completing_signed_out_is_401_and_bad_ids_are_422(client: TestClient) -> None:
    mari, _, home_id = household_with_tasks(client)
    task = sluket(client, mari, home_id)

    assert complete(client, {}, home_id, task["id"], task["instance_id"]).status_code == 401
    assert complete(client, mari, home_id, task["id"], "ikke-en-uuid").status_code == 422
