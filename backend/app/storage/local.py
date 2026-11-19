"""Photos in a folder on disk: local running and the tests (Story 4.2, FR-22, AD-15)."""

from pathlib import Path


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
        path.parent.mkdir(parents=True, exist_ok=True)
        # Written next to the target and renamed, so a reader never sees half a photo.
        temp = path.with_name(path.name + ".tmp")
        temp.write_bytes(data)
        temp.replace(path)

    def read(self, key: str) -> bytes | None:
        path = self._path(key)
        return path.read_bytes() if path.is_file() else None
