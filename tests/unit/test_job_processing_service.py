from unittest.mock import AsyncMock, Mock

import pytest

from app.exceptions.exceptions import DatabaseConnectionError
from app.services.job_processing_service import JobProcessingService


@pytest.mark.asyncio
async def test_full_cycle_propagates_data_base_error():
    service = JobProcessingService(
        sources=[],
        session_factory=Mock(),
        analysis_agent=Mock(),
        filter_agent=Mock()
    )

    service.scrape_and_save = AsyncMock(
        side_effect=DatabaseConnectionError(
            'Database is unavailable'
        )
    )
    service.analyze_new_jobs = AsyncMock()
    service.filter_analyzed_jobs = AsyncMock()

    with pytest.raises(DatabaseConnectionError):
        await service.run_full_cycle()

    service.analyze_new_jobs.assert_not_awaited()
    service.filter_analyzed_jobs.assert_not_awaited()