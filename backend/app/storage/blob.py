"""Photos in a private Vercel Blob store (Story 4.2, AD-5).

Private, with overwrite on, under the key the server computed. The SDK reads the token from
`BLOB_READ_WRITE_TOKEN`. No Blob URL ever leaves the backend: every view goes through a backend
route that runs `require_role` first (Story 4.3). The SDK's top-level `put_blob` and `get_blob` are
coroutines; called without `await` they do nothing and raise nothing, so the synchronous ones from
`vercel.blob.sync` are used (a test guards that). The real store is only reachable on Vercel.
"""

from vercel.blob import BlobError, BlobNotFoundError
from vercel.blob.sync import delete_blob, get_blob, put_blob

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

    def delete(self, key: str) -> None:
        try:
            delete_blob(key)
        except BlobNotFoundError:
            return
        except BlobError as error:
            raise StorageError("Kunne ikke slette bildet.") from error
