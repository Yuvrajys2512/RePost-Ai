import asyncio
import pytest

from app.db.session import init_db


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """Session-scoped fixture to automatically create and synchronize database tables on test startup."""
    asyncio.run(init_db())
