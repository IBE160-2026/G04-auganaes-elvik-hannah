"""Registration, login, silent refresh and logout (Story 1.2, FR-1, AD-7).

The access token goes in the response body and is kept in memory by the frontend. The refresh
token goes in an httpOnly cookie that only /api/auth/refresh receives.
"""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, StringConstraints
from sqlmodel import Session

from app.config import Settings
from app.db import get_session
from app.domain import accounts, homes, invites, tokens
from app.models.user import EMAIL_MAX_LENGTH, NAME_MAX_LENGTH, User
from app.permissions.current_user import CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "husly_refresh"
REFRESH_COOKIE_PATH = "/api/auth/refresh"
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

EMAIL_TAKEN = "Det finnes allerede en konto med denne e-posten."
WRONG_CREDENTIALS = "Feil e-post eller passord."
SESSION_EXPIRED = "Økten er utløpt. Logg inn på nytt."

SessionDep = Annotated[Session, Depends(get_session)]
Password = Annotated[str, Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)]
DisplayName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_MAX_LENGTH)
]


class RegisterRequest(BaseModel):
    email: EmailStr
    name: DisplayName
    password: Password
    # Story 1.4: register through an invite link and join its Home in the same request.
    invite_token: (
        Annotated[str, Field(min_length=1, max_length=invites.TOKEN_MAX_LENGTH)] | None
    ) = None


class LoginRequest(BaseModel):
    email: Annotated[str, Field(max_length=EMAIL_MAX_LENGTH)]
    password: Annotated[str, Field(max_length=PASSWORD_MAX_LENGTH)]


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut


class RegisterResponse(AuthResponse):
    # Story 1.4: the Home joined through invite_token; null without one or when the link was
    # no longer valid (the account is created either way).
    joined_home_id: uuid.UUID | None = None


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _cookie_attributes(settings: Settings) -> dict[str, object]:
    """Shared by set and clear, so the browser always matches and removes the same cookie."""
    return {
        "path": REFRESH_COOKIE_PATH,
        "httponly": True,
        "samesite": "lax",
        "secure": settings.cookie_secure,
    }


def set_refresh_cookie(response: Response, settings: Settings, user_id: uuid.UUID) -> None:
    refresh = tokens.issue(user_id, "refresh", settings.jwt_secret)
    response.set_cookie(
        REFRESH_COOKIE,
        refresh.token,
        max_age=refresh.expires_in,
        **_cookie_attributes(settings),
    )


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(REFRESH_COOKIE, **_cookie_attributes(settings))


def _signed_in(response: Response, settings: Settings, user: User) -> AuthResponse:
    """Issue a fresh access token in the body and a fresh refresh cookie."""
    set_refresh_cookie(response, settings, user.id)
    access = tokens.issue(user.id, "access", settings.jwt_secret)
    return AuthResponse(
        access_token=access.token, user=UserOut.model_validate(user, from_attributes=True)
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest, request: Request, response: Response, session: SessionDep
) -> RegisterResponse:
    try:
        user = accounts.register(session, email=body.email, name=body.name, password=body.password)
    except accounts.EmailTaken:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=EMAIL_TAKEN) from None
    joined_home_id = None
    if body.invite_token is not None:
        try:
            joined_home_id = invites.accept(session, body.invite_token, user).home.id
        except (invites.InviteInvalid, homes.AlreadyMember, homes.InOtherHome):
            # The account stays; the invite page then shows why the link did not work.
            pass
    signed_in = _signed_in(response, _settings(request), user)
    return RegisterResponse(**signed_in.model_dump(), joined_home_id=joined_home_id)


@router.post("/login")
def login(
    body: LoginRequest, request: Request, response: Response, session: SessionDep
) -> AuthResponse:
    user = accounts.authenticate(session, email=body.email, password=body.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=WRONG_CREDENTIALS)
    return _signed_in(response, _settings(request), user)


@router.post(
    "/refresh",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid refresh cookie"}},
)
def refresh(
    request: Request,
    response: Response,
    session: SessionDep,
    husly_refresh: Annotated[str | None, Cookie()] = None,
) -> AuthResponse:
    settings = _settings(request)
    user = None
    if husly_refresh is not None:
        try:
            user_id = tokens.decode(husly_refresh, "refresh", settings.jwt_secret)
            user = session.get(User, user_id)
        except tokens.InvalidToken:
            pass
    if user is None:
        # Returned, not raised: a raised HTTPException would drop the cleared cookie.
        failed = JSONResponse({"detail": SESSION_EXPIRED}, status_code=status.HTTP_401_UNAUTHORIZED)
        clear_refresh_cookie(failed, settings)
        return failed
    return _signed_in(response, settings, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> Response:
    """Clears the refresh cookie. Idempotent: works with or without one."""
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_refresh_cookie(response, _settings(request))
    return response


@router.get("/me")
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user, from_attributes=True)
