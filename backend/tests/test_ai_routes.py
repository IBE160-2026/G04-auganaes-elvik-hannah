"""Story 5.1 (FR-14, AD-2, AD-4): POST /api/homes/{home_id}/tasks/{task_id}/answer."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, select

from app import ai
from app.ai import mock_answers, service
from app.ai.providers import AiRequest, GeminiProvider, ProviderAnswer
from app.models.ai_usage import AiUsage
from app.routes.ai import LIMIT_REACHED
from app.routes.deps import TASK_NOT_FOUND
from tests.helpers import register_via_api, sign_up
from tests.test_tasks_routes import ALL, create_home, join, list_tasks, set_up


def a_home_with_tasks(client: TestClient) -> tuple[dict[str, str], str, dict[str, str]]:
    """Mari's household with the eight catalog Tasks; returns her auth, the Home id and the
    `rens-sluket` Task."""
    mari = sign_up(client, "Mari")
    home_id = create_home(client, mari)
    assert set_up(client, mari, home_id, ALL).status_code == 201
    tasks = list_tasks(client, mari, home_id).json()["tasks"]
    task = next(t for t in tasks if t["task_type"] == "rens-sluket")
    return mari, home_id, task


def url(home_id: str, task: dict) -> str:
    return f"/api/homes/{home_id}/tasks/{task['id']}/answer"


def test_tapping_the_question_mark_answers_from_the_mock_with_the_disclaimer(
    client: TestClient,
) -> None:
    mari, home_id, task = a_home_with_tasks(client)
    response = client.post(url(home_id, task), json={}, headers=mari)
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "answer": mock_answers.BY_TASK_TYPE["rens-sluket"],
        "disclaimer": ai.DISCLAIMER,
        "demo": True,
    }


def test_a_chemical_question_is_answered_with_the_disclaimer(client: TestClient) -> None:
    mari, home_id, task = a_home_with_tasks(client)
    body = {"question": "Hvilket middel egner seg på fliser?"}
    response = client.post(url(home_id, task), json=body, headers=mari)
    assert response.status_code == 200 and response.json()["disclaimer"] == ai.DISCLAIMER


def test_a_tenant_may_ask_too(client: TestClient) -> None:
    mari, home_id, task = a_home_with_tasks(client)
    landlord = sign_up(client, "Kari")
    landlord_home = create_home(client, landlord, "landlord")
    assert set_up(client, landlord, landlord_home, ALL).status_code == 201
    anders = join(client, landlord, landlord_home, "Anders")
    tenant_task = list_tasks(client, anders, landlord_home).json()["tasks"][0]
    response = client.post(url(landlord_home, tenant_task), json={}, headers=anders)
    assert response.status_code == 200 and response.json()["status"] == "ok"


def test_the_21st_call_is_429_with_when_it_resets_and_never_reaches_the_provider(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    mari, home_id, task = a_home_with_tasks(client)
    calls: list[AiRequest] = []

    class Counting:
        demo = True

        def ask(self, request: AiRequest) -> ProviderAnswer:
            calls.append(request)
            return ProviderAnswer("ok", "Svar")

    monkeypatch.setattr(service, "select_provider", lambda: Counting())
    for _ in range(20):
        assert client.post(url(home_id, task), json={}, headers=mari).status_code == 200
    response = client.post(url(home_id, task), json={}, headers=mari)
    assert response.status_code == 429
    body = response.json()
    assert body["detail"] == LIMIT_REACHED and "20" in body["detail"]
    assert body["resets_at"].endswith("Z") or "+00:00" in body["resets_at"]
    assert len(calls) == 20


def test_each_user_has_their_own_count(client: TestClient) -> None:
    mari, home_id, task = a_home_with_tasks(client)
    jonas = join(client, mari, home_id, "Jonas")
    for _ in range(20):
        client.post(url(home_id, task), json={}, headers=mari)
    assert client.post(url(home_id, task), json={}, headers=mari).status_code == 429
    assert client.post(url(home_id, task), json={}, headers=jonas).status_code == 200


def test_the_request_to_gemini_has_no_user_name_email_or_home_name(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # End to end through the route: Kari's name and e-mail and the Home's name never leave.
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        text = json.dumps({"confidence": "ok", "answer": "Svar"})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})

    kari = register_via_api(client, "Kari Nordmann")
    auth = {"Authorization": f"Bearer {kari.json()['access_token']}"}
    home = client.post(
        "/api/homes", json={"name": "Hemmelig Borettslag", "type": "household"}, headers=auth
    )
    home_id = home.json()["id"]
    assert set_up(client, auth, home_id, ALL).status_code == 201
    task = next(
        t
        for t in list_tasks(client, auth, home_id).json()["tasks"]
        if t["task_type"] == "rens-sluket"
    )
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        service, "select_provider", lambda: GeminiProvider("nokkel", "modell", transport)
    )
    response = client.post(url(home_id, task), json={"question": "Hva med kalk?"}, headers=auth)
    assert response.status_code == 200 and response.json()["demo"] is False
    body = seen[0].content.decode()
    assert "Rens sluket" in body and "Hva med kalk?" in body
    for private in ("Kari", "Nordmann", kari.json()["user"]["email"], "Hemmelig", "Borettslag"):
        assert private not in body


def test_a_failing_provider_is_a_200_error_answer_and_not_a_500(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Broken:
        demo = False

        def ask(self, request: AiRequest) -> ProviderAnswer:
            raise RuntimeError("nede")

    mari, home_id, task = a_home_with_tasks(client)
    monkeypatch.setattr(service, "select_provider", lambda: Broken())
    response = client.post(url(home_id, task), json={}, headers=mari)
    assert response.status_code == 200
    assert response.json()["status"] == "error" and response.json()["disclaimer"] == ai.DISCLAIMER


def test_a_question_over_300_characters_is_422(client: TestClient, engine: Engine) -> None:
    mari, home_id, task = a_home_with_tasks(client)
    ok = client.post(url(home_id, task), json={"question": "x" * 300}, headers=mari)
    too_long = client.post(url(home_id, task), json={"question": "x" * 301}, headers=mari)
    assert (ok.status_code, too_long.status_code) == (200, 422)
    with Session(engine) as session:
        # The refused one reached neither the provider nor the count.
        assert [row.count for row in session.exec(select(AiUsage))] == [1]


def test_a_non_member_gets_403_and_a_foreign_or_unknown_task_404(client: TestClient) -> None:
    mari, home_id, task = a_home_with_tasks(client)
    outsider = sign_up(client, "Ola")
    assert client.post(url(home_id, task), json={}, headers=outsider).status_code == 403
    assert client.post(url(home_id, task), json={}).status_code == 401
    other_home = create_home(client, outsider)
    response = client.post(url(other_home, task), json={}, headers=outsider)
    assert response.status_code == 404 and response.json()["detail"] == TASK_NOT_FOUND
    missing = {"id": "00000000-0000-0000-0000-000000000000"}
    assert client.post(url(home_id, missing), json={}, headers=mari).status_code == 404


def test_an_archived_task_is_404_and_nothing_is_counted(client: TestClient, engine: Engine) -> None:
    mari, home_id, task = a_home_with_tasks(client)
    assert (
        client.delete(f"/api/homes/{home_id}/tasks/{task['id']}", headers=mari).status_code == 204
    )
    response = client.post(url(home_id, task), json={}, headers=mari)
    assert response.status_code == 404
    with Session(engine) as session:
        assert session.exec(select(AiUsage)).all() == []
