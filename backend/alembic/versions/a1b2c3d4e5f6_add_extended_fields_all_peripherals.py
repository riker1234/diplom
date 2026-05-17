"""add extended fields to all peripherals

Revision ID: a1b2c3d4e5f6
Revises: 9c0e7ecfa788
Create Date: 2026-05-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9c0e7ecfa788'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # keyboards
    op.add_column('keyboards', sa.Column('has_rgb', sa.Boolean(), nullable=True))
    op.add_column('keyboards', sa.Column('layout', sa.String(), nullable=True))
    op.add_column('keyboards', sa.Column('key_count', sa.Integer(), nullable=True))
    op.add_column('keyboards', sa.Column('color', sa.String(), nullable=True))

    # monitors
    op.add_column('monitors', sa.Column('response_time_ms', sa.Float(), nullable=True))
    op.add_column('monitors', sa.Column('brightness_nits', sa.Integer(), nullable=True))
    op.add_column('monitors', sa.Column('hdr', sa.Boolean(), nullable=True))
    op.add_column('monitors', sa.Column('color', sa.String(), nullable=True))

    # headphones
    op.add_column('headphones', sa.Column('frequency_response', sa.String(), nullable=True))
    op.add_column('headphones', sa.Column('impedance_ohm', sa.Integer(), nullable=True))
    op.add_column('headphones', sa.Column('color', sa.String(), nullable=True))
    op.add_column('headphones', sa.Column('has_rgb', sa.Boolean(), nullable=True))

    # microphones
    op.add_column('microphones', sa.Column('sample_rate', sa.String(), nullable=True))
    op.add_column('microphones', sa.Column('bit_depth', sa.String(), nullable=True))
    op.add_column('microphones', sa.Column('color', sa.String(), nullable=True))

    # mousepads
    op.add_column('mousepads', sa.Column('color', sa.String(), nullable=True))
    op.add_column('mousepads', sa.Column('thickness_mm', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('mousepads', 'thickness_mm')
    op.drop_column('mousepads', 'color')

    op.drop_column('microphones', 'color')
    op.drop_column('microphones', 'bit_depth')
    op.drop_column('microphones', 'sample_rate')

    op.drop_column('headphones', 'has_rgb')
    op.drop_column('headphones', 'color')
    op.drop_column('headphones', 'impedance_ohm')
    op.drop_column('headphones', 'frequency_response')

    op.drop_column('monitors', 'color')
    op.drop_column('monitors', 'hdr')
    op.drop_column('monitors', 'brightness_nits')
    op.drop_column('monitors', 'response_time_ms')

    op.drop_column('keyboards', 'color')
    op.drop_column('keyboards', 'key_count')
    op.drop_column('keyboards', 'layout')
    op.drop_column('keyboards', 'has_rgb')
