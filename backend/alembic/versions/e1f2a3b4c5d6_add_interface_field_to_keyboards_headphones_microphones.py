"""add interface field to keyboards headphones microphones

Revision ID: e1f2a3b4c5d6
Revises: 40506041e8c4
Create Date: 2026-05-29 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = '40506041e8c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('keyboards', sa.Column('interface', sa.String(), nullable=True))
    op.add_column('headphones', sa.Column('interface', sa.String(), nullable=True))
    op.add_column('microphones', sa.Column('interface', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('keyboards', 'interface')
    op.drop_column('headphones', 'interface')
    op.drop_column('microphones', 'interface')
