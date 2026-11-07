"""The example Household Home for Mari and Jonas (Story 1.3, FR-22). Listed in the README.

Mari creates it and Jonas joins it, both through domain/homes.py. Each is checked on its own,
so a run that stopped halfway is completed next time. Never deletes or overwrites.
"""

from sqlmodel import Session, select

from app.domain import homes
from app.models.home import HOME_TYPES
from app.models.membership import Membership
from app.models.user import User
from app.seed.users import EXAMPLE_USERS

EXAMPLE_HOME_NAME = "Mari og Jonas sitt hjem"
CREATOR_EMAIL = EXAMPLE_USERS[0].email  # Mari
JOINER_EMAIL = EXAMPLE_USERS[1].email  # Jonas


def _user(session: Session, email: str) -> User:
    return session.exec(select(User).where(User.email == email)).one()


def seed_homes(session: Session) -> None:
    mari = _user(session, CREATOR_EMAIL)
    jonas = _user(session, JOINER_EMAIL)

    home = next(
        (h.home for h in homes.homes_for(session, mari) if h.home.name == EXAMPLE_HOME_NAME),
        None,
    )
    if home is not None:
        print(f"Hjemmet «{EXAMPLE_HOME_NAME}» finnes allerede")
    elif homes.allowed_types(session, mari) != list(HOME_TYPES):
        print(f"Hoppet over «{EXAMPLE_HOME_NAME}»: {CREATOR_EMAIL} er allerede med i et annet hjem")
        return
    else:
        home = homes.create_home(session, mari, name=EXAMPLE_HOME_NAME, type="household").home
        print(f"Opprettet hjemmet «{EXAMPLE_HOME_NAME}» med {CREATOR_EMAIL}")

    jonas_homes = session.exec(select(Membership.home_id).where(Membership.user_id == jonas.id))
    jonas_home_ids = set(jonas_homes.all())
    if home.id in jonas_home_ids:
        print(f"{JOINER_EMAIL} er allerede med i «{EXAMPLE_HOME_NAME}»")
    elif jonas_home_ids:
        print(f"Hoppet over {JOINER_EMAIL}: er allerede med i et annet hjem")
    else:
        homes.add_member(session, home, jonas)
        print(f"La til {JOINER_EMAIL} i «{EXAMPLE_HOME_NAME}»")
