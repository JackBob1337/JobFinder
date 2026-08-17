from openai import AsyncOpenAI
import json


from app.core.config import settings
from app.schemas.job_analyses import JobAnalysisResult
from app.schemas.ats_check_result import ATSCheckResult

ATS_CHECK_SYSTEM_PROMPT = """You are an ATS (Applicant Tracking System) simulator.
    Evaluate how well this resume summary matches the job requirements.

    Return JSON:
    {
        "passed": bool,
        "score": int (0-100),
        "missing_keywords": [...],
        "missing_skills": [...],
        "weak_bullets": [...],
        "issues": [...],
        "recommendations": [...]
    }

    passed=true only if score >= 75.
"""

class ATSCheckAgent:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def check(self, summary: str, analysis: JobAnalysisResult) -> ATSCheckResult:
        user_prompt = '''
            Job requirements: {analysis.required_skills}
            Resume summary: {summary}
        '''

        response = await self.client.chat.completions.create(
            model='gpt-5-mini',
            messages=[
                {'role': 'system', 'content': ATS_CHECK_SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.2,
            response_format={'type': 'json_object'},
        )

        content = response.choices[0].message.content
        if content is None:
            raise ValueError('LLM returned empty response for ATS check')

        raw_result = json.loads(content)

        return ATSCheckResult(**raw_result)

    

        