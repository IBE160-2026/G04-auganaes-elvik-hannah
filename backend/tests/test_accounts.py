"""Story 1.2 (FR-1): registration and credential checks in the domain layer."""

from unittest.mock import patch

import pytest
from sqlmodel import Session

from app.domain import accounts


def test_register_normalises_email_and_name_and_hashes_password(session: Session) -> None:
    user = accounts.register(
        session, email="  Ola@Example.COM ", name="  Ola ", password="hemmelig1"
    )

    assert user.email == "ola@example.com"
    assert user.name == "Ola"
    assert user.password_hash != "hemmelig1"
    assert user.password_hash.startswith("$argon2id$")


def test_register_duplicate_email_in_other_casing_raises_email_taken(session: Session) -> None:
    accounts.register(session, email="ola@example.com", name="Ola", password="hemmelig1")

    with pytest.raises(accounts.EmailTaken):
        accounts.register(session, email="Ola@Example.com ", name="Ola 2", password="hemmelig2")


def test_session_is_usable_after_a_duplicate(session: Session) -> None:
    accounts.register(session, email="ola@example.com", name="Ola", password="hemmelig1")
    with pytest.raises(accounts.EmailTaken):
        accounts.register(session, email="ola@example.com", name="Ola", password="hemmelig1")

    other = accounts.register(session, email="kari@example.com", name="Kari", password="hemmelig1")

    assert other.email == "kari@example.com"


def test_authenticate_with_any_email_casing(session: Session) -> None:
    user = accounts.register(session, email="ola@example.com", name="Ola", password="hemmelig1")

    assert accounts.authenticate(session, email=" OLA@example.com", password="hemmelig1") == user


def test_authenticate_wrong_password_returns_none(session: Session) -> None:
    accounts.register(session, email="ola@example.com", name="Ola", password="hemmelig1")

    assert accounts.authenticate(session, email="ola@example.com", password="feilfeil1") is None


def test_unknown_email_still_runs_one_hash_verification(session: Session) -> None:
    with patch.object(
        accounts.password_hash, "verify", wraps=accounts.password_hash.verify
    ) as verify:
        result = accounts.authenticate(session, email="ingen@example.com", password="hemmelig1")

    assert result is None
    assert verify.call_count == 1
