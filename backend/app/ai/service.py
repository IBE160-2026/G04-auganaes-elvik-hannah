"""answer_question: the one function every AI surface calls (Story 5.1, FR-14, AD-4).

It counts the call against the user's daily limit, asks the provider within a deadline, and
turns every failure into status "error"; the route never sees a provider exception. The
disclaimer is its own field on every answer and never part of the text.
"""

import logging
import queue
import threading
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from sqlmodel import Session

from app.ai.providers import (
    AI_TIMEOUT_SECONDS,
    AiProvider,
    AiRequest,
    ProviderAnswer,
    select_provider,
)
from app.clock import utc_now
from app.domain import ai_usage

logger = logging.getLogger(__name__)

AI_DAILY_LIMIT = ai_usage.AI_DAILY_LIMIT

DISCLAIMER = (
    "KI kan ta feil. Vær forsiktig, særlig med kjemikalier og rengjøringsmidler: les og følg "
    "alltid instruksjonene på produktet."
)
ERROR_TEXT = "Vi fikk ikke svar fra KI-tjenesten akkurat nå."
QUESTION_MAX_LENGTH = 300


class DeadlineExceeded(Exception):
    """The provider did not answer within the deadline."""


def _ask_within(provider: AiProvider, request: AiRequest, timeout: float) -> ProviderAnswer:
    """Runs provider.ask on its own daemon thread and waits at most `timeout` seconds.

    One thread per call, not a small pool: hung calls then never make later calls queue behind
    them and miss the deadline without reaching the provider. A thread that outlives the deadline
    ends when the provider's own timeout does. Never a `with ThreadPoolExecutor` block either,
    whose exit waits for the provider.
    """
    outcome: queue.Queue[ProviderAnswer | Exception] = queue.Queue(maxsize=1)

    def run() -> None:
        try:
            outcome.put(provider.ask(request))
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
    *,
    provider: AiProvider | None = None,
    today: date | None = None,
) -> AiAnswer:
    """Counts the call, asks the provider, and returns the answer. Raises only LimitReached."""
    day = today if today is not None else utc_now().date()
    # Before counting, so a provider that cannot be built never spends one of the user's calls.
    chosen = provider if provider is not None else select_provider()
    if not ai_usage.try_count_call(session, user_id, day, AI_DAILY_LIMIT):
        raise LimitReached(ai_usage.next_reset(day))

    asked = (question or "").strip() or default_question(task_name)
    request = AiRequest(task_name, task_type, asked)
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
