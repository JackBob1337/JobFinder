from datetime import datetime
from app.db.base import Base
from app.schemas.job_match import MatchStatusEnum
from sqlalchemy import ForeignKey, Float, Integer, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Enum as SqlEnum


class JobMatch(Base):
    __tablename__ = 'job_matches'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey('jobs.id'), nullable=False, unique=True)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[MatchStatusEnum] = mapped_column(SqlEnum(MatchStatusEnum, name='matchstatus'), nullable=False)
    analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
