import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock
from pydantic import HttpUrl
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError
from uuid import uuid4

from app.db.session import async_session_factory, engine
from app.db.job_repository import JobRepository
from app.models.job import Job
from app.schemas.raw_job import JobSourceEnum, RawJob

from app.db.job_match_repository import JobMatchRepository
from app.exceptions.exceptions import ForeignKeyViolationError, DatabaseUnavailableError
from app.schemas.job_match import JobMatchResult, MatchStatusEnum


@pytest_asyncio.fixture(autouse=True)
async def reset_database_engine():
    await engine.dispose()
    yield
    await engine.dispose()

def make_raw_job(**overrides):
    values = {
        "title": "Backend Developer",
        "company": "Test Company",
        "description": "Test job description",
        "url": HttpUrl(
            "https://example.com/jobs/{uuid64()}"
        ),
        "source": JobSourceEnum.NOFLUFFJOBS,
    }

    values.update(overrides)
    return RawJob(**values)

@pytest.mark.asyncio
async def test_saving_same_job_twice_does_not_create_duplicate():
    raw_job = make_raw_job()

    async with async_session_factory() as session:
        repository = JobRepository(session)

        first = await repository.save(raw_job)
        second = await repository.save(raw_job)

        assert first is not None
        assert second is None

        result = await session.execute(
            select(Job).where(
                Job.source == raw_job.source,
                Job.url == str(raw_job.url),
            )
        )

        jobs = list(result.scalars().all())

        assert len(jobs) == 1

        await session.execute(
            delete(Job).where(Job.id == first.id)
        )

        await session.commit()


@pytest.mark.asyncio
async def test_jobs_with_same_title_but_different_urls_are_not_duplicates():
    first_raw_job = make_raw_job(
        url=HttpUrl(
            "https://example.com/jobs/first"
        )
    )
    second_raw_job = make_raw_job(
        url=HttpUrl(
            "https://example.com/jobs/second"
        )
    )

    async with async_session_factory() as session:
        repository = JobRepository(session)

        first = await repository.save(first_raw_job)
        second = await repository.save(second_raw_job)

        assert first is not None
        assert second is not None

        await session.execute(
            delete(Job).where(
                Job.id.in_([first.id, second.id])
            )
        )

        await session.commit()


@pytest.mark.asyncio
async def test_job_match_with_invalid_job_id_raises_foreign_key_error():
    result = JobMatchResult(
        job_id=1_000_000_000,
        relevance_score=0.8,
        reasoning='Test reasoning',
        status=MatchStatusEnum.APPROVED
    )

    async with async_session_factory() as session:
        repository = JobMatchRepository(session)

        with pytest.raises(ForeignKeyViolationError):
            await repository.save(result)

@pytest.mark.asyncio
async def test_database_connection_error_is_not_returned_as_none():
    session = Mock(spec=AsyncSession)

    existing = Mock()
    existing.scalar_one_or_none.return_value = None
    
    session.execute = AsyncMock(return_value=existing)
    session.add = Mock()
    session.commit = AsyncMock(
        side_effect=OperationalError(
            'INSERT INTO jobs',
            {},
            OSError('connection refused'),
        )
    )
    session.rollback = AsyncMock()

    repository = JobRepository(session)

    with pytest.raises(DatabaseUnavailableError):
        await repository.save(make_raw_job())

    session.rollback.assert_awaited_once()