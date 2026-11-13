"""Database engine and session management for the IPC-BNS transition platform.

SQLAlchemy 2.0-style setup. The database URL is taken from the ``DATABASE_URL``
environment variable and defaults to a local SQLite file under ``data/``.

SQLite specifics handled here:
- ``check_same_thread=False`` so the engine can be shared across FastAPI
  worker threads.
- In-memory SQLite URLs (``sqlite://`` / ``sqlite:///:memory:``) are pinned to
  a :class:`~sqlalchemy.pool.StaticPool` so every session sees the same
  database — essential for tests.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

DEFAULT_DATABASE_URL = "sqlite:///./data/ipc_bns.db"

_IN_MEMORY_SQLITE_URLS = {"sqlite://", "sqlite:///:memory:"}


class Base(DeclarativeBase):
    """Declarative base for all ORM models in the platform."""


def get_database_url() -> str:
    """Return the configured database URL (env var or default)."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_db_engine(url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine for the given (or configured) URL.

    Args:
        url: Explicit database URL. Falls back to ``DATABASE_URL`` env var,
            then to :data:`DEFAULT_DATABASE_URL`.

    Returns:
        A configured :class:`~sqlalchemy.engine.Engine`.
    """
    resolved = url or get_database_url()
    connect_args: dict[str, Any] = {}
    engine_kwargs: dict[str, Any] = {}

    if resolved.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if resolved in _IN_MEMORY_SQLITE_URLS:
            # Keep a single shared connection so all sessions see the same
            # in-memory database (used by the test suite).
            engine_kwargs["poolclass"] = StaticPool

    return create_engine(resolved, connect_args=connect_args, **engine_kwargs)


# Session factory. Not bound at import time — bind per call so tests can
# supply their own engines. ``expire_on_commit=False`` keeps loaded objects
# usable after the session commits/closes.
SessionLocal = sessionmaker(
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)

_engine: Engine | None = None


def get_engine() -> Engine:
    """Return the process-wide default engine, creating it lazily."""
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


def reset_engine() -> None:
    """Dispose of the cached default engine (mainly for tests)."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def get_db(engine: Engine | None = None) -> Generator[Session, None, None]:
    """Yield a database session; usable as a FastAPI dependency.

    Args:
        engine: Optional engine override; defaults to :func:`get_engine`.
    """
    session = SessionLocal(bind=engine or get_engine())
    try:
        yield session
    finally:
        session.close()
