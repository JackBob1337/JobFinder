from abc import ABC, abstractmethod
from app.schemas.raw_job import RawJob

class JobSource(ABC):
    @abstractmethod
    async def fetch_jobs(self) -> list[RawJob]:
        pass
