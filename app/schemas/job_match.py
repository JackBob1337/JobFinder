from pydantic import BaseModel, Field
from enum import Enum

class MatchStatusEnum(str, Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

class JobMatchResult(BaseModel):
    job_id: int
    relevance_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    analysis: dict | None = None
    status: MatchStatusEnum