"""Shared route dependencies and schemas (Epic 1 retro, deferred to Epic 2; Story 2.1).

Route modules import the session, the error body and the Role aliases from here instead of from
each other. Each Role alias is require_role with the domain's set of Roles, so who may do what
is stated once in app/domain and every Home-scoped route reads it through require_role (AD-2).
"""

from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.domain import homes, tasks
from app.models.membership import ROLES, Membership
from app.permissions.require_role import require_role

SessionDep = Annotated[Session, Depends(get_session)]


class ErrorOut(BaseModel):
    detail: str


# Story 1.5: any Member of the Home, whatever their Role.
AnyMember = Annotated[Membership, Depends(require_role(*ROLES))]
# Story 1.4: a Household Member or the Landlord.
Inviter = Annotated[Membership, Depends(require_role(*sorted(homes.INVITER_ROLES)))]
# Story 1.8 (decisions 1 and 2): who may leave, and who may remove.
Leaver = Annotated[Membership, Depends(require_role(*sorted(homes.LEAVER_ROLES)))]
Landlord = Annotated[Membership, Depends(require_role("landlord"))]
# Story 2.1: who may set up a Home's Tasks.
TaskSetter = Annotated[Membership, Depends(require_role(*sorted(tasks.SETUP_ROLES)))]
