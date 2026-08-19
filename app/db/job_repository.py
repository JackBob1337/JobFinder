from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import (
    IntegrityError,
    DBAPIError,
    OperationalError
)
from app.exceptions.exceptions import (
    DatabaseUnavailableError,
    ForeignKeyViolationError
)


from app.models.job import Job
from app.schemas.raw_job import RawJob
from app.models.job_match import JobMatch
from app.models.job_analyses import JobAnalysis

class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, raw_job: RawJob) -> Job | None:
        try:
            existing = await self.session.execute(
                select(Job).where(
                    Job.source == raw_job.source,
                    Job.url == str(raw_job.url),
                )
            )

            if existing.scalar_one_or_none() is not None:
                return None
            
            job = Job(
                title=raw_job.title,
                company=raw_job.company,
                location=raw_job.location,
                is_remote=raw_job.is_remote,
                description=raw_job.description,
                url=str(raw_job.url),
                source=raw_job.source,
                job_types=raw_job.job_types,
                tags=raw_job.tags,
                published_at=raw_job.published_at,
            )

            self.session.add(job)           
            await self.session.commit()
            return job
        
        except IntegrityError as exc:
            await self.session.rollback()

            sqlstate = getattr(exc.orig, 'sqlstate', None)

            if sqlstate == '23505':
                return None

            if sqlstate == '23503':
                raise ForeignKeyViolationError(
                    'Job match references a non-existing job'
                ) from exc

            raise

        except OperationalError as exc:
            await self.session.rollback()
            raise DatabaseUnavailableError(
                'Database is unavailable'
            ) from exc

        except DBAPIError as exc:
            await self.session.rollback()

            if exc.connection_invalidated:
                raise DatabaseUnavailableError(
                    'Database connection was invalidated'
                ) from exc

            raise
        
    async def save_bulk(self, raw_jobs: list[RawJob]) -> int:
        saved_count = 0
        for raw_job in raw_jobs:
            result = await self.save(raw_job)
            if result is not None:
                saved_count += 1
        
        return saved_count
    
    async def get_all(self) -> list[Job]: 
        result = await self.session.execute(select(Job))
        
        return list(result.scalars().all())

    async def get_job_by_id(self, job_id: int) -> Job | None:
        result = await self.session.execute(
            select(Job).where(Job.id == job_id)
        )
        
        return result.scalar_one_or_none()
    
    async def get_unevaluated_jobs(self) -> list[Job]:
        subquery = select(JobMatch.job_id)
        result = await self.session.execute(
            select(Job).where(Job.id.not_in(subquery))
        )
        return list(result.scalars().all())

    async def get_jobs_without_analysis(
        self,
        limit: int | None = None
    ) -> list[Job]:
        subquery = select(JobAnalysis.job_id)
        query = (
            select(Job)
            .where(Job.id.not_in(subquery))
            .order_by(Job.id)
        )

        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)

        return list(result.scalars().all())
    
    async def get_latest_jobs(self, limit: int) -> list[Job]:
        result = await self.session.execute(
            select(Job).order_by(Job.id.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_analyzed_but_unfiltered_jobs(
        self,
        limit: int | None = None
    ) -> list[Job]:
        analyzed_subquery = select(JobAnalysis.job_id)
        matched_subquery = select(JobMatch.job_id)

        query = (
            select(Job)
            .where(Job.id.in_(analyzed_subquery))
            .where(Job.id.not_in(matched_subquery))
            .order_by(Job.id)
        )

        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)

        return list(result.scalars().all())

