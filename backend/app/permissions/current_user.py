"""The signed-in user from `Authorization: Bearer <access token>` (Story 1.2, AD-7)."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.db import get_session
from app.domain import tokens
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)

NOT_SIGNED_IN = "Du må logge inn på nytt."


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=NOT_SIGNED_IN,
        headers={"WWW-Authenticate": "Bearer"},
    )


def current_user(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise _unauthorized()
    try:
        user_id = tokens.decode(
            credentials.credentials, "access", request.app.state.settings.jwt_secret
        )
    except tokens.InvalidToken:
        raise _unauthorized() from None
    user = session.get(User, user_id)
    if user is None:
        raise _unauthorized()
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def optional_user(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User | None:
    """Story 1.4: the signed-in user, or None without a Bearer token.

    A Bearer token that is present but invalid or expired still gives 401, so the frontend
    refreshes and retries instead of being shown the signed-out view by mistake.
    """
    if credentials is None:
        return None
    return current_user(request, session, credentials)


OptionalUser = Annotated[User | None, Depends(optional_user)]
