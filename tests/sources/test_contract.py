import inspect
from typing import get_type_hints
from pydantic import ValidationError

import pytest

from app.schemas.raw_job import RawJob
from app.sources.arbeitnow import ArbeitnowSource
from app.sources.justjoinit import JustJoinItSource
from app.sources.nofluffjobs import NoFluffJobsSource

from tests.unit.test_schemas import make_raw_job

ADAPTERS = (ArbeitnowSource, JustJoinItSource, NoFluffJobsSource)

@pytest.mark.parametrize('adapter_cls', ADAPTERS)
def test_adapter_contract(adapter_cls):
    assert isinstance(adapter_cls.name, str )
    assert adapter_cls.name.strip()
    assert list(inspect.signature(adapter_cls.fetch_jobs).parameters) == [
        'self'
    ]
    assert get_type_hints(adapter_cls.fetch_jobs)['return'] == list[RawJob]


@pytest.mark.parametrize('field', ['title', 'company', 'description'])
@pytest.mark.parametrize('value', ['', ' '])
def test_required_text_rejects_blank(field, value):
    with pytest.raises(ValidationError):
        make_raw_job(**{field: value})


@pytest.mark.parametrize('url', ['bad-url', '/jobs/1', 'ftp://example.com/job'])
def test_raw_job_rejects_bad_url(url):
    with pytest.raises(ValidationError):
        make_raw_job(url=url)
