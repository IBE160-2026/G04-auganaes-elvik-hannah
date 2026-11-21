"""Helpers for the concurrency tests: threads that start together, each with its own Session."""

import threading
import uuid
from collections.abc import Callable
from typing import Any

from sqlmodel import Session

from app.domain import accounts, homes
from app.models.home import Home
from app.models.membership import Membership
from app.models.user import User
from tests.helpers import PASSWORD

Outcome = tuple[str, Any]  # ("ok", value) or ("error", exception)


def new_user(session: Session, name: str = "Ola") -> User:
    return accounts.register(
        session,
        email=f"{name.lower()}-{uuid.uuid4().hex[:8]}@example.com",
        name=name,
        password=PASSWORD,
    )


def household(session: Session, name: str = "Mari") -> tuple[User, Home]:
    owner = new_user(session, name)
    return owner, homes.create_home(session, owner, name="Kollektivet", type="household").home


def membership(session: Session, user_id: uuid.UUID, home_id: uuid.UUID) -> Membership:
    from sqlmodel import select

    return session.exec(
        select(Membership).where(Membership.user_id == user_id, Membership.home_id == home_id)
    ).one()


def race(
    make_session: Callable[[], Session], jobs: list[Callable[[Session], Any]]
) -> list[Outcome]:
    """Runs every job in its own thread and Session, released together by a barrier.

    Returns one outcome per job, in order. A job that raises is reported, never lost, so the test
    decides which exceptions are the expected «lost the race» and which are bugs.
    """
    barrier = threading.Barrier(len(jobs))
    outcomes: list[Outcome | None] = [None] * len(jobs)

    def worker(index: int, job: Callable[[Session], Any]) -> None:
        with make_session() as session:
            barrier.wait(timeout=30)
            try:
                outcomes[index] = ("ok", job(session))
            except Exception as error:  # noqa: BLE001
                session.rollback()
                outcomes[index] = ("error", error)

    threads = [threading.Thread(target=worker, args=(i, job)) for i, job in enumerate(jobs)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
        assert not thread.is_alive(), "a job did not finish: a lock was never released"
    return [outcome for outcome in outcomes if outcome is not None]


def wins(outcomes: list[Outcome]) -> int:
    return sum(1 for kind, _ in outcomes if kind == "ok")


def errors(outcomes: list[Outcome]) -> list[Exception]:
    return [value for kind, value in outcomes if kind == "error"]


def blocks_while_locked(
    make_session: Callable[[], Session],
    lock_sql: str,
    params: dict[str, Any],
    job: Callable[[Session], Any],
    hold: float = 1.5,
) -> tuple[bool, Outcome]:
    """Holds `lock_sql` (a SELECT ... FOR KEY SHARE) open in one transaction and runs `job` meanwhile.

    Returns whether the job was still waiting after `hold` seconds (it needs that row lock) and its
    outcome once the lock was released. A deterministic check that a function takes a given lock,
    where a race between threads only shows a missing lock by chance.
    """
    from sqlalchemy import text

    outcome: list[Outcome] = []

    def run() -> None:
        with make_session() as session:
            try:
                outcome.append(("ok", job(session)))
            except Exception as error:  # noqa: BLE001
                session.rollback()
                outcome.append(("error", error))

    with make_session() as holder:
        holder.execute(text(lock_sql), params)
        thread = threading.Thread(target=run)
        thread.start()
        thread.join(timeout=hold)
        blocked = thread.is_alive()
        holder.rollback()
    thread.join(timeout=30)
    assert not thread.is_alive(), "the job never finished after the lock was released"
    return blocked, outcome[0]
