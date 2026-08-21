from abc import ABC, abstractmethod
from typing import ClassVar
from app.schemas.raw_job import RawJob

class JobSource(ABC):
    name: ClassVar[str]

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        name = cls.__dict__.get('name')
        if not isinstance(name ,str) or not name.strip():
            raise TypeError(f'{cls.__name__} must define non-empty name')
        
    @abstractmethod
    async def fetch_jobs(self) -> list[RawJob]:
        raise NotImplementedError
