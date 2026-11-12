"""The AI providers behind one interface (Story 5.1, AD-4, AD-15).

A provider gets an AiRequest and nothing else: the task's name, its catalog type and the
question. User names, e-mail addresses and Home names have no way in (FR-14). The Gemini provider
is used only when GEMINI_API_KEY is set; the mock answers otherwise, and always in tests.
"""

import json
from typing import Literal, NamedTuple, Protocol

import httpx

from app.ai import mock_answers
from app.config import get_gemini_api_key, get_gemini_model

# The service's deadline per AI call, and the Gemini client's own timeout, so a hung request ends.
AI_TIMEOUT_SECONDS = 10
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# `gemini-4-hydrogen` took up to 50 seconds on Vercel (Story 5.1 smoke test), far past
# AI_TIMEOUT_SECONDS; `gemini-3.1-flash-lite` with thinking LOW answered in 1-2 seconds. The
# field belongs to the Gemini 3 and 4 models; an older model (GEMINI_MODEL) would refuse it and
# every answer would be «error».
GEMINI_THINKING_LEVEL = "LOW"

SYSTEM_INSTRUCTION = (
    "Du er en hjelper i en app for husarbeid. Svar bare på norsk bokmål og aldri på andre "
    "språk, heller ikke delvis. Svar kort og konkret, gjerne i noen få steg. Du svarer bare på "
    "spørsmål om oppgaven du får oppgitt og om husarbeid, rengjøring, vedlikehold og utstyr og "
    "rengjøringsmidler i hjemmet; spørsmål om hvilket middel som passer på et underlag er "
    "alltid innenfor. Gjelder spørsmålet noe annet, svarer du ikke på det, men sier kort at du "
    "bare kan hjelpe med husarbeid og oppgaven, og lar confidence være «ok». Hvis du nevner "
    "rengjøringsmidler eller kjemikalier, si at man må lese og følge instruksjonene på "
    "produktet og aldri blande midler. Hvis du er usikker, sett confidence til «low»."
)

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "confidence": {"type": "STRING", "enum": ["ok", "low"]},
        "answer": {"type": "STRING"},
    },
    "required": ["confidence", "answer"],
}


class AiRequest(NamedTuple):
    """Everything a provider may see (FR-14)."""

    task_name: str
    # The catalog key, or None for a custom Task.
    task_type: str | None
    question: str


class ProviderAnswer(NamedTuple):
    confidence: Literal["ok", "low"]
    answer: str


class AiProvider(Protocol):
    # True when the answer is canned, so the UI can say so.
    demo: bool

    def ask(self, request: AiRequest) -> ProviderAnswer: ...


class MockProvider:
    demo = True

    def ask(self, request: AiRequest) -> ProviderAnswer:
        return ProviderAnswer("ok", mock_answers.answer_for(request.task_type))


class GeminiProvider:
    demo = False

    def __init__(
        self, api_key: str, model: str, transport: httpx.BaseTransport | None = None
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._transport = transport

    def build_body(self, request: AiRequest) -> dict:
        # The question only ever goes in the user content, never in the system instruction.
        user_text = (
            f"Oppgave: {request.task_name}\n"
            f"Oppgavetype: {request.task_type or 'egendefinert'}\n"
            f"Spørsmål: {request.question}"
        )
        return {
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "contents": [{"role": "user", "parts": [{"text": user_text}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": RESPONSE_SCHEMA,
                "temperature": 0.3,
                "thinkingConfig": {"thinkingLevel": GEMINI_THINKING_LEVEL},
            },
        }

    def ask(self, request: AiRequest) -> ProviderAnswer:
        # The key goes in a header, never in the URL, and no error here carries the request.
        with httpx.Client(transport=self._transport, timeout=AI_TIMEOUT_SECONDS) as client:
            response = client.post(
                GEMINI_URL.format(model=self._model),
                json=self.build_body(request),
                headers={"x-goog-api-key": self._api_key},
            )
        response.raise_for_status()
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)
        confidence, answer = data["confidence"], data["answer"]
        if confidence not in ("ok", "low") or not isinstance(answer, str) or not answer.strip():
            raise ValueError("unexpected answer shape")
        return ProviderAnswer(confidence, answer.strip())


def select_provider() -> AiProvider:
    """Gemini when GEMINI_API_KEY is set, otherwise the mock (AD-15)."""
    key = get_gemini_api_key()
    if key is None:
        return MockProvider()
    return GeminiProvider(key, get_gemini_model())
