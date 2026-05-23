import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models import Base


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """
    Session-scoped fixture that bootstraps a fresh in-memory SQLite database
    for testing, bypassing any Postgres connection requirement.
    All tables are created from the current metadata (always fresh schema).
    """
    import app.db.session as session_module

    # Override the engine and session factory with an in-memory SQLite instance
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", pool_pre_ping=True)
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def _setup():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_setup())

    # Patch module-level globals so the app uses the in-memory DB for tests
    session_module.engine = test_engine
    session_module.AsyncSessionLocal = test_session_factory
