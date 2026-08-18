from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Boolean, ARRAY, false, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


from sqlalchemy import Enum as SqlEnum
from app.schemas.raw_job import JobSourceEnum
from app.db.base import Base

class Job(Base):
    __tablename__ = 'jobs'
    __table_args__ = (
        UniqueConstraint(
            'source',
            'url',
            name='uq_jobs_source_url',
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, unique=False, nullable=False, index=True)
    company: Mapped[str] = mapped_column(String, unique=False, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false(), default=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    job_types: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source: Mapped[JobSourceEnum] = mapped_column(SqlEnum(JobSourceEnum, name="jobsource"), nullable=False)
    published_at: Mapped[datetime | None ] = mapped_column(DateTime(timezone=True), nullable=True)
    found_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
