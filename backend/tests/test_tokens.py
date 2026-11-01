"""Story 1.2 (AD-7, AD-2): JWTs carry only the user id and are checked for type and claims."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.domain import tokens

SECRET = "test-secret-som-er-minst-32-byte-lang"
USER_ID = uuid.uuid4()


def claims_of(token: str) -> dict[str, object]:
    return jwt.decode(token, SECRET, algorithms=["HS256"])


@pytest.mark.parametrize(
    ("token_type", "ttl"), [("access", timedelta(minutes=15)), ("refresh", timedelta(days=30))]
)
def test_issue_carries_only_the_five_claims(token_type: tokens.TokenType, ttl: timedelta) -> None:
    issued = tokens.issue(USER_ID, token_type, SECRET)
    claims = claims_of(issued.token)

    assert set(claims) == {"sub", "type", "jti", "iat", "exp"}
    assert claims["sub"] == str(USER_ID)
    assert claims["type"] == token_type
    assert claims["exp"] - claims["iat"] == ttl.total_seconds()
    assert issued.expires_in == ttl.total_seconds()


def test_two_tokens_in_the_same_second_differ() -> None:
    first = tokens.issue(USER_ID, "refresh", SECRET).token
    second = tokens.issue(USER_ID, "refresh", SECRET).token

    assert first != second


def test_decode_returns_user_id() -> None:
    token = tokens.issue(USER_ID, "access", SECRET).token

    assert tokens.decode(token, "access", SECRET) == USER_ID


@pytest.mark.parametrize(("issued_as", "expected"), [("access", "refresh"), ("refresh", "access")])
def test_wrong_type_is_rejected(issued_as: tokens.TokenType, expected: tokens.TokenType) -> None:
    token = tokens.issue(USER_ID, issued_as, SECRET).token

    with pytest.raises(tokens.InvalidToken):
        tokens.decode(token, expected, SECRET)


def test_expired_token_is_rejected() -> None:
    past = datetime.now(UTC) - timedelta(hours=1)
    claims = {"sub": str(USER_ID), "type": "access", "jti": "x", "iat": past, "exp": past}
    token = jwt.encode(claims, SECRET, algorithm="HS256")

    with pytest.raises(tokens.InvalidToken):
        tokens.decode(token, "access", SECRET)


def test_token_signed_with_another_secret_is_rejected() -> None:
    token = tokens.issue(USER_ID, "access", "en-annen-hemmelighet-som-er-32-byte").token

    with pytest.raises(tokens.InvalidToken):
        tokens.decode(token, "access", SECRET)


@pytest.mark.parametrize("missing", ["sub", "type", "jti", "iat", "exp"])
def test_token_missing_a_claim_is_rejected(missing: str) -> None:
    now = datetime.now(UTC)
    claims = {
        "sub": str(USER_ID),
        "type": "access",
        "jti": "x",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    del claims[missing]
    token = jwt.encode(claims, SECRET, algorithm="HS256")

    with pytest.raises(tokens.InvalidToken):
        tokens.decode(token, "access", SECRET)


def test_alg_none_is_rejected() -> None:
    now = datetime.now(UTC)
    claims = {
        "sub": str(USER_ID),
        "type": "access",
        "jti": "x",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    token = jwt.encode(claims, None, algorithm="none")

    with pytest.raises(tokens.InvalidToken):
        tokens.decode(token, "access", SECRET)


@pytest.mark.parametrize("garbage", ["", "abc", "a.b.c"])
def test_garbage_is_rejected(garbage: str) -> None:
    with pytest.raises(tokens.InvalidToken):
        tokens.decode(garbage, "access", SECRET)


def test_non_uuid_subject_is_rejected() -> None:
    now = datetime.now(UTC)
    claims = {
        "sub": "ikke-uuid",
        "type": "access",
        "jti": "x",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    token = jwt.encode(claims, SECRET, algorithm="HS256")

    with pytest.raises(tokens.InvalidToken):
        tokens.decode(token, "access", SECRET)
