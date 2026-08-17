from pydantic import BaseModel

class ATSCheckResult(BaseModel):
    passed: bool
    score: int
    missing_keywords: list[str] = []
    missing_skills: list[str] = []
    weak_bullets: list[str] = []
    issues: list[str] = []
    recommendations: list[str] = []
