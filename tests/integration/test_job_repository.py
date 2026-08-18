import pytest
import pytest_asyncio
from pydantic import HttpUrl
from sqlalchemy import delete, select
from uuid import uuid4

from app.db.session import async_session_factory, engine
from app.db.job_repository import JobRepository
from app.models.job import Job
from app.schemas.raw_job import JobSourceEnum, RawJob


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



