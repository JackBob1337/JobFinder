import asyncio
 
from app.sources.arbeitnow import ArbeitnowSource
from app.db.job_repository import JobRepository
from app.db.session import async_session_factory

async def main():
    source = ArbeitnowSource()
    raw_jobs = await source.fetch_jobs()

    async with async_session_factory() as session:
        repo = JobRepository(session)
        saved = await repo.save_bulk(raw_jobs)
        print(f'Saved {saved} from {len(raw_jobs)}')
    
if __name__ == "__main__":
    asyncio.run(main())
