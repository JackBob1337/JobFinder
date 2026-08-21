from pydantic import BaseModel, ConfigDict, HttpUrl, Field, field_validator
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

class JobSourceEnum(str, Enum):
    ARBEITNOW = "arbeitnow"
    ADZUNA = "adzuna"
    REMOTIVE = "remotive"
    JUSTJOINIT = 'justjoinit'
    NOFLUFFJOBS = 'nofluffjobs'

class RawJob(BaseModel):
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    location: Optional[str] = None
    is_remote: bool = False
    description: str = Field(min_length=1)
    job_types: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    url: HttpUrl
    source: JobSourceEnum
    published_at: Optional[datetime] = None
    found_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator('location', mode='before')
    @classmethod
    def blank_location_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        
        return value

    @field_validator('title', 'company', 'description')
    @classmethod
    def title_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('{value} can`t be empty')
        return value
