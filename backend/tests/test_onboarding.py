"""Story 5.3 (FR-16, AD-4, AD-16): the onboarding guide of a Landlord Home.

The introduction is written once when the Tasks are set up (mock provider in the tests, Gemini
only over httpx.MockTransport); the name and the Must tasks are read live. Every route is
Home-scoped and goes through require_role.
"""

import json
import time
import uuid

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app import ai
from app.ai import mock_answers, providers, service
from app.ai.providers import AiRequest, GeminiProvider, GuideRequest, ProviderAnswer
from app.domain import ai_usage, onboarding
from app.models.ai_usage import AiUsage
from app.models.home import Home
from app.models.membership import Membership
from app.models.onboarding_guide import INTRO_MAX_LENGTH, OnboardingGuide
from app.permissions.require_role import FORBIDDEN
from app.routes.onboarding import NO_GUIDE_YET
from tests.helpers import register_via_api, sign_up
from tests.test_tasks_routes import ALL, create_home, join, list_tasks, set_up

MUST = [t for t in ALL if t["classification"] == "must"]
SHOULD = [t for t in ALL if t["classification"] == "should"]


def guide_url(home_id: str) -> str:
    return f"/api/homes/{home_id}/onboarding-guide"


def a_landlord_home(client: TestClient, chosen: list | None = None):
    """Kari's Landlord Home with its Tasks set up, and Anders as its Tenant."""
    kari = sign_up(client, "Kari")
    home_id = create_home(client, kari, "landlord")
    assert set_up(client, kari, home_id, chosen or ALL).status_code == 201
    anders = join(client, kari, home_id, "Anders")
    return kari, anders, home_id


def stored(engine: Engine, home_id: str) -> OnboardingGuide | None:
    with Session(engine) as session:
        return session.get(OnboardingGuide, uuid.UUID(home_id))


def usage(engine: Engine) -> int:
    with Session(engine) as session:
        return sum(row.count for row in session.exec(select(AiUsage)).all())


class Spy:
    """A provider that counts guide calls and answers as told."""

    demo = False

    def __init__(self, result: str | Exception = "Velkommen til hjemmet!") -> None:
        self.result = result
        self.guide_requests: list[GuideRequest] = []

    def ask(self, request: AiRequest) -> ProviderAnswer:  # pragma: no cover - not used here
        raise AssertionError("the guide must not ask a question")

    def write_guide(self, request: GuideRequest) -> str:
        self.guide_requests.append(request)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def use(monkeypatch: pytest.MonkeyPatch, provider) -> None:
    monkeypatch.setattr(service, "select_provider", lambda: provider)


# --- generated once, at setup -----------------------------------------------------------------


def test_setting_up_a_landlord_home_stores_the_introduction_from_the_mock(
    client: TestClient, engine: Engine
) -> None:
    kari, _, home_id = a_landlord_home(client)
    row = stored(engine, home_id)
    assert row is not None and row.source == "demo" and row.intro == mock_answers.GUIDE_DEMO
    assert usage(engine) == 1


def test_a_household_home_gets_no_guide_and_no_ai_call(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = Spy()
    use(monkeypatch, spy)
    mari = sign_up(client, "Mari")
    home_id = create_home(client, mari, "household")
    assert set_up(client, mari, home_id, ALL).status_code == 201
    assert stored(engine, home_id) is None and spy.guide_requests == [] and usage(engine) == 0


def test_a_real_provider_marks_the_introduction_ai(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    use(monkeypatch, Spy("Hei, ny leietaker!"))
    _, anders, home_id = a_landlord_home(client)
    row = stored(engine, home_id)
    assert row is not None and (row.source, row.intro) == ("ai", "Hei, ny leietaker!")
    body = client.get(guide_url(home_id), headers=anders).json()
    assert body["source"] == "ai" and body["demo"] is False
    assert body["disclaimer"] == ai.DISCLAIMER and body["intro"] == "Hei, ny leietaker!"


def test_a_failing_provider_still_sets_up_and_stores_the_fallback(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    use(monkeypatch, Spy(RuntimeError("nede")))
    kari = sign_up(client, "Kari")
    home_id = create_home(client, kari, "landlord")
    assert set_up(client, kari, home_id, ALL).status_code == 201
    row = stored(engine, home_id)
    assert row is not None and row.source == "fallback"
    assert row.intro == onboarding.FALLBACK_INTRO
    # The call reached the provider, so it counts (FR-14).
    assert usage(engine) == 1


def test_a_slow_provider_gives_the_fallback_within_the_deadline(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Slow(Spy):
        def write_guide(self, request: GuideRequest) -> str:
            time.sleep(2)
            return "for sent"

    use(monkeypatch, Slow())
    monkeypatch.setattr(service, "AI_TIMEOUT_SECONDS", 0.2)
    started = time.monotonic()
    kari = sign_up(client, "Kari")
    home_id = create_home(client, kari, "landlord")
    assert set_up(client, kari, home_id, ALL).status_code == 201
    assert time.monotonic() - started < 1.5
    row = stored(engine, home_id)
    assert row is not None and row.source == "fallback"


def test_a_landlord_who_used_the_twenty_calls_still_sets_up_with_the_fallback(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = Spy()
    use(monkeypatch, spy)
    kari = sign_up(client, "Kari")
    home_id = create_home(client, kari, "landlord")
    with Session(engine) as session:
        user_id = session.exec(
            select(Membership.user_id).where(Membership.home_id == uuid.UUID(home_id))
        ).one()
        for _ in range(ai_usage.AI_DAILY_LIMIT):
            assert ai_usage.try_count_call(session, user_id, service.utc_today(), 20)
    assert set_up(client, kari, home_id, ALL).status_code == 201
    row = stored(engine, home_id)
    assert row is not None and row.source == "fallback" and spy.guide_requests == []
    assert usage(engine) == 20


def test_a_provider_that_cannot_be_chosen_gives_the_fallback_and_spends_no_call(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken() -> object:
        raise RuntimeError("ingen leverandør")

    monkeypatch.setattr(service, "select_provider", broken)
    kari = sign_up(client, "Kari")
    home_id = create_home(client, kari, "landlord")
    assert set_up(client, kari, home_id, ALL).status_code == 201
    row = stored(engine, home_id)
    assert row is not None and row.source == "fallback" and usage(engine) == 0


# --- reading and the Home-specific part ------------------------------------------------------


def test_the_guide_names_the_home_and_lists_the_current_must_tasks_with_frequencies(
    client: TestClient,
) -> None:
    _, anders, home_id = a_landlord_home(client)
    response = client.get(guide_url(home_id), headers=anders)
    assert response.status_code == 200
    body = response.json()
    assert body["home_name"] == "Hjem" and body["dismissed"] is False
    assert body["source"] == "demo" and body["demo"] is True
    assert body["disclaimer"] == ai.DISCLAIMER and body["intro"] == mock_answers.GUIDE_DEMO
    listed = {(t["name"], t["frequency_days"]) for t in body["must_tasks"]}
    assert listed == {(t["name"], t["frequency_days"]) for t in list_must(client, anders, home_id)}
    assert len(listed) == len(MUST) > 0


def list_must(client: TestClient, auth: dict[str, str], home_id: str) -> list[dict]:
    rows = list_tasks(client, auth, home_id).json()["tasks"]
    return [t for t in rows if t["classification"] == "must"]


def test_the_fallback_text_has_no_disclaimer_and_no_demo_marker(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    use(monkeypatch, Spy(RuntimeError("nede")))
    _, anders, home_id = a_landlord_home(client)
    body = client.get(guide_url(home_id), headers=anders).json()
    assert body["source"] == "fallback" and body["disclaimer"] is None and body["demo"] is False


def test_later_changes_to_the_tasks_show_in_the_list_but_not_in_the_introduction(
    client: TestClient,
) -> None:
    kari, anders, home_id = a_landlord_home(client, MUST[:2])
    before = client.get(guide_url(home_id), headers=anders).json()
    archived = list_must(client, kari, home_id)[0]
    added = client.post(
        f"/api/homes/{home_id}/tasks",
        json={"name": "Vann blomstene", "classification": "must", "frequency_days": 7},
        headers=kari,
    )
    assert added.status_code == 201
    assert (
        client.delete(f"/api/homes/{home_id}/tasks/{archived['id']}", headers=kari).status_code
        == 204
    )
    after = client.get(guide_url(home_id), headers=anders).json()
    names = [t["name"] for t in after["must_tasks"]]
    assert "Vann blomstene" in names and archived["name"] not in names
    assert after["intro"] == before["intro"]


def test_two_homes_with_different_must_tasks_never_get_the_same_list(client: TestClient) -> None:
    _, anders_a, home_a = a_landlord_home(client, MUST[:1])
    _, anders_b, home_b = a_landlord_home(client, MUST[1:2])
    a = client.get(guide_url(home_a), headers=anders_a).json()
    b = client.get(guide_url(home_b), headers=anders_b).json()
    assert a["must_tasks"] != b["must_tasks"]


def test_should_tasks_are_not_in_the_list(client: TestClient) -> None:
    _, anders, home_id = a_landlord_home(client, [*MUST[:1], *SHOULD[:1]])
    body = client.get(guide_url(home_id), headers=anders).json()
    assert [t["name"] for t in body["must_tasks"]] == [
        list_must(client, anders, home_id)[0]["name"]
    ]


def test_reading_never_calls_the_provider_again(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = Spy()
    use(monkeypatch, spy)
    _, anders, home_id = a_landlord_home(client)
    for _ in range(3):
        assert client.get(guide_url(home_id), headers=anders).status_code == 200
    assert len(spy.guide_requests) == 1


def test_a_home_set_up_before_the_guide_shows_the_fallback_and_stores_nothing(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, anders, home_id = a_landlord_home(client)
    with Session(engine) as session:
        session.delete(session.get(OnboardingGuide, uuid.UUID(home_id)))
        session.commit()
    spy = Spy()
    use(monkeypatch, spy)
    body = client.get(guide_url(home_id), headers=anders).json()
    assert body["source"] == "fallback" and body["intro"] == onboarding.FALLBACK_INTRO
    assert stored(engine, home_id) is None and spy.guide_requests == []


def test_a_stored_introduction_is_never_replaced_and_is_not_even_written_again(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = Home(name="H", type="landlord")
    session.add(home)
    session.commit()
    onboarding.store_guide(session, home.id, "Første", "ai")
    added: list[object] = []
    original = session.add
    monkeypatch.setattr(session, "add", lambda row: (added.append(row), original(row))[1])
    onboarding.store_guide(session, home.id, "Andre", "demo")
    row = session.get(OnboardingGuide, home.id)
    assert row is not None and (row.intro, row.source) == ("Første", "ai")
    # The early return: no second row is even attempted (the primary key would only refuse it).
    assert added == []


def test_two_writers_at_once_keep_the_first_and_the_second_does_not_raise(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = Home(name="H", type="landlord")
    session.add(home)
    session.commit()
    onboarding.store_guide(session, home.id, "Første", "ai")
    # The second writer looked before the first committed: its lookup finds nothing.
    monkeypatch.setattr(session, "get", lambda *args, **kwargs: None)
    onboarding.store_guide(session, home.id, "Andre", "demo")
    monkeypatch.undo()
    row = session.get(OnboardingGuide, home.id)
    assert row is not None and (row.intro, row.source) == ("Første", "ai")


def test_an_unknown_source_is_refused_by_the_database(session: Session) -> None:
    home = Home(name="H", type="landlord")
    session.add(home)
    session.commit()
    session.add(OnboardingGuide(home_id=home.id, intro="x", source="manuell"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


# --- who may do what --------------------------------------------------------------------------


def test_the_landlord_reads_the_guide_but_it_is_not_dismissed_for_them(client: TestClient) -> None:
    kari, _, home_id = a_landlord_home(client)
    assert client.get(guide_url(home_id), headers=kari).status_code == 200
    assert client.post(guide_url(home_id) + "/dismiss", headers=kari).status_code == 403


def test_a_household_member_and_an_outsider_get_403(client: TestClient) -> None:
    mari = sign_up(client, "Mari")
    household = create_home(client, mari, "household")
    assert set_up(client, mari, household, ALL).status_code == 201
    outsider = sign_up(client, "Ukjent")
    _, _, landlord_home = a_landlord_home(client)
    for url, auth in [(household, mari), (landlord_home, outsider)]:
        assert client.get(guide_url(url), headers=auth).json() == {"detail": FORBIDDEN}
        assert client.get(guide_url(url), headers=auth).status_code == 403
        assert client.post(guide_url(url) + "/dismiss", headers=auth).status_code == 403


def test_signed_out_is_401(client: TestClient) -> None:
    _, _, home_id = a_landlord_home(client)
    assert client.get(guide_url(home_id)).status_code == 401
    assert client.post(guide_url(home_id) + "/dismiss").status_code == 401


def test_before_the_tasks_are_set_up_there_is_no_guide(client: TestClient) -> None:
    kari = sign_up(client, "Kari")
    home_id = create_home(client, kari, "landlord")
    response = client.get(guide_url(home_id), headers=kari)
    assert response.status_code == 404 and response.json() == {"detail": NO_GUIDE_YET}


def test_home_out_says_who_may_view_the_guide(client: TestClient) -> None:
    kari, anders, _ = a_landlord_home(client)
    mari = sign_up(client, "Mari")
    household = create_home(client, mari, "household")
    assert set_up(client, mari, household, ALL).status_code == 201
    empty = sign_up(client, "Tom")
    empty_home = create_home(client, empty, "landlord")

    def flag(auth: dict[str, str]) -> list[bool]:
        homes = client.get("/api/homes", headers=auth).json()["homes"]
        return [h["can_view_guide"] for h in homes]

    assert flag(kari) == [True] and flag(anders) == [True]
    assert flag(mari) == [False] and flag(empty) == [False]
    # A Landlord Home before setup has no guide to view, and the server says so.
    assert client.get(guide_url(empty_home), headers=empty).status_code == 404


# --- dismissing -------------------------------------------------------------------------------


def test_dismissing_is_idempotent_and_per_tenant(client: TestClient, engine: Engine) -> None:
    kari, anders, home_id = a_landlord_home(client)
    petter = join(client, kari, home_id, "Petter")
    assert client.post(guide_url(home_id) + "/dismiss", headers=anders).status_code == 204
    with Session(engine) as session:
        first = session.exec(
            select(Membership.onboarding_dismissed_at).where(
                Membership.home_id == uuid.UUID(home_id),
                Membership.onboarding_dismissed_at.is_not(None),
            )
        ).one()
    assert client.post(guide_url(home_id) + "/dismiss", headers=anders).status_code == 204
    assert client.get(guide_url(home_id), headers=anders).json()["dismissed"] is True
    assert client.get(guide_url(home_id), headers=petter).json()["dismissed"] is False
    with Session(engine) as session:
        again = session.exec(
            select(Membership.onboarding_dismissed_at).where(
                Membership.onboarding_dismissed_at.is_not(None)
            )
        ).one()
    assert again == first


def test_a_tenant_who_leaves_and_is_invited_again_sees_the_card_again(client: TestClient) -> None:
    kari, anders, home_id = a_landlord_home(client)
    assert client.post(guide_url(home_id) + "/dismiss", headers=anders).status_code == 204
    assert client.delete(f"/api/homes/{home_id}/members/me", headers=anders).status_code == 204
    token = client.post(f"/api/homes/{home_id}/invites", headers=kari).json()["token"]
    assert client.post(f"/api/invites/{token}/accept", headers=anders).status_code == 200
    assert client.get(guide_url(home_id), headers=anders).json()["dismissed"] is False


# --- what reaches the provider ---------------------------------------------------------------


def test_the_gemini_request_has_only_the_must_tasks_and_the_guide_instruction(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        text = json.dumps({"intro": "Velkommen!"})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})

    monkeypatch.setattr(
        service,
        "select_provider",
        lambda: GeminiProvider("nokkel", "modell", httpx.MockTransport(handler)),
    )
    kari = register_via_api(client, "Kari Nordmann")
    auth = {"Authorization": f"Bearer {kari.json()['access_token']}"}
    home = client.post(
        "/api/homes", json={"name": "Hemmelig Borettslag", "type": "landlord"}, headers=auth
    )
    home_id = home.json()["id"]
    chosen = [*MUST[:2], *SHOULD[:1]]
    assert set_up(client, auth, home_id, chosen).status_code == 201
    sent = json.loads(seen[0].content)
    text = seen[0].content.decode()
    for private in ("Kari", "Nordmann", kari.json()["user"]["email"], "Hemmelig", "Borettslag"):
        assert private not in text
    user_text = sent["contents"][0]["parts"][0]["text"]
    for task in MUST[:2]:
        assert task["task_type"] in user_text and f"hver {task['frequency_days']}. dag" in user_text
    # A Bør task never reaches the provider: only the Must tasks are listed.
    assert SHOULD[0]["task_type"] not in user_text
    assert sent["systemInstruction"]["parts"][0]["text"] == providers.GUIDE_INSTRUCTION
    # Nothing else rides along: the body has exactly these parts, and one user turn.
    assert set(sent) == {"systemInstruction", "contents", "generationConfig"}
    assert len(sent["contents"]) == 1 and sent["contents"][0]["role"] == "user"
    assert len(sent["contents"][0]["parts"]) == 1
    assert len(user_text.splitlines()) == 1 + len(MUST[:2])
    assert str(home_id) not in text
    assert "Hemmelig" not in providers.GUIDE_INSTRUCTION


def test_the_guide_instruction_asks_for_norwegian_how_the_app_works_and_no_cleaning_howto() -> None:
    # A tripwire on the wording only: what the model writes cannot be tested offline.
    text = providers.GUIDE_INSTRUCTION
    assert "norsk bokmål" in text and "høyst 120 ord" in text
    assert "ikke forklare hvordan noe rengjøres" in text


def test_a_gemini_guide_with_a_blank_intro_is_the_fallback(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        text = json.dumps({"intro": "   "})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})

    monkeypatch.setattr(
        service,
        "select_provider",
        lambda: GeminiProvider("nokkel", "modell", httpx.MockTransport(handler)),
    )
    _, _, home_id = a_landlord_home(client)
    row = stored(engine, home_id)
    assert row is not None and row.source == "fallback"


def test_an_answer_longer_than_the_table_holds_is_the_fallback_not_a_cut_sentence(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    use(monkeypatch, Spy("x" * (INTRO_MAX_LENGTH + 1)))
    _, _, home_id = a_landlord_home(client)
    row = stored(engine, home_id)
    assert row is not None and row.source == "fallback" and row.intro == onboarding.FALLBACK_INTRO


def test_an_answer_exactly_as_long_as_the_table_holds_is_kept(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    use(monkeypatch, Spy("x" * INTRO_MAX_LENGTH))
    _, _, home_id = a_landlord_home(client)
    row = stored(engine, home_id)
    assert row is not None and row.source == "ai" and len(row.intro) == INTRO_MAX_LENGTH


def test_a_home_with_no_must_tasks_gets_the_fixed_text_and_no_ai_call(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    spy = Spy()
    use(monkeypatch, spy)
    _, _, home_id = a_landlord_home(client, SHOULD[:2])
    row = stored(engine, home_id)
    assert row is not None and row.source == "fallback"
    assert spy.guide_requests == [] and usage(engine) == 0


@pytest.mark.parametrize(
    "body",
    ["ikke json", json.dumps({}), json.dumps({"intro": 5}), json.dumps({"intro": None})],
    ids=["not-json", "no-intro", "number", "null"],
)
def test_a_malformed_gemini_guide_is_the_fallback(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch, body: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": body}]}}]})

    monkeypatch.setattr(
        service,
        "select_provider",
        lambda: GeminiProvider("nokkel", "modell", httpx.MockTransport(handler)),
    )
    _, _, home_id = a_landlord_home(client)
    row = stored(engine, home_id)
    assert row is not None and row.source == "fallback"


def test_a_database_failure_while_storing_never_undoes_the_setup(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*args: object, **kwargs: object) -> None:
        raise RuntimeError("databasen falt ut")

    monkeypatch.setattr(onboarding, "store_guide", broken)
    kari = sign_up(client, "Kari")
    home_id = create_home(client, kari, "landlord")
    assert set_up(client, kari, home_id, ALL).status_code == 201
    assert stored(engine, home_id) is None
    assert client.get(guide_url(home_id), headers=kari).json()["source"] == "fallback"
