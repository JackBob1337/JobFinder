from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.job_match_repository import JobMatchRepository
from app.schemas.job_match import JobMatchResult, MatchStatusEnum

@pytest.mark.asyncio
async def test_get_by_job_id_filters_by_foreign_key():
    session = MagicMock()
    session.execute = AsyncMock()

    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    repository = JobMatchRepository(session)

    await repository.get_by_job_id(42)

    statement = session.execute.call_args.args[0]
    sql = str(
        statement.compile(
            compile_kwargs={'literal_binds': True}
        )
    )

    assert 'job_matches.job_id = 42' in sql

@pytest.mark.asyncio 
async def test_save_persists_analysis_payload():
    session = MagicMock()
    session.commit = AsyncMock()

    repository = JobMatchRepository(session)

    result = JobMatchResult(
        job_id=1,
        relevance_score=0.8,
        reasoning="Strong match",
        status=MatchStatusEnum.APPROVED,
        analysis={
            "required_skills": ["Python", "FastAPI"],
        },
    )

    await repository.save(result)

    saved_match = session.add.call_args.args[0]

    assert saved_match.analysis == result.analysis