"""Where Photo Evidence is kept, behind one interface (Story 4.2, FR-19, FR-22, AD-5, AD-15).

`get_photo_store` picks the private Vercel Blob store only when `BLOB_READ_WRITE_TOKEN` is set.
Otherwise a folder on disk holds the photos under the same keys, so Photo Evidence runs and is
tested offline with no account. A store keeps one object per key and overwrites it: there is no
history (FR-19).
"""

from app.config import blob_is_configured, get_photo_storage_dir
from app.storage.base import PhotoStore, StorageError
from app.storage.blob import BlobPhotoStore
from app.storage.local import LocalPhotoStore

__all__ = ["BlobPhotoStore", "LocalPhotoStore", "PhotoStore", "StorageError", "get_photo_store"]


def get_photo_store() -> PhotoStore:
    if blob_is_configured():
        return BlobPhotoStore()
    return LocalPhotoStore(get_photo_storage_dir())
