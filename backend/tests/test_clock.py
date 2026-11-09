"""Epic 1 retro, action 2 (A3): one clock, and every response datetime carries a zone.

SQLite (the test database) gives timestamps back without a zone; Postgres keeps it.
"""

import importlib
import inspect
import pkgutil
import typing
import uuid
from datetime import UTC, datetime, timedelta, timezone

from fastapi.testclient import TestClient
from pydantic import AfterValidator, BaseModel, TypeAdapter

import app.routes
from app.clock import UtcDatetime, as_utc, to_utc, utc_now
from app.routes.homes import HomeOut
from app.routes.invites import InviteOut
from tests.helpers import sign_up

NAIVE = datetime(2026, 11, 8, 12, 0)
OSLO = timezone(timedelta(hours=1))


def has_zone(value: str) -> bool:
    return value.endswith("Z") or value.endswith("+00:00")


def test_utc_now_is_aware_utc() -> None:
    assert utc_now().utcoffset() == timedelta(0)


def test_as_utc_gives_a_naive_value_utc() -> None:
    assert as_utc(NAIVE) == NAIVE.replace(tzinfo=UTC)


def test_as_utc_leaves_an_aware_value_unchanged() -> None:
    aware = NAIVE.replace(tzinfo=OSLO)
    assert as_utc(aware) is aware


def test_utc_datetime_gives_a_naive_value_utc() -> None:
    value = TypeAdapter(UtcDatetime).validate_python(NAIVE)
    assert value == NAIVE.replace(tzinfo=UTC)
    assert value.tzinfo == UTC


def test_utc_datetime_converts_another_zone_to_utc() -> None:
    value = TypeAdapter(UtcDatetime).validate_python(NAIVE.replace(tzinfo=OSLO))
    assert value == datetime(2026, 11, 8, 11, 0, tzinfo=UTC)
    assert value.tzinfo == UTC


def test_home_out_serialises_created_at_with_a_zone() -> None:
    home = HomeOut(
        id=uuid.uuid4(),
        name="Kollektivet",
        type="household",
        role="household_member",
        created_at=NAIVE,
        can_invite=True,
        can_leave=True,
        can_set_up_tasks=True,
        has_tasks=False,
    )
    assert has_zone(home.model_dump(mode="json")["created_at"])


def test_invite_out_serialises_expires_at_with_a_zone() -> None:
    invite = InviteOut(token="t", role="tenant", expires_at=NAIVE)
    assert has_zone(invite.model_dump(mode="json")["expires_at"])


def test_post_and_get_homes_return_created_at_with_a_zone(client: TestClient) -> None:
    auth = sign_up(client)
    created = client.post("/api/homes", json={"name": "Hjem", "type": "household"}, headers=auth)
    assert created.status_code == 201
    assert has_zone(created.json()["created_at"])

    listed = client.get("/api/homes", headers=auth)
    assert listed.status_code == 200
    assert has_zone(listed.json()["homes"][0]["created_at"])


def test_accepting_an_invite_returns_created_at_with_a_zone(client: TestClient) -> None:
    mari = sign_up(client, "Mari")
    home = client.post("/api/homes", json={"name": "Hjem", "type": "household"}, headers=mari)
    token = client.post(f"/api/homes/{home.json()['id']}/invites", headers=mari).json()["token"]

    accepted = client.post(f"/api/invites/{token}/accept", headers=sign_up(client, "Jonas"))

    assert accepted.status_code == 200
    assert has_zone(accepted.json()["created_at"])


def _is_utc(metadata: list[object]) -> bool:
    return any(isinstance(m, AfterValidator) and m.func is to_utc for m in metadata)


def _plain_datetimes(annotation: object, metadata: list[object]) -> bool:
    """True if a datetime somewhere in the annotation lacks the UtcDatetime validator."""
    if annotation is datetime:
        return not _is_utc(metadata)
    if typing.get_origin(annotation) is typing.Annotated:
        inner, *extra = typing.get_args(annotation)
        return _plain_datetimes(inner, list(extra))
    return any(_plain_datetimes(arg, []) for arg in typing.get_args(annotation))


def plain_datetime_fields(model: type[BaseModel]) -> list[str]:
    return [
        f"{model.__name__}.{name}"
        for name, field in model.model_fields.items()
        if _plain_datetimes(field.annotation, list(field.metadata))
    ]


def route_models() -> list[type[BaseModel]]:
    """Every Pydantic model defined in a module under app.routes."""
    found = []
    for info in pkgutil.iter_modules(app.routes.__path__, "app.routes."):
        module = importlib.import_module(info.name)
        found += [
            obj
            for obj in vars(module).values()
            if inspect.isclass(obj)
            and issubclass(obj, BaseModel)
            and obj.__module__ == module.__name__
        ]
    return found


def test_every_route_model_datetime_is_utc_datetime() -> None:
    models = route_models()
    assert HomeOut in models and InviteOut in models
    assert [f for m in models for f in plain_datetime_fields(m)] == []


def test_the_sweep_catches_a_plain_datetime() -> None:
    class Throwaway(BaseModel):
        good: UtcDatetime
        optional_good: UtcDatetime | None = None
        due_at: datetime
        maybe: datetime | None = None
        many: list[datetime] = []

    assert plain_datetime_fields(Throwaway) == [
        "Throwaway.due_at",
        "Throwaway.maybe",
        "Throwaway.many",
    ]
