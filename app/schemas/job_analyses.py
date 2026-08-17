from pydantic import BaseModel, Field

class JobAnalysisResult(BaseModel):
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    responsibilities: list[str] = []
    soft_skills: list[str] = []
    ats_keywords: list[str] = []
    seniority: str| None = None
    min_years_experience: int | None = Field(default=None, ge=0)

