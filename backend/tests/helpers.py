"""Shared test helpers (Epic 1 retro, action 2, A2): plain functions, no fixtures.

Fixtures stay in conftest.py. The domain's register is reached as accounts.register, so the
API helper register_via_api never shares a name with it.
"""

import re
import uuid

import httpx
from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app.domain import accounts
from app.models.user import User

PASSWORD = "hemmelig1"


def _email(name: str) -> str:
    """A unique, valid address; the local part keeps only a-z and 0-9 ("Søren" → "sren")."""
    local = re.sub(r"[^a-z0-9]", "", name.lower()) or "user"
    return f"{local}-{uuid.uuid4().hex[:6]}@example.com"


def new_user(session: Session, name: str = "Ola") -> User:
    """A user with a unique email, registered through the domain."""
    return accounts.register(session, email=_email(name), name=name, password=PASSWORD)


def register_via_api(client: TestClient, name: str = "Ola", **extra: object) -> httpx.Response:
    """POST /api/auth/register with a unique email; `extra` adds fields such as invite_token."""
    return client.post(
        "/api/auth/register",
        json={"email": _email(name), "name": name, "password": PASSWORD, **extra},
    )


def sign_up(client: TestClient, name: str = "Ola") -> dict[str, str]:
    """Registers a new user and returns the Authorization header for them."""
    response = register_via_api(client, name)
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def auth_for(client: TestClient, email: str) -> dict[str, str]:
    """Signs in an existing user (password PASSWORD) and returns the Authorization header."""
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def count(session: Session, model: type) -> int:
    return session.exec(select(func.count()).select_from(model)).one()
