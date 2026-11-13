"""Web Push registration (Story 3.1, FR-10, AD-12). Sending is Story 3.2.

User-scoped, not Home-scoped: a device belongs to a User whatever Homes they are in, so these
routes use CurrentUser and no require_role. Every call touches only the caller's own rows.
"""

from typing import Annotated

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from app.config import get_vapid_public_key, push_is_mock
from app.domain import push
from app.models.push_subscription import ENDPOINT_MAX_LENGTH, KEY_MAX_LENGTH
from app.permissions.current_user import CurrentUser
from app.routes.deps import SessionDep

router = APIRouter(prefix="/push", tags=["push"])

# Story 3.2 will POST to this address, so it must be an https URL in visible ASCII. Real push
# services always are; this also keeps a long non-ASCII value out of the unique index.
Endpoint = Annotated[
    str,
    Field(max_length=ENDPOINT_MAX_LENGTH, pattern=r"^https://[\x21-\x7e]+$"),
]
Key = Annotated[str, Field(min_length=1, max_length=KEY_MAX_LENGTH)]


class PushConfigOut(BaseModel):
    public_key: str
    # True without VAPID keys: the dev key is handed out and the mock sender records pushes.
    mock: bool


class SubscriptionIn(BaseModel):
    endpoint: Endpoint
    p256dh: Key
    auth: Key


class EndpointIn(BaseModel):
    endpoint: Endpoint


@router.get("/config", response_model=PushConfigOut)
def push_config(_user: CurrentUser) -> PushConfigOut:
    return PushConfigOut(public_key=get_vapid_public_key(), mock=push_is_mock())


@router.put("/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
def register_subscription(body: SubscriptionIn, user: CurrentUser, session: SessionDep) -> Response:
    push.register_subscription(session, user.id, body.endpoint, body.p256dh, body.auth)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
def remove_subscription(body: EndpointIn, user: CurrentUser, session: SessionDep) -> Response:
    push.remove_subscription(session, user.id, body.endpoint)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
