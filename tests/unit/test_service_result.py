import pytest
from pydantic import ValidationError

from app.schemas.results import (
    ResultError, 
    ServiceResult,
    PipelineResult,
    RepositoryResult
)

def make_errors(**overrides):
    values = {
        'item_id': 'job-1',
        'message': 'Analysis failed' 
    }

    values.update(overrides)

    return ResultError(**values)


def make_service_result(**overrides):
    values = {
        'total': 5,
        'succeeded': 2,
        'skipped': 2,
        'failed': 1,
        'errors': [make_errors()],
    }

    values.update(overrides)
    return ServiceResult(**values)



def test_service_result_accepts_valid_counts():
    result = make_service_result()

    assert result.total == 5
    assert result.succeeded == 2
    assert result.skipped == 2
    assert result.failed == 1
    assert len(result.errors) == 1


def test_service_result_inconsistent_counts():
    with pytest.raises(ValidationError):
        make_service_result(
            total=3,
            succeeded=3,
            failed=1,
        )


def test_service_result_rejects_wrong_error_count():
    with pytest.raises(ValidationError):
        make_service_result(
            errors=[]
        )


def test_service_result_rejects_negative_counts():
    with pytest.raises(ValidationError):
        make_service_result(
            total=1,
            succeeded=0,
            failed=0,
        )


def test_service_result_accepts_skipped_items():
    result = ServiceResult(
        total=5,
        succeeded=3,
        skipped=2,
        failed=0,
        errors=[],
    )

    assert result.skipped == 2


def test_pipeline_result_contains_all_stage_result():
    stage_result = ServiceResult(
        total=2,
        succeeded=2,
        skipped=0,
        failed=0,
        errors=[],
    )

    pipeline_result = PipelineResult(
        scrapped=stage_result,
        analyzed=stage_result,
        filtered=stage_result
    )

    assert pipeline_result.scrapped.succeeded == 2
    assert pipeline_result.analyzed.succeeded == 2
    assert pipeline_result.filtered.succeeded == 2