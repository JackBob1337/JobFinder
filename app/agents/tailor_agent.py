import json
from openai import AsyncOpenAI

from app.core.config import settings
from app.models.job import Job
from app.schemas.job_analyses import JobAnalysisResult
from app.schemas.cv_content import CVEntry
from data.parse_cv import CVParser

SYSTEM_PROMPT = """
    You are an expert technical resume writer specializing in ATS-optimized resumes for software engineering and IT roles.

    Your task is to rewrite ONLY the candidate's Professional Summary so it is better aligned with a target job while remaining 100% factually accurate.

    ## Context

    The rewritten summary will be evaluated in two stages:

    1. An Applicant Tracking System (ATS) that searches for relevant keywords, technologies, role titles, and skills.
    2. A human recruiter who expects clear, natural, and credible writing.

    The summary must perform well for both.

    ## Source Priority

    The candidate's CV is the single source of truth.

    The job analysis represents the target requirements and optimization goals.

    If there is any conflict between them, ALWAYS follow the CV.

    ## Your Objective

    Rewrite the Professional Summary to:

    - maximize relevance to the target position;
    - naturally incorporate the most relevant ATS keywords;
    - emphasize the candidate's strongest matching experience;
    - remain concise, professional, and believable.

    Do NOT rewrite any other part of the resume.

    ## Hard Rules

    These rules must never be violated.

    - Never invent experience, projects, companies, responsibilities, achievements, certifications, education, or technologies.
    - Never claim proficiency in a technology unless it explicitly appears in the candidate's CV.
    - Never increase or decrease the candidate's seniority.
    - Never change years of experience.
    - Never change job titles.
    - Never exaggerate responsibilities or impact.
    - Never imply experience the candidate does not have.

    If the job requires something missing from the CV, simply omit it rather than attempting to compensate for the gap.

    ## Allowed Transformations

    You MAY:

    - reorder information;
    - emphasize the most relevant experience;
    - combine related ideas;
    - rewrite sentences for clarity;
    - use industry-standard terminology;
    - replace phrases with equivalent wording;
    - surface existing skills earlier in the summary.

    Example:

    CV:
    "Built REST APIs using FastAPI."

    Acceptable:
    "Experienced in designing and developing REST APIs with FastAPI."

    This is a rephrasing of an existing fact, not new information.

    ## ATS Optimization

    Prioritize required skills over preferred skills.

    Use only keywords that truthfully describe the candidate.

    Naturally integrate the most relevant ATS keywords into complete sentences.

    Do NOT stuff keywords.

    Focus on the strongest 5–10 relevant keywords instead of attempting to include everything from the job description.

    ## Writing Style

    Write as if the candidate wrote it.

    The tone should be:

    - confident;
    - technical;
    - concise;
    - professional;
    - natural.

    Avoid generic buzzwords and empty phrases such as:

    - "results-driven professional"
    - "passionate engineer"
    - "excellent communication skills"
    - "hard-working team player"

    unless those ideas are explicitly supported by the CV.

    The summary is not a biography.

    Select only the experience most relevant to the target role.

    ## Length

    - 60–100 words
    - 2–4 sentences
    - No bullet points

    ## Output

    Return ONLY the rewritten Professional Summary.

    Do not explain your reasoning.

    Do not include markdown.

    Do not include quotation marks.

    Do not return JSON.
"""

BULLETS_REWRITE_SYSTEM_PROMPT = """
    You are an expert technical resume writer specializing in ATS-optimized resumes for software engineering and IT roles.

    Your task is to rewrite the bullet points of a single CV experience or project entry so they are better aligned with a target job while remaining 100% factually accurate.

    ## Source of truth

    The provided CV entry (title, stack, and bullet points) is the ONLY source of truth.

    The target job description defines what should be emphasized, not what should be added.

    If there is any conflict between the CV entry and the job description, ALWAYS follow the CV entry.

    ## Your objective

    Rewrite every bullet to:

    * maximize relevance to the target role;
    * make the technical contribution clearer and more specific;
    * naturally emphasize skills and technologies relevant to the target job;
    * improve ATS keyword alignment;
    * preserve credibility and factual accuracy.

    The rewritten bullets should sound stronger, more technical, and more focused without changing the underlying experience.

    ## Hard rules

    These rules must never be violated.

    * Never invent technologies, tools, frameworks, databases, cloud services, responsibilities, achievements, metrics, scale, ownership, or impact.
    * Never claim experience that is not explicitly supported by the provided CV entry.
    * Never upgrade responsibility level.

    * "contributed to" is not "led";
    * "used" is not "architected";
    * "worked on" is not "owned".
    * Never add technologies that are not present in the provided CV entry (title, stack, or bullets).
    * Never change the number of bullets.
    * Never change the order of bullets.

    ## Using the stack

    You MAY explicitly mention technologies from the provided stack when they are directly relevant to the work described in a bullet.

    Example:

    Stack:
    Python, FastAPI, PostgreSQL

    Original bullet:
    Built CRUD operations for product management.

    Acceptable rewrite:
    Built CRUD APIs with FastAPI and PostgreSQL for product management.

    This is acceptable because FastAPI and PostgreSQL are already part of the provided CV entry.

    Do NOT introduce technologies unrelated to the described work.

    ## ATS optimization

    Prioritize required skills over preferred skills.

    Emphasize relevant existing experience rather than forcing keyword insertion.

    Use precise technical terminology.

    Preserve important engineering keywords already present in the CV entry.

    Do not stuff keywords unnaturally.

    ## Writing style

    Write like an experienced software engineer wrote the resume.

    Use strong technical action verbs.

    Prefer concrete engineering language over generic descriptions.

    Avoid AI-style marketing language and buzzwords such as:

    * spearheaded
    * leveraged
    * drove
    * championed
    * revolutionized

    Keep bullets concise and similar in length to the original.

    Do not use em dash characters (—).

    ## Output

    Return ONLY valid JSON in this exact format:

    {
    "bullets": [
    "bullet 1",
    "bullet 2"
    ]
    }

    Return only the JSON object and nothing else.
"""

class TailorAgent:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.parser = CVParser()
        self.cv_text = self.parser.load_cv_text()

    async def tailor_summary(
            self, 
            job_title: str, 
            analysis: JobAnalysisResult, 
            match_reasoning: str,
            extra_feedback = ''
        ) -> str:
        feedback_section = ''
        if extra_feedback:
            feedback_section = f'''
            ## IMPORTANT - Feedback from previous attempt
            {extra_feedback}

            Address these specific issues in this rewrite
        '''
        user_prompt = f"""
            Rewrite the PROFESSIONAL SUMMARY section of this CV to better match the job below.

            {feedback_section}

            Full CV:
                {self.cv_text}

            Target Position:
                {job_title}

            Required Skills:
                {', '.join(analysis.required_skills)}

            Preferred Skills:
                {','.join(analysis.preferred_skills)}
            
            ATS Keywords:
                {', '.join(analysis.ats_keywords)}
            
            Responsibilities:
                {chr(10).join('- ' + r for r in analysis.responsibilities)}   

            Candidate-Vacancy Fit Insights:
                {match_reasoning}

            Use these insights to emphasize the strongest matching experience, skills, and achievements in the new summary. Do not invent experience that is not present in the CV.
        """

        response = await self.client.chat.completions.create(
            model='gpt-5.4-mini',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.2,
        )

        raw_content = response.choices[0].message.content

        if raw_content is None:
            raise ValueError('LLM returned empty response for summary rewrite')
        
        new_summary = raw_content.strip()

        return new_summary

    async def tailor_bullets(
            self, 
            entry: CVEntry,
            job_title: str, 
            analysis: JobAnalysisResult
        ) -> list[str]:
        user_prompt = f"""
            Target job: {job_title}

            Required skills:
            {', '.join(analysis.required_skills)}

            Responsibilities:
            {'; '.join(analysis.responsibilities)}

            Candidate experience:
            Title: {entry.title}

            Stack:
            {', '.join(entry.stack)}

            Original bullets:
            {chr(10).join(f"{i+1}. {b}" for i, b in enumerate(entry.bullets))}

            Rewrite every bullet to better match the target job while remaining
            100% factually accurate.

            Use technologies from the stack when they are relevant to the bullet.

            Keep the same number and order of bullets.
        """

        response = await self.client.chat.completions.create(
            model='gpt-5.4-mini',
            messages=[
                {'role': 'system', 'content': BULLETS_REWRITE_SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.2,
            response_format={'type': 'json_object'}
        )

        raw_content = response.choices[0].message.content
        if raw_content is None:
            raise ValueError('GPT returned empty response for bullets rewrite')

        raw_data = json.loads(raw_content)
        new_bullets = raw_data.get('bullets', [])

        print(f"\n[DEBUG] Raw LLM response: {raw_content}")
        return new_bullets



