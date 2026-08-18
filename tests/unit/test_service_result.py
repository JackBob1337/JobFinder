import pytest
from pydantic import ValidationError

from app.schemas.service_result import ServiceError, ServiceResult


def make_errors(**overrides):
    values = {
        'item_id': 'job-1',
        'message': 'Analysis failed' 
    }

    values.update(overrides)

    return ServiceError(**values)


def make_service_result(**overrides):
    values = {
        'total': 3,
        'succeeded': 2,
        'failed': 1,
        'errors': [make_errors()],
    }

    values.update(overrides)
    return ServiceResult(**values)



def test_service_result_accepts_valid_counts():
    result = make_service_result()

    assert result.total == 3
    assert result.succeeded == 2
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