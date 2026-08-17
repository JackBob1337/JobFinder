import asyncio
from datetime import datetime

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from app.sources.arbeitnow import strip_html
from app.sources.base import JobSource
from app.models.job import Job
from app.schemas.raw_job import RawJob, JobSourceEnum

from app.core.config import settings
from app.core.logger import logger
from app.exceptions.exceptions import SourceFetchException

class JustJoinItSource(JobSource):
    ACTOR_ID = "trev0n/justjoinit-scraper"
    name = 'justjoinit'

    @staticmethod
    def _normalize_required_skills(required_skills: list[object] | None) -> list[str]:
        if not required_skills:
            return []

        normalized_skills: list[str] = []
        for skill in required_skills:
            if isinstance(skill, str):
                skill_name = skill.strip()
            elif isinstance(skill, dict):
                skill_name = str(skill.get("name", "")).strip()
            else:
                skill_name = str(skill).strip()

            if skill_name:
                normalized_skills.append(skill_name)

        return normalized_skills

    @staticmethod
    def _parse_published_at(raw: str | None) -> datetime | None:
        if not raw:
            return None

        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))

        except ValueError:
            logger.warning('Unparseable publishedAt: %r', raw)
            return None

    def _parse_item(self, item: dict) -> RawJob | None:
        try:
            title = item['title']
            company = item['companyName']
            url = item['jobUrl']
            
        except KeyError as e:
            logger.warning(
                "Skipping item, missing required field %s. title=%r url=%r",
                e,
                item.get("title"),
                item.get("jobUrl"),
            )
            return None

        return RawJob(
                title=title,
                company=company,
                location=item.get("city"),
                is_remote=item.get("workplaceType") == "remote",
                description=strip_html(item.get("description") or ""),
                url=url,
                source=JobSourceEnum.JUSTJOINIT,
                job_types=[item["experienceLevel"]] if item.get("experienceLevel") else [],
                tags=self._normalize_required_skills(item.get("requiredSkills")),
                published_at=self._parse_published_at(item.get("publishedAt")),
            )

    async def _run_actor(self, query: str) -> tuple:
        client = ApifyClient(settings.apify_api_token)
        run_input = {
                    "category": query,
                    "experienceLevel": ["junior", "intern"],
                    "location": "all-locations",
                    "maxItems": 100,
                    "extractFullDetails": True, 
                }

        try:
            run = await asyncio.to_thread(
                client.actor(self.ACTOR_ID).call, run_input=run_input
            )
        except ApifyApiError as e:
            raise SourceFetchException(self.name, e) from e

        if run is None:
            raise SourceFetchException(self.name, RuntimeError("Apify run returned None"))

        return run.default_dataset_id, client

    async def fetch_jobs(self, query: str = 'python') -> list[RawJob]:
        dataset_id, client = await self._run_actor(query)

        try:
            items = await asyncio.to_thread(
                lambda: list(client.dataset(dataset_id).iterate_items())
            )
        except ApifyApiError as e: 
            raise SourceFetchException(self.name, e) from e

        jobs = [self._parse_item(item) for item in items]
        return [job for job in jobs if job is not None]

    
