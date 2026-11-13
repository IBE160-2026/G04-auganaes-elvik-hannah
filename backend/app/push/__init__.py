"""Web Push delivery behind one interface (Story 3.2, FR-10, AD-8, AD-15)."""

from app.push.hosts import is_allowed_endpoint
from app.push.senders import (
    MOCK_SENDER,
    MockSender,
    PushMessage,
    PushTarget,
    Sender,
    SendResult,
    get_sender,
)

__all__ = [
    "MOCK_SENDER",
    "MockSender",
    "PushMessage",
    "PushTarget",
    "SendResult",
    "Sender",
    "get_sender",
    "is_allowed_endpoint",
]
