"""Story 1.1 (FR-22): health check and CORS against configured origins only."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, parse_origins
from app.main import create_app

ALLOWED = "http://localhost:5173"


@pytest.fixture
def client() -> TestClient:
    settings = Settings(database_url="postgresql+psycopg://unused", cors_origins=[ALLOWED])
    return TestClient(create_app(settings))


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_configured_origin(client: TestClient) -> None:
    response = client.get("/api/health", headers={"Origin": ALLOWED})
    assert response.headers["access-control-allow-origin"] == ALLOWED
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_rejects_other_origin(client: TestClient) -> None:
    response = client.get("/api/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_allows_configured_origin(client: TestClient) -> None:
    response = client.options(
        "/api/health",
        headers={"Origin": ALLOWED, "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_preflight_rejects_other_origin(client: TestClient) -> None:
    response = client.options(
        "/api/health",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_parse_origins_splits_and_trims() -> None:
    assert parse_origins(" http://a.test , http://b.test,,") == ["http://a.test", "http://b.test"]


def test_parse_origins_rejects_wildcard() -> None:
    with pytest.raises(ValueError):
        parse_origins("*")
