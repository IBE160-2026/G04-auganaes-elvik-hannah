"""Story 1.6 (FR-22, AD-15): the seed command. Steps run on SQLite; run() gets fakes."""

import pytest
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, func, select

from app import seed
from app.domain.accounts import authenticate, register
from app.models.user import User
from app.seed.users import EXAMPLE_PASSWORD, EXAMPLE_USERS, seed_users


@pytest.fixture(autouse=True)
def local_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("DATABASE_URL", "DATABASE_URL_UNPOOLED", "VERCEL"):
        monkeypatch.delenv(name, raising=False)


def user_count(session: Session) -> int:
    return session.exec(select(func.count()).select_from(User)).one()


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


def test_steps_start_with_users() -> None:
    assert seed.STEPS == (seed_users,)


def test_example_emails_are_normalised() -> None:
    assert all(user.email == user.email.strip().lower() for user in EXAMPLE_USERS)
    assert len(EXAMPLE_USERS) >= 2


def test_fresh_db_migrates_and_creates_users(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    calls = Calls(session)
    assert seed.run(upgrade=calls.upgrade, session_factory=calls.session_factory) == 0
    assert calls.upgraded == 1
    assert user_count(session) == 2
    for user in EXAMPLE_USERS:
        assert authenticate(session, email=user.email, password=EXAMPLE_PASSWORD) is not None
    assert "Opprettet bruker mari@example.com" in capsys.readouterr().out


def test_rerun_is_idempotent(session: Session, capsys: pytest.CaptureFixture[str]) -> None:
    calls = Calls(session)
    assert seed.run(upgrade=calls.upgrade, session_factory=calls.session_factory) == 0
    ids = set(session.exec(select(User.id)).all())
    capsys.readouterr()

    assert seed.run(upgrade=calls.upgrade, session_factory=calls.session_factory) == 0
    assert user_count(session) == 2
    assert set(session.exec(select(User.id)).all()) == ids
    out = capsys.readouterr().out
    assert out.count("finnes allerede") == 2


def test_partial_skips_existing_user_with_other_casing(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    existing = register(session, email="  Mari@Example.COM ", name="Mari", password="annet-passord")
    seed_users(session)

    assert user_count(session) == 2
    mari = session.exec(select(User).where(User.email == "mari@example.com")).one()
    # Never overwritten: the existing row keeps its name and password.
    assert mari.id == existing.id and mari.name == "Mari"
    assert authenticate(session, email="mari@example.com", password="annet-passord") is not None
    out = capsys.readouterr().out
    assert "Bruker mari@example.com finnes allerede" in out
    assert "Opprettet bruker jonas@example.com" in out


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
