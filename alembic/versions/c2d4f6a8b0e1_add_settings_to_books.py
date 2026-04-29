"""add settings to books

Revision ID: c2d4f6a8b0e1
Revises: aebc36cf515f
Create Date: 2026-04-26 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c2d4f6a8b0e1"
down_revision: str | Sequence[str] | None = "aebc36cf515f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "books",
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("books", "settings")
