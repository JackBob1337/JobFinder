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
from app.schemas.results import (
    ResultError,
    ServiceResult,
    PipelineResult,
)

from app.core.logger import logger

class JobProcessingService:
    ANALYZE_CONCURRENCY = 5
    FILTER_CONCURRENCY = 5
    ANALYSIS_BATCH_SIZE = 100
    FILTER_BATCH_SIZE = 100

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

    @staticmethod
    def _build_analysis_result(analyzed_job) -> JobAnalysisResult:
        return JobAnalysisResult(
            required_skills=analyzed_job.required_skills,
            preferred_skills=analyzed_job.preferred_skills,
            responsibilities=analyzed_job.responsibilities,
            soft_skills=analyzed_job.raw_json.get(
                "soft_skills",
                [],
            ),
            ats_keywords=analyzed_job.ats_keywords,
            seniority=analyzed_job.seniority,
            min_years_experience=analyzed_job.min_years_experience,
        )

    async def _fetch_from_source(self, source) -> list[RawJob]:
        try:
            return await source.fetch_jobs()
        except SourceFetchException:
            logger.exception('Source fetch failed')
            return []

    async def _save_jobs(self, source_name: str, raw_jobs: list[RawJob]) -> ServiceResult:
        if not raw_jobs:
            return ServiceResult(
                total=0,
                succeeded=0,
                skipped=0,
                failed=0,
                errors=[],
            )

        try:
            async with self.session_factory() as session:
                job_repo = JobRepository(session)
                repository_result = await job_repo.save_bulk(raw_jobs)
                return ServiceResult(
                    total=repository_result.total,
                    succeeded=repository_result.succeeded,
                    skipped=repository_result.skipped,
                    failed=repository_result.failed,
                    errors=repository_result.errors,
                )

        except DatabaseConnectionError:
            logger.critical("Database unreachable, aborting scrape")
            raise

        except RepositoryError as exc:
            logger.exception(
                "Failed to save jobs from %s",
                source_name,
            )

            errors = [
                ResultError(
                    item_id=str(raw_job.url),
                    message=str(exc),
                )
                for raw_job in raw_jobs
            ]

            return ServiceResult(
                total=len(raw_jobs),
                succeeded=0,
                skipped=0,
                failed=len(raw_jobs),
                errors=errors,
            )

    async def _process_source(self, source) -> ServiceResult:
        raw_jobs = await self._fetch_from_source(source)
        return await self._save_jobs(getattr(source, 'name', repr(source)), raw_jobs)

    async def _analyze_job(
            self, 
            job: Job, 
            semaphore: asyncio.Semaphore,
    ) -> tuple[bool, ResultError | None]:
        async with semaphore:
            async with self.session_factory() as session:
                job_repo = JobRepository(session)
                analysis_repo = JobAnalysisRepository(session)

                job_for_analysis = await job_repo.get_job_by_id(job.id)

                if job_for_analysis is None:
                    logger.exception(
                        "[analyze] Job %s is not found",
                        job.title,
                    )

                    return (
                        False,
                        ResultError(
                            item_id=str(job.id),
                            message='Job not found',
                        )
                    )

                try:
                    result = await self.analysis_agent.analyze(job)
                    await analysis_repo.save(job.id, result, raw_json=result.model_dump())
                    logger.info("[analyze] OK: %s", job.title)
                    return True, None
                
                except Exception as exc:
                    logger.exception("[analyze] Failed: %s", job.title)
                    return (
                        False,
                        ResultError(
                            item_id=str(job.id),
                            message=str(exc),
                        )
                    )

    async def _evaluate_and_save_match(
            self, 
            job: Job,
            analysis: JobAnalysisResult,
            match_repo: JobMatchRepository,
    ) -> tuple[bool, ResultError | None]:
        try:
            result = await self.filter_agent.evaluate(job, analysis)
            saved_match = await match_repo.save(result)

            if saved_match is None:
                logger.warning(
                    "[filter] Analysis not found for job %s",
                    job.id,
                )
                return (
                    False,
                    ResultError(
                        item_id=str(job.id),
                        message="Match was not saved"
                    )
                )
            
            logger.info(f"[filter] {job.title}: {result.status} (score: {result.relevance_score})")
            return True, None

        except DatabaseConnectionError:
            raise

        except FilterError as exc:
            logger.error(
                "[filter] %s error: %s",
                job.title,
                exc,
            )

            return (
                False,
                ResultError(
                    item_id=str(job.id),
                    message=str(exc),
                ),
            )

        except Exception as exc:
            logger.exception(
                '[filter] Unexpected error for %s',
                job.title
            )

            return (
                False,
                ResultError(
                    item_id=str(job.id),
                    message=str(exc),
                ),
            )
           
    async def _filter_one_job(
        self, 
        job: Job, 
        semaphore: asyncio.Semaphore,
    ) -> tuple[bool, ResultError | None]:
        async with semaphore:
            async with self.session_factory() as session:
                analysis_repo = JobAnalysisRepository(session)
                match_repo = JobMatchRepository(session)

                analyzed_job = await analysis_repo.get_by_job_id(job.id)

                if analyzed_job is None:
                    logger.warning(f"'[filter] Not analysis for '{job.title}'")
                    return (
                        False,
                        ResultError(
                            item_id=str(job.id),
                            message="Analysis not found",
                        ),
                    )

                analysis = self._build_analysis_result(analyzed_job)

                return await self._evaluate_and_save_match(
                    job,
                    analysis,
                    match_repo,
                )

    async def scrape_and_save(self) -> ServiceResult:
        results =  await asyncio.gather(
            *(
                self._process_source(source)
                for source in self.sources
            )
        )

        return ServiceResult(
            total=sum(result.total for result in results),
            succeeded=sum(
                result.succeeded
                for result in results
            ),
            skipped=sum(
                result.skipped
                for result in results
            ),
            failed=sum(
                result.failed
                for result in results
            ),
            errors=[
                error
                for result in results
                for error in result.errors
            ],
        )
    
    async def analyze_new_jobs(self) -> ServiceResult:
        async with self.session_factory() as session:
            job_repo = JobRepository(session)
            jobs = await job_repo.get_jobs_without_analysis(
                limit=self.ANALYSIS_BATCH_SIZE
            )
        
        logger.info(f'[analyze] Found {len(jobs)} jobs without analyze')

        semaphore = asyncio.Semaphore(self.ANALYZE_CONCURRENCY)
        tasks = [self._analyze_job(job, semaphore) for job in jobs]
        outcomes = await asyncio.gather(*tasks)

        success_count = sum(
            success for success, error in outcomes
        )

        errors = [
            error
            for success, error in outcomes
            if error is not None
        ]

        return ServiceResult(
            total=len(jobs),
            succeeded=success_count,
            failed=len(errors),
            errors=errors,
        )
    
    async def filter_analyzed_jobs(self) -> ServiceResult:
        async with self.session_factory() as session:
            job_repo = JobRepository(session)
            jobs = await job_repo.get_analyzed_but_unfiltered_jobs(
                limit=self.FILTER_BATCH_SIZE
            )
        
        logger.info(f'[filter] Found {len(jobs)} vacancies')

        semaphore = asyncio.Semaphore(self.FILTER_CONCURRENCY)
        tasks = [
            self._filter_one_job(job, semaphore) 
            for job in jobs
        ]

        outcomes = await asyncio.gather(*tasks)

        success_count = sum(
            success
            for success, error in outcomes
        )

        errors = [
            error
            for success, error in outcomes
            if error is not None
        ]

        return ServiceResult(
            total=len(jobs),
            succeeded=success_count,
            failed=len(errors),
            errors=errors,
        )
        
   
    async def run_full_cycle(self) -> PipelineResult:
        logger.info("=== Starting full pipeline cycle ===")

        try:
            scraped = await self.scrape_and_save()

        except DatabaseConnectionError:
            logger.critical(
                'Database unreachable during scrape'
            )
            raise
       
        analyzed = await self.analyze_new_jobs()
        filtered = await self.filter_analyzed_jobs()

        logger.info(f'=== Pipeline cycle finished ===')

        return PipelineResult(
            scrapped=scraped,
            analyzed=analyzed,
            filtered=filtered
        )

        

    
        