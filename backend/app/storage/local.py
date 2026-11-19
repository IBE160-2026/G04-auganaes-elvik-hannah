"""Photos in a folder on disk: local running and the tests (Story 4.2, FR-22, AD-15)."""

import uuid
from pathlib import Path

from app.storage.base import StorageError


class LocalPhotoStore:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def _path(self, key: str) -> Path:
        path = (self._root / key).resolve()
        # The key is computed on the server, but a path outside the folder is refused anyway.
        if not path.is_relative_to(self._root):
            raise ValueError("Ugyldig lagringsnøkkel.")
        return path

    def put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        # Written next to the target under its own name and renamed, so a reader never sees half
        # a photo and two parallel writes never share a temporary file.
        temp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp.write_bytes(data)
            temp.replace(path)
        except OSError as error:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass  # Nothing to clean up when the folder itself could not be made.
            raise StorageError("Kunne ikke lagre bildet.") from error

    def read(self, key: str) -> bytes | None:
        path = self._path(key)
        return path.read_bytes() if path.is_file() else None
