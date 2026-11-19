"""Story 4.2 (FR-19, FR-22, AD-5, AD-15): the photo stores."""

from pathlib import Path

import pytest

from app.storage import BlobPhotoStore, LocalPhotoStore, get_photo_store

KEY = "tasks/00000000-0000-4000-8000-000000000001/evidence.jpg"


def test_the_local_store_keeps_one_object_per_key_and_overwrites(tmp_path: Path) -> None:
    store = LocalPhotoStore(tmp_path)

    store.put(KEY, b"first")
    store.put(KEY, b"second")

    # Guards the overwrite: a key never holds two photos (no history, FR-19).
    assert store.read(KEY) == b"second"
    assert [p.name for p in (tmp_path / "tasks").rglob("*") if p.is_file()] == ["evidence.jpg"]


def test_a_missing_key_reads_as_none(tmp_path: Path) -> None:
    assert LocalPhotoStore(tmp_path).read(KEY) is None


@pytest.mark.parametrize("key", ["../outside.jpg", "tasks/../../outside.jpg", "/etc/passwd"])
def test_a_key_outside_the_folder_is_refused(tmp_path: Path, key: str) -> None:
    store = LocalPhotoStore(tmp_path / "photos")

    # Guards `path.is_relative_to(self._root)`: the key is the server's, but never trusted blindly.
    with pytest.raises(ValueError):
        store.put(key, b"x")


def test_no_token_means_the_local_folder(
    monkeypatch: pytest.MonkeyPatch, local_photo_store: Path
) -> None:
    store = get_photo_store()

    # Guards `blob_is_configured()`: no token, no external account (FR-22, AD-15).
    assert isinstance(store, LocalPhotoStore)
    store.put(KEY, b"x")
    assert (local_photo_store / KEY).read_bytes() == b"x"


def test_a_token_picks_the_blob_store(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "vercel_blob_rw_test")

    assert isinstance(get_photo_store(), BlobPhotoStore)


def test_the_blob_store_writes_private_with_overwrite_and_reads_none_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from vercel.blob import BlobNotFoundError

    import app.storage.blob as blob_module

    calls: list[tuple[str, bytes, dict[str, object]]] = []

    def fake_put(key: str, data: bytes, **kwargs: object) -> None:
        calls.append((key, data, kwargs))

    def fake_get(key: str, **kwargs: object) -> object:
        raise BlobNotFoundError("ingen")

    monkeypatch.setattr(blob_module, "put_blob", fake_put)
    monkeypatch.setattr(blob_module, "get_blob", fake_get)
    store = BlobPhotoStore()

    store.put(KEY, b"jpeg")

    # Guards access="private" and allow_overwrite=True (AD-5): never a public URL, never a suffix.
    assert calls == [
        (
            KEY,
            b"jpeg",
            {"access": "private", "content_type": "image/jpeg", "allow_overwrite": True},
        )
    ]
    assert store.read(KEY) is None


def test_a_failed_write_is_a_storage_error_and_leaves_no_temp_file(tmp_path: Path) -> None:
    from app.storage import StorageError

    blocker = tmp_path / "tasks"
    blocker.write_text("a file where the folder should be")
    store = LocalPhotoStore(tmp_path)

    # Guards the OSError mapping: the route turns it into a 503, not an unhandled 500.
    with pytest.raises(StorageError):
        store.put(KEY, b"x")
    assert [p.name for p in tmp_path.rglob("*.tmp")] == []


def test_two_writes_to_one_key_do_not_share_a_temporary_file(tmp_path: Path) -> None:
    store = LocalPhotoStore(tmp_path)
    store.put(KEY, b"one")
    store.put(KEY, b"two")

    # Guards the unique temporary name: nothing is left over and the last write wins.
    assert store.read(KEY) == b"two"
    assert list((tmp_path / "tasks").rglob("*.tmp")) == []
