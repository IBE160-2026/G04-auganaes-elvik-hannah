"""Invite links: create, preview and accept (Story 1.4, FR-2, UJ-1, UJ-2).

Creating is Home-scoped and goes through require_role: only a Household Member or the Landlord
of that Home (homes.INVITER_ROLES). The preview is public, so the invite page can show the Home
before sign-in; with a Bearer token it also says whether the viewer can join.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, status
from pydantic import BaseModel

from app.clock import UtcDatetime
from app.domain import homes, invites
from app.models.home import HomeType
from app.models.membership import Role
from app.permissions.current_user import CurrentUser, OptionalUser
from app.routes.deps import ErrorOut, Inviter, SessionDep
from app.routes.homes import HomeOut, home_out_for

router = APIRouter(tags=["invites"])

_INVALID = "Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra"
_ASK_WHOM: dict[HomeType | None, str] = {
    "landlord": "utleieren",
    "household": "et husstandsmedlem",
    None: "den som inviterte deg",
}

Token = Annotated[str, Path(min_length=1, max_length=invites.TOKEN_MAX_LENGTH)]


def invalid_message(home_type: HomeType | None) -> str:
    return f"{_INVALID} {_ASK_WHOM[home_type]}."


def already_member_message(home_name: str) -> str:
    return f"Du er allerede med i «{home_name}»."


def in_other_home_message(home_name: str) -> str:
    return f"Du er allerede med i «{home_name}». Du kan bare være med i ett hjem om gangen."


class InviteOut(BaseModel):
    # Shown once: only its hash is stored.
    token: str
    # The Role whoever joins gets, from the Home type.
    role: Role
    expires_at: UtcDatetime


class InvitePreviewOut(BaseModel):
    status: Literal["valid", "invalid"]
    # Null only for an unknown token.
    home_type: HomeType | None
    home_name: str | None = None
    role: Role | None = None
    # Only with a valid Bearer token.
    viewer: Literal["can_join", "already_member", "in_other_home"] | None = None
    other_home_name: str | None = None


@router.post(
    "/homes/{home_id}/invites",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not a Household Member or the Landlord of this Home",
        }
    },
)
def create_invite(inviter: Inviter, session: SessionDep) -> InviteOut:
    # home_id is read by require_role, which also puts it in the OpenAPI path.
    created = invites.create_invite(session, inviter)
    return InviteOut(
        token=created.token,
        role=created.link.role,
        expires_at=created.link.expires_at,
    )


@router.get(
    "/invites/{token}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "A Bearer token was sent but is invalid"}
    },
)
def preview_invite(token: Token, viewer: OptionalUser, session: SessionDep) -> InvitePreviewOut:
    result = invites.preview(session, token, viewer)
    return InvitePreviewOut(
        status=result.status,
        home_type=result.home_type,
        home_name=result.home.name if result.home else None,
        role=result.role,
        viewer=result.viewer,
        other_home_name=result.other_home.name if result.other_home else None,
    )


@router.post(
    "/invites/{token}/accept",
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorOut,
            "description": "Already a Member here, or Member or Tenant in another Home",
        },
        status.HTTP_410_GONE: {
            "model": ErrorOut,
            "description": "Unknown, expired, or used by someone else",
        },
    },
)
def accept_invite(token: Token, user: CurrentUser, session: SessionDep) -> HomeOut:
    try:
        joined = invites.accept(session, token, user)
    except invites.InviteInvalid as exc:
        raise HTTPException(status.HTTP_410_GONE, detail=invalid_message(exc.home_type)) from None
    except homes.AlreadyMember as exc:
        detail = already_member_message(exc.home.name)
        raise HTTPException(status.HTTP_409_CONFLICT, detail=detail) from None
    except homes.InOtherHome as exc:
        detail = in_other_home_message(exc.home.name)
        raise HTTPException(status.HTTP_409_CONFLICT, detail=detail) from None
    return home_out_for(session, joined)
