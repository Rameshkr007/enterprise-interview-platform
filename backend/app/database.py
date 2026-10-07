from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _build_engine(test_mode: bool = False) -> AsyncEngine:
    kwargs: dict = {
        "echo": settings.DB_ECHO,
        "future": True,
    }
    if test_mode:
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_size"] = settings.DB_POOL_SIZE
        kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
        kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 3600

    return create_async_engine(str(settings.DATABASE_URL), **kwargs)


engine: AsyncEngine = _build_engine()

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_database_health() -> bool:
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False


async def dispose_engine() -> None:
    await engine.dispose()
