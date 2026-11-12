"""Push subscriptions per User and device (Story 3.1, FR-10, AD-8, AD-12).

One row per device, found by its endpoint. Registering is idempotent: the same endpoint again
updates its keys and, if another User signed in on that browser, its owner. A User keeps at most
MAX_SUBSCRIPTIONS_PER_USER rows; a newer one pushes the oldest out.
"""

import uuid

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.clock import utc_now
from app.models.push_subscription import PushSubscription

MAX_SUBSCRIPTIONS_PER_USER = 10


def _trim(session: Session, user_id: uuid.UUID) -> None:
    rows = session.exec(
        select(PushSubscription)
        .where(PushSubscription.user_id == user_id)
        .order_by(col(PushSubscription.updated_at).desc(), col(PushSubscription.created_at).desc())
    ).all()
    for old in rows[MAX_SUBSCRIPTIONS_PER_USER:]:
        session.delete(old)


def register_subscription(
    session: Session, user_id: uuid.UUID, endpoint: str, p256dh: str, auth: str
) -> None:
    """Stores this device for the User, or refreshes the row that already has the endpoint."""
    for _ in range(2):
        row = session.exec(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        ).first()
        if row is None:
            session.add(
                PushSubscription(user_id=user_id, endpoint=endpoint, p256dh=p256dh, auth=auth)
            )
        else:
            row.user_id = user_id
            row.p256dh = p256dh
            row.auth = auth
            row.updated_at = utc_now()
            session.add(row)
        try:
            session.flush()
        except IntegrityError:
            # A parallel registration of the same endpoint inserted first: update that row.
            session.rollback()
            continue
        _trim(session, user_id)
        session.commit()
        return
    raise RuntimeError("Kunne ikke lagre push-abonnementet.")


def remove_subscription(session: Session, user_id: uuid.UUID, endpoint: str) -> None:
    """Deletes this device's row if it is the User's own. Nothing to delete is fine."""
    session.execute(
        delete(PushSubscription).where(
            col(PushSubscription.user_id) == user_id, col(PushSubscription.endpoint) == endpoint
        )
    )
    session.commit()
