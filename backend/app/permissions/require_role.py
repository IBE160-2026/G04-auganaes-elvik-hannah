"""Home-scoped permission check (Story 1.4, AD-2; reused by Story 1.5 and Epics 2–6).

`require_role(*roles)` builds a dependency for a route with a `home_id` path parameter. It
loads the caller's Membership in that Home from the database (never from the JWT, body or
query) and returns it. A wrong Role, no Membership and an unknown Home all give the same 403,
so the answer does not reveal whether a Home exists.
"""

import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models.membership import Membership, Role
from app.permissions.current_user import CurrentUser

FORBIDDEN = "Du har ikke tilgang til dette i dette hjemmet."


def require_role(*roles: Role) -> Callable[..., Membership]:
    allowed = frozenset(roles)

    def dependency(
        home_id: uuid.UUID,
        user: CurrentUser,
        session: Annotated[Session, Depends(get_session)],
    ) -> Membership:
        membership = session.exec(
            select(Membership).where(Membership.user_id == user.id, Membership.home_id == home_id)
        ).first()
        if membership is None or membership.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=FORBIDDEN)
        return membership

    return dependency
