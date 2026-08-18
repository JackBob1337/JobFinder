import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_are_created_from_environment(monkeypatch):
    monkeypatch.setenv(
        'DATABASE_URL',
        'postgresql+asyncpg://env_user:env_password@localhost:5432/env_db',
    )
    monkeypatch.setenv('OPENAI_API_KEY', 'env-openai-key')
    monkeypatch.setenv('APIFY_API_TOKEN', 'env-apify-token')

    settings = Settings(_env_file=None)

    assert settings.database_url.endswith('/env_db')
    assert settings.openai_api_key == 'env-openai-key'
    assert settings.apify_api_token == 'env-apify-token'

def test_database_url_is_required(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('APIFY_API_TOKEN', raising=False)

    with pytest.raises(ValidationError) as error:
        Settings(
            _env_file=None,
            openai_api_key='test-openai',
            apify_api_token='test-apify',
        )

    assert 'database_url' in str(error.value)

def test_application_config_imports_without_provider_keys(tmp_path):
    project_root = Path(__file__).resolve().parents[1]

    environment = os.environ.copy()
    environment['DATABASE_URL'] = (
        'postgresql+asyncpg://test:test@localhost:5432/test_db'
    )
    environment.pop('OPENAI_API_KEY', None)
    environment.pop('APIFY_API_TOKEN', None)

    current_pythonpath = environment.get('PYTHONPATH', '')
    environment['PYTHONPATH'] = (
        str(project_root)
        + os.pathsep
        + current_pythonpath
    )

    result = subprocess.run(
        [
            sys.executable,
            '-c',
            "import app.core.config; print('config_import_ok')",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, result.stderr
    assert 'config_import_ok' in result.stdout