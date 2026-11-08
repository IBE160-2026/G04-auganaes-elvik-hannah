"""Access and refresh JWTs (Story 1.2, AD-7). They carry the user id only, never a Role (AD-2)."""

import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Literal

import jwt

from app.clock import utc_now

ALGORITHM = "HS256"
ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=30)
REQUIRED_CLAIMS = ["sub", "type", "jti", "iat", "exp"]

TokenType = Literal["access", "refresh"]
_TTL: dict[TokenType, timedelta] = {"access": ACCESS_TTL, "refresh": REFRESH_TTL}


class InvalidToken(Exception):
    """Missing, expired, tampered, or of the wrong type."""


@dataclass(frozen=True)
class IssuedToken:
    token: str
    expires_in: int  # seconds


def issue(user_id: uuid.UUID, token_type: TokenType, secret: str) -> IssuedToken:
    now = utc_now()
    ttl = _TTL[token_type]
    claims = {
        "sub": str(user_id),
        "type": token_type,
        # Random, so two tokens issued in the same second still differ (rotation is visible).
        "jti": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + ttl,
    }
    return IssuedToken(jwt.encode(claims, secret, algorithm=ALGORITHM), int(ttl.total_seconds()))


def decode(token: str, expected_type: TokenType, secret: str) -> uuid.UUID:
    """The user id in a valid token of the expected type. Raises InvalidToken otherwise."""
    try:
        claims = jwt.decode(
            token, secret, algorithms=[ALGORITHM], options={"require": REQUIRED_CLAIMS}
        )
        if claims["type"] != expected_type:
            raise InvalidToken
        return uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError, TypeError) as error:
        raise InvalidToken from error
