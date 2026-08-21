from unittest.mock import Mock

import pytest

import app.services.job_processing_service as service_module
from app.schemas.results import ServiceResult
from app.services.job_processing_service import JobProcessingService


class FakeSessionContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeJobRepository:
    def __init__(self, session):
        self.session = session

    async def get_jobs_without_analysis(self, limit=None):
        return []


@pytest.mark.asyncio
async def test_analyze_new_jobs_returns_service_result_for_empty_batch(
    monkeypatch,
):
    monkeypatch.setattr(
        service_module,
        'JobRepository',
        FakeJobRepository
    )

    service = JobProcessingService(
        sources=[],
        session_factory=lambda: FakeSessionContext(),
        analysis_agent=Mock(),
        filter_agent=Mock()
    )

    result = await service.analyze_new_jobs()

    assert isinstance(result, ServiceResult)
    assert result.total == 0
    assert result.succeeded == 0
    assert result.failed == 0
    assert result.errors == []
    