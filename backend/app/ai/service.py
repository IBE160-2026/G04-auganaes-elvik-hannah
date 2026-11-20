"""answer_question: the one function every AI surface calls (Story 5.1, FR-14, AD-4).

It counts the call against the user's daily limit, asks the provider within a deadline, and
turns every failure into status "error"; the route never sees a provider exception. The
disclaimer is its own field on every answer and never part of the text.
"""

import logging
import queue
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from sqlmodel import Session

from app.ai.providers import (
    AI_TIMEOUT_SECONDS,
    AiProvider,
    AiRequest,
    ChatTurn,
    GuideRequest,
    GuideTask,
    ProviderAnswer,
    select_provider,
)
from app.clock import utc_today
from app.domain import ai_usage, onboarding
from app.models.onboarding_guide import INTRO_MAX_LENGTH

logger = logging.getLogger(__name__)

AI_DAILY_LIMIT = ai_usage.AI_DAILY_LIMIT

DISCLAIMER = (
    "KI kan ta feil. Vær forsiktig, særlig med kjemikalier og rengjøringsmidler: les og følg "
    "alltid instruksjonene på produktet."
)
ERROR_TEXT = "Vi fikk ikke svar fra KI-tjenesten akkurat nå."
QUESTION_MAX_LENGTH = 300
# A chat's earlier turns (Story 5.2): at most 10 entries (five exchanges), the AI's answers longer
# than a question may be.
HISTORY_MAX_ENTRIES = 10
HISTORY_ANSWER_MAX_LENGTH = 2000


class DeadlineExceeded(Exception):
    """The provider did not answer within the deadline."""


def _within[T](call: Callable[[], T], timeout: float) -> T:
    """Runs `call` on its own daemon thread and waits at most `timeout` seconds.

    One thread per call, not a small pool: hung calls then never make later calls queue behind
    them and miss the deadline without reaching the provider. A thread that outlives the deadline
    ends when the provider's own timeout does. Never a `with ThreadPoolExecutor` block either,
    whose exit waits for the provider.
    """
    outcome: queue.Queue[T | Exception] = queue.Queue(maxsize=1)

    def run() -> None:
        try:
            outcome.put(call())
        except Exception as exc:
            outcome.put(exc)

    threading.Thread(target=run, daemon=True, name="ai-call").start()
    try:
        value = outcome.get(timeout=timeout)
    except queue.Empty:
        raise DeadlineExceeded from None
    if isinstance(value, Exception):
        raise value
    return value


def _ask_within(provider: AiProvider, request: AiRequest, timeout: float) -> ProviderAnswer:
    return _within(lambda: provider.ask(request), timeout)


def _ask_guide_within(provider: AiProvider, request: GuideRequest, timeout: float) -> str:
    return _within(lambda: provider.write_guide(request), timeout)


@dataclass(frozen=True)
class AiAnswer:
    status: Literal["ok", "low_confidence", "error"]
    answer: str
    disclaimer: str
    demo: bool


class LimitReached(Exception):
    """The user has used today's calls. resets_at is when the count restarts (UTC)."""

    def __init__(self, resets_at: datetime) -> None:
        super().__init__("daily AI limit reached")
        self.resets_at = resets_at


def default_question(task_name: str) -> str:
    return f"Hvordan gjør jeg «{task_name}»?"


def answer_question(
    session: Session,
    user_id: uuid.UUID,
    task_name: str,
    task_type: str | None,
    question: str | None = None,
    history: tuple[ChatTurn, ...] = (),
    *,
    provider: AiProvider | None = None,
    today: date | None = None,
) -> AiAnswer:
    """Counts the call, asks the provider, and returns the answer. Raises only LimitReached.

    `history` is a chat's earlier completed turns, already validated by the route (Story 5.2).
    """
    day = today if today is not None else utc_today()
    # Before counting, so a provider that cannot be built never spends one of the user's calls.
    chosen = provider if provider is not None else select_provider()
    if not ai_usage.try_count_call(session, user_id, day, AI_DAILY_LIMIT):
        raise LimitReached(ai_usage.next_reset(day))

    asked = (question or "").strip() or default_question(task_name)
    request = AiRequest(task_name, task_type, asked, history)
    try:
        result = _ask_within(chosen, request, AI_TIMEOUT_SECONDS)
    except DeadlineExceeded:
        logger.warning("KI-leverandøren svarte ikke innen %s sekunder.", AI_TIMEOUT_SECONDS)
        return AiAnswer("error", ERROR_TEXT, DISCLAIMER, chosen.demo)
    except Exception as exc:
        # The type name only: the exception text may carry the URL or headers.
        logger.warning("KI-leverandøren feilet: %s", type(exc).__name__)
        return AiAnswer("error", ERROR_TEXT, DISCLAIMER, chosen.demo)
    status = "ok" if result.confidence == "ok" else "low_confidence"
    return AiAnswer(status, result.answer, DISCLAIMER, chosen.demo)


@dataclass(frozen=True)
class GuideIntro:
    text: str
    # ai: Gemini wrote it. demo: the mock did. fallback: the fixed text (nothing could be asked).
    source: Literal["ai", "demo", "fallback"]


def generate_guide_intro(
    session: Session,
    user_id: uuid.UUID,
    must_tasks: list[onboarding.MustTask],
    *,
    provider: AiProvider | None = None,
    today: date | None = None,
) -> GuideIntro:
    """Writes the introduction to a Home's onboarding guide (Story 5.3, FR-16).

    One counted call against the user's daily limit, asked within the same deadline as every AI
    call. It never raises: the limit being reached, a failing or slow provider and a bad answer
    all give the fixed fallback text, so setting up a Home never fails because of the guide.
    Only the Must tasks' names, catalog types and frequencies go to the provider.
    """
    day = today if today is not None else utc_today()
    fallback = GuideIntro(onboarding.FALLBACK_INTRO, "fallback")
    try:
        # Before counting, so a provider that cannot be built spends no call.
        chosen = provider if provider is not None else select_provider()
    except Exception as exc:
        logger.warning("KI-leverandøren kunne ikke velges: %s", type(exc).__name__)
        return fallback
    if not ai_usage.try_count_call(session, user_id, day, AI_DAILY_LIMIT):
        return fallback
    request = GuideRequest(
        tuple(GuideTask(t.name, t.task_type, t.frequency_days) for t in must_tasks)
    )
    try:
        text = _ask_guide_within(chosen, request, AI_TIMEOUT_SECONDS)
    except Exception as exc:
        # The type name only: the exception text may carry the URL or headers.
        logger.warning("KI-leverandøren kunne ikke skrive guiden: %s", type(exc).__name__)
        return fallback
    # Bounded to what the table holds; a real answer is far shorter (120 words at most).
    return GuideIntro(text[:INTRO_MAX_LENGTH], "demo" if chosen.demo else "ai")
