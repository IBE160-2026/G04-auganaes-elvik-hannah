"""The caller's Homes: list and create (Story 1.3, FR-1, FR-3), and one Home's Members (Story 1.5).

GET and POST /homes are user-scoped: there is no home_id in their paths, and the list is
filtered on the caller's own Memberships. GET /homes/{home_id}/members is Home-scoped and goes
through require_role, like every route with {home_id} (AD-2, tests/test_permissions.py).

Story 1.8 (FR-23, AD-16): DELETE /homes/{home_id}/members/me (leave) and
DELETE /homes/{home_id}/members/{user_id} (a Landlord removes a Tenant), both through require_role
and domain/homes. Every refusal is the same 403 as require_role's.

Story 2.1: HomeOut says whether the caller may set up Tasks and whether the Home has any.
Story 2.3: and whether the caller may adjust a Task's Må/Bør and Frequency.

Story 1.9: one rule for creating and joining. A refused Household create answers 409 with the
same message as joining (routes/messages).
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, StringConstraints
from sqlmodel import Session

from app.clock import UtcDatetime
from app.domain import homes, tasks
from app.models.home import HOME_NAME_MAX_LENGTH, HomeType
from app.models.membership import Role
from app.permissions.current_user import CurrentUser
from app.permissions.require_role import FORBIDDEN
from app.routes.deps import AnyMember, ErrorOut, Landlord, Leaver, SessionDep
from app.routes.messages import in_other_home_message

router = APIRouter(prefix="/homes", tags=["homes"])

HomeName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=HOME_NAME_MAX_LENGTH)
]


class CreateHomeRequest(BaseModel):
    name: HomeName
    type: HomeType


class HomeOut(BaseModel):
    id: uuid.UUID
    name: str
    type: HomeType
    # The caller's Role in this Home.
    role: Role
    created_at: UtcDatetime
    # Story 1.4: whether the caller may create invite links here. Decided by the domain, so
    # the frontend never re-implements the rule.
    can_invite: bool
    # Story 1.8: whether the caller may leave this Home (not a Landlord in their own Home).
    can_leave: bool
    # Story 2.1: whether the caller may set up this Home's Tasks, and whether it has any.
    can_set_up_tasks: bool
    has_tasks: bool
    # Story 2.3: whether the caller may change a Task's Må/Bør and Frequency (a Tenant may not).
    # Story 2.6: the same flag covers adding and removing Tasks.
    can_adjust_tasks: bool


class HomesOut(BaseModel):
    # The Home the caller most recently created or joined first.
    homes: list[HomeOut]
    # The Home types the caller may create (Story 1.9): Landlord Home always, Household Home
    # only when lived_in_home_id is null.
    allowed_types: list[HomeType]
    # The Home where the caller is Household Member or Tenant, if any (the one-Home limit).
    lived_in_home_id: uuid.UUID | None


def home_out(member_home: homes.MemberHome, *, has_tasks: bool) -> HomeOut:
    home = member_home.home
    return HomeOut(
        id=home.id,
        name=home.name,
        type=home.type,
        role=member_home.role,
        created_at=home.created_at,
        can_invite=homes.can_invite(member_home.role),
        can_leave=homes.can_leave(member_home.role),
        can_set_up_tasks=tasks.can_set_up_tasks(member_home.role),
        has_tasks=has_tasks,
        can_adjust_tasks=tasks.can_adjust_tasks(member_home.role),
    )


def home_out_for(session: Session, member_home: homes.MemberHome) -> HomeOut:
    """home_out for one Home, looking up whether it has Tasks."""
    return home_out(member_home, has_tasks=tasks.has_tasks(session, member_home.home.id))


@router.get("")
def list_homes(user: CurrentUser, session: SessionDep) -> HomesOut:
    member_homes = homes.homes_for(session, user)
    with_tasks = tasks.home_ids_with_tasks(session, (h.home.id for h in member_homes))
    lived_in = homes.lived_in_home(session, user)
    return HomesOut(
        homes=[home_out(h, has_tasks=h.home.id in with_tasks) for h in member_homes],
        allowed_types=homes.allowed_types(session, user),
        lived_in_home_id=lived_in.id if lived_in is not None else None,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorOut,
            "description": "Household Home refused: the caller already lives in another Home",
        }
    },
)
def create_home(body: CreateHomeRequest, user: CurrentUser, session: SessionDep) -> HomeOut:
    try:
        created = homes.create_home(session, user, name=body.name, type=body.type)
    except homes.HomeCreationNotAllowed as exc:
        detail = in_other_home_message(exc.home.name)
        raise HTTPException(status.HTTP_409_CONFLICT, detail=detail) from None
    # A new Home has no Tasks yet; Task Setup follows (Story 2.1).
    return home_out(created, has_tasks=False)


class MemberOut(BaseModel):
    user_id: uuid.UUID
    name: str
    role: Role
    # True on the caller's own row. No email is sent (decision 1), so a Tenant cannot collect
    # the other Tenants' addresses.
    is_you: bool
    # Story 1.8: whether the caller may remove this Member (a Landlord, on a Tenant's row).
    # Never true on the caller's own row.
    can_remove: bool


class MembersOut(BaseModel):
    # The Landlord first, then in the order they joined.
    members: list[MemberOut]


@router.get(
    "/{home_id}/members",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not a Member of this Home, or no such Home",
        }
    },
)
def list_members(member: AnyMember, session: SessionDep) -> MembersOut:
    # home_id is read by require_role, which also puts it in the OpenAPI path.
    return MembersOut(
        members=[
            MemberOut(
                user_id=m.user_id,
                name=m.name,
                role=m.role,
                is_you=m.user_id == member.user_id,
                can_remove=m.user_id != member.user_id and homes.can_remove(member.role, m.role),
            )
            for m in homes.members_of(session, member.home_id)
        ]
    )


# Registered before /members/{user_id}, so "me" is never read as a user id.
@router.delete(
    "/{home_id}/members/me",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "A Landlord in their own Home, not a Member, or no such Home",
        }
    },
)
def leave_home(member: Leaver, session: SessionDep) -> None:
    homes.leave(session, member)


@router.delete(
    "/{home_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not the Landlord here, no such Home, or the user is not a Tenant here",
        }
    },
)
def remove_member(user_id: uuid.UUID, landlord: Landlord, session: SessionDep) -> None:
    try:
        homes.remove_tenant(session, landlord, user_id)
    except homes.NotATenant:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=FORBIDDEN) from None
