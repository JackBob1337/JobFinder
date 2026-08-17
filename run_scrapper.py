import asyncio

from app.db.session import async_session_factory
from app.db.job_repository import JobRepository
from app.sources.arbeitnow import ArbeitnowSource
from app.sources.justjoinit import JustJoinItSource


async def main():
    sources = [
        ArbeitnowSource(),
        JustJoinItSource(),
    ]

    async with async_session_factory() as session:
        repo = JobRepository(session)

        for source in sources:
            source_name = source.__class__.__name__
            print(f"\n=== Собираю вакансии из {source_name} ===")

            try:
                jobs = await source.fetch_jobs()
                print(f"Получено вакансий: {len(jobs)}")

                saved = await repo.save_bulk(jobs)
                print(f"Сохранено новых: {saved} из {len(jobs)}")

            except Exception as e:
                print(f"⚠️ Ошибка при сборе из {source_name}: {e}")
                continue

    print("\nГотово.")


if __name__ == "__main__":
    asyncio.run(main())