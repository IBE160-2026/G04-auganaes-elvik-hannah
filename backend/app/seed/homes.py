"""The example Homes (Story 1.3 and 1.4, FR-22). Listed in the README.

Mari creates a Household Home and Jonas joins it. Kari creates a Landlord Home and Anders joins
it as a Tenant through an invite link, the way a real user would. All through the domain
services. Each row is checked on its own, so a run that stopped halfway is completed next
time. Never deletes or overwrites.
"""

from sqlmodel import Session, select

from app.domain import homes, invites
from app.models.home import Home
from app.models.membership import Membership
from app.models.user import User
from app.seed.users import EXAMPLE_USERS

EXAMPLE_HOME_NAME = "Mari og Jonas sitt hjem"
CREATOR_EMAIL = EXAMPLE_USERS[0].email  # Mari
JOINER_EMAIL = EXAMPLE_USERS[1].email  # Jonas

LANDLORD_HOME_NAME = "Storgata 12"
LANDLORD_EMAIL = EXAMPLE_USERS[2].email  # Kari
TENANT_EMAIL = EXAMPLE_USERS[3].email  # Anders


def _user(session: Session, email: str) -> User:
    return session.exec(select(User).where(User.email == email)).one()


def _own_home(session: Session, user: User, name: str) -> Home | None:
    return next((h.home for h in homes.homes_for(session, user) if h.home.name == name), None)


def _seed_household(session: Session) -> None:
    mari = _user(session, CREATOR_EMAIL)
    jonas = _user(session, JOINER_EMAIL)

    home = _own_home(session, mari, EXAMPLE_HOME_NAME)
    if home is not None:
        print(f"Hjemmet «{EXAMPLE_HOME_NAME}» finnes allerede")
    elif "household" not in homes.allowed_types(session, mari):
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


def _seed_landlord(session: Session) -> None:
    kari = _user(session, LANDLORD_EMAIL)
    anders = _user(session, TENANT_EMAIL)

    home = _own_home(session, kari, LANDLORD_HOME_NAME)
    if home is not None:
        print(f"Hjemmet «{LANDLORD_HOME_NAME}» finnes allerede")
    else:
        # Story 1.9: a Landlord Home may always be created.
        home = homes.create_home(session, kari, name=LANDLORD_HOME_NAME, type="landlord").home
        print(f"Opprettet hjemmet «{LANDLORD_HOME_NAME}» med {LANDLORD_EMAIL}")

    # Checked first, so an invite link is created only when Anders will be added.
    blocker = homes.join_blocker(session, home, anders)
    if isinstance(blocker, homes.AlreadyMember):
        print(f"{TENANT_EMAIL} er allerede med i «{LANDLORD_HOME_NAME}»")
        return
    if isinstance(blocker, homes.InOtherHome):
        print(f"Hoppet over {TENANT_EMAIL}: er allerede med i «{blocker.home.name}»")
        return
    inviter = session.exec(
        select(Membership).where(Membership.user_id == kari.id, Membership.home_id == home.id)
    ).one()
    created = invites.create_invite(session, inviter)
    try:
        invites.accept(session, created.token, anders)
    except (homes.AlreadyMember, homes.InOtherHome) as exc:
        print(f"Hoppet over {TENANT_EMAIL}: er allerede med i «{exc.home.name}»")
        return
    print(f"La til {TENANT_EMAIL} i «{LANDLORD_HOME_NAME}» gjennom en invitasjonslenke")


def seed_homes(session: Session) -> None:
    _seed_household(session)
    _seed_landlord(session)
