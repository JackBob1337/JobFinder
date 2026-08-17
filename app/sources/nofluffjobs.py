from app.sources.base import JobSource
from app.schemas.raw_job import RawJob, JobSourceEnum
import json
import httpx
from pydantic import HttpUrl
from dataclasses import dataclass, field
from app.core.logger import logger
from datetime import datetime, timezone
from app.sources.arbeitnow import strip_html
import asyncio
from collections import defaultdict
import hashlib

from app.exceptions.exceptions import SourceFetchException

@dataclass
class NoFluffJobsSearch:
    page_size: int = 1000
    salary_currency: str = 'PLN'
    salary_period: str = 'month'
    region: str = 'pl'
    language: str = 'pl-PL'
    seniority: list[str] = field(
        default_factory=lambda: ['Junior']
    )

class NoFluffJobsSource(JobSource):
    BASE_URL = "https://nofluffjobs.com/api/search/posting"
    name = 'nofluffjobs'

    HEADERS = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/infiniteSearch+json",
        "user-agent": "Mozilla/5.0",
        "origin": "https://nofluffjobs.com",
        "referer": "https://nofluffjobs.com/pl",
        "nfj-global-context": json.dumps({
            "region": "PL",
            "lang": "pl",
            "global_is_employer_logged_in": False,
            "global_is_candidate_logged_in": False,
            "global_internal_traffic": False,
            "global_partnerId": None,
            "global_salary_match_enabled": True,
        }),
    }

    def _build_params(self, search: NoFluffJobsSearch) -> dict:
        return {
            "pageFrom": 1,
            "pageTo": 1,
            "pageSize": search.page_size,
            "salaryCurrency": search.salary_currency,
            "salaryPeriod": search.salary_period,
            "region": search.region,
            "language": search.language,
        }

    def _build_payload(self, search: NoFluffJobsSearch, query: str) -> dict:
        return {
             "criteriaSearch": {
                "city": [],
                "company": [],
                "category": [],
                "country": [],
                "employment": [],
                "seniority": search.seniority,
                "requirement": [],
                "salary": [],
                "more": [],
                "applicationStatus": [],
                "keyword": [query],
                "jobLanguage": [],
                "jobPosition": [],
                "province": [],
                "id": [],
                "withSalaryMatch": [],
            },
            "pageSize": search.page_size,
            "withSalaryMatch": True,
        }

 

    def _get_description_from_details(self, details: dict) -> str | None:
        description = details.get('description')
        if description is None:
            return None

        return strip_html(description)
    
    def _get_description_from_requirements(self, requirements: dict) -> str | None:
        description = requirements.get('description')
        if description is None:
            return None
        
        return strip_html(description)

    def _get_daily_tasks(self, details: dict) -> list[str] | None:
        tasks = details.get('specs', {}).get('dailyTasks', [])
        if not tasks:
            return None

        return tasks

    def _get_musts(self, details: dict) -> list[dict]:
        musts = details.get('musts', [])
        if not musts:
            return []

        return [m['value'] for m in musts if 'value' in m]

    def _build_description(self, details: dict | None) -> str:
        if details is None:
            return ''
        
        main_desc = self._get_description_from_details(details.get('details', {}))
        requirements_desc = self._get_description_from_requirements(details.get('requirements', {}))
        daily_tasks = self._get_daily_tasks(details)

        parts = []

        if main_desc:
            parts.append(main_desc)
        if requirements_desc:
            parts.append(f'Requirements: \n{requirements_desc}')
        if daily_tasks:
            parts.append('Responsibilities:\n' + '\n'.join(f'- {t}' for t in daily_tasks))

        return '\n\n'.join(parts)

    def _get_location(self, item) -> tuple[str| None, bool]:
        location_data = item.get('location', {})
        places = location_data.get('places', [])
        city = places[0].get('city') if places else None
        is_remote = location_data.get('fullyRemote', False)
        
        return city, is_remote 

    def _parse_item(self, item: dict, details: dict) -> RawJob | None:
        try: 
            title = item['title']
            company = item['name']
            slug = item['url']

        except KeyError as e:
            logger.warning("Skipping item, missing required field %s. title=%r", e, item.get("title"))
            return None

        city, is_remote = self._get_location(item)

        tile_tags = [
            tile['value'] for tile in item.get('tiles', {}).get('value', [])
            if tile.get('type') == 'requirement'
        ]

        musts_tags = self._get_musts(details.get('requirements', {})) if details else []

        tags = list(set(tile_tags + musts_tags))

        posted_ms = item.get('posted')
        published_at = (
            datetime.fromtimestamp(posted_ms / 1000, tz=timezone.utc) if posted_ms else None
        )

        return RawJob(
            title=title,
            company=company,
            location=city,
            is_remote=is_remote,
            description=self._build_description(details),
            url=HttpUrl(f"https://nofluffjobs.com/pl/job/{slug}"),
            source=JobSourceEnum.NOFLUFFJOBS,
            job_types=item.get('seniority', []),
            tags=tags,
            published_at=published_at
        )

    async def _fetch_details(self, client: httpx.AsyncClient, job_id: str, max_retries: int = 2) -> dict | None:
        for attempt in range(1, max_retries + 1):
            try:
                response = await client.get(
                    f"https://nofluffjobs.com/api/posting/{job_id}",
                    headers={"user-agent": "Mozilla/5.0"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                if attempt < max_retries:
                    logger.warning(
                        f"[{self.name}] Try {attempt}/{max_retries} couldn`t fetch details for {job_id}: {e}. Retry"
                    )
                    await asyncio.sleep(1)
                else:
                    logger.warning(f"[{self.name}] Couldn`t fetch details for {job_id}: {e}")
                    return None
        return None


    async def fetch_jobs(self, query: str = 'python') -> list[RawJob]:
        search = NoFluffJobsSearch()
        params = self._build_params(search)
        payload = self._build_payload(search, query)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL,
                    headers=self.HEADERS,
                    params=params,
                    json=payload
                )

                response.raise_for_status()
                data = response.json()

                postings = data.get('postings', [])
                logger.info(f"[{self.name}] Получено {len(postings)} вакансий")

                sem = asyncio.Semaphore(10)

                async def fetch(job_id):
                    async with sem:
                        return await self._fetch_details(client, job_id)

                details_list = await asyncio.gather(*(fetch(p['id']) for p in postings))
                
                jobs = [
                    self._parse_item(posting, details)
                    for posting, details in zip(postings, details_list)
                    if details is not None
                ]

        except httpx.HTTPError as e:
            raise SourceFetchException(self.name, e)

        return jobs

    def _description_hash(self, job: RawJob) -> str:
            if not job.description.strip():
                return str(job.url)
            normalized = ''.join(job.description.lower().split())
            return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def collect_jobs(self, jobs: list[RawJob]) -> dict[tuple[str, str], list[RawJob]]:
        jobs_by_key: dict[tuple[str, str], list[RawJob]] = defaultdict(list)

        for job in jobs:
            key = (
                job.company.strip().lower(),
                job.title.strip().lower(),
            )
            jobs_by_key[key].append(job)

        return jobs_by_key

    def _group_by_description(self, jobs: list[RawJob]) -> dict[str, list[RawJob]]:
        by_description: dict[str, list[RawJob]] = defaultdict(list)
        for job in jobs:
            by_description[self._description_hash(job)].append(job)

        return by_description

    def _merge_locations(self, jobs: list[RawJob]) -> RawJob:
        base = jobs[0]
        locations = sorted({job.location for job in jobs if job.location})
        merged_location = ', '.join(locations) if locations else None

        return base.model_copy(update={'location': merged_location})

    def _resolve_duplicates(self, jobs: list[RawJob]) -> RawJob:
        if len(jobs) == 1:
            return jobs[0]

        return self._merge_locations(jobs)

    def deduplicate_jobs(self, jobs: list[RawJob]) -> list[RawJob]:
        jobs_by_key = self.collect_jobs(jobs)
        result: list[RawJob] = []

        for group in jobs_by_key.values():
            by_description = self._group_by_description(group)
            for duplicates in by_description.values():
                result.append(self._resolve_duplicates(duplicates))

        return result
        
async def main():
    source = NoFluffJobsSource()
    jobs = await source.fetch_jobs()
    job_collection = source.collect_jobs(jobs)
    result = source.deduplicate_jobs(jobs)

    print(f"До дедупликации: {len(jobs)}")
    print(f"После дедупликации: {len(result)}")

    for job in result:
        print(f"{job.company} | {job.title} | {job.location}")

    # print(first_job.model_dump())

    with open('nofluffjobs_output.txt', 'w', encoding='utf-8') as f:
        f.write(f"\nВсего собрано: {len(jobs)}\n")
        for job in jobs:
            f.write(f"- {job.title} | {job.company} | {job.location} | remote={job.is_remote}\n")
            f.write(f"  tags: {job.tags}\n")
            f.write(f"  description length: {len(job.description)}\n\n")
            print()
        print(f"\nВсего собрано: {len(jobs)}\n")

if __name__ == "__main__":
    asyncio.run(main())

    

