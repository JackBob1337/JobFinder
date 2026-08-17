from pydantic import BaseModel, HttpUrl, Field, field_validator
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

class JobSourceEnum(str, Enum):
    ARBEITNOW = "arbeitnow"
    ADZUNA = "adzuna"
    REMOTIVE = "remotive"
    JUSTJOINIT = 'justjoinit'
    NOFLUFFJOBS = 'nonfluffjobs'

class RawJob(BaseModel):
    title: str 
    company: str
    location: Optional[str]
    is_remote: bool = False
    description: str
    job_types: list[str] = []
    tags: list[str] = []
    url: HttpUrl
    source: JobSourceEnum
    published_at: Optional[datetime] = None
    found_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator('title', 'company')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('title can`t be empty')
        return v

