"""The push senders (Story 3.2, FR-10, FR-22, AD-15).

`get_sender` picks the real Web Push sender only when both VAPID keys are set. Otherwise the mock
records what it would have sent, so the due-check runs offline, and always in tests. A sender never
raises for a delivery problem: it answers `sent`, `gone` (the push service says this device no
longer exists, so its row can go) or `failed`.
"""

import json
import logging
from collections import deque
from typing import Literal, NamedTuple, Protocol

from pywebpush import WebPushException, webpush

from app.config import get_vapid_private_key, get_vapid_subject, push_is_mock

logger = logging.getLogger(__name__)

# The push service gets this long; a hung request must not hold the daily job.
PUSH_TIMEOUT_SECONDS = 10
# How many recorded pushes the mock keeps in memory.
MOCK_KEEP = 200

SendResult = Literal["sent", "gone", "failed"]


class PushTarget(NamedTuple):
    endpoint: str
    p256dh: str
    auth: str


class PushMessage(NamedTuple):
    title: str
    body: str
    # A path in this app; the service worker opens it on a tap.
    url: str
    # A newer push with the same tag replaces the older one in the tray.
    tag: str

    def payload(self) -> str:
        return json.dumps(self._asdict(), ensure_ascii=False)


class Sender(Protocol):
    def send(self, target: PushTarget, message: PushMessage) -> SendResult: ...


class MockSender:
    """Records what would have been sent instead of delivering it (FR-22)."""

    def __init__(self) -> None:
        self.sent: deque[tuple[PushTarget, PushMessage]] = deque(maxlen=MOCK_KEEP)

    def send(self, target: PushTarget, message: PushMessage) -> SendResult:
        logger.info("Mock-push (ikke sendt): %s", message.title)
        self.sent.append((target, message))
        return "sent"


class WebPushSender:
    def __init__(self, private_key: str, subject: str) -> None:
        self._private_key = private_key
        self._subject = subject

    def send(self, target: PushTarget, message: PushMessage) -> SendResult:
        try:
            webpush(
                subscription_info={
                    "endpoint": target.endpoint,
                    "keys": {"p256dh": target.p256dh, "auth": target.auth},
                },
                data=message.payload(),
                vapid_private_key=self._private_key,
                vapid_claims={"sub": self._subject},
                timeout=PUSH_TIMEOUT_SECONDS,
                ttl=24 * 3600,
            )
        except WebPushException as error:
            if error.status_code in (404, 410):
                return "gone"
            logger.warning("Push feilet (HTTP %s).", error.status_code)
            return "failed"
        except Exception as error:
            # A timeout or network error. The class names the cause; the endpoint is not logged.
            logger.warning("Push feilet (%s).", type(error).__name__)
            return "failed"
        return "sent"


MOCK_SENDER = MockSender()


def get_sender() -> Sender:
    private_key = get_vapid_private_key()
    if push_is_mock() or private_key is None:
        return MOCK_SENDER
    return WebPushSender(private_key, get_vapid_subject())
