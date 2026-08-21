import httpx
import pytest

from unittest.mock import AsyncMock

from app.sources.http import request_json

URL = "https://example.com/jobs"

@pytest.mark.asyncio
async def test_503_then_200_reties_once(monkeypatch):
    client = AsyncMock(spec=httpx.AsyncClient)
    request = httpx.Request('GET', URL)

    client.request.side_effect = [
        httpx.Response(503, request=request),
        httpx.Response(200, json={"jobs": []}, request=request),
    ]

    monkeypatch.setattr('app.sources.http.asyncio.sleep', AsyncMock())

    result = await request_json(
        client,
        'GET',
        URL,
        source_name='test',
        attempts=3
    )

    assert result == {'jobs': []}
    assert client.request.call_count == 2


@pytest.mark.asyncio
async def test_transport_error_reties(monkeypatch):
    client = AsyncMock(spec=httpx.AsyncClient)
    request = httpx.Request('GET', URL)

    client.request.side_effect = [
        httpx.ConnectTimeout('timeout', request=request),
        httpx.Response(200, json={"jobs": []}, request=request),
    ]

    monkeypatch.setattr('app.sources.http.asyncio.sleep', AsyncMock())
    
    result = await request_json(
        client,
        'GET',
        URL,
        source_name='test',
        attempts=3
    )

    assert result == {'jobs': []}
    assert client.request.call_count == 2
    