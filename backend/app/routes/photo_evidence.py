"""The Landlord's Photo Evidence requirement on a Task (Story 4.1, FR-18, AD-6).

Home-scoped, so it goes through require_role (the Landlord alias) before anything else. It saves
one boolean on one Task; eligibility is checked in the domain, never read from the request.
"""

import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.domain import photo_evidence, tasks
from app.routes.deps import TASK_NOT_FOUND, ErrorOut, Landlord, SessionDep

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
