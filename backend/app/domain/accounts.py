"""Registration and credential checks (Story 1.2, FR-1). Routes stay thin and call these."""

from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.user import User

# Argon2id with pwdlib's recommended parameters.
password_hash = PasswordHash.recommended()

# Verified against when the email is unknown, so a failed login takes as long either way.
_DUMMY_HASH = password_hash.hash("husly-dummy-password")


class EmailTaken(Exception):
    """An account with this email already exists."""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register(session: Session, *, email: str, name: str, password: str) -> User:
    """Create a user. Raises EmailTaken on a duplicate, also when two requests race."""
    user = User(
        email=normalize_email(email),
        name=name.strip(),
        password_hash=password_hash.hash(password),
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise EmailTaken from None
    session.refresh(user)
    return user


def authenticate(session: Session, *, email: str, password: str) -> User | None:
    """The user if the credentials match, otherwise None. Always runs one hash check."""
    user = session.exec(select(User).where(User.email == normalize_email(email))).first()
    if user is None:
        password_hash.verify(password, _DUMMY_HASH)
        return None
    if not password_hash.verify(password, user.password_hash):
        return None
    return user
