"""Story 2.1 (FR-4, FR-8, AD-2, AD-6): GET /api/task-types, POST /api/homes/{home_id}/tasks/setup,
GET /api/homes/{home_id}/tasks and HomeOut's can_set_up_tasks / has_tasks.
"""

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, select

from app.clock import utc_now
from app.domain import homes, tasks
from app.domain.task_types import CATALOG_VERSION, FREQUENCY_DAYS, TASK_TYPES
from app.models.task import Task, TaskInstance
from app.permissions.require_role import FORBIDDEN
from app.routes.tasks import ALREADY_SET_UP
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
            "task_type",
            "name",
            "classification",
            "frequency_days",
            "due_on",
            "due_status",
            "days_until_due",
        }
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
        task = session.exec(select(Task)).one()
        session.add(TaskInstance(task_id=task.id, due_on=today + timedelta(days=offset)))
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
