"""sync schema with models: add keyboard_type to keyboards

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-06-02 00:00:00.000000

Idempotent: the column was previously added to live databases via a backfill
script outside Alembic, so this migration only adds it where it is missing.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    insp = inspect(op.get_bind())
    return column in [c['name'] for c in insp.get_columns(table)]


def upgrade() -> None:
    if not _has_column('keyboards', 'keyboard_type'):
        op.add_column('keyboards', sa.Column('keyboard_type', sa.String(), nullable=True))


def downgrade() -> None:
    if _has_column('keyboards', 'keyboard_type'):
        op.drop_column('keyboards', 'keyboard_type')
