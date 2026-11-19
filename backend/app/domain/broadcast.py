"""The Landlord's ad-hoc broadcast to a Home's Tenants (Story 3.4, FR-12, AD-14, AD-16, FR-22).

Sent directly and synchronously when the Landlord asks, never through the daily due-check. Only
*current* Tenants are addressed (a Tenant who left has no Membership, AD-16). A Tenant counts as
reached when at least one of their devices accepted the push; the rest are `without_push`, so the
Landlord is not told "Sendt til 3" when only one phone could receive it. A send is not retried.
"""

import uuid
from typing import NamedTuple

from sqlmodel import Session, col, select

from app.domain import push
from app.models.membership import Membership, Role
from app.push import PushMessage, Sender

MESSAGE_MAX_LENGTH = 300
TITLE = "Melding fra utleier"
TAG_PREFIX = "husly-melding"


class BroadcastResult(NamedTuple):
    recipients: int
    without_push: int


class NoTenants(Exception):
    """The Home has no current Tenant, so there is nobody to send to."""


def can_broadcast(role: Role) -> bool:
    return role == "landlord"


def send_broadcast(
    session: Session, sender: Sender, home_id: uuid.UUID, text: str
) -> BroadcastResult:
    tenant_ids = session.exec(
        select(Membership.user_id)
        .where(Membership.home_id == home_id, Membership.role == "tenant")
        .order_by(col(Membership.created_at), col(Membership.id))
    ).all()
    if not tenant_ids:
        raise NoTenants
    # Its own tag per send, so a newer message never replaces an older one in the tray.
    message = PushMessage(
        title=TITLE, body=text, url=f"/hjem/{home_id}", tag=f"{TAG_PREFIX}-{uuid.uuid4().hex[:8]}"
    )
    reached = sum(
        1 for user_id in tenant_ids if push.deliver(session, sender, user_id, message) > 0
    )
    return BroadcastResult(recipients=reached, without_push=len(tenant_ids) - reached)
