"""rename partitions to chapters

Revision ID: d3e5f7a9b2c4
Revises: c2d4f6a8b0e1
Create Date: 2026-04-26 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'd3e5f7a9b2c4'
down_revision: Union[str, Sequence[str], None] = 'c2d4f6a8b0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('DROP TABLE IF EXISTS chapters')
    op.rename_table('partitions', 'chapters')
    op.alter_column('chapters', 'partition_number', new_column_name='chapter_number')
    op.execute('ALTER INDEX ix_partitions_book_id RENAME TO ix_chapters_book_id')
    op.alter_column('books', 'total_partitions', new_column_name='total_chapters')
    op.alter_column('books', 'current_partition', new_column_name='current_chapter')
    op.alter_column('books', 'reading_partition', new_column_name='reading_chapter')


def downgrade() -> None:
    op.alter_column('books', 'reading_chapter', new_column_name='reading_partition')
    op.alter_column('books', 'current_chapter', new_column_name='current_partition')
    op.alter_column('books', 'total_chapters', new_column_name='total_partitions')
    op.execute('ALTER INDEX ix_chapters_book_id RENAME TO ix_partitions_book_id')
    op.alter_column('chapters', 'chapter_number', new_column_name='partition_number')
    op.rename_table('chapters', 'partitions')
