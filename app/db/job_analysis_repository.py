from app.models.job_analyses import JobAnalysis
from app.models.job import Job
from app.models.job_match import JobMatch
from app.schemas.job_analyses import JobAnalysisResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select


class JobAnalysisRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, job_id: int, result: JobAnalysisResult, raw_json: dict) -> JobAnalysis | None:
        analysis = JobAnalysis(
            job_id=job_id,
            required_skills=result.required_skills,
            preferred_skills=result.preferred_skills,
            seniority=result.seniority,
            min_years_experience=result.min_years_experience,
            responsibilities=result.responsibilities,
            ats_keywords=result.ats_keywords,
            raw_json=raw_json,
        )
        self.session.add(analysis)
        try:
            await self.session.commit()
            return analysis
        
        except IntegrityError:
            await self.session.rollback()
            return None
        
    async def get_by_job_id(self, job_id: int) -> JobAnalysis | None:
        result = await self.session.execute(
            select(JobAnalysis).where(JobAnalysis.job_id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_jobs_without_analysis(self) -> list[Job]:
        subquery = select(JobAnalysis.job_id)
        result = await self.session.execute(
            select(Job).where(Job.id.not_in(subquery))
        )

        return list(result.scalars().all())


    