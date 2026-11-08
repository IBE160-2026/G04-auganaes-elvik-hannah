"""Story 1.5 (FR-3, SM-6, AD-2): every Home-scoped route goes through require_role.

The routes are found by walking the app, not listed by hand, so a route added in Epics 2–6
without require_role fails here without anyone remembering to add a test. Every API route with a
path placeholder must have {home_id} among its placeholders (and so require_role), or be on
NOT_HOME_SCOPED with a reason; today that is only the two token-scoped /api/invites/{token} routes.
"""

import re
import uuid
from collections.abc import Iterator

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute, RouteContext, iter_route_contexts
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session

from app.config import Settings
from app.domain import homes
from app.main import create_app
from app.models.membership import ROLES
from app.permissions.current_user import CurrentUser
from app.permissions.require_role import FORBIDDEN
from tests.helpers import auth_for, new_user

REQUIRE_ROLE = "require_role.<locals>.dependency"
PLACEHOLDER = re.compile(r"\{([^}:]+)(?::[^}]*)?\}")


def api_routes(app: FastAPI) -> list[RouteContext]:
    """Every API route with its full path, including those from included routers. This FastAPI
    version includes routers lazily, so app.routes alone does not list them; this is the same
    walk the OpenAPI schema uses."""
    return [c for c in iter_route_contexts(app.routes) if isinstance(c.original_route, APIRoute)]


def dependants(dependant: Dependant) -> Iterator[Dependant]:
    yield dependant
    for sub in dependant.dependencies:
        yield from dependants(sub)


def has_require_role(route: RouteContext) -> bool:
    return any(
        getattr(d.call, "__qualname__", None) == REQUIRE_ROLE for d in dependants(route.dependant)
    )


def placeholders(path: str) -> list[str]:
    return PLACEHOLDER.findall(path)


# Routes with a path placeholder that are not Home-scoped, each with the reason.
NOT_HOME_SCOPED = {
    "/api/invites/{token}": "token-scoped: the invite page is shown before the viewer is a Member",
    "/api/invites/{token}/accept": "token-scoped: the caller is not a Member until this succeeds",
}


def home_routes(routes: list[RouteContext]) -> list[RouteContext]:
    return [r for r in routes if "home_id" in placeholders(r.path)]


ROUTES = api_routes(
    create_app(Settings(database_url="postgresql+psycopg://unused", jwt_secret="x" * 32))
)
HOME_ROUTES = home_routes(ROUTES)


def test_the_walk_finds_the_home_scoped_routes() -> None:
    # Never passes vacuously: invites (1.4) and members (1.5) are Home-scoped today.
    assert len(HOME_ROUTES) >= 2
    paths = {r.path for r in HOME_ROUTES}
    assert {
        "/api/homes/{home_id}/invites",
        "/api/homes/{home_id}/members",
        # Story 1.8
        "/api/homes/{home_id}/members/me",
        "/api/homes/{home_id}/members/{user_id}",
    } <= paths


def test_the_walk_catches_a_home_id_route_without_require_role() -> None:
    # The AC: a new {home_id} route without require_role makes this file fail.
    router = APIRouter(prefix="/homes")

    @router.get("/{home_id}/tasks")
    def forgotten(home_id: uuid.UUID, user: CurrentUser) -> None: ...

    app = FastAPI()
    app.include_router(router, prefix="/api")
    [route] = home_routes(api_routes(app))
    assert route.path == "/api/homes/{home_id}/tasks"
    assert not has_require_role(route)


@pytest.mark.parametrize("route", HOME_ROUTES, ids=lambda r: f"{sorted(r.methods)} {r.path}")
def test_every_home_id_route_uses_require_role(route: RouteContext) -> None:
    assert has_require_role(route), f"{route.path} has {{home_id}} but no require_role"


@pytest.mark.parametrize("route", ROUTES, ids=lambda r: f"{sorted(r.methods)} {r.path}")
def test_every_route_with_a_placeholder_is_home_scoped_or_allowlisted(route: RouteContext) -> None:
    # Catches a Home-scoped route under another name, e.g. /api/tasks/{task_id}.
    names = placeholders(route.path)
    if names:
        assert "home_id" in names or route.path in NOT_HOME_SCOPED, route.path


@pytest.mark.parametrize("route", ROUTES, ids=lambda r: f"{sorted(r.methods)} {r.path}")
def test_require_role_only_on_routes_with_home_id_in_the_path(route: RouteContext) -> None:
    # Otherwise require_role would have no home_id to read (AD-2: never from the query).
    if has_require_role(route):
        assert "home_id" in placeholders(route.path)


@pytest.mark.parametrize("route", ROUTES, ids=lambda r: f"{sorted(r.methods)} {r.path}")
def test_the_home_under_api_homes_is_always_called_home_id(route: RouteContext) -> None:
    match = re.match(r"^/api/homes/(\{[^}]*\})", route.path)
    if match:
        assert placeholders(match.group(1)) == ["home_id"], route.path


@pytest.mark.parametrize("route", ROUTES, ids=lambda r: f"{sorted(r.methods)} {r.path}")
def test_no_route_takes_home_id_from_anywhere_but_the_path(route: RouteContext) -> None:
    for dependant in dependants(route.dependant):
        for param in (
            *dependant.query_params,
            *dependant.header_params,
            *dependant.cookie_params,
            *dependant.body_params,
        ):
            assert "home_id" not in (param.name, param.alias), route.path
        for param in dependant.body_params:
            # An embedded body model with a home_id field counts too.
            fields = getattr(param.field_info.annotation, "model_fields", {})
            assert "home_id" not in fields, route.path


@pytest.mark.parametrize("role", ROLES)
def test_a_member_of_one_home_gets_403_on_every_route_of_another(
    client: TestClient, engine: Engine, role: str
) -> None:
    """Cross-Home sweep: whatever the caller's Role in A, every {home_id} route for B is 403."""
    with Session(engine) as session:
        caller = new_user(session, "Caller")
        if role == "tenant":
            home_a = homes.create_home(
                session, new_user(session, "Eier"), name="A", type="landlord"
            )
            homes.add_member(session, home_a.home, caller)
        else:
            home_type = "landlord" if role == "landlord" else "household"
            homes.create_home(session, caller, name="A", type=home_type)
        home_b = homes.create_home(session, new_user(session, "B"), name="B", type="household").home
        assert [h.role for h in homes.homes_for(session, caller)] == [role]
        home_b_id, email = str(home_b.id), caller.email
    auth = auth_for(client, email)

    for route in HOME_ROUTES:
        path = PLACEHOLDER.sub(
            lambda m: home_b_id if m.group(1) == "home_id" else str(uuid.uuid4()), route.path
        )
        for method in route.methods:
            response = client.request(method, path, headers=auth)
            assert response.status_code == 403, f"{method} {route.path}: {response.status_code}"
            assert response.json() == {"detail": FORBIDDEN}
