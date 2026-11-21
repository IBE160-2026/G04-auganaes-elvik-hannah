"""Postgres concurrency tests (Epic 1 retro P3, deferred-work.md): the row locks in the domain.

SQLite ignores `FOR UPDATE`, so these run against a real Postgres (see conftest.py). Each test
starts several threads at once, each with its own Session, and checks the invariant the lock
protects. A race is probabilistic, so each test repeats ROUNDS times with fresh data: with the lock
every round holds, and without it a round breaks with high probability (the mutation check in the
PR). Each test names the lock it guards.
"""

import uuid
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import func
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.domain import account_deletion, fairness, homes, invites, photo_evidence, task_types, tasks
from app.models.fairness_nudge import FairnessNudge
from app.models.home import Home
from app.models.membership import Membership
from app.models.photo_evidence import PhotoEvidence
from app.models.task import Task, TaskInstance
from app.models.user import User
from app.storage import LocalPhotoStore
from tests.helpers import PASSWORD
from tests.postgres.conftest import create_database, drop_database, start_migration
from tests.postgres.helpers import (
    blocks_while_locked,
    errors,
    household,
    membership,
    new_user,
    race,
    wins,
)

ROUNDS = 8
TODAY = date(2026, 11, 21)
TYPES = [t.key for t in task_types.TASK_TYPES]
JPEG_A = b"\xff\xd8\xff\xe0" + b"aaaa" * 40 + b"\xff\xd9"
JPEG_B = b"\xff\xd8\xff\xe0" + b"bbbb" * 40 + b"\xff\xd9"

MakeSession = Callable[[], Session]


def count(session: Session, model: type, **where: object) -> int:
    query = select(func.count()).select_from(model)
    for column, value in where.items():
        query = query.where(getattr(model, column) == value)
    return session.exec(query).one()


def landlord_with_tasks(
    session: Session, choices: int = 2, required_photo: bool = False
) -> tuple[User, Home, list[Task], list[TaskInstance]]:
    landlord = new_user(session, "Kari")
    home = homes.create_home(session, landlord, name="Storgata 12", type="landlord").home
    member = membership(session, landlord.id, home.id)
    rows = tasks.set_up_tasks(
        session,
        member,
        [tasks.TaskChoice(TYPES[i], "must", 7) for i in range(choices)],
        today=TODAY,
    )
    task_rows = [r.task for r in rows]
    instances = [session.get(TaskInstance, r.instance_id) for r in rows]
    if required_photo:
        for task in task_rows:
            task.requires_photo_evidence = True
            session.add(task)
        session.commit()
    return landlord, home, task_rows, [i for i in instances if i is not None]


@pytest.mark.parametrize("round_", range(ROUNDS))
def test_two_parallel_household_creates_make_one_home(
    pg_engine: Engine, make_session: MakeSession, round_: int
) -> None:
    # Guards the user-row lock in homes.create_home: the one-Home limit is checked after it.
    with make_session() as setup:
        user_id = new_user(setup).id

    def create(session: Session) -> object:
        user = session.get(User, user_id)
        assert user is not None
        return homes.create_home(session, user, name="Mitt", type="household")

    outcomes = race(make_session, [create] * 6)

    assert wins(outcomes) == 1
    assert all(isinstance(e, homes.HomeCreationNotAllowed) for e in errors(outcomes))
    with make_session() as check:
        assert count(check, Membership, user_id=user_id) == 1


@pytest.mark.parametrize("round_", range(ROUNDS))
def test_two_parallel_accepts_of_one_link_give_one_membership(
    pg_engine: Engine, make_session: MakeSession, round_: int
) -> None:
    # Guards the link lock in invites.accept: a link is used by one person.
    with make_session() as setup:
        owner, home = household(setup)
        token = invites.create_invite(setup, membership(setup, owner.id, home.id)).token
        joiners = [new_user(setup, f"Gjest{i}").id for i in range(6)]
        home_id = home.id

    def accept_as(user_id: uuid.UUID) -> Callable[[Session], object]:
        def job(session: Session) -> object:
            user = session.get(User, user_id)
            assert user is not None
            return invites.accept(session, token, user)

        return job

    outcomes = race(make_session, [accept_as(u) for u in joiners])

    assert wins(outcomes) == 1
    assert all(isinstance(e, invites.InviteInvalid) for e in errors(outcomes))
    with make_session() as check:
        assert count(check, Membership, home_id=home_id) == 2


@pytest.mark.parametrize("round_", range(ROUNDS))
def test_one_user_joining_two_homes_at_once_joins_one(
    pg_engine: Engine, make_session: MakeSession, round_: int
) -> None:
    # Guards the user-row lock in homes.add_member: the one-Home limit is checked after it.
    with make_session() as setup:
        first_owner, first = household(setup, "Mari")
        second_owner, second = household(setup, "Nils")
        tokens = [
            invites.create_invite(setup, membership(setup, first_owner.id, first.id)).token,
            invites.create_invite(setup, membership(setup, second_owner.id, second.id)).token,
        ]
        visitor_id = new_user(setup, "Besokende").id

    def accept(token: str) -> Callable[[Session], object]:
        def job(session: Session) -> object:
            visitor = session.get(User, visitor_id)
            assert visitor is not None
            return invites.accept(session, token, visitor)

        return job

    outcomes = race(make_session, [accept(t) for t in tokens])

    assert wins(outcomes) == 1
    assert [type(e) for e in errors(outcomes)] == [homes.InOtherHome]
    with make_session() as check:
        assert count(check, Membership, user_id=visitor_id) == 1


@pytest.mark.parametrize("round_", range(ROUNDS))
def test_two_parallel_setups_with_different_choices_commit_only_one(
    pg_engine: Engine, make_session: MakeSession, round_: int
) -> None:
    # Guards the Home-row lock in tasks.set_up_tasks: two setups never mix their Tasks.
    with make_session() as setup:
        landlord = new_user(setup, "Kari")
        home = homes.create_home(setup, landlord, name="Storgata 12", type="landlord").home
        landlord_id, home_id = landlord.id, home.id

    def set_up(types: list[str]) -> Callable[[Session], object]:
        def job(session: Session) -> object:
            member = membership(session, landlord_id, home_id)
            return tasks.set_up_tasks(
                session, member, [tasks.TaskChoice(t, "must", 7) for t in types], today=TODAY
            )

        return job

    outcomes = race(make_session, [set_up(TYPES[:3]), set_up(TYPES[3:5])])

    assert wins(outcomes) == 1
    assert [type(e) for e in errors(outcomes)] == [tasks.TasksAlreadySetUp]
    winner = next(len(value) for kind, value in outcomes if kind == "ok")
    with make_session() as check:
        assert count(check, Task, home_id=home_id) == winner


@pytest.mark.parametrize("round_", range(ROUNDS))
def test_parallel_frequency_changes_keep_the_date_in_step_with_the_final_frequency(
    pg_engine: Engine, make_session: MakeSession, round_: int
) -> None:
    # Guards the Task-row lock in tasks.adjust_task: one save's Frequency is never mixed with the
    # other's date shift (due = start + final Frequency, whatever the order).
    with make_session() as setup:
        landlord, home, rows, instances = landlord_with_tasks(setup, 1)
        task_id, start = rows[0].id, instances[0].due_on - timedelta(days=7)
        landlord_id, home_id = landlord.id, home.id

    def change(days: int) -> Callable[[Session], object]:
        def job(session: Session) -> object:
            member = membership(session, landlord_id, home_id)
            return tasks.adjust_task(session, member, task_id, frequency_days=days)  # type: ignore[arg-type]

        return job

    outcomes = race(make_session, [change(14), change(30), change(60)])

    assert errors(outcomes) == []
    with make_session() as check:
        task = check.get(Task, task_id)
        assert task is not None
        due = check.exec(
            select(TaskInstance.due_on).where(
                TaskInstance.task_id == task_id, col_open(TaskInstance)
            )
        ).one()
        assert due == start + timedelta(days=task.frequency_days)


def col_open(model: type[TaskInstance]) -> object:
    return model.completed_at.is_(None)  # type: ignore[attr-defined]


@pytest.mark.parametrize("round_", range(ROUNDS))
def test_two_tenants_uploading_for_one_instance_leave_one_consistent_photo(
    pg_engine: Engine, make_session: MakeSession, tmp_path: Path, round_: int
) -> None:
    # Guards the Task and instance locks in photo_evidence.complete_with_photo: the stored photo,
    # the evidence row and the completer are always the same person's.
    store = LocalPhotoStore(tmp_path / f"photos{round_}")
    with make_session() as setup:
        _landlord, home, rows, instances = landlord_with_tasks(setup, 1, required_photo=True)
        task_id, instance_id, home_id = rows[0].id, instances[0].id, home.id
        first = new_user(setup, "Anders")
        second = new_user(setup, "Berit")
        for tenant in (first, second):
            homes.add_member(setup, setup.get(Home, home_id), tenant)  # type: ignore[arg-type]
        photos = {first.id: JPEG_A, second.id: JPEG_B}

    def upload(user_id: uuid.UUID) -> Callable[[Session], object]:
        def job(session: Session) -> object:
            return photo_evidence.complete_with_photo(
                session,
                store,
                membership(session, user_id, home_id),
                task_id,
                instance_id,
                photos[user_id],
            )

        return job

    outcomes = race(make_session, [upload(first.id), upload(second.id)])

    assert errors(outcomes) == []
    with make_session() as check:
        instance = check.get(TaskInstance, instance_id)
        evidence = check.get(PhotoEvidence, task_id)
        assert instance is not None and evidence is not None
        assert instance.completed_at is not None
        assert evidence.uploaded_by_user_id == instance.completed_by_user_id
        assert (
            store.read(photo_evidence.evidence_key(task_id)) == photos[evidence.uploaded_by_user_id]
        )
        assert count(check, PhotoEvidence, task_id=task_id) == 1


@pytest.mark.parametrize("round_", range(ROUNDS))
def test_two_runs_claiming_one_nudge_both_succeed_and_leave_one_row(
    pg_engine: Engine, make_session: MakeSession, round_: int
) -> None:
    # Guards the IntegrityError branch in fairness._claim: a parallel run that got there first is
    # fine (the primary key on the instance is the backstop).
    with make_session() as setup:
        _landlord, _home, _rows, instances = landlord_with_tasks(setup, 1)
        instance_id = instances[0].id

    def claim(session: Session) -> object:
        return fairness._claim(session, instance_id, TODAY)

    outcomes = race(make_session, [claim] * 4)

    assert errors(outcomes) == []
    with make_session() as check:
        assert count(check, FairnessNudge, task_instance_id=instance_id) == 1


@pytest.mark.parametrize("round_", range(ROUNDS))
def test_the_same_account_deleted_twice_at_once_is_deleted_once(
    pg_engine: Engine, make_session: MakeSession, tmp_path: Path, round_: int
) -> None:
    # Guards the user-row lock and the deleted check in account_deletion.delete_account.
    store = LocalPhotoStore(tmp_path)
    with make_session() as setup:
        owner, _home = household(setup)
        owner_id = owner.id

    def delete(session: Session) -> object:
        user = session.get(User, owner_id)
        assert user is not None
        return account_deletion.delete_account(session, user, PASSWORD, store)

    outcomes = race(make_session, [delete, delete])

    assert wins(outcomes) == 1
    assert [type(e) for e in errors(outcomes)] == [account_deletion.WrongPassword]


@pytest.mark.parametrize("round_", range(ROUNDS))
def test_two_members_deleting_at_once_leave_no_empty_home_behind(
    pg_engine: Engine, make_session: MakeSession, tmp_path: Path, round_: int
) -> None:
    # Guards the Home locks in delete_account: each sees the other's Membership go before it decides
    # whether the Home is empty, so the last one out deletes it.
    store = LocalPhotoStore(tmp_path)
    with make_session() as setup:
        owner, home = household(setup)
        other = new_user(setup, "Jonas")
        homes.add_member(setup, home, other)
        home_id, owner_id, other_id = home.id, owner.id, other.id

    def delete(user_id: uuid.UUID) -> Callable[[Session], object]:
        def job(session: Session) -> object:
            user = session.get(User, user_id)
            assert user is not None
            return account_deletion.delete_account(session, user, PASSWORD, store)

        return job

    outcomes = race(make_session, [delete(owner_id), delete(other_id)])

    assert errors(outcomes) == []
    with make_session() as check:
        assert count(check, Home, id=home_id) == 0


@pytest.mark.parametrize("round_", range(ROUNDS))
def test_a_landlord_deleting_while_a_tenant_joins_never_strands_either(
    pg_engine: Engine, make_session: MakeSession, tmp_path: Path, round_: int
) -> None:
    # Guards the Home lock in homes.add_member and the lock order in invites.accept: either the
    # Tenant joined first (the deletion is refused) or the Home went first (the join is refused).
    # Never an unhandled integrity error, and never a deadlock.
    store = LocalPhotoStore(tmp_path)
    with make_session() as setup:
        landlord = new_user(setup, "Kari")
        home = homes.create_home(setup, landlord, name="Storgata 12", type="landlord").home
        token = invites.create_invite(setup, membership(setup, landlord.id, home.id)).token
        tenant_id, home_id, landlord_id = new_user(setup, "Anders").id, home.id, landlord.id

    def delete(session: Session) -> object:
        user = session.get(User, landlord_id)
        assert user is not None
        return account_deletion.delete_account(session, user, PASSWORD, store)

    def join(session: Session) -> object:
        tenant = session.get(User, tenant_id)
        assert tenant is not None
        return invites.accept(session, token, tenant)

    deleted, joined = race(make_session, [delete, join])

    with make_session() as check:
        if deleted[0] == "ok":
            assert joined[0] == "error" and isinstance(joined[1], invites.InviteInvalid)
            assert count(check, Home, id=home_id) == 0
            assert count(check, Membership, user_id=tenant_id) == 0
        else:
            assert isinstance(deleted[1], account_deletion.LandlordHasTenants)
            assert joined[0] == "ok"
            assert count(check, Membership, user_id=tenant_id, home_id=home_id) == 1
            assert count(check, Home, id=home_id) == 1


def test_two_deploys_migrating_at_once_both_succeed_and_reach_head() -> None:
    # Guards the advisory lock in alembic/env.py (Story 1.7): without it the second process meets
    # the tables the first one just created and fails.
    url = create_database()
    try:
        processes = [start_migration(url), start_migration(url)]
        outputs = [p.communicate(timeout=180)[0] for p in processes]
        assert [p.returncode for p in processes] == [0, 0], outputs
        from sqlalchemy import create_engine, text

        engine = create_engine(url)
        with engine.connect() as connection:
            versions = connection.execute(text("SELECT count(*) FROM alembic_version")).scalar_one()
        engine.dispose()
        assert versions == 1
    finally:
        drop_database(url)


# A race between threads shows a missing lock only by chance (a narrow window). These hold a row
# lock in another transaction and require the function to wait for it: deterministic, one per lock.
# The held lock is FOR KEY SHARE, which conflicts only with an explicit FOR UPDATE (a plain UPDATE,
# an INSERT with a foreign key or the function's other writes are compatible with it), so the test
# fails when the function does not take the lock, not because a write happened to collide.


def test_adjust_task_waits_for_the_task_row(pg_engine: Engine, make_session: MakeSession) -> None:
    # Guards `with_for_update()` on the Task in tasks.adjust_task.
    with make_session() as setup:
        landlord, home, rows, _instances = landlord_with_tasks(setup, 1)
        task_id, landlord_id, home_id = rows[0].id, landlord.id, home.id

    def job(session: Session) -> object:
        member = membership(session, landlord_id, home_id)
        return tasks.adjust_task(session, member, task_id, frequency_days=14)  # type: ignore[arg-type]

    blocked, outcome = blocks_while_locked(
        make_session, "SELECT id FROM tasks WHERE id = :id FOR KEY SHARE", {"id": task_id}, job
    )

    assert blocked and outcome[0] == "ok"


def test_set_up_tasks_waits_for_the_home_row(pg_engine: Engine, make_session: MakeSession) -> None:
    # Guards `with_for_update()` on the Home in tasks.set_up_tasks.
    with make_session() as setup:
        landlord = new_user(setup, "Kari")
        home = homes.create_home(setup, landlord, name="Storgata 12", type="landlord").home
        landlord_id, home_id = landlord.id, home.id

    def job(session: Session) -> object:
        member = membership(session, landlord_id, home_id)
        return tasks.set_up_tasks(
            session, member, [tasks.TaskChoice(TYPES[0], "must", 7)], today=TODAY
        )

    blocked, outcome = blocks_while_locked(
        make_session, "SELECT id FROM homes WHERE id = :id FOR KEY SHARE", {"id": home_id}, job
    )

    assert blocked and outcome[0] == "ok"


def test_add_member_waits_for_the_home_row(pg_engine: Engine, make_session: MakeSession) -> None:
    # Guards the Home lock in homes.add_member (a Home cannot be deleted under a join).
    with make_session() as setup:
        _owner, home = household(setup)
        joiner_id, home_id = new_user(setup, "Gjest").id, home.id

    def job(session: Session) -> object:
        joiner, target = session.get(User, joiner_id), session.get(Home, home_id)
        assert joiner is not None and target is not None
        return homes.add_member(session, target, joiner)

    blocked, outcome = blocks_while_locked(
        make_session, "SELECT id FROM homes WHERE id = :id FOR KEY SHARE", {"id": home_id}, job
    )

    assert blocked and outcome[0] == "ok"


def test_add_member_waits_for_the_user_row(pg_engine: Engine, make_session: MakeSession) -> None:
    # Guards the user-row lock in homes.add_member.
    with make_session() as setup:
        _owner, home = household(setup)
        joiner_id, home_id = new_user(setup, "Gjest").id, home.id

    def job(session: Session) -> object:
        joiner, target = session.get(User, joiner_id), session.get(Home, home_id)
        assert joiner is not None and target is not None
        return homes.add_member(session, target, joiner)

    blocked, outcome = blocks_while_locked(
        make_session, "SELECT id FROM users WHERE id = :id FOR KEY SHARE", {"id": joiner_id}, job
    )

    assert blocked and outcome[0] == "ok"


def test_create_home_waits_for_the_user_row(pg_engine: Engine, make_session: MakeSession) -> None:
    # Guards the user-row lock in homes.create_home.
    with make_session() as setup:
        user_id = new_user(setup).id

    def job(session: Session) -> object:
        user = session.get(User, user_id)
        assert user is not None
        return homes.create_home(session, user, name="Mitt", type="household")

    blocked, outcome = blocks_while_locked(
        make_session, "SELECT id FROM users WHERE id = :id FOR KEY SHARE", {"id": user_id}, job
    )

    assert blocked and outcome[0] == "ok"


def test_delete_account_waits_for_the_homes_of_the_user(
    pg_engine: Engine, make_session: MakeSession, tmp_path: Path
) -> None:
    # Guards the Home lock in account_deletion.delete_account (it keeps two members deleting at once
    # from both leaving the Home behind, and a join from racing it). The user-row lock is not held
    # here: the function updates the unique e-mail column, which waits for any lock on that row
    # anyway, so it is guarded by the race test of the same account deleted twice.
    store = LocalPhotoStore(tmp_path)
    with make_session() as setup:
        owner, home = household(setup)
        # A second member keeps the Home alive, so deleting the Home row cannot be what waits.
        homes.add_member(setup, home, new_user(setup, "Jonas"))
        owner_id, home_id = owner.id, home.id

    def job(session: Session) -> object:
        user = session.get(User, owner_id)
        assert user is not None
        return account_deletion.delete_account(session, user, PASSWORD, store)

    blocked, outcome = blocks_while_locked(
        make_session, "SELECT id FROM homes WHERE id = :id FOR KEY SHARE", {"id": home_id}, job
    )

    assert blocked and outcome[0] == "ok"


def test_accept_waits_for_the_link_row(pg_engine: Engine, make_session: MakeSession) -> None:
    # Guards the link lock in invites.accept: a second accepter waits and then finds it used.
    with make_session() as setup:
        owner, home = household(setup)
        token = invites.create_invite(setup, membership(setup, owner.id, home.id)).token
        joiner_id = new_user(setup, "Gjest").id
        link_hash = invites.hash_token(token)

    def job(session: Session) -> object:
        joiner = session.get(User, joiner_id)
        assert joiner is not None
        return invites.accept(session, token, joiner)

    blocked, outcome = blocks_while_locked(
        make_session,
        "SELECT id FROM invite_links WHERE token_hash = :h FOR KEY SHARE",
        {"h": link_hash},
        job,
    )

    assert blocked and outcome[0] == "ok"
