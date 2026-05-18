"""add wb fields to all models

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-18
"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    for table in ("mice", "keyboards", "monitors", "headphones", "microphones", "mousepads"):
        op.add_column(table, sa.Column('wb_sku', sa.String(), nullable=True))
        op.add_column(table, sa.Column('wb_url', sa.String(), nullable=True))
        op.add_column(table, sa.Column('wb_price', sa.Float(), nullable=True))
        op.create_unique_constraint(f'uq_{table}_wb_sku', table, ['wb_sku'])


def downgrade():
    for table in ("mice", "keyboards", "monitors", "headphones", "microphones", "mousepads"):
        op.drop_constraint(f'uq_{table}_wb_sku', table, type_='unique')
        op.drop_column(table, 'wb_price')
        op.drop_column(table, 'wb_url')
        op.drop_column(table, 'wb_sku')
