import socket
from pathlib import Path
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import Base


def _sqlite_path() -> Path:
    return Path(__file__).resolve().parents[2] / "repost_ai.db"


def _sqlite_url() -> str:
    return f"sqlite+aiosqlite:///{_sqlite_path()}"


def is_postgres_responsive() -> bool:
    try:
        with socket.create_connection(("localhost", 5432), timeout=1):
            return True
    except OSError:
        return False


def create_engine_from_settings():
    settings = get_settings()
    db_url = settings.database_url

    # Self-healing local dev fallback: if Postgres is unreachable, fall back to SQLite
    if "localhost:5432" in db_url and not is_postgres_responsive():
        db_url = _sqlite_url()

    return create_async_engine(db_url, pool_pre_ping=True)


def _make_session_factory(eng):
    return async_sessionmaker(eng, expire_on_commit=False)


def _switch_to_sqlite():
    """Replace the module-level engine and session factory with a SQLite-backed one."""
    global engine, AsyncSessionLocal
    engine = create_async_engine(_sqlite_url(), pool_pre_ping=True)
    AsyncSessionLocal = _make_session_factory(engine)


engine = create_engine_from_settings()
AsyncSessionLocal = _make_session_factory(engine)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except Exception:
        if "postgresql" in str(engine.url):
            _switch_to_sqlite()
            async with AsyncSessionLocal() as session:
                yield session
        else:
            raise


async def init_db() -> None:
    """Create all tables, falling back to SQLite if Postgres auth/connection fails."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        if "postgresql" in str(engine.url):
            _switch_to_sqlite()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            raise
