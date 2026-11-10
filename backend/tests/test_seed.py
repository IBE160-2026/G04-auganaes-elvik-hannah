"""Story 1.6 (FR-22, AD-15): the seed command. Steps run on SQLite; run() gets fakes.

Story 1.4: plus the Landlord Kari's Home and the Tenant Anders, who joins it by invite link.

Story 2.1 (FR-4, FR-8, decisions 4 and 7): plus eight Tasks in each example Home, set up as of
an earlier date so some are due soon or overdue; a Home the homes step skipped gets none.

Story 1.9 (issue #30): a Landlord Home may always be created, and a Landlord elsewhere may still
create a Household Home.
"""

from datetime import timedelta

import pytest
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, select

from app import seed
from app.clock import utc_now
from app.domain import homes, task_types, tasks
from app.domain.accounts import authenticate, register
from app.models.home import Home
from app.models.invite_link import InviteLink
from app.models.membership import Membership
from app.models.task import Task, TaskInstance
from app.models.user import User
from app.seed.homes import EXAMPLE_HOME_NAME, LANDLORD_HOME_NAME, seed_homes
from app.seed.tasks import seed_tasks
from app.seed.users import EXAMPLE_PASSWORD, EXAMPLE_USERS, seed_users
from tests.helpers import count


@pytest.fixture(autouse=True)
def local_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("DATABASE_URL", "DATABASE_URL_UNPOOLED", "VERCEL"):
        monkeypatch.delenv(name, raising=False)


def by_email(session: Session, email: str) -> User:
    return session.exec(select(User).where(User.email == email)).one()


MARI, JONAS, KARI, ANDERS = (user.email for user in EXAMPLE_USERS[:4])

# What a full seed gives: users, Homes, Memberships, invite links, Tasks, TaskInstances.
FULL = (4, 2, 4, 1, 16, 16)
MODELS = (User, Home, Membership, InviteLink, Task, TaskInstance)
# The same without the tasks step.
HOMES_ONLY = FULL[:4]


def counts(session: Session) -> tuple[int, ...]:
    return tuple(count(session, model) for model in MODELS)


def task_count(session: Session, home: Home) -> int:
    return len(tasks.tasks_of(session, home.id))


def own_home(session: Session, email: str, name: str) -> Home:
    return next(
        h.home for h in homes.homes_for(session, by_email(session, email)) if h.home.name == name
    )


class Calls:
    def __init__(self, session: Session | None = None) -> None:
        self.session = session
        self.upgraded = 0
        self.sessions = 0

    def upgrade(self) -> None:
        self.upgraded += 1

    def session_factory(self) -> Session:
        self.sessions += 1
        assert self.session is not None
        return self.session


def test_steps_are_users_then_homes_then_tasks() -> None:
    assert seed.STEPS == (seed_users, seed_homes, seed_tasks)


def test_example_emails_are_normalised() -> None:
    assert all(user.email == user.email.strip().lower() for user in EXAMPLE_USERS)
    assert len(EXAMPLE_USERS) >= 4
    # seed/homes.py picks users by index; Mari and Jonas must stay first.
    assert [u.email for u in EXAMPLE_USERS[:4]] == [
        "mari@example.com",
        "jonas@example.com",
        "kari@example.com",
        "anders@example.com",
    ]


def test_fresh_db_migrates_and_creates_users(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    calls = Calls(session)
    assert seed.run(upgrade=calls.upgrade, session_factory=calls.session_factory) == 0
    assert calls.upgraded == 1
    assert counts(session) == FULL
    for user in EXAMPLE_USERS:
        assert authenticate(session, email=user.email, password=EXAMPLE_PASSWORD) is not None
    out = capsys.readouterr().out
    assert "Opprettet bruker mari@example.com" in out
    assert f"Opprettet hjemmet «{EXAMPLE_HOME_NAME}»" in out
    assert f"Opprettet hjemmet «{LANDLORD_HOME_NAME}»" in out
    assert f"La til {ANDERS}" in out
    assert f"Satte opp 8 oppgaver i «{EXAMPLE_HOME_NAME}»" in out
    assert f"Satte opp 8 oppgaver i «{LANDLORD_HOME_NAME}»" in out


@pytest.mark.parametrize(("email", "name"), [(MARI, EXAMPLE_HOME_NAME), (KARI, LANDLORD_HOME_NAME)])
def test_fresh_db_gives_both_homes_every_catalog_task_some_due_soon_or_overdue(
    session: Session, email: str, name: str
) -> None:
    for step in seed.STEPS:
        step(session)

    listed = tasks.tasks_of(session, own_home(session, email, name).id)
    assert sorted(row.task.task_type for row in listed) == sorted(
        t.key for t in task_types.TASK_TYPES
    )
    for row in listed:
        entry = task_types.task_type(row.task.task_type)
        assert entry is not None
        assert (row.task.classification, row.task.frequency_days) == (
            entry.classification,
            entry.frequency_days,
        )
    today = utc_now().date()
    assert any(row.due_on < today for row in listed), "nothing overdue"
    assert any(today <= row.due_on <= today + timedelta(days=7) for row in listed), "nothing soon"


def test_fresh_db_gives_mari_and_jonas_one_household_home(session: Session) -> None:
    seed_users(session)
    seed_homes(session)

    for email in (MARI, JONAS):
        member_homes = homes.homes_for(session, by_email(session, email))
        assert [(h.home.name, h.home.type, h.role) for h in member_homes] == [
            (EXAMPLE_HOME_NAME, "household", "household_member")
        ]
    assert count(session, Home) == 2 and count(session, Membership) == 4


def test_fresh_db_gives_kari_a_landlord_home_and_anders_joins_by_invite(session: Session) -> None:
    seed_users(session)
    seed_homes(session)

    kari_homes = homes.homes_for(session, by_email(session, KARI))
    assert [(h.home.name, h.home.type, h.role) for h in kari_homes] == [
        (LANDLORD_HOME_NAME, "landlord", "landlord")
    ]
    anders = by_email(session, ANDERS)
    assert [(h.home.name, h.role) for h in homes.homes_for(session, anders)] == [
        (LANDLORD_HOME_NAME, "tenant")
    ]
    link = session.exec(select(InviteLink)).one()
    assert (link.role, link.used_by_user_id) == ("tenant", anders.id)
    assert link.used_at is not None


def test_rerun_is_idempotent(session: Session, capsys: pytest.CaptureFixture[str]) -> None:
    calls = Calls(session)
    assert seed.run(upgrade=calls.upgrade, session_factory=calls.session_factory) == 0
    ids = set(session.exec(select(User.id)).all())
    capsys.readouterr()

    assert seed.run(upgrade=calls.upgrade, session_factory=calls.session_factory) == 0
    assert set(session.exec(select(User.id)).all()) == ids
    assert counts(session) == FULL
    out = capsys.readouterr().out
    # Four users and two Homes; Jonas's and Anders's Memberships say "er allerede med".
    assert out.count("finnes allerede") == 6
    assert f"{JONAS} er allerede med" in out
    assert f"{ANDERS} er allerede med" in out
    # Story 2.1: both Homes' Tasks are left as they are.
    assert f"Oppgavene i «{EXAMPLE_HOME_NAME}» er allerede satt opp" in out
    assert f"Oppgavene i «{LANDLORD_HOME_NAME}» er allerede satt opp" in out
    assert "Satte opp" not in out


def test_partial_skips_existing_user_with_other_casing(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    existing = register(session, email="  Mari@Example.COM ", name="Mari", password="annet-passord")
    seed_users(session)

    assert count(session, User) == 4
    mari = session.exec(select(User).where(User.email == "mari@example.com")).one()
    # Never overwritten: the existing row keeps its name and password.
    assert mari.id == existing.id and mari.name == "Mari"
    assert authenticate(session, email="mari@example.com", password="annet-passord") is not None
    out = capsys.readouterr().out
    assert "Bruker mari@example.com finnes allerede" in out
    assert "Opprettet bruker jonas@example.com" in out


def test_partial_run_adds_jonas_to_the_existing_home(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_users(session)
    home = homes.create_home(
        session, by_email(session, MARI), name=EXAMPLE_HOME_NAME, type="household"
    ).home
    capsys.readouterr()

    seed_homes(session)

    assert count(session, Home) == 2
    assert [h.home.id for h in homes.homes_for(session, by_email(session, JONAS))] == [home.id]
    out = capsys.readouterr().out
    assert "finnes allerede" in out and f"La til {JONAS}" in out


def test_jonas_in_another_home_is_skipped_with_a_reason(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_users(session)
    jonas = by_email(session, JONAS)
    other = homes.create_home(session, jonas, name="Jonas sitt", type="household").home
    capsys.readouterr()

    seed_homes(session)

    assert [h.home.id for h in homes.homes_for(session, jonas)] == [other.id]
    # Plus Kari's Home with Kari and Anders.
    assert count(session, Home) == 3 and count(session, Membership) == 4
    assert f"Hoppet over {JONAS}" in capsys.readouterr().out


def test_mari_in_another_home_is_skipped_and_nothing_is_written(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_users(session)
    homes.create_home(session, by_email(session, MARI), name="Maris", type="household")
    capsys.readouterr()

    seed_homes(session)
    seed_tasks(session)

    # Mari's own Home, then Kari's with Kari and Anders.
    assert count(session, Home) == 2 and count(session, Membership) == 3
    out = capsys.readouterr().out
    assert f"Hoppet over «{EXAMPLE_HOME_NAME}»" in out
    # Story 2.1: Mari's other Home gets no Tasks; Kari's still does.
    assert task_count(session, own_home(session, MARI, "Maris")) == 0
    assert task_count(session, own_home(session, KARI, LANDLORD_HOME_NAME)) == 8
    assert f"Hoppet over oppgavene i «{EXAMPLE_HOME_NAME}»" in out


def test_partial_run_adds_anders_to_karis_existing_home_with_one_link(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_users(session)
    home = homes.create_home(
        session, by_email(session, KARI), name=LANDLORD_HOME_NAME, type="landlord"
    ).home
    capsys.readouterr()

    seed_homes(session)

    assert [h.home.id for h in homes.homes_for(session, by_email(session, ANDERS))] == [home.id]
    assert counts(session)[:4] == HOMES_ONLY
    out = capsys.readouterr().out
    assert f"Hjemmet «{LANDLORD_HOME_NAME}» finnes allerede" in out and f"La til {ANDERS}" in out


def test_anders_in_another_home_is_skipped_and_no_link_is_made(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_users(session)
    anders = by_email(session, ANDERS)
    other = homes.create_home(session, anders, name="Anders sitt", type="household").home
    capsys.readouterr()

    seed_homes(session)

    assert [h.home.id for h in homes.homes_for(session, anders)] == [other.id]
    assert count(session, InviteLink) == 0
    assert f"Hoppet over {ANDERS}: er allerede med i «Anders sitt»" in capsys.readouterr().out


def test_kari_in_a_household_home_still_gets_storgata_12_and_anders_joins(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_users(session)
    homes.create_home(session, by_email(session, KARI), name="Karis", type="household")
    capsys.readouterr()

    seed_homes(session)
    seed_tasks(session)

    storgata = own_home(session, KARI, LANDLORD_HOME_NAME)
    roles = {h.home.name: h.role for h in homes.homes_for(session, by_email(session, KARI))}
    assert roles == {"Karis": "household_member", LANDLORD_HOME_NAME: "landlord"}
    assert [h.home.id for h in homes.homes_for(session, by_email(session, ANDERS))] == [storgata.id]
    assert count(session, InviteLink) == 1
    assert task_count(session, storgata) == 8
    assert task_count(session, own_home(session, KARI, "Karis")) == 0
    assert homes.fr3_violations(session) == []


def test_mari_landlord_elsewhere_still_gets_the_household_home(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_users(session)
    homes.create_home(session, by_email(session, MARI), name="Marias utleie", type="landlord")
    capsys.readouterr()

    seed_homes(session)

    home = own_home(session, MARI, EXAMPLE_HOME_NAME)
    assert {h.home.id for h in homes.homes_for(session, by_email(session, JONAS))} == {home.id}
    assert f"Opprettet hjemmet «{EXAMPLE_HOME_NAME}»" in capsys.readouterr().out
    assert homes.fr3_violations(session) == []


def test_a_home_set_up_by_hand_is_left_as_it_is(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_users(session)
    seed_homes(session)
    home = own_home(session, MARI, EXAMPLE_HOME_NAME)
    mari = by_email(session, MARI)
    membership = session.exec(
        select(Membership).where(Membership.home_id == home.id, Membership.user_id == mari.id)
    ).one()
    tasks.set_up_tasks(session, membership, [tasks.TaskChoice("gulv", "must", 7)])
    capsys.readouterr()

    seed_tasks(session)

    assert [
        (r.task.task_type, r.task.classification) for r in tasks.tasks_of(session, home.id)
    ] == [("gulv", "must")]
    assert f"Oppgavene i «{EXAMPLE_HOME_NAME}» er allerede satt opp" in capsys.readouterr().out


def _db_down() -> None:
    raise OperationalError("SELECT 1", {}, Exception("connection refused"))


def test_db_down_exits_1_with_hint(capsys: pytest.CaptureFixture[str]) -> None:
    calls = Calls()
    assert seed.run(upgrade=_db_down, session_factory=calls.session_factory) == 1
    assert calls.sessions == 0
    err = capsys.readouterr().err
    assert "docker compose up -d --wait" in err
    # The underlying cause is shown too, e.g. a wrong password instead of a stopped database.
    assert "connection refused" in err


def test_db_down_during_steps_exits_1(capsys: pytest.CaptureFixture[str]) -> None:
    def broken_session() -> Session:
        _db_down()
        raise AssertionError

    assert seed.run(upgrade=lambda: None, session_factory=broken_session) == 1
    assert "docker compose up -d --wait" in capsys.readouterr().err


def _assert_refused(capsys: pytest.CaptureFixture[str], expected: str) -> None:
    calls = Calls()
    code = seed.run(upgrade=calls.upgrade, session_factory=calls.session_factory)
    assert code == 2
    assert calls.upgraded == 0 and calls.sessions == 0
    err = capsys.readouterr().err
    assert expected in err and "Ingenting er skrevet" in err


def test_refuses_on_vercel(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("VERCEL", "1")
    _assert_refused(capsys, "Vercel")


@pytest.mark.parametrize("name", ["DATABASE_URL", "DATABASE_URL_UNPOOLED"])
def test_refuses_remote_database(
    name: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(name, "postgresql://u:p@ep-demo-123.eu-central-1.aws.neon.tech/neondb")
    _assert_refused(capsys, "ep-demo-123.eu-central-1.aws.neon.tech")


@pytest.mark.parametrize("key", ["host", "hostaddr"])
def test_refuses_host_in_query(
    key: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"postgresql://u:p@localhost/db?{key}=db.example.org")
    _assert_refused(capsys, f"{key}=db.example.org")


@pytest.mark.parametrize("url", ["not a url", "postgresql://u:p@remote.example:5432,localhost/db"])
def test_refuses_unparseable_url(
    url: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("DATABASE_URL", url)
    _assert_refused(capsys, "<ugyldig URL>")


def test_refuses_url_without_host(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u@/db")
    _assert_refused(capsys, "<ingen vert>")


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://husly:husly@localhost:5433/husly",
        "postgresql://husly:husly@127.0.0.1:5433/husly",
        "postgresql://husly:husly@[::1]:5433/husly",
        "postgresql://husly:husly@LOCALHOST:5433/husly",
    ],
)
def test_local_urls_are_allowed(url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", url)
    assert seed.local_only_refusal() is None


def test_default_url_is_allowed() -> None:
    assert seed.local_only_refusal() is None


def test_alembic_ini_path_exists() -> None:
    assert seed.ALEMBIC_INI.is_file()
