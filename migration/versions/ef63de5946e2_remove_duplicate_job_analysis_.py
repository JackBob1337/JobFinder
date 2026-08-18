"""remove duplicate job analysis constraints 

Revision ID: ef63de5946e2
Revises: efac3ba1e1d4
Create Date: 2026-08-19 00:01:07.629000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'ef63de5946e2'
down_revision: Union[str, Sequence[str], None] = 'efac3ba1e1d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        'uq_job_analyses_job_id',
        'job_analyses',
        type_='unique',
    )

    op.drop_constraint(
        'fk_job_analyses_job_id',
        'job_analyses',
        type_='foreignkey'
    )


def downgrade() -> None:
    op.create_unique_constraint(
        'uq_job_analyses_job_id',
        'job_analyses',
        ['job_id'],
    )

    op.create_foreign_key(
        'fk_job_analyses_job_id',
        'job_analyses',
        'jobs',
        ['job_id'],
        ['id']
    )