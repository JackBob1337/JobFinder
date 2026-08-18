"""use source and url as job identity

Revision ID: 8708405d7d0d
Revises: ef63de5946e2
Create Date: 2026-08-19 00:09:09.745988

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '8708405d7d0d'
down_revision: Union[str, Sequence[str], None] = 'ef63de5946e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        'jobs_url_key',
        'jobs',
        type_='unique',
    )

    op.create_unique_constraint(
        'uq_jobs_source_url',
        'jobs',
        ['source', 'url'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_jobs_source_url',
        'jobs',
        type_='unique',
    )

    op.create_unique_constraint(
        'jobs_url_key',
        'jobs',
        ['url'],
    )