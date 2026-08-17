"""add justjoinit to jobsource enum

Revision ID: d26154dbbe46
Revises: b6488b38fe84
Create Date: 2026-07-15 23:00:29.484785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd26154dbbe46'
down_revision: Union[str, Sequence[str], None] = 'b6488b38fe84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE jobsource ADD VALUE 'JUSTJOINIT'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
