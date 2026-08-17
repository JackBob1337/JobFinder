import json
from openai import AsyncOpenAI

from app.core.config import settings
from app.models.job import Job
from app.schemas.job_match import JobMatchResult, MatchStatusEnum
from app.schemas.job_analyses import JobAnalysisResult
from app.cv.base_cv import load_base_cv_text

from app.exceptions.exceptions import FilterError

SYSTEM_PROMPT = """
    You are an expert technical recruiter.

    Your task is to determine how well a job vacancy matches the candidate.

    The candidate's CV will always be provided separately in the prompt or conversation.
    Treat the CV as the ONLY source of truth about the candidate's:
    - skills
    - technologies
    - work experience
    - seniority
    - education
    - career goals

    Never assume the candidate has skills or experience that are not explicitly stated in the CV.

    Your job is NOT to evaluate whether the vacancy is good.
    Your job is to evaluate whether THIS candidate is a realistic fit for THIS vacancy.

    Evaluation priorities (highest to lowest):

    1. Seniority match
    2. Relevant commercial experience
    3. Technology stack overlap
    4. Backend/domain relevance
    5. Missing skills (penalize only if they are essential)

    Guidelines:

    - Strongly penalize vacancies requiring significantly more experience than shown in the CV.
    - If the vacancy explicitly requires more years of commercial experience than the candidate has, reduce the score substantially.
    - Prefer vacancies that the candidate could realistically obtain today.
    - Missing secondary technologies should only slightly reduce the score if they can reasonably be learned on the job.
    - If years of experience are not stated, infer seniority from the overall wording of the vacancy.
    - Do not reward technologies that appear only in the vacancy but not in the CV.
    - If important information is missing in either the CV or the vacancy, make conservative assumptions.

    Scoring:

    1.0 = Excellent match
    0.8-0.9 = Strong match
    0.6-0.7 = Good match
    0.5 = Borderline but worth applying
    0.3-0.4 = Weak match
    0.0-0.2 = Poor match

    Return ONLY valid JSON.

    Schema:

    {
    "relevance_score": <float between 0.0 and 1.0>,
    "reasoning": "<1-2 concise sentences in English explaining the decision>",
    "status": "<approved|rejected>"
    }

    Rules:
    - approved if relevance_score >= 0.50
    - rejected otherwise

    Output JSON only.
    """

class FilterAgent:
    def __init__(self): 
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.cv_text = load_base_cv_text()
    
    async def evaluate(self, job: Job, analysis: JobAnalysisResult) -> JobMatchResult:
        user_prompt = f"""
            Evaluate the following job vacancy against the candidate CV.

            ## Candidate CV

            {self.cv_text}

            ---

            ## Job Vacancy

            Job title: 
                {job.title}

            Seniority: 
                {analysis.seniority}

            Required skills: 
                {', '.join(analysis.required_skills)}

            Preferred skills: 
                {', '.join(analysis.preferred_skills)}

            Min years experience: 
                {analysis.min_years_experience}
                
            Responsibilities: 
                {'; '.join(analysis.responsibilities)}
        """
        try:
            response = await self.client.chat.completions.create(
                model='gpt-4.1-nano',
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_prompt}
                ],
                temperature=0.2,
                response_format={'type': 'json_object'},
            )
    
            content = response.choices[0].message.content
            if content is None:
                raise ValueError('GPT returned empty response content')
    
            raw_result = json.loads(content)
    
    
            return JobMatchResult(
                job_id=job.id,
                relevance_score=raw_result['relevance_score'],
                reasoning=raw_result['reasoning'],
                status=MatchStatusEnum(raw_result['status'])
            )

        except Exception as e:
            raise FilterError(job.id, e) from e

        

