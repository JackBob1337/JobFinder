from app.models.cv_version import CVVersion
from app.models.job_match import JobMatch, MatchStatusEnum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

class CVVersionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, job_id: int, file_path: str) -> CVVersion | None:
        cv_version = CVVersion(
            job_id=job_id,
            file_path=file_path
        )

        self.session.add(cv_version)
        try:
            await self.session.commit()
            return cv_version
        
        except IntegrityError:
            await self.session.rollback()
            return None

    async def get_by_job_id(self, job_id: int) -> CVVersion | None:
        result = await self.session.execute(
            select(CVVersion)
            .where(CVVersion.job_id == job_id)
        )

        return result.scalar_one_or_none()
    
    async def get_approved_jobs_without_cv(self) -> list[int]:
        cv_subquery = select(CVVersion.job_id)
        result = await self.session.execute(
            select(JobMatch.job_id)
            .where(JobMatch.status == MatchStatusEnum.APPROVED)
            .where(JobMatch.job_id.not_in(cv_subquery))
        )

        return list(result.scalars().all())
    
    
        