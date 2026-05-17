"""add dns fields to all models

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ('mice', 'keyboards', 'monitors', 'headphones', 'microphones', 'mousepads'):
        op.add_column(table, sa.Column('dns_sku', sa.String(), nullable=True))
        op.add_column(table, sa.Column('dns_url', sa.String(), nullable=True))
        op.add_column(table, sa.Column('dns_price', sa.Float(), nullable=True))
        op.create_unique_constraint(f'uq_{table}_dns_sku', table, ['dns_sku'])


def downgrade() -> None:
    for table in ('mice', 'keyboards', 'monitors', 'headphones', 'microphones', 'mousepads'):
        op.drop_constraint(f'uq_{table}_dns_sku', table, type_='unique')
        op.drop_column(table, 'dns_price')
        op.drop_column(table, 'dns_url')
        op.drop_column(table, 'dns_sku')
