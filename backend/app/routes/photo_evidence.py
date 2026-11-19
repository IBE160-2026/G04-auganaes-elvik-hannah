"""The Landlord's Photo Evidence requirement on a Task (Story 4.1, FR-18, AD-6).

Home-scoped, so it goes through require_role (the Landlord alias) before anything else. It saves
one boolean on one Task; eligibility is checked in the domain, never read from the request.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.clock import utc_today
from app.domain import photo_evidence, tasks
from app.routes.deps import TASK_NOT_FOUND, ErrorOut, Landlord, SessionDep, Tenant
from app.routes.tasks import TaskOut, task_out
from app.storage import PhotoStore, get_photo_store

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


# The body is the JPEG itself, not a form: no multipart overhead against Vercel's 4.5 MB limit.
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
    },
)
async def upload_photo_evidence(
    task_id: uuid.UUID,
    instance_id: uuid.UUID,
    request: Request,
    tenant: Tenant,
    session: SessionDep,
    store: Annotated[PhotoStore, Depends(get_photo_store)],
) -> TaskOut:
    """Completes the instance with the photo as the body (AD-3); answers after the work is done."""
    # Refused before the body is read when the client says it is too big.
    declared = request.headers.get("content-length")
    if (
        declared is not None
        and declared.isdigit()
        and int(declared) > photo_evidence.MAX_PHOTO_BYTES
    ):
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, detail=photo_evidence.TOO_LARGE)
    data = await request.body()
    try:
        row = photo_evidence.complete_with_photo(session, store, tenant, task_id, instance_id, data)
    except photo_evidence.InvalidPhoto as exc:
        code = (
            status.HTTP_413_CONTENT_TOO_LARGE
            if exc.too_large
            else status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )
        raise HTTPException(code, detail=exc.message) from None
    except photo_evidence.PhotoNotRequired as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=exc.message) from None
    except tasks.TaskNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND) from None
    return task_out(row, utc_today(), tenant.user_id)
