"""add nofluffjobs to jobsource enum

Revision ID: efac3ba1e1d4
Revises: 6764f24c8c0f
Create Date: 2026-08-18 23:53:36.869943

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efac3ba1e1d4'
down_revision: Union[str, Sequence[str], None] = '6764f24c8c0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TYPE jobsource ADD VALUE IF NOT EXISTS 'NOFLUFFJOBS'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
