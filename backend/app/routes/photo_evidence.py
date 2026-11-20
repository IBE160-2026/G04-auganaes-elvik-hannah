"""The Landlord's Photo Evidence requirement (Story 4.1, FR-18, AD-6), the Tenant's upload (4.2) and
the Landlord's view of the photo (4.3, FR-19, NFR5).

Home-scoped, so it goes through require_role (the Landlord alias) before anything else. It saves
one boolean on one Task; eligibility is checked in the domain, never read from the request.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from app.clock import UtcDatetime, utc_today
from app.domain import photo_evidence, tasks
from app.routes.deps import TASK_NOT_FOUND, ErrorOut, Landlord, SessionDep, Tenant
from app.routes.tasks import TaskOut, task_out
from app.storage import PhotoStore, StorageError, get_photo_store

router = APIRouter(tags=["photo-evidence"])


class RequirementIn(BaseModel):
    required: bool


class RequirementOut(BaseModel):
    requires_photo_evidence: bool


@router.put(
    "/homes/{home_id}/tasks/{task_id}/photo-evidence-requirement",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not the Landlord of this Home",
        },
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut, "description": "No such Task in this Home"},
        status.HTTP_409_CONFLICT: {
            "model": ErrorOut,
            "description": "The Task is not a Must Task of a type that may require a photo",
        },
    },
)
def set_requirement(
    task_id: uuid.UUID, body: RequirementIn, landlord: Landlord, session: SessionDep
) -> RequirementOut:
    try:
        stored = photo_evidence.set_requirement(session, landlord, task_id, body.required)
    except tasks.TaskNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND) from None
    except photo_evidence.CannotRequire as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=exc.message) from None
    return RequirementOut(requires_photo_evidence=stored)


async def read_photo_body(request: Request) -> bytes:
    """The request body, read in pieces and refused (413) once it passes the photo limit.

    Counted as it arrives, so a body without a Content-Length (chunked) or with a wrong one is
    never buffered whole before the size is known.
    """
    declared = request.headers.get("content-length")
    if (
        declared is not None
        and declared.isdigit()
        and int(declared) > photo_evidence.MAX_PHOTO_BYTES
    ):
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, detail=photo_evidence.TOO_LARGE)
    received = bytearray()
    async for chunk in request.stream():
        received.extend(chunk)
        if len(received) > photo_evidence.MAX_PHOTO_BYTES:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, detail=photo_evidence.TOO_LARGE)
    return bytes(received)


# The body is the JPEG itself, not a form: no multipart overhead against Vercel's 4.5 MB limit.
# A plain `def`, so the database and storage work runs in the threadpool, not on the event loop.
@router.post(
    "/homes/{home_id}/tasks/{task_id}/instances/{instance_id}/photo-evidence",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"image/jpeg": {"schema": {"type": "string", "format": "binary"}}},
        }
    },
    responses={
        status.HTTP_403_FORBIDDEN: {"model": ErrorOut, "description": "Not a Tenant of this Home"},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut, "description": "No such Task or instance"},
        status.HTTP_409_CONFLICT: {"model": ErrorOut, "description": "The Task needs no photo"},
        status.HTTP_413_CONTENT_TOO_LARGE: {"model": ErrorOut, "description": "Photo too large"},
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {"model": ErrorOut, "description": "Not a JPEG"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorOut, "description": "Photo not saved"},
    },
)
def upload_photo_evidence(
    task_id: uuid.UUID,
    instance_id: uuid.UUID,
    data: Annotated[bytes, Depends(read_photo_body)],
    tenant: Tenant,
    session: SessionDep,
    store: Annotated[PhotoStore, Depends(get_photo_store)],
) -> TaskOut:
    """Completes the instance with the photo as the body (AD-3); answers after the work is done."""
    try:
        row = photo_evidence.complete_with_photo(session, store, tenant, task_id, instance_id, data)
    except tasks.TaskNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND) from None
    except photo_evidence.PhotoNotRequired as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=exc.message) from None
    except photo_evidence.InvalidPhoto as exc:
        code = (
            status.HTTP_413_CONTENT_TOO_LARGE
            if exc.too_large
            else status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )
        raise HTTPException(code, detail=exc.message) from None
    except StorageError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail=photo_evidence.STORE_FAILED
        ) from None
    return task_out(row, utc_today(), tenant.user_id)


class EvidenceOut(BaseModel):
    # Written by the server at upload: «Bildebevis lastet opp av Martin, 29. sep».
    description: str
    uploaded_at: UtcDatetime


class EvidenceInfoOut(BaseModel):
    # null until a Tenant has uploaded a photo; «no photo yet» is not a 404 (that means no Task).
    evidence: EvidenceOut | None


@router.get(
    "/homes/{home_id}/tasks/{task_id}/photo-evidence",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not the Landlord of this Home",
        },
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut, "description": "No such Task in this Home"},
    },
)
def get_photo_evidence(
    task_id: uuid.UUID, landlord: Landlord, session: SessionDep
) -> EvidenceInfoOut:
    try:
        row = photo_evidence.current_evidence(session, landlord, task_id)
    except tasks.TaskNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND) from None
    if row is None:
        return EvidenceInfoOut(evidence=None)
    return EvidenceInfoOut(
        evidence=EvidenceOut(description=row.description, uploaded_at=row.uploaded_at)
    )


@router.get(
    "/homes/{home_id}/tasks/{task_id}/photo-evidence/image",
    response_class=Response,
    responses={
        status.HTTP_200_OK: {
            "content": {"image/jpeg": {"schema": {"type": "string", "format": "binary"}}},
            "description": "The Task's current photo",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not the Landlord of this Home",
        },
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut, "description": "No such Task, or no photo"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorOut, "description": "Photo not read"},
    },
)
def get_photo_evidence_image(
    task_id: uuid.UUID,
    landlord: Landlord,
    session: SessionDep,
    store: Annotated[PhotoStore, Depends(get_photo_store)],
) -> Response:
    """Streams the photo through the backend after `require_role`: never a Blob URL (AD-5, NFR5)."""
    try:
        data = photo_evidence.read_photo(session, store, landlord, task_id)
    except tasks.TaskNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND) from None
    except photo_evidence.NoEvidence as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message) from None
    except StorageError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail=photo_evidence.READ_FAILED
        ) from None
    # Per-user authorised content: never kept by a shared cache (Vercel's CDN, a proxy).
    return Response(
        content=data,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )
