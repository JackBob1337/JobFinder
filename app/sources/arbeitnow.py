from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

from app.sources.base import JobSource
from app.schemas.raw_job import RawJob, JobSourceEnum

def strip_html(raw_html: str) -> str:
    return BeautifulSoup(raw_html, 'html.parser').get_text(separator='\n').strip()

class ArbeitnowSource(JobSource):
    BASE_URL = "https://www.arbeitnow.com/api/job-board-api"

    async def fetch_jobs(self) -> list[RawJob]:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL)
            response.raise_for_status()
            data = response.json()

        jobs = []

        for item in data['data']:
            job = RawJob(
                title=item["title"],
                company=item["company_name"],
                location=item.get("location"),
                is_remote=item.get("remote", False),
                description=strip_html(item["description"]),
                job_types=item.get('job_types'),
                tags=item.get('tags'),
                url=item["url"],
                source=JobSourceEnum.ARBEITNOW,
                published_at=datetime.fromtimestamp(item["created_at"], tz=timezone.utc),
            )
            jobs.append(job)

        return jobs

