"""Photos in a private Vercel Blob store (Story 4.2, AD-5).

Private, with overwrite on, under the key the server computed. The SDK reads the token from
`BLOB_READ_WRITE_TOKEN`. No Blob URL ever leaves the backend: every view goes through a backend
route that runs `require_role` first (Story 4.3). This adapter cannot be exercised offline, so it
is only run once a store exists.
"""

from vercel.blob import BlobError, BlobNotFoundError, get_blob, put_blob

from app.storage.base import StorageError

CONTENT_TYPE = "image/jpeg"


class BlobPhotoStore:
    def put(self, key: str, data: bytes) -> None:
        try:
            put_blob(key, data, access="private", content_type=CONTENT_TYPE, allow_overwrite=True)
        except BlobError as error:
            raise StorageError("Kunne ikke lagre bildet.") from error

    def read(self, key: str) -> bytes | None:
        try:
            return get_blob(key, access="private").body
        except BlobNotFoundError:
            return None
        except BlobError as error:
            raise StorageError("Kunne ikke hente bildet.") from error
