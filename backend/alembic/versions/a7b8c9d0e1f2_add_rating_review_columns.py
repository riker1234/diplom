"""add per-source rating + review_count columns

Revision ID: a7b8c9d0e1f2
Revises: f2a3b4c5d6e7
Create Date: 2026-06-03 00:00:00.000000

Idempotent: adds ozon/citilink/wb rating + reviews to every product table only
where missing, so it is safe on fresh, local and prod databases.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ["mice", "keyboards", "monitors", "headphones", "microphones", "mousepads"]
_COLUMNS = [
    ("ozon_rating", sa.Float),
    ("ozon_reviews", sa.Integer),
    ("citilink_rating", sa.Float),
    ("citilink_reviews", sa.Integer),
    ("wb_rating", sa.Float),
    ("wb_reviews", sa.Integer),
]


def _existing(table: str) -> set[str]:
    insp = inspect(op.get_bind())
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    for table in _TABLES:
        have = _existing(table)
        for name, coltype in _COLUMNS:
            if name not in have:
                op.add_column(table, sa.Column(name, coltype(), nullable=True))


def downgrade() -> None:
    for table in _TABLES:
        have = _existing(table)
        for name, _ in _COLUMNS:
            if name in have:
                op.drop_column(table, name)
