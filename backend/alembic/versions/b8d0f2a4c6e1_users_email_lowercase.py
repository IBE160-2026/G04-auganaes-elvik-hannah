"""users.email is lowercase in the database (deferred from Story 1.2)

Written by hand after the model: a CHECK so the database, not only `accounts.normalize_email`,
keeps e-mail addresses lowercase. Every address is stored lowercased by `accounts.register`, so
existing rows satisfy it.

Revision ID: b8d0f2a4c6e1
Revises: a7c9e1b3d5f2
Create Date: 2026-11-21 22:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "b8d0f2a4c6e1"
down_revision: str | Sequence[str] | None = "a7c9e1b3d5f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint("ck_users_email_lowercase", "users", "email = lower(email)")


def downgrade() -> None:
    op.drop_constraint("ck_users_email_lowercase", "users", type_="check")
