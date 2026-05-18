"""Shared async DB engine and session factory (one pool per bot process)."""

from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from config.settings import Settings
from db.session import create_engine, create_session_factory

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def database_enabled(settings: Settings) -> bool:
    return bool(settings.database_url)


async def init_database(settings: Settings) -> None:
    global _engine, _session_factory
    if not settings.database_url:
        return
    if _engine is not None:
        return
    _engine = create_engine(settings)
    _session_factory = create_session_factory(_engine)


async def close_database() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Database is not initialized — call init_database() at startup")
    return _session_factory
