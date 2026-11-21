"""users.deleted_at (Story 1.10, FR-25, AD-17)

Written by hand after the model: a nullable time set when an account is deleted. The user row is
anonymised and kept, so no foreign key changes and no ondelete is needed.

Revision ID: a7c9e1b3d5f2
Revises: f1a3c5e7b9d2
Create Date: 2026-11-21 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7c9e1b3d5f2"
down_revision: str | Sequence[str] | None = "f1a3c5e7b9d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "deleted_at")
