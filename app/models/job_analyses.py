from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, ARRAY, DateTime, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime


class JobAnalysis(Base):
    __tablename__ = 'job_analyses'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey('jobs.id'), nullable=False, unique=True)
    required_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    seniority: Mapped[str | None] = mapped_column(String, nullable=True)
    min_years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    responsibilities: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    ats_keywords: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    raw_json: Mapped[dict] = mapped_column(JSONB)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())



