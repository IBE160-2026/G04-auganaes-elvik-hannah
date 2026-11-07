"""Example users for local running (Story 1.6, FR-22). Credentials are listed in the README.

Stories 1.4–1.5 add a Landlord and a Tenant here. Later steps look users up by email.
"""

from typing import NamedTuple

from sqlmodel import Session

from app.domain.accounts import EmailTaken, register

EXAMPLE_PASSWORD = "husly-demo"


class ExampleUser(NamedTuple):
    email: str
    name: str


# Emails already lowercase, the way accounts.normalize_email stores them.
EXAMPLE_USERS = (
    ExampleUser("mari@example.com", "Mari Nordmann"),
    ExampleUser("jonas@example.com", "Jonas Berg"),
)


def seed_users(session: Session) -> None:
    """Register each example user through accounts.register; skip those that exist."""
    for user in EXAMPLE_USERS:
        try:
            register(session, email=user.email, name=user.name, password=EXAMPLE_PASSWORD)
        except EmailTaken:
            print(f"Bruker {user.email} finnes allerede")
        else:
            print(f"Opprettet bruker {user.email} ({user.name})")
