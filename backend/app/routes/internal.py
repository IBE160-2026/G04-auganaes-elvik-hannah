"""Endpoints called by the platform, not by users (Story 3.2, AD-8).

`GET /api/internal/run-due-check` is the only trigger of the daily due-check. Vercel Cron calls it
with `Authorization: Bearer <CRON_SECRET>`. It is left out of the OpenAPI document: the frontend
never calls it, and it has no Home, so there is no Role to require.
"""

import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.clock import utc_today
from app.config import get_cron_secret, is_vercel, push_is_mock
from app.domain import due_check
from app.push import Sender, get_sender
from app.routes.deps import SessionDep

router = APIRouter(prefix="/internal", tags=["internal"], include_in_schema=False)

UNAUTHORIZED = "Mangler riktig hemmelighet."


def require_cron_secret(authorization: Annotated[str | None, Header()] = None) -> None:
    """Rejects any call without the right Bearer secret.

    Without CRON_SECRET every call is rejected on Vercel and whenever real VAPID keys are set,
    so only local mock mode (FR-22) can run the job by hand with no secret.
    """
    secret = get_cron_secret()
    if secret is None:
        if is_vercel() or not push_is_mock():
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, UNAUTHORIZED)
        return
    expected = f"Bearer {secret}".encode()
    given = (authorization or "").encode()
    if not hmac.compare_digest(given, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, UNAUTHORIZED)


class DueCheckOut(BaseModel):
    members: int
    tasks: int
    pushes: int


@router.get(
    "/run-due-check", response_model=DueCheckOut, dependencies=[Depends(require_cron_secret)]
)
def run_due_check(
    session: SessionDep, sender: Annotated[Sender, Depends(get_sender)]
) -> DueCheckOut:
    return DueCheckOut(**due_check.run_due_check(session, sender, utc_today())._asdict())
