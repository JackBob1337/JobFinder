from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.dialects import postgresql

from app.db.job_repository import JobRepository


def make_session():
    session = Mock()

    scalars = Mock()
    scalars.all.return_value = []

    result = Mock()
    result.scalars.return_value = scalars

    session.execute = AsyncMock(return_value=result)

    return session


def compile_sql(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={
                'literal_binds': True
            }
        )
    )


@pytest.mark.asyncio
async def test_get_jobs_without_analysis_applies_limit():
    session = make_session()
    repository = JobRepository(session)

    await repository.get_jobs_without_analysis(limit=100)

    statement = session.execute.await_args.args[0]
    sql =  compile_sql(statement)

    assert 'LIMIT 100' in sql


@pytest.mark.asyncio
async def test_get_analyzed_but_unfiltered_jobs_applies_limit():
    session = make_session()
    repository = JobRepository(session)

    await repository.get_analyzed_but_unfiltered_jobs(limit=100)

    statement = session.execute.await_args.args[0]
    sql = compile_sql(statement)

    assert 'LIMIT 100' in sql

