from typing import TypedDict
from app.schemas.job_analyses import JobAnalysisResult
from app.schemas.ats_check_result import ATSCheckResult

class TailorState(TypedDict):
    job_title: str
    analysis: JobAnalysisResult
    match_reasoning: str
    current_summary: str
    ats_result: ATSCheckResult | None
    retry_count: int
    max_retries: int

