import httpx
import pytest

from unittest.mock import AsyncMock

from app.exceptions.exceptions import (
    InvalidSourcePayloadException,
    SourceFetchException,
    TransientSourceFetchException,
)

from app.sources.http import request_json


URL = "https://example.com/jobs"


@pytest.mark.asyncio
async def test_404_does_not_retries(monkeypatch):
    client = AsyncMock(spec=httpx.AsyncClient)

    client.request.return_value = httpx.Response(
        404,
        request=httpx.Request('GET', URL)
    )

    sleep_mock = AsyncMock()
    monkeypatch.setattr("app.sources.http.asyncio.sleep", sleep_mock)

    with pytest.raises(SourceFetchException):
        await request_json(
            client,
            'GET',
            URL,
            source_name='test',
            attempts=3
        )

    assert client.request.call_count == 1
    sleep_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_malformed_json_does_not_retry(monkeypatch):
    client = AsyncMock(spec=httpx.AsyncClient)

    client.request.return_value = httpx.Response(
        200,
        content=b'not-json',
        request=httpx.Request('GET', URL)
    )

    sleep_mock = AsyncMock()
    monkeypatch.setattr('app.sources.http.asyncio.sleep', sleep_mock)

    with pytest.raises(InvalidSourcePayloadException):
        await request_json(
            client,
            'GET',
            URL,
            source_name='test',
            attempts=3
        )

    assert client.request.call_count == 1
    sleep_mock.assert_not_awaited()
    

@pytest.mark.asyncio
async def test_exhausting_raises_transient_exception(monkeypatch):
    client = AsyncMock(spec = httpx.AsyncClient)

    client.request.return_value = httpx.Response(
        503,
        request=httpx.Request('GET', URL)
    )

    monkeypatch.setattr("app.sources.http.asyncio.sleep", AsyncMock())

    with pytest.raises(TransientSourceFetchException):
        await request_json(
            client,
            'GET',
            URL,
            source_name='test',
            attempts=3
        )

    assert client.request.call_count == 3


@pytest.mark.asyncio
async def test_exception_preserves_source_name_and_cause(monkeypatch):
    client = AsyncMock(spec = httpx.AsyncClient)

    client.request.return_value = httpx.Response(
        503,
        request=httpx.Request('GET', URL)
    )

    monkeypatch.setattr("app.sources.http.asyncio.sleep", AsyncMock())

    with pytest.raises(TransientSourceFetchException) as exc_info:
        await request_json(
            client,
            'GET',
            URL,
            source_name='linkedin',
            attempts=1
        )

    exc = exc_info.value

    assert exc.source_name == 'linkedin'
    assert isinstance(exc.cause, httpx.HTTPStatusError)
    assert exc.__cause__ is exc.cause

    


