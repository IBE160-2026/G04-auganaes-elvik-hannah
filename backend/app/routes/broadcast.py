"""The Landlord's broadcast to a Home's Tenants (Story 3.4, FR-12, AD-14).

Home-scoped, so it goes through require_role (the Landlord alias) before anything else. The push
is sent in this request, not by the cron (AD-14). The response names nobody: only counts.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints

from app.domain import broadcast
from app.push import Sender, get_sender
from app.routes.deps import ErrorOut, Landlord, SessionDep

router = APIRouter(prefix="/homes", tags=["broadcast"])

NO_TENANTS = "Det er ingen leietakere i hjemmet ennå."

MessageText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=broadcast.MESSAGE_MAX_LENGTH),
]


class BroadcastIn(BaseModel):
    message: MessageText


class BroadcastOut(BaseModel):
    # Current Tenants with at least one device that took the push.
    recipients: int
    # Current Tenants with no device that took it (no device, or every send failed).
    without_push: int


@router.post(
    "/{home_id}/broadcast",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not the Landlord of this Home, or no such Home",
        },
        status.HTTP_409_CONFLICT: {"model": ErrorOut, "description": "The Home has no Tenants"},
    },
)
def send_broadcast(
    home_id: uuid.UUID,
    body: BroadcastIn,
    _landlord: Landlord,
    session: SessionDep,
    sender: Annotated[Sender, Depends(get_sender)],
) -> BroadcastOut:
    try:
        result = broadcast.send_broadcast(session, sender, home_id, body.message)
    except broadcast.NoTenants:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=NO_TENANTS) from None
    return BroadcastOut(**result._asdict())
