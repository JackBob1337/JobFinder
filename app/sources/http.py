import asyncio

import httpx

from app.exceptions.exceptions import (
    SourceFetchException,
    TransientSourceFetchException,
    InvalidSourcePayloadException
)

TRANSIENT_STATUSES = {408, 425, 429, 500, 502, 503, 504}


async def request_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    source_name: str,
    attempts: int,
    **kwargs,
) -> object:
    for attempt in range(1, attempts + 1):
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            transient = exc.response.status_code in TRANSIENT_STATUSES

            if not transient:
                raise SourceFetchException(source_name, exc) from exc
            
            if attempt == attempts:
                raise TransientSourceFetchException(
                    source_name, exc
                ) from exc
            
        except httpx.TransportError as exc:
            if attempt == attempts:
                raise TransientSourceFetchException(
                    source_name, exc
                ) from exc
            
        else:
            try:
                return response.json()

            except ValueError as exc:
                raise InvalidSourcePayloadException(
                    source_name, exc
                ) from exc

        await asyncio.sleep(0.25 ** 2 ** (attempt - 1))

    raise AssertionError('unreachable')