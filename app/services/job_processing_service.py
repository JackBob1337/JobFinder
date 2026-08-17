import asyncio
from collections.abc import Callable
from sqlalchemy.ext.asyncio import AsyncSession

from app.sources.base import JobSource
from app.schemas.raw_job import RawJob
from app.schemas.job_analyses import JobAnalysisResult
from app.models.job import Job
from app.db.job_repository import JobRepository
from app.db.job_analysis_repository import JobAnalysisRepository
from app.db.job_match_repository import JobMatchRepository
from app.agents.analysis_agent import AnalysisAgent
from app.agents.filter_agent import FilterAgent

from app.exceptions.exceptions import (
    SourceFetchException,
    DatabaseConnectionError,
    RepositoryError,
    FilterError
)

from app.core.logger import logger

class JobProcessingService:
    ANALYZE_CONCURRENCY = 5
    FILTER_CONCURRENCY = 5

    def __init__(
        self,
        sources: list[JobSource],
        session_factory: Callable[[], AsyncSession],
        analysis_agent: AnalysisAgent,
        filter_agent: FilterAgent,
    ) -> None:
        self.sources = sources
        self.session_factory = session_factory
        self.analysis_agent = analysis_agent
        self.filter_agent = filter_agent

    async def _fetch_from_source(self, source) -> list[RawJob]:
        try:
            return await source.fetch_jobs()
        except SourceFetchException:
            logger.exception('Source fetch failed')
            return []

    async def _save_jobs(self, source_name: str, raw_jobs: list[RawJob]) -> int:
        if not raw_jobs:
            return 0

        try:
            async with self.session_factory() as session:
                job_repo = JobRepository(session)
                return await job_repo.save_bulk(raw_jobs)

        except DatabaseConnectionError:
            logger.critical("Database unreachable, aborting scrape")
            raise

        except RepositoryError:
            logger.exception("Failed to save jobs from %s", source_name)
            return 0

    async def _process_source(self, source) -> int:
        raw_jobs = await self._fetch_from_source(source)
        return await self._save_jobs(getattr(source, 'name', repr(source)), raw_jobs)

    async def _analyze_job(self, job: Job, semaphore: asyncio.Semaphore,) -> bool:
        async with semaphore:
            async with self.session_factory() as session:
                job_repo = JobRepository(session)
                analysis_repo = JobAnalysisRepository(session)

                job_for_analysis = await job_repo.get_job_by_id(job.id)

                if job_for_analysis is None:
                    logger.warning(f"[analyze] Job {job.id} is not found")

                try:
                    result = await self.analysis_agent.analyze(job)
                    await analysis_repo.save(job.id, result, raw_json=result.model_dump())
                    logger.info("[analyze] OK: %s", job.title)
                    return True
                
                except Exception:
                    logger.exception("[analyze] Failed: %s", job.title)
                    return False
            
    async def _filter_one_job(self, job: Job, semaphore: asyncio.Semaphore) -> bool:

        async with semaphore:
            async with self.session_factory() as session:
                analysis_repo = JobAnalysisRepository(session)
                match_repo = JobMatchRepository(session)

                analyzed_job = await analysis_repo.get_by_job_id(job.id)

                if analyzed_job is None:
                    logger.warning(f"'[filter] Not analysis for '{job.title}'")
                    return False

                analysis = JobAnalysisResult(
                    required_skills=analyzed_job.required_skills,
                    preferred_skills=analyzed_job.preferred_skills,
                    responsibilities=analyzed_job.responsibilities,
                    soft_skills=analyzed_job.raw_json.get('soft_skills', []),
                    ats_keywords=analyzed_job.ats_keywords,
                    seniority=analyzed_job.seniority,
                    min_years_experience=analyzed_job.min_years_experience
                )

                try:
                    result = await self.filter_agent.evaluate(job, analysis)
                    await match_repo.save(result)
                    logger.info(f"[filter] {job.title}: {result.status} (score: {result.relevance_score})")
                    return True
                
                except FilterError as e:
                    logger.error(f'[filter] {job.title} error: {e}')
                    return False

    async def scrape_and_save(self) -> int:
        results =  await asyncio.gather(
            *(self._process_source(source) for source in self.sources)
        )

        total_saved = 0
        for result in results:
            if isinstance(result, DatabaseConnectionError):
                raise result
            
            total_saved += result
        return total_saved
    
    async def analyze_new_jobs(self) -> dict:
        async with self.session_factory() as session:
            job_repo = JobRepository(session)
            jobs = await job_repo.get_jobs_without_analysis()
        
        logger.info(f'[analyze] Found {len(jobs)} jobs without analyze')

        semaphore = asyncio.Semaphore(self.ANALYZE_CONCURRENCY)
        tasks = [self._analyze_job(job, semaphore) for job in jobs]
        result = await asyncio.gather(*tasks)
        success_count = sum(result)

        logger.info(f"[analyze] Done: {success_count} из {len(jobs)}")
        return {"total": len(jobs), "success": success_count}

    async def filter_analyzed_jobs(self):
        async with self.session_factory() as session:
            job_repo = JobRepository(session)
            jobs = await job_repo.get_analyzed_but_unfiltered_jobs()
        
        logger.info(f'[filter] Found {len(jobs)} vacancies')

        semaphore = asyncio.Semaphore(self.FILTER_CONCURRENCY)
        tasks = [self._filter_one_job(job, semaphore) for job in jobs]
        result = await asyncio.gather(*tasks)
        success_count = sum(result)

        logger.info(f"[filter] Done: {success_count} из {len(jobs)}")
        return {"total": len(jobs), "success": success_count}
   
    async def run_full_cycle(self) -> dict:
        logger.info("=== Starting full pipeline cycle ===")

        scraped = 0
        try:
            scraped = await self.scrape_and_save()

        except DatabaseConnectionError:
            logger.critical('Database unreachable during scrape, continuing with existing jobs')
       
        total_analyzed = await self.analyze_new_jobs()
        total_filtered = await self.filter_analyzed_jobs()

        logger.info(f'=== Pipeline cycle finished ===')

        return {
            'scraped': scraped,
            'analyzed': total_analyzed,
            'filtered': total_filtered 
        }

    
        