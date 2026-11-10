"""Refusal messages shared by creating Homes and joining them (Story 1.4, Story 1.9).

In their own module so routes/homes and routes/invites can both import them without a cycle.
"""


def already_member_message(home_name: str) -> str:
    return f"Du er allerede med i «{home_name}»."


def in_other_home_message(home_name: str) -> str:
    return f"Du er allerede med i «{home_name}». Du kan bare være med i ett hjem om gangen."
