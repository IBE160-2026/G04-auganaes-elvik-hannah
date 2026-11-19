"""tasks.requires_photo_evidence (Story 4.1, FR-18, AD-6)

Written by hand after the model change: one NOT NULL boolean with server default false, so every
existing Task starts without a requirement and no backfill is needed. Eligibility is not stored:
it is read from the catalog by key (domain/photo_evidence). A named CHECK keeps the one invariant
the catalog cannot: only a Must Task may require a photo.

Revision ID: d6f1b3a9c2e8
Revises: c4e8a2f6b1d7
Create Date: 2026-11-19 23:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d6f1b3a9c2e8"
down_revision: str | Sequence[str] | None = "c4e8a2f6b1d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("tasks") as batch:
        batch.add_column(
            sa.Column(
                "requires_photo_evidence", sa.Boolean(), server_default=sa.false(), nullable=False
            )
        )
        batch.create_check_constraint(
            "ck_tasks_photo_evidence_must", "NOT requires_photo_evidence OR classification = 'must'"
        )


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch:
        batch.drop_constraint("ck_tasks_photo_evidence_must", type_="check")
        batch.drop_column("requires_photo_evidence")
