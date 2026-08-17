from pydantic import BaseModel
from dataclasses import dataclass
from app.schemas.job_analyses import JobAnalysisResult


@dataclass
class TailorJob:
    id: int
    title: str
    company: str
    description: str

@dataclass
class TailorContext:
    job: TailorJob
    analysis: JobAnalysisResult
    match_reasoning: str

    