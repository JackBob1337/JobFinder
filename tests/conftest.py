import pytest
import os 


os.environ.setdefault(
    'DATABASE_URL',
    "postgresql+asyncpg://test:test@localhost:5432/test_db",
)