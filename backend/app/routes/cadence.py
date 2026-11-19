"""The Landlord's notification cadence for a Home (Story 3.5, FR-13).

Home-scoped, so it goes through require_role (the Landlord alias) before anything else. It saves
one number; the daily due-check reads it (domain/cadence). It never touches a task's Frequency.
"""

import uuid
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.domain import cadence
from app.routes.deps import ErrorOut, Landlord, SessionDep

router = APIRouter(prefix="/homes", tags=["cadence"])


class CadenceIn(BaseModel):
    # The options of models/home.CADENCE_OPTIONS; anything else is a 422.
    days: Literal[1, 2, 7]


class CadenceOut(BaseModel):
    notification_cadence_days: int


@router.put(
    "/{home_id}/notification-cadence",
    responses={403: {"model": ErrorOut, "description": "Not the Landlord of this Home"}},
)
def set_cadence(
    home_id: uuid.UUID, body: CadenceIn, _landlord: Landlord, session: SessionDep
) -> CadenceOut:
    home = cadence.set_cadence(session, home_id, body.days)
    return CadenceOut(notification_cadence_days=home.notification_cadence_days)
