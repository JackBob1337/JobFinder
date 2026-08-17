import json
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.job_analyses import JobAnalysisResult
from app.models.job import Job
from app.models.job_analyses import JobAnalysis


SYSTEM_PROMPT = """
    You are a Job Description Analysis Agent.

    Your task is to analyze raw job descriptions and extract structured information that will be used for resume matching and resume customization.

    You do NOT evaluate candidates.
    You do NOT compare the job with a resume.
    You do NOT write summaries.
    You only extract requirements from the job description.

    Rules:

    1. Extract only information explicitly mentioned in the job description.

    2. Never invent technologies, responsibilities, seniority levels, or requirements.

    3. Separate mandatory requirements from optional preferences.

    4. Normalize technology names:
    - "Postgres" -> "PostgreSQL"
    - "Amazon Web Services" -> "AWS"
    - "React.js" -> "React"

    5. Extract:
    - required technical skills
    - preferred technical skills
    - responsibilities
    - soft skills
    - years of experience
    - seniority level
    - education requirements
    - language requirements
    - location/remote information
    - ATS keywords

    6. If information is missing, return an empty array or null.
    Do not guess.

    7. Return valid JSON only.
    No markdown.
    No explanations.

    Return ONLY valid JSON:

    {
        "job_title": null,

        "seniority": null,

        "required_skills": [],

        "preferred_skills": [],

        "responsibilities": [],

        "soft_skills": [],

        "experience_requirements": {
            "years": null,
            "description": null
        },

        "education_requirements": [],

        "language_requirements": [],

        "location": {
            "remote": null,
            "hybrid": null,
            "onsite": null,
            "details": null
        },

        "ats_keywords": []
    }

"""

def safe_parse_years(value) -> int | None:
    """Пытается получить int из значения, которое LLM мог вернуть как угодно"""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        # пробуем вытащить число из строки, если оно там есть
        import re
        match = re.search(r'\d+', value)
        if match:
            return int(match.group())
        return None  # текст без числа вообще ("mehrjährige Erfahrung") — не можем извлечь
    return None

class AnalysisAgent:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def analyze(self, job: Job) -> JobAnalysisResult:
        user_prompt = f"""
            Analyze this job description.

            Title:
                {job.title}

            Description:
                {job.description}
        """
        response = await self.client.chat.completions.create(
            model='gpt-4.1-nano',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.2,
            response_format={'type': 'json_object'}
        )

        content = response.choices[0].message.content
        if content is None:
            raise ValueError('GPT returned empty response content')
        
        raw_result = json.loads(content)

        min_years = raw_result.get("experience_requirements", {}).get("years")
        min_years = safe_parse_years(min_years)  # добавь эту строку

        
        return JobAnalysisResult(
                required_skills=raw_result.get("required_skills", []),
                preferred_skills=raw_result.get("preferred_skills", []),
                responsibilities=raw_result.get("responsibilities", []),
                soft_skills=raw_result.get("soft_skills", []),
                ats_keywords=raw_result.get("ats_keywords", []),
                seniority=raw_result.get("seniority"),
                min_years_experience=min_years,
            )
        


