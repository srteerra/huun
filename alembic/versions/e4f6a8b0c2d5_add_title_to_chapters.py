"""add title to chapters

Revision ID: e4f6a8b0c2d5
Revises: d3e5f7a9b2c4
Create Date: 2026-04-26 23:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e4f6a8b0c2d5'
down_revision: Union[str, Sequence[str], None] = 'd3e5f7a9b2c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chapters', sa.Column('title', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('chapters', 'title')
