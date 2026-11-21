"""Deleting an account (Story 1.10, FR-25, AD-17, AD-16).

The user row is never deleted: it is anonymised (name «Tidligere medlem», an unusable e-mail and
password, `deleted_at` set), so every row that references the User (completions, Photo Evidence,
used invite links) stays valid and no `ON DELETE` rule is needed. Everything that only exists for
this user is deleted by statement, in one transaction: Memberships, push devices, claimed
notifications, daily AI counts and unused invite links. A Home left without a Member is deleted
with its Tasks, instances, evidence rows and stored photos. A Landlord with a Tenant in any
Landlord Home is refused before anything changes (FR-23: remove the Tenants first).

The stored photos are removed after the commit, one by one: a store failure cannot be rolled back,
so it is logged and the account is deleted all the same (an orphan photo is unreachable).
`tables_pointing_at` is what the test reads, so a new table that references users or Homes fails
it until this function handles it.
"""

import logging
import uuid
from datetime import date

from sqlalchemy import delete
from sqlmodel import Session, SQLModel, col, select

from app.clock import to_utc, utc_now
from app.domain import accounts, photo_evidence
from app.models.ai_usage import AiUsage
from app.models.due_notification import DueNotification
from app.models.fairness_nudge import FairnessNudge
from app.models.home import Home
from app.models.invite_link import InviteLink
from app.models.membership import Membership
from app.models.onboarding_guide import OnboardingGuide
from app.models.photo_evidence import DESCRIPTION_MAX_LENGTH, PhotoEvidence
from app.models.push_subscription import PushSubscription
from app.models.task import Task, TaskInstance
from app.models.user import User
from app.storage import PhotoStore

logger = logging.getLogger(__name__)

WRONG_PASSWORD = "Passordet stemmer ikke."
LANDLORD_HAS_TENANTS = "Du må fjerne leietakerne før du kan slette kontoen. Gjelder: {homes}."

# Not an Argon2 hash, so verify() can never succeed on it.
UNUSABLE_PASSWORD_HASH = "!"


class WrongPassword(Exception):
    """The password given to confirm the deletion does not match."""


class LandlordHasTenants(Exception):
    """A Landlord Home of the user still has a Tenant, so the Landlord may not go (FR-23)."""

    def __init__(self, home_names: list[str]) -> None:
        super().__init__(LANDLORD_HAS_TENANTS.format(homes=", ".join(home_names)))
        self.home_names = home_names


def is_deleted(user: User) -> bool:
    return user.deleted_at is not None


def tables_pointing_at(parent: str) -> set[str]:
    """Names of tables with a foreign key to `parent` ("users" or "homes"), from the metadata."""
    return {
        table.name
        for table in SQLModel.metadata.tables.values()
        if any(fk.column.table.name == parent for fk in table.foreign_keys)
    }


def _delete_home(session: Session, home_id: uuid.UUID) -> list[str]:
    """Deletes a Home with everything under it and returns the keys of its stored photos."""
    task_ids = list(session.exec(select(Task.id).where(Task.home_id == home_id)).all())
    keys = [
        photo_evidence.evidence_key(task_id)
        for task_id in session.exec(
            select(PhotoEvidence.task_id).where(col(PhotoEvidence.task_id).in_(task_ids))
        ).all()
    ]
    if task_ids:
        instance_ids = select(TaskInstance.id).where(col(TaskInstance.task_id).in_(task_ids))
        session.execute(delete(PhotoEvidence).where(col(PhotoEvidence.task_id).in_(task_ids)))
        session.execute(
            delete(FairnessNudge).where(col(FairnessNudge.task_instance_id).in_(instance_ids))
        )
        session.execute(
            delete(DueNotification).where(col(DueNotification.task_instance_id).in_(instance_ids))
        )
        session.execute(delete(TaskInstance).where(col(TaskInstance.task_id).in_(task_ids)))
        session.execute(delete(Task).where(col(Task.id).in_(task_ids)))
    session.execute(delete(InviteLink).where(col(InviteLink.home_id) == home_id))
    session.execute(delete(OnboardingGuide).where(col(OnboardingGuide.home_id) == home_id))
    session.execute(delete(Membership).where(col(Membership.home_id) == home_id))
    session.execute(delete(Home).where(col(Home.id) == home_id))
    return keys


def _tenant_homes(session: Session, memberships: list[Membership]) -> list[str]:
    """Names of the user's Landlord Homes that still have a Tenant."""
    landlord_home_ids = [m.home_id for m in memberships if m.role == "landlord"]
    if not landlord_home_ids:
        return []
    homes = session.exec(select(Home).where(col(Home.id).in_(landlord_home_ids))).all()
    with_tenant = set(
        session.exec(
            select(Membership.home_id).where(
                col(Membership.home_id).in_(landlord_home_ids), Membership.role == "tenant"
            )
        ).all()
    )
    return sorted(home.name for home in homes if home.id in with_tenant)


def delete_account(session: Session, user: User, password: str, store: PhotoStore) -> None:
    """Anonymises the user and deletes what only exists for them (see the module docstring).

    Raises WrongPassword or LandlordHasTenants before anything changes. Any other failure rolls
    the whole transaction back.
    """
    if is_deleted(user) or not accounts.password_hash.verify(password, user.password_hash):
        raise WrongPassword
    memberships = list(session.exec(select(Membership).where(Membership.user_id == user.id)).all())
    # Locks, in a fixed order (no deadlock between two deleting at once): the user row, so the same
    # account cannot be deleted twice in parallel, and the user's Homes, so two Members deleting at
    # the same time each see the other's Membership go before deciding the Home is empty. SQLite
    # ignores FOR UPDATE; the Postgres race is a deferred concurrency test (deferred-work.md).
    session.exec(select(User.id).where(User.id == user.id).with_for_update()).all()
    session.refresh(user)
    if is_deleted(user):
        session.rollback()
        raise WrongPassword
    session.exec(
        select(Home.id)
        .where(col(Home.id).in_([m.home_id for m in memberships]))
        .order_by(col(Home.id))
        .with_for_update()
    ).all()
    blocking = _tenant_homes(session, memberships)
    if blocking:
        session.rollback()
        raise LandlordHasTenants(blocking)

    keys: list[str] = []
    try:
        home_ids = [m.home_id for m in memberships]
        session.execute(delete(Membership).where(col(Membership.user_id) == user.id))
        for home_id in home_ids:
            still_has_member = session.exec(
                select(Membership.id).where(Membership.home_id == home_id)
            ).first()
            if still_has_member is None:
                keys += _delete_home(session, home_id)
        session.execute(delete(PushSubscription).where(col(PushSubscription.user_id) == user.id))
        session.execute(delete(DueNotification).where(col(DueNotification.user_id) == user.id))
        session.execute(delete(AiUsage).where(col(AiUsage.user_id) == user.id))
        session.execute(
            delete(InviteLink).where(
                col(InviteLink.created_by_user_id) == user.id, col(InviteLink.used_at).is_(None)
            )
        )
        for evidence in session.exec(
            select(PhotoEvidence).where(PhotoEvidence.uploaded_by_user_id == user.id)
        ).all():
            evidence.description = photo_evidence.describe(
                photo_evidence.FORMER_MEMBER, _day(evidence)
            )[:DESCRIPTION_MAX_LENGTH]
        user.name = photo_evidence.FORMER_MEMBER
        user.email = f"deleted-{user.id}@deleted.invalid"
        user.password_hash = UNUSABLE_PASSWORD_HASH
        user.deleted_at = utc_now()
        session.commit()
    except Exception:
        session.rollback()
        raise

    for key in keys:
        try:
            store.delete(key)
        except Exception:  # noqa: BLE001 - the account is already deleted; never turn it into a 500
            logger.warning("Fikk ikke slettet bildet %s etter kontosletting", key, exc_info=True)


def _day(evidence: PhotoEvidence) -> date:
    return to_utc(evidence.uploaded_at).date()
