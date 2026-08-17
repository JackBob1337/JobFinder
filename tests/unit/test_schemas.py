import pytest
from pydantic import ValidationError

from app.schemas.raw_job import JobSourceEnum, RawJob
from app.schemas.job_analyses import JobAnalysisResult
from app.schemas.ats_check_result import ATSCheckResult
from app.schemas.job_match import JobMatchResult, MatchStatusEnum


def make_raw_job(**overrides):
    values = {
        'title': 'Python Developer',
        'company': 'Example company',
        'description': 'Example description',
        'url': 'https://example.com/jobs/1',
        'source': JobSourceEnum.ARBEITNOW
    }

    values.update(overrides)
    return RawJob(**values)

def make_job_match(**overrides):
    values = {
        'job_id': 1,
        'relevance_score': 0.5,
        'reasoning': 'test reasoning',
        'status': MatchStatusEnum.REJECTED
    }

    values.update(overrides)
    return JobMatchResult(**values)


def test_location_is_optional():
    job = make_raw_job()

    assert job.location is None


def test_job_types_and_tags_default_to_empty_lists():
    job = make_raw_job()

    assert job.job_types == []
    assert job.tags == []


def test_title_cannot_be_empty():
    with pytest.raises(ValidationError):
        make_raw_job(title=' ')


def test_company_cannot_be_empty():
    with pytest.raises(ValidationError):
        make_raw_job(company=' ')


def test_nofluffjobs_source_value_is_stable():
    assert JobSourceEnum.NOFLUFFJOBS.value == "nofluffjobs"


def test_min_years_experience_cannot_be_negative():
    with pytest.raises(ValidationError):
        JobAnalysisResult(min_years_experience=-1)


@pytest.mark.parametrize('score', [-1, 101])
def test_ats_score_must_be_between_zero_and_hundred(score):
    with pytest.raises(ValidationError):
        ATSCheckResult(
            passed=False,
            score=score
        )


@pytest.mark.parametrize('score', [-0.01, 1.01])
def test_relevance_score_must_be_between_zero_and_one(score):
    with pytest.raises(ValidationError):
        make_job_match(relevance_score=score)


@pytest.mark.parametrize('score', [0.0, 1.0])
def test_relevance_score_boundaries_are_valid(score):
    result = make_job_match(relevance_score=score)

    assert result.relevance_score == score