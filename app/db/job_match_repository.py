from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.job_match import JobMatchResult
from app.models.job_match import JobMatch

from sqlalchemy.exc import IntegrityError


class JobMatchRepository():
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, result: JobMatchResult) -> JobMatch | None:

        match = JobMatch(
            job_id=result.job_id,
            relevance_score=result.relevance_score,
            reasoning=result.reasoning,
            status=result.status,
            analysis=result.analysis,
        )
        self.session.add(match)
        try:
            await self.session.commit()
            return match

        except IntegrityError:
            await self.session.rollback()
            return None

    async def get_by_job_id(self, job_id: int) -> JobMatch | None:
        result = await self.session.execute(
            select(JobMatch)
            .where(JobMatch.job_id == job_id)
        ) 

        return result.scalar_one_or_none()
        


    
