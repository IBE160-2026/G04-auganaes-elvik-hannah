"""The caller's Homes: list and create (Story 1.3, FR-1, FR-3).

User-scoped, not Home-scoped: there is no home_id in these paths, and the list is filtered on
the caller's own Memberships, so require_role (Story 1.5) is not needed here.
"""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from sqlmodel import Session

from app.db import get_session
from app.domain import homes
from app.models.home import HOME_NAME_MAX_LENGTH, HomeType
from app.models.membership import Role
from app.permissions.current_user import CurrentUser

router = APIRouter(prefix="/homes", tags=["homes"])

LANDLORD_ONLY = (
    "Som utleier kan du bare opprette flere utleieboliger. Bor du selv i et kollektiv, "
    "blir du med der gjennom en invitasjon."
)
ALREADY_IN_HOME = (
    "Du er allerede med i et hjem. Vil du bli med i et annet, trenger du en invitasjon."
)

SessionDep = Annotated[Session, Depends(get_session)]
HomeName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=HOME_NAME_MAX_LENGTH)
]


class CreateHomeRequest(BaseModel):
    name: HomeName
    type: HomeType


class ErrorOut(BaseModel):
    detail: str


class HomeOut(BaseModel):
    id: uuid.UUID
    name: str
    type: HomeType
    # The caller's Role in this Home.
    role: Role
    created_at: datetime


class HomesOut(BaseModel):
    # Newest first.
    homes: list[HomeOut]
    # The Home types the caller may create; empty when they join by invite instead.
    allowed_types: list[HomeType]


def _out(member_home: homes.MemberHome) -> HomeOut:
    home = member_home.home
    return HomeOut(
        id=home.id,
        name=home.name,
        type=home.type,
        role=member_home.role,
        created_at=home.created_at,
    )


@router.get("")
def list_homes(user: CurrentUser, session: SessionDep) -> HomesOut:
    return HomesOut(
        homes=[_out(h) for h in homes.homes_for(session, user)],
        allowed_types=homes.allowed_types(session, user),
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorOut,
            "description": "The caller may not create a Home of this type",
        }
    },
)
def create_home(body: CreateHomeRequest, user: CurrentUser, session: SessionDep) -> HomeOut:
    try:
        created = homes.create_home(session, user, name=body.name, type=body.type)
    except homes.HomeCreationNotAllowed as exc:
        detail = LANDLORD_ONLY if exc.allowed else ALREADY_IN_HOME
        raise HTTPException(status.HTTP_409_CONFLICT, detail=detail) from None
    return _out(created)
