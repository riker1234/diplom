"""add citilink fields to all models

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-18
"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ('mice', 'keyboards', 'monitors', 'headphones', 'microphones', 'mousepads'):
        op.add_column(table, sa.Column('citilink_sku', sa.String(), nullable=True))
        op.add_column(table, sa.Column('citilink_url', sa.String(), nullable=True))
        op.add_column(table, sa.Column('citilink_price', sa.Float(), nullable=True))
        op.create_unique_constraint(f'uq_{table}_citilink_sku', table, ['citilink_sku'])


def downgrade() -> None:
    for table in ('mice', 'keyboards', 'monitors', 'headphones', 'microphones', 'mousepads'):
        op.drop_constraint(f'uq_{table}_citilink_sku', table, type_='unique')
        op.drop_column(table, 'citilink_price')
        op.drop_column(table, 'citilink_url')
        op.drop_column(table, 'citilink_sku')
