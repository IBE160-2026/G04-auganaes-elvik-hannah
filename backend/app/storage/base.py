"""The interface every photo store implements (Story 4.2, AD-5)."""

from typing import Protocol


class PhotoStore(Protocol):
    def put(self, key: str, data: bytes) -> None:
        """Stores `data` under `key`, replacing whatever was there."""

    def read(self, key: str) -> bytes | None:
        """The bytes under `key`, or None when nothing is stored there."""
