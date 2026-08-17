from collections.abc import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.tailor_agent import TailorAgent
from pathlib import Path
from app.db.job_repository import JobRepository
from app.db.job_analysis_repository import JobAnalysisRepository
from app.db.cv_version_repository import CVVersionRepository
from app.db.job_match_repository import JobMatchRepository
from app.schemas.job_analyses import JobAnalysisResult
from app.schemas.tailor_context import TailorJob, TailorContext

from app.core.logger import logger

class CVTailorService:
    def __init__(
            self, 
            session_factory: Callable[[], AsyncSession],
            tailor_agent_factory: Callable[[], TailorAgent],
            output_dir: Path
        ):
            self.session_factory = session_factory
            self.tailor_agent_factory = tailor_agent_factory
            self.output_dir = output_dir

    async def _get_tailor_context(self, job_id: int) -> TailorContext | None:
         async with self.session_factory() as session:
            job_repo = JobRepository(session)
            analysis_repo = JobAnalysisRepository(session)
            match_repo = JobMatchRepository(session)

            job = await job_repo.get_job_by_id(job_id)

            if job is None:
                logger.warning(f'[tailor] Job {job_id} didn`t find')
                return None

            analyzed_job = await analysis_repo.get_by_job_id(job_id)

            if analyzed_job is None:
                logger.warning(f'[tailor] Job {job_id} is not analyzed')
                return None

            analysis = JobAnalysisResult(
                required_skills=analyzed_job.required_skills,
                preferred_skills=analyzed_job.preferred_skills,
                responsibilities=analyzed_job.responsibilities,
                soft_skills=analyzed_job.raw_json.get('soft_skills', []),
                ats_keywords=analyzed_job.ats_keywords,
                seniority=analyzed_job.seniority,
                min_years_experience=analyzed_job.min_years_experience,
            )

            matched = await match_repo.get_by_job_id(job_id)

            if matched is None:
                logger.warning(f'[tailor] Didn`t find match for job {job_id}')
                return None

            return TailorContext(
                job=TailorJob(
                    id=job.id,
                    title=job.title,
                    company=job.company,
                    description=job.description
                ),
                analysis=analysis,
                match_reasoning=matched.reasoning
            )                

    async def _tailor_one_job(self, job_id: int) -> bool:
        context = await self._get_tailor_context(job_id)

        if context is None:
            return False

        try:
            tailor_agent = self.tailor_agent_factory()

            # --- Summary ---
            new_summary = await tailor_agent.tailor_summary(
                job_title=context.job.title,
                analysis=context.analysis,
                match_reasoning=context.match_reasoning,
            )
            tailor_agent.parser.rewrite_summary(new_summary)

            # --- Experience ---
            experience = tailor_agent.parser.get_experience("PROFESSIONAL EXPERIENCE")

            if experience.bullets:
                new_experience_bullets = await tailor_agent.tailor_bullets(
                    experience=experience,
                    job_title=context.job.title,
                    analysis=context.analysis,
                )
                tailor_agent.parser.rewrite_bullets(
                    new_experience_bullets,
                    "PROFESSIONAL EXPERIENCE",
                )

            # --- Projects ---
            projects = tailor_agent.parser.get_experience("PROJECTS")

            if projects.bullets:
                new_project_bullets = await tailor_agent.tailor_bullets(
                    experience=projects,
                    job_title=context.job.title,
                    analysis=context.analysis,
                )
                tailor_agent.parser.rewrite_bullets(
                    new_project_bullets,
                    "PROJECTS",
                )

            # --- Save ---
            output_path = self.output_dir / f"cv_{job_id}_{context.job.company}.docx"
            tailor_agent.parser.save(output_path)

            async with self.session_factory() as session:
                cv_version_repo = CVVersionRepository(session)
                await cv_version_repo.save(job_id, str(output_path))

            logger.info(f"[tailor] CV ready: {context.job.title} → {output_path}")
            return True

        except Exception:
            logger.exception(f"[tailor] Error for '{context.job.title}'")
            return False
                        
    async def tailor_approved_jobs(self) -> dict:
        async with self.session_factory() as session:
            cv_repo = CVVersionRepository(session)
            jobs_id = await cv_repo.get_approved_jobs_without_cv()

        logger.info(f'[tailor] Found {len(jobs_id)} jobs for tailoring')

        results = []

        for job_id in jobs_id:
            result = await self._tailor_one_job(job_id)
            results.append(result)

        success_count  = sum(results)
        logger.info(f'[tailor] Ready: {success_count} from {len(results)}')
        return {'total': len(results), 'success': success_count}
