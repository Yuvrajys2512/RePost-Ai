import socket
from pathlib import Path
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import Base


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
        sqlite_path = Path(__file__).resolve().parents[2] / "repost_ai.db"
        db_url = f"sqlite+aiosqlite:///{sqlite_path}"

    return create_async_engine(db_url, pool_pre_ping=True)


engine = create_engine_from_settings()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

